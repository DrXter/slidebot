# SlideBot

A local chat assistant that turns your documents into branded, consulting-style slides.

It works the way a senior consultant builds a deck: read the source, plan a storyline, pick the right
visual for each slide, write it, look at the result, and rework anything weak. A **local Ollama model**
does the thinking and writing; a **python-pptx renderer** owns the design (Deloitte green/black palette,
Open Sans, wordmark footer). Nothing leaves your machine.

```
 upload doc ─▶ "Plan a deck" ─▶ storyline + a different visual per slide ─▶ you approve ("build it")
                                                                                 │
   for each slide:  plan notes ─▶ write JSON (few-shot) ─▶ rule checks + overflow estimate
                         ▲                                     ─▶ partner-style review (score /5)
                         │                                     ─▶ optional vision review of the rendered image
                         └──────── refine until clean (max 3 rounds) ◀──────────┘
                                                                                 │
                                       renderer.py ─▶ deck.pptx ─▶ preview, edit by chat, download
```

## Slide layouts

| Layout | Use for |
|---|---|
| `cover` | Dark title page with the square-grid motif |
| `columns` | 3-5 phases, workstreams or pillars: chevron headers, bullets, green panel, outcome line, dark milestone/example box, two banners |
| `timeline` | Gantt chart over months or quarters, numbered milestones, up to two side boxes |
| `flow` | 3-7 numbered process steps on a connected line, with optional loop-back and exception branch |
| `stack` | Layers from foundation to top (today / the gap / what we add), before-after pairs, callout |
| `hub` | Central outcome with four spokes, plus a dark panel of tiles and headline stats |
| `comparison` | Today vs future (or A vs B) rows with arrows and a highlight box |
| `quad` | "A + B" building blocks feeding four outcomes in a 2x2 around a centre |
| `grid` | 3-6 icon cards (benefits, reasons, pillars) |
| `closing` | Thank-you page |

The model only writes content. All positions, colours and fonts live in `renderer.py`, so output stays on-brand.

## Install on RHEL 9 (also Rocky / Alma)

```bash
git clone https://github.com/DrXter/slidebot.git
cd slidebot
./setup_rhel.sh            # installs python3.11, Ollama, pulls qwen2.5:14b, creates .venv
./run.sh                   # starts on http://<host>:8501
```

Options: `PY=python3.12 ./setup_rhel.sh`, `MODEL=llama3.1:8b ./setup_rhel.sh`, `PORT=9000 ./run.sh`.

If the server has a firewall, open the port: `sudo firewall-cmd --add-port=8501/tcp --permanent && sudo firewall-cmd --reload`.

**Previews:** the app shows slide thumbnails when LibreOffice (`libreoffice-impress`) and `poppler-utils`
are installed. Without them it still builds and downloads the .pptx.

### Manual install (any OS)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:14b
streamlit run app.py
```

## Using it

1. Upload a source document in the sidebar (.docx, .pdf, .txt, .md).
2. **Plan the deck:** "Plan a deck from this document for the client's CISO".
   You get a storyline and a slide list, each with a different visual. Adjust it in chat
   ("make slide 4 a comparison", "add a timeline after slide 3"), then say **build it**.
3. Or work slide by slide:
   - "Add a flow slide on the remediation process with the exception branch"
   - "Turn the five phases into a columns slide with milestones in the dark boxes"
   - "Add a stack slide: SOC 2 today, the AI gap, what we add"
   - "Shorten the bullets on slide 2" / "Delete slide 3" / "Add a closing slide"
4. Check the preview, edit any slide's JSON directly with **Edit JSON**, use **Undo** if needed.
5. **Download PowerPoint**. You can also save and reload the deck as JSON.

## How it keeps quality up

In **Best** mode (sidebar, default) every new or edited slide goes through:

1. **Plan**: free-text notes first: the single message, how to split the content, taglines, facts to use.
2. **Write**: JSON constrained by the layout schema, guided by a worked example of the same layout (`examples.py`).
3. **Check** (`quality.py`, in code): word limits per field, sentence case, buzzwords, numbers not in the source,
   duplicates, uneven columns, and **text overflow** estimated by rendering the slide off-screen and measuring every text box.
4. **Review**: a partner-style critique scores the slide 1-5 and names specific weak fields.
5. **Look** (optional): a vision model (e.g. `gemma3:27b`, `qwen2.5vl:7b`) reviews the rendered image for overflow,
   clutter and balance. Pick it under "Visual review model"; needs LibreOffice.
6. **Refine**: the model fixes exactly the issues found; repeats until clean (max 3 rounds).

Each reply shows what happened, e.g. `plan written > slide written > round 1: 2 rule issue(s), review 4/5 > round 2: 0 rule issue(s), review 5/5`.
**Fast** mode does a single write with code auto-fixes.

To raise quality further, add your own best slides to `examples.py`: the model copies tone and length from examples more than from rules.

## Choosing a model

Content quality depends mostly on model size. The layout is identical whatever model you use.

| Model | Memory needed (approx.) | Notes |
|---|---|---|
| `qwen2.5:14b` (default) | 10 GB | Good JSON reliability; adequate writing |
| `qwen2.5:32b` / `qwen3:32b` | 20-24 GB | Clearly better condensing and taglines; recommended if you have the memory |
| `gemma3:27b` | 18 GB | Strong writing quality |
| `llama3.3:70b` | 43 GB | Closest to hosted-model quality; needs a large GPU or lots of RAM |
| `qwen2.5:7b` / `llama3.1:8b` | 5-6 GB | Fast, but expect more editing |

Switch models with `ollama pull <model>` and pick it in the sidebar. Use the 32k context window for long documents if you have the memory.

## Customising

- **Branding:** edit `BRAND` at the top of `renderer.py` (name, font, colours).
- **New layout:** add a pydantic model in `schemas.py`, a `render_<layout>` function in `renderer.py`,
  register both in `LAYOUTS` / `RENDERERS`, and describe it in `LAYOUT_GUIDE` in `llm.py`.
- **Writing style:** edit `STYLE` in `llm.py`.
- **Render without the UI:** `python renderer.py sample_deck.json out.pptx`

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit chat UI, deck state, previews, downloads |
| `llm.py` | Ollama calls: route, deck planning, plan/write/review/refine pipeline, vision review |
| `examples.py` | Worked examples per layout (few-shot) |
| `quality.py` | Code-level quality checks, overflow estimate and auto-fixes |
| `schemas.py` | Pydantic models for each layout (also the JSON schemas sent to Ollama) |
| `renderer.py` | JSON → .pptx layouts and brand tokens |
| `icons/` | Icon PNGs (white, dark, green) |
| `sample_deck.json` | Example deck covering every layout |

Icons are from Font Awesome Free (CC BY 4.0), rendered to PNG via react-icons.
