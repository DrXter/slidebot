"""SlideBot: a local chat assistant that builds branded slides.

Run:  streamlit run app.py
Needs Ollama running locally (ollama serve) with a model pulled (e.g. ollama pull qwen2.5:14b).
"""
import copy
import glob
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile

import streamlit as st

from llm import LLM, outline, plan_text
from renderer import render_deck
from schemas import LAYOUTS

st.set_page_config(page_title="SlideBot", layout="wide")

# Streamlit renamed use_container_width -> width="stretch" in newer releases; support both.
_ST_VER = tuple(int(x) for x in st.__version__.split(".")[:2])
FULL = {"width": "stretch"} if _ST_VER >= (1, 48) else {"use_container_width": True}


# ---------- helpers -------------------------------------------------------------
def read_source(upload):
    name = upload.name.lower()
    data = upload.getvalue()
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for r in t.rows:
                parts.append(" | ".join(c.text.strip() for c in r.cells))
        return "\n".join(parts)
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            st.error("Install pypdf to read PDFs: pip install pypdf")
            return ""
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    return data.decode("utf-8", errors="ignore")


@st.cache_data(show_spinner=False)
def previews(pptx_bytes):
    """Render slide thumbnails with LibreOffice if it is installed; otherwise return []."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "deck.pptx")
        open(src, "wb").write(pptx_bytes)
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, src],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        pdf = os.path.join(tmp, "deck.pdf")
        if not os.path.exists(pdf):
            return []
        if shutil.which("pdftoppm"):
            subprocess.run(["pdftoppm", "-png", "-r", "60", pdf, os.path.join(tmp, "p")], timeout=120)
            return [open(f, "rb").read() for f in sorted(glob.glob(os.path.join(tmp, "p-*.png")))]
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf)
            return [pg.get_pixmap(dpi=60).tobytes("png") for pg in doc]
        except ImportError:
            return []


def push_undo():
    st.session_state.undo.append(copy.deepcopy(st.session_state.deck))
    st.session_state.undo = st.session_state.undo[-20:]


def say(role, content):
    st.session_state.chat.append({"role": role, "content": content})


# ---------- state -----------------------------------------------------------------
for k, v in {"deck": [], "chat": [], "undo": [], "source": "", "source_name": "", "plan": None}.items():
    st.session_state.setdefault(k, v)

# ---------- sidebar -----------------------------------------------------------------
with st.sidebar:
    st.header("SlideBot")
    host = st.text_input("Ollama host", "http://localhost:11434")
    model_name = "qwen2.5:14b"
    try:
        from ollama import Client
        names = [m.model for m in Client(host=host).list().models]
        if names:
            model_name = st.selectbox("Model", names, index=names.index(model_name) if model_name in names else 0)
        else:
            st.warning("No models found. Run: ollama pull qwen2.5:14b")
    except Exception:
        st.error("Cannot reach Ollama. Start it with: ollama serve")
        model_name = st.text_input("Model", model_name)

    quality = "best" if st.radio("Quality", ["Best (plan, write, check, review, refine)", "Fast (single pass)"], index=0).startswith("Best") else "fast"
    vision_model = None
    try:
        vis_opts = ["(none)"] + names
    except NameError:
        vis_opts = ["(none)"]
    vsel = st.selectbox("Visual review model (optional)", vis_opts, index=0,
                        help="A vision model such as gemma3 or qwen2.5vl looks at each rendered slide and flags overflow or clutter. Needs LibreOffice.")
    if vsel != "(none)":
        vision_model = vsel
    num_ctx = st.select_slider("Context window (tokens)", options=[8192, 16384, 32768], value=16384,
                               help="Larger reads more of long documents but needs more memory")

    up = st.file_uploader("Source document", type=["docx", "txt", "md", "pdf"])
    if up and up.name != st.session_state.source_name:
        st.session_state.source = read_source(up)
        st.session_state.source_name = up.name
        say("assistant", f"Loaded **{up.name}** ({len(st.session_state.source):,} characters). Tell me what slides you want.")
    if st.session_state.source_name:
        st.caption(f"Source: {st.session_state.source_name}")

    c1, c2 = st.columns(2)
    if c1.button("Undo", **FULL) and st.session_state.undo:
        st.session_state.deck = st.session_state.undo.pop()
        say("assistant", "Undone.")
    if c2.button("Clear deck", **FULL):
        push_undo(); st.session_state.deck = []

    st.divider()
    st.download_button("Download deck JSON", json.dumps(st.session_state.deck, indent=1),
                       file_name="deck.json", mime="application/json", **FULL)
    jup = st.file_uploader("Load deck JSON", type=["json"], key="jup")
    if jup and st.button("Replace deck with this JSON", **FULL):
        try:
            data = json.loads(jup.getvalue())
            for d in data:
                LAYOUTS[d["layout"]].model_validate(d)
            push_undo(); st.session_state.deck = data
        except Exception as e:
            st.error(f"Invalid deck JSON: {e}")

def render_png(slide):
    imgs = previews(render_deck([slide]))
    return imgs[0] if imgs else None


llm = LLM(model=model_name, host=host, quality=quality, num_ctx=num_ctx, vision_model=vision_model, render_png=render_png)

# ---------- layout --------------------------------------------------------------------
left, right = st.columns([5, 6])

with left:
    st.subheader("Chat")
    box = st.container(height=560)
    for m in st.session_state.chat:
        box.chat_message(m["role"]).markdown(m["content"])
    prompt = st.chat_input("e.g. 'Plan a deck from this document', 'Add a comparison slide', 'Shorten slide 2'")

if prompt:
    say("user", prompt)
    deck = st.session_state.deck
    try:
        with st.spinner("Thinking..."):
            route = llm.route(prompt, outline(deck), bool(st.session_state.source), st.session_state.plan is not None)
        if route.action == "plan_deck":
            with st.spinner("Reading the source and planning the storyline..."):
                plan = llm.plan_deck(prompt, st.session_state.source, st.session_state.plan)
            st.session_state.plan = plan
            say("assistant", plan_text(plan))
        elif route.action == "build_plan" and st.session_state.plan:
            plan = st.session_state.plan
            push_undo()
            prog = st.progress(0.0, text="Building slides...")
            notes = []
            for n, p in enumerate(plan["slides"], 1):
                prog.progress((n - 1) / len(plan["slides"]), text=f"Slide {n}/{len(plan['slides'])}: {p['title']}")
                req = f"Title: {p['title']}. Message: {p['message']}. Content: {p['content']}. Deck storyline: {plan['storyline']}"
                slide = llm.generate(p["layout"], req, st.session_state.source, outline(deck))
                deck.append(slide)
                notes.append(f"{len(deck)}. {p['layout']}: `{' > '.join(llm.log)}`")
            prog.empty()
            st.session_state.plan = None
            say("assistant", f"Built {len(plan['slides'])} slides.\n\n" + "\n".join(notes) +
                "\n\nReview them on the right; ask me to change any slide by number.")
        elif route.action == "add_slide":
            layout = route.layout or "columns"
            with st.spinner(f"Writing a {layout} slide..."):
                slide = llm.generate(layout, prompt, st.session_state.source, outline(deck))
            push_undo()
            pos = route.slide_number - 1 if route.slide_number and 1 <= route.slide_number <= len(deck) + 1 else len(deck)
            deck.insert(pos, slide)
            say("assistant", f"{route.reply}\n\nAdded slide {pos + 1} ({layout}).\n\n`{' > '.join(llm.log)}`")
        elif route.action == "edit_slide":
            i = (route.slide_number or len(deck)) - 1
            if not 0 <= i < len(deck):
                say("assistant", "Which slide number should I change?")
            else:
                with st.spinner(f"Editing slide {i + 1}..."):
                    new = llm.edit(deck[i], prompt, st.session_state.source)
                push_undo(); deck[i] = new
                say("assistant", f"{route.reply}\n\nUpdated slide {i + 1}.\n\n`{' > '.join(llm.log)}`")
        elif route.action == "delete_slide":
            i = (route.slide_number or 0) - 1
            if 0 <= i < len(deck):
                push_undo(); deck.pop(i)
                say("assistant", f"Removed slide {i + 1}.")
            else:
                say("assistant", "Which slide number should I remove?")
        else:
            say("assistant", route.reply)
    except Exception as e:
        say("assistant", f"Something went wrong: `{e}`")
    st.rerun()

with right:
    st.subheader("Deck")
    deck = st.session_state.deck
    if not deck:
        st.info("No slides yet. Upload a source document, then ask: 'Plan a deck from this document'. "
                "I'll propose a storyline with a different visual per slide; say 'build it' to create them. "
                "You can also ask for single slides, e.g. 'Add a flow slide on the remediation process'.")
    else:
        pptx_bytes = render_deck(deck)
        st.download_button("Download PowerPoint", pptx_bytes, file_name="deck.pptx",
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           type="primary", **FULL)
        imgs = previews(pptx_bytes)
        for i, d in enumerate(deck):
            with st.expander(f"{i + 1}. [{d['layout']}] {d.get('title', '')}", expanded=(i == len(deck) - 1)):
                if i < len(imgs):
                    st.image(imgs[i], **FULL)
                else:
                    st.caption("Install LibreOffice to see previews here.")
                with st.popover("Edit JSON"):
                    txt = st.text_area("Slide JSON", json.dumps(d, indent=1), height=320, key=f"j{i}_{hashlib.md5(json.dumps(d).encode()).hexdigest()[:6]}")
                    if st.button("Apply", key=f"a{i}"):
                        try:
                            new = json.loads(txt); LAYOUTS[new["layout"]].model_validate(new)
                            push_undo(); deck[i] = new; st.rerun()
                        except Exception as e:
                            st.error(str(e))
