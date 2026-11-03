"""Talks to a local Ollama model. Recreates the workflow of a senior consultant building a deck:

Deck level
  plan_deck()  read the source, write a storyline and choose a DIFFERENT visual for each slide
Slide level (quality="best")
  1. plan      free-text notes: the one message, how to split content, taglines, facts to use
  2. write     JSON constrained by the layout schema, guided by a worked example of that layout
  3. check     code checks (quality.py): word limits, sentence case, buzzwords, invented numbers,
               duplicates, and TEXT OVERFLOW estimated from the actual rendered layout
  4. review    a partner-style critique (score 1-5 + specific issues) of the slide JSON
  5. look      optional: a vision model reviews the rendered slide image for clutter and overflow
  6. refine    the model fixes exactly the issues found; repeat until clean (max 3 rounds)
quality="fast" does steps 2-3 only, with code auto-fixes.
"""
import base64
import json
from pydantic import ValidationError
from ollama import Client

from schemas import LAYOUTS, Route, DeckPlan, Critique
from examples import EXAMPLES
from quality import autofix, check

STYLE = """You are a senior consultant writing executive slides for a Big 4 firm.
Write like this:
- Sentence case everywhere (only the first word and proper nouns capitalised).
- Titles state the takeaway or the topic crisply; subtitles add the 'so what'.
- Short, concrete, parallel phrases. Start bullets with a verb or a noun, never with "To" or "We will".
- Each column/card/step makes ONE distinct point; no repetition across them.
- Taglines are a crisp promise (e.g. "Fix at estate level, not asset by asset"), not a restated header.
- Outcome lines say what changes for the client, in plain words.
- Use only facts, numbers, dates and names from the source or the user's message. Never invent figures.
- No buzzwords (leverage, synergy, seamless, robust, holistic, unlock, empower, cutting-edge, best-in-class).
- Respect every word limit in the schema descriptions. Shorter is better.
- Pick icons from the allowed list whose meaning fits best."""

LAYOUT_GUIDE = """Available layouts (choose the one whose SHAPE matches the content):
- cover: dark title page.
- columns: 3-5 phases, workstreams or pillars side by side; bullets, a green panel, an outcome line, a dark milestone/example box.
- flow: 3-7 numbered process steps on a connected line, with an optional loop-back and an exception branch.
- timeline: Gantt chart over months/quarters with milestones and up to two side boxes.
- stack: 2-4 layers from foundation to top (what exists today, the gap, what we add), optional before/after pairs and a callout.
- hub: one central outcome with 4 spokes (e.g. Assess/Design/Implement/Validate) plus a dark panel of tiles and stats.
- comparison: today vs future (or A vs B) rows with arrows and a highlight box.
- quad: 'A + B' building blocks feeding four outcomes in a 2x2 around a centre (value propositions, joint offers).
- grid: 3-6 icon cards (reasons, benefits, principles).
- closing: thank-you page."""

REVIEW = """You are a Big 4 partner reviewing a slide before it goes to a client executive.
Score it 1-5 (5 = ready to send) and list specific, fixable issues. Check:
- Does the title land one clear message? Is the subtitle the 'so what'?
- Is every element distinct and parallel in form? Any repetition or filler?
- Are taglines and outcomes sharp and specific, not generic?
- Is the content faithful to the source (no invented numbers or claims)?
- Is anything too long to read at a glance?
Name the field in each issue (e.g. 'columns[2].tagline restates the header')."""

VISUAL = """You are reviewing the rendered slide image. List specific problems only:
text that overflows or overlaps, boxes that look crowded or empty, unbalanced columns,
hard-to-read text. Quote the text involved. If it looks clean, return no issues."""


