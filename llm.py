"""Talks to a local Ollama model.

Pipeline for a new slide (quality="best"):
  1. plan    - free-text storyline: what goes where, strongest message, taglines (models write better after thinking)
  2. write   - JSON constrained by the layout schema, guided by a worked example of the same layout
  3. check   - code checks (quality.py): word limits, sentence case, buzzwords, invented numbers, duplicates
  4. refine  - the model fixes exactly the flagged issues (up to 2 rounds)
quality="fast" skips steps 1 and 4.
"""
import json
from pydantic import ValidationError
from ollama import Client

from schemas import LAYOUTS, Route
from examples import EXAMPLES
from quality import autofix, check

STYLE = """You are a senior consultant writing executive slides for a Big 4 firm.
Write like this:
- Sentence case everywhere (only the first word and proper nouns capitalised).
- Short, concrete, parallel phrases. Start bullets with a verb or a noun, never with "To" or "We will".
- Each column/card makes ONE distinct point; no repetition across columns.
- Taglines are a crisp promise (e.g. "Fix at estate level, not asset by asset"), not a restated header.
- Outcome lines say what changes for the client, in plain words.
- Use only facts, numbers, dates and names from the source or the user's message. Never invent figures.
- No buzzwords (leverage, synergy, seamless, robust, holistic, unlock, empower, cutting-edge, best-in-class).
- Respect every word limit in the schema descriptions. Shorter is better.
- Pick icons from the allowed list whose meaning fits best."""

LAYOUT_GUIDE = """Available layouts:
- cover: dark title page.
- columns: 3-5 phases, workstreams or pillars side by side, each with bullets, a green panel, an outcome line and a dark box (milestone or example). Use for phase approaches and workstreams.
- timeline: Gantt chart over periods (months/quarters) with milestones and up to two side boxes.
- grid: 3-6 icon cards (benefits, reasons, pillars, principles).
- closing: thank-you page."""


class LLM:
    def __init__(self, model="qwen2.5:14b", host="http://localhost:11434", temperature=0.2, num_ctx=16384, quality="best"):
        self.model = model
        self.client = Client(host=host)
        self.options = {"temperature": temperature, "num_ctx": num_ctx}
        self.quality = quality
        self.log = []          # last pipeline steps, shown in the UI

    # ---- low level ----------------------------------------------------------------
    def _chat(self, messages, schema=None, temperature=None):
        opts = dict(self.options)
        if temperature is not None:
            opts["temperature"] = temperature
        kw = {"format": schema} if schema else {}
        resp = self.client.chat(model=self.model, messages=messages, options=opts, **kw)
        return resp.message.content

    def _ask(self, schema_model, messages, retries=2):
        last_err = None
        for _ in range(retries + 1):
            raw = self._chat(messages, schema=schema_model.model_json_schema())
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

    # ---- jobs -----------------------------------------------------------------------
    def route(self, user_msg, deck_outline, has_source):
        msgs = [
            {"role": "system", "content": "You are a slide-building assistant. Decide what to do with the user's message.\n" + LAYOUT_GUIDE +
             "\nUse add_slide to create a slide, edit_slide to change an existing one (needs slide_number), delete_slide to remove one, answer for questions or chat."},
            {"role": "user", "content": f"Current deck:\n{deck_outline or '(empty)'}\n\nSource document loaded: {has_source}\n\nUser message: {user_msg}"},
        ]
        return self._ask(Route, msgs)

    def plan(self, layout, user_msg, source_text, deck_outline):
        msgs = [
            {"role": "system", "content": STYLE},
            {"role": "user", "content": (
                f"Plan one '{layout}' slide before writing it. Do not write JSON.\n"
                f"Request: {user_msg}\n\nOther slides already in the deck (do not repeat them):\n{deck_outline or '(none)'}\n\n"
                f"Source document:\n{source_text[:24000] or '(none)'}\n\n"
                "Write brief notes:\n"
                "1. The single message this slide must land (one sentence) and an action-style title.\n"
                "2. How to split the content into columns/cards/rows, in order, and why.\n"
                "3. For each: the exact facts from the source to use, a crisp tagline, and the outcome.\n"
                "4. Any numbers or dates from the source worth showing (quote them exactly).")},
        ]
        return self._chat(msgs, temperature=0.4)

    def _refine(self, model, slide, issues, source_text):
        msgs = [
            {"role": "system", "content": STYLE + "\nYou are fixing a slide. Change only what the issues require; keep everything else."},
            {"role": "user", "content": f"Slide JSON:\n{json.dumps(slide, ensure_ascii=False, indent=1)}\n\nFix these issues:\n- " + "\n- ".join(issues[:20]) +
             f"\n\nSource (for facts):\n{source_text[:12000] or '(none)'}"},
        ]
        return model.model_validate(autofix(self._ask(model, msgs).model_dump())).model_dump()

    def _polish(self, model, slide, source_text):
        slide = autofix(slide)
        if self.quality != "best":
            return slide
        for rnd in range(2):
            issues = check(slide, source_text)
            self.log.append(f"check {rnd + 1}: {len(issues)} issue(s)" + (": " + "; ".join(i.split(':')[0] for i in issues[:6]) if issues else ""))
            if not issues:
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
        lines.append(f"{i}. [{d['layout']}] {t}{extra}")
    return "\n".join(lines)
