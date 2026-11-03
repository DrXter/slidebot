"""Talks to a local Ollama model using structured outputs.

Three jobs:
  route()    decide what the user wants (add / edit / delete a slide, or just answer)
  generate() write a new slide of a given layout from the user's request + source document
  edit()     rewrite an existing slide according to the user's instruction
Each call passes a JSON schema via `format`, so Ollama can only return valid slide data.
"""
import json
from pydantic import ValidationError
from ollama import Client

from schemas import LAYOUTS, Route

STYLE = """You write content for executive consulting slides.
Rules:
- Sentence case. Short, concrete phrases. No filler, no marketing fluff.
- Respect every length limit in the schema descriptions; shorter is better.
- Use only facts from the source document or the user's message. Never invent numbers, dates, client names or claims.
- Keep the user's terminology and spelling.
- Icons must be chosen from the allowed list; pick the closest meaning."""

LAYOUT_GUIDE = """Available layouts:
- cover: title page (dark).
- columns: 3-5 phases, workstreams or pillars side by side, each with bullets, a green panel, an outcome line and a dark box (milestone or example). Use for phase approaches and workstreams.
- timeline: Gantt chart over periods (months/quarters) with milestones and up to two side boxes.
- grid: 3-6 icon cards (benefits, reasons, pillars, principles).
- closing: thank-you page."""


class LLM:
    def __init__(self, model="qwen2.5:14b", host="http://localhost:11434", temperature=0.2):
        self.model = model
        self.client = Client(host=host)
        self.options = {"temperature": temperature, "num_ctx": 16384}

    def _ask(self, schema_model, messages, retries=2):
        last_err = None
        for _ in range(retries + 1):
            resp = self.client.chat(model=self.model, messages=messages,
                                    format=schema_model.model_json_schema(), options=self.options)
            raw = resp.message.content
            try:
                return schema_model.model_validate_json(raw)
            except ValidationError as e:
                last_err = e
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"That JSON was invalid: {e.errors()[:3]}. Return corrected JSON only."},
                ]
        raise RuntimeError(f"Model did not return valid JSON: {last_err}")

    def route(self, user_msg, deck_outline, has_source):
        msgs = [
            {"role": "system", "content": "You are a slide-building assistant. Decide what to do with the user's message.\n" + LAYOUT_GUIDE +
             "\nUse add_slide to create a slide, edit_slide to change an existing one (needs slide_number), delete_slide to remove one, answer for questions or chat."},
            {"role": "user", "content": f"Current deck:\n{deck_outline or '(empty)'}\n\nSource document loaded: {has_source}\n\nUser message: {user_msg}"},
        ]
        return self._ask(Route, msgs)

    def generate(self, layout, user_msg, source_text="", deck_outline=""):
        model = LAYOUTS[layout]
        src = source_text[:24000]
        msgs = [
            {"role": "system", "content": STYLE},
            {"role": "user", "content": f"Create one '{layout}' slide.\n\nRequest: {user_msg}\n\nOther slides in the deck (avoid repeating them):\n{deck_outline or '(none)'}\n\nSource document:\n{src or '(none provided; use only the request)'}"},
        ]
        return self._ask(model, msgs).model_dump()

    def edit(self, slide, user_msg, source_text=""):
        model = LAYOUTS[slide["layout"]]
        msgs = [
            {"role": "system", "content": STYLE + "\nYou are editing an existing slide. Change only what the instruction asks; keep everything else identical."},
            {"role": "user", "content": f"Current slide JSON:\n{json.dumps(slide, indent=1)}\n\nInstruction: {user_msg}\n\nSource document (for reference):\n{source_text[:12000] or '(none)'}"},
        ]
        return self._ask(model, msgs).model_dump()


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
