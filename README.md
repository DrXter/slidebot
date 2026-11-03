# SlideBot

A local chat assistant that turns your documents into branded, consulting-style slides.

You chat with it ("turn the phases into a columns slide", "add a delivery timeline", "shorten slide 2"),
a **local Ollama model** writes the slide content as structured JSON, and a **python-pptx renderer**
lays it out in a fixed design (Deloitte green/black palette, Open Sans, wordmark footer).
Nothing leaves your machine.

```
 you ──chat──▶ Streamlit app ──▶ Ollama (route: add / edit / delete / answer)
                                   │
                                   ▼
                      Ollama structured output (JSON matching schemas.py)
                                   │
                                   ▼
                      renderer.py  ──▶  deck.pptx  ──▶ preview + download
```

## Slide layouts

| Layout | Use for |
|---|---|
| `cover` | Dark title page with the square-grid motif |
| `columns` | 3-5 phases, workstreams or pillars: chevron headers, bullets, green panel, outcome line, dark milestone/example box, two banners |
| `timeline` | Gantt chart over months or quarters, numbered milestones, up to two side boxes |
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
2. Ask for slides in plain language:
   - "Create a cover: Configuration Assurance Programme, prepared for Example Client"
   - "Turn the five phases into a columns slide with milestones in the dark boxes"
   - "Add a timeline from Nov to Jun with the workstreams and milestones"
   - "Make a grid slide of the four acceleration reasons"
   - "Shorten the bullets on slide 2" / "Delete slide 3" / "Add a closing slide"
3. Check the preview, tweak any slide's JSON directly with **Edit JSON**, use **Undo** if needed.
4. **Download PowerPoint**. You can also save and reload the deck as JSON.

## How it keeps quality up

In **Best** mode (sidebar, default) every new or edited slide goes through:

1. **Plan**: the model first writes free-text notes: the single message, how to split the content, taglines, facts to use.
2. **Write**: JSON constrained by the layout schema, guided by a worked example of the same layout (`examples.py`).
3. **Check** (`quality.py`, in code): word limits per field, sentence case, buzzwords, numbers not found in the source, duplicates, uneven columns.
4. **Refine**: the model fixes exactly the flagged issues (up to two rounds).

The steps taken are shown under each reply, e.g. `plan written > slide written > check 1: 3 issue(s) > check 2: 0 issue(s)`.
**Fast** mode skips planning and refining.

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
| `llm.py` | Ollama calls: route, generate, edit (structured outputs) |
| `examples.py` | Worked examples per layout (few-shot) |
| `quality.py` | Code-level quality checks and auto-fixes |
| `schemas.py` | Pydantic models for each layout (also the JSON schemas sent to Ollama) |
| `renderer.py` | JSON → .pptx layouts and brand tokens |
| `icons/` | Icon PNGs (white, dark, green) |
| `sample_deck.json` | Example deck covering every layout |

Icons are from Font Awesome Free (CC BY 4.0), rendered to PNG via react-icons.