class LLM:
    def __init__(self, model="qwen2.5:14b", host="http://localhost:11434", temperature=0.2, num_ctx=16384,
                 quality="best", vision_model=None, render_png=None):
        self.model = model
        self.client = Client(host=host)
        self.options = {"temperature": temperature, "num_ctx": num_ctx}
        self.quality = quality
        self.vision_model = vision_model          # e.g. "gemma3:27b" or "qwen2.5vl:7b"; None to skip
        self.render_png = render_png              # callable(slide_dict) -> PNG bytes or None
        self.log = []

    # ---- low level ------------------------------------------------------------------
    def _chat(self, messages, schema=None, temperature=None, model=None):
        opts = dict(self.options)
        if temperature is not None:
            opts["temperature"] = temperature
        kw = {"format": schema} if schema else {}
        resp = self.client.chat(model=model or self.model, messages=messages, options=opts, **kw)
        return resp.message.content

    def _ask(self, schema_model, messages, retries=2, model=None):
        last_err = None
        for _ in range(retries + 1):
            raw = self._chat(messages, schema=schema_model.model_json_schema(), model=model)
            try:
                return schema_model.model_validate_json(raw)
            except ValidationError as e:
                last_err = e
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"That JSON was invalid: {e.errors()[:3]}. Return corrected JSON only."},
                ]
        raise RuntimeError(f"Model did not return valid JSON: {last_err}")

    @staticmethod
    def _example_turns(layout):
        ex = EXAMPLES.get(layout)
        if not ex:
            return []
        return [
            {"role": "user", "content": f"Example request. Source:\n{ex['source']}\n\nWrite one '{layout}' slide."},
            {"role": "assistant", "content": json.dumps(ex["slide"], ensure_ascii=False)},
        ]

    # ---- routing and deck planning ------------------------------------------------------
    def route(self, user_msg, deck_outline, has_source, has_plan=False):
        msgs = [
            {"role": "system", "content": "You are a slide-building assistant. Decide what to do with the user's message.\n" + LAYOUT_GUIDE +
             "\nActions: plan_deck = propose a storyline for a whole deck (use when the user asks for a deck, several slides, or 'slides from this document');"
             " build_plan = build all slides of the proposed plan (use when the user approves the plan, e.g. 'build it', 'go ahead');"
             " add_slide = create one slide; edit_slide = change one slide (needs slide_number); delete_slide = remove one; answer = questions or chat."},
            {"role": "user", "content": f"Current deck:\n{deck_outline or '(empty)'}\n\nSource document loaded: {has_source}\nA deck plan is waiting for approval: {has_plan}\n\nUser message: {user_msg}"},
        ]
        return self._ask(Route, msgs)

    def plan_deck(self, user_msg, source_text, prior=None):
        if prior:
            msgs = [
                {"role": "system", "content": STYLE + "\n\n" + LAYOUT_GUIDE},
                {"role": "user", "content": f"Here is the current deck plan:\n{json.dumps(prior, ensure_ascii=False, indent=1)}\n\n"
                 f"Revise it as requested, keeping everything else: {user_msg}\n\nSource:\n{source_text[:20000]}"},
            ]
            return self._ask(DeckPlan, msgs).model_dump()
        msgs = [
            {"role": "system", "content": STYLE + "\n\n" + LAYOUT_GUIDE},
            {"role": "user", "content": (
                "Plan an executive deck from the source. First read it and work out the storyline: what the audience must believe by the end, "
                "and the logical order (context and problem, approach, how it works, proof and plan, value). Then assign each slide the layout whose "
                "shape fits its content. Use a VARIETY of layouts: do not use the same content layout more than twice, and do not default to "
                "process columns. Start with a cover and end with a closing slide.\n\n"
                f"User request: {user_msg}\n\nSource:\n{source_text[:30000]}")},
        ]
        plan = self._ask(DeckPlan, msgs)
        return plan.model_dump()

    # ---- slide pipeline -----------------------------------------------------------------
    def plan(self, layout, user_msg, source_text, deck_outline):
        msgs = [
            {"role": "system", "content": STYLE},
            {"role": "user", "content": (
                f"Plan one '{layout}' slide before writing it. Do not write JSON.\n"
                f"Request: {user_msg}\n\nOther slides already in the deck (do not repeat them):\n{deck_outline or '(none)'}\n\n"
                f"Source document:\n{source_text[:24000] or '(none)'}\n\n"
                "Write brief notes:\n"
                "1. The single message this slide must land (one sentence) and a crisp title.\n"
                "2. How to split the content into the layout's parts, in order, and why.\n"
                "3. For each part: the exact facts from the source to use, a crisp tagline, and the outcome.\n"
                "4. Any numbers or dates from the source worth showing (quote them exactly).")},
        ]
        return self._chat(msgs, temperature=0.4)

    def review(self, slide, source_text):
        msgs = [{"role": "system", "content": REVIEW},
                {"role": "user", "content": f"Slide JSON:\n{json.dumps(slide, ensure_ascii=False, indent=1)}\n\nSource:\n{source_text[:12000] or '(none)'}"}]
        return self._ask(Critique, msgs)

    def look(self, slide):
        if not (self.vision_model and self.render_png):
            return None
        png = self.render_png(slide)
        if not png:
            return None
        msgs = [{"role": "system", "content": VISUAL},
                {"role": "user", "content": "Review this slide.", "images": [base64.b64encode(png).decode()]}]
        return self._ask(Critique, msgs, model=self.vision_model)

    def _refine(self, model, slide, issues, source_text):
        msgs = [
            {"role": "system", "content": STYLE + "\nYou are fixing a slide. Change only what the issues require; keep everything else."},
            {"role": "user", "content": f"Slide JSON:\n{json.dumps(slide, ensure_ascii=False, indent=1)}\n\nFix these issues:\n- " + "\n- ".join(issues[:20]) +
             f"\n\nSource (for facts):\n{source_text[:12000] or '(none)'}"},
        ]
        return model.model_validate(autofix(self._ask(model, msgs).model_dump())).model_dump()

    def _polish(self, model, slide, source_text):
        slide = autofix(slide)
        rounds = 3 if self.quality == "best" else 1
        for rnd in range(rounds):
            issues = check(slide, source_text)
            tag = f"round {rnd + 1}: {len(issues)} rule issue(s)"
            if self.quality == "best":
                crit = self.review(slide, source_text)
                if crit.score < 5:
                    issues += crit.issues
                tag += f", review {crit.score}/5"
                vis = self.look(slide)
                if vis is not None:
                    issues += vis.issues
                    tag += f", visual {len(vis.issues)} issue(s)"
            self.log.append(tag)
            if not issues or self.quality != "best" or rnd == rounds - 1:
                break
            slide = self._refine(model, slide, issues, source_text)
        return slide

    def generate(self, layout, user_msg, source_text="", deck_outline=""):
        self.log = []
        model = LAYOUTS[layout]
        notes = ""
        if self.quality == "best" and layout not in ("closing",):
            notes = self.plan(layout, user_msg, source_text, deck_outline)
            self.log.append("plan written")
        msgs = [{"role": "system", "content": STYLE}] + self._example_turns(layout) + [
            {"role": "user", "content": (
                f"Write one '{layout}' slide, matching the quality, tone and length of the example.\n"
                f"Request: {user_msg}\n\nOther slides in the deck (avoid repeating them):\n{deck_outline or '(none)'}\n\n"
                + (f"Your plan:\n{notes}\n\n" if notes else "")
                + f"Source document:\n{source_text[:24000] or '(none provided; use only the request)'}")},
        ]
        slide = self._ask(model, msgs).model_dump()
        self.log.append("slide written")
        if layout == "closing":
            return slide
        return self._polish(model, slide, source_text + "\n" + user_msg)

    def edit(self, slide, user_msg, source_text=""):
        self.log = []
        model = LAYOUTS[slide["layout"]]
        msgs = [{"role": "system", "content": STYLE + "\nYou are editing an existing slide. Change only what the instruction asks; keep everything else identical."}] \
            + self._example_turns(slide["layout"]) + [
            {"role": "user", "content": f"Current slide JSON:\n{json.dumps(slide, ensure_ascii=False, indent=1)}\n\nInstruction: {user_msg}\n\nSource document (for reference):\n{source_text[:12000] or '(none)'}"},
        ]
        new = self._ask(model, msgs).model_dump()
        self.log.append("slide edited")
        return self._polish(model, new, source_text + "\n" + user_msg + "\n" + json.dumps(slide))


def outline(deck):
    """One line per slide, used to give the model context cheaply."""
    lines = []
    for i, d in enumerate(deck, 1):
        t = d.get("title", "")
        extra = ""
        if d["layout"] == "columns":
            extra = ": " + ", ".join(c["header"] for c in d["columns"])
        elif d["layout"] == "grid":
            extra = ": " + ", ".join(c["title"] for c in d["cards"])
        elif d["layout"] == "flow":
            extra = ": " + ", ".join(c["title"] for c in d["steps"])
        lines.append(f"{i}. [{d['layout']}] {t}{extra}")
    return "\n".join(lines)


def plan_text(plan):
    lines = [f"**Storyline:** {plan['storyline']}", ""]
    for i, p in enumerate(plan["slides"], 1):
        lines.append(f"{i}. **{p['title']}** `{p['layout']}`: {p['message']}")
    lines.append("")
    lines.append("Say **build it** to create all slides, or tell me what to change (e.g. 'make slide 4 a comparison').")
    return "\n".join(lines)
