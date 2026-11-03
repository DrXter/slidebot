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

## Choosing a model

| Model | Notes |
|---|---|
| `qwen2.5:14b` (default) | Best balance of quality and JSON reliability; needs ~10 GB RAM/VRAM |
| `qwen2.5:7b` / `llama3.1:8b` | Lighter; more editing needed |
| `qwen2.5:32b` | Better condensing of long documents; needs a larger GPU |

The app retries automatically if the model returns invalid JSON.

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
| `schemas.py` | Pydantic models for each layout (also the JSON schemas sent to Ollama) |
| `renderer.py` | JSON → .pptx layouts and brand tokens |
| `icons/` | Icon PNGs (white, dark, green) |
| `sample_deck.json` | Example deck covering every layout |

Icons are from Font Awesome Free (CC BY 4.0), rendered to PNG via react-icons.
