"""Render slide JSON (see schemas.py) into a branded 16:9 .pptx.

All layout decisions live here, so the language model only ever writes content.
"""
import io
import os
import random
from lxml import etree
from pptx import Presentation
from pptx.util import Inches as I, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

from schemas import ICON_FILES

HERE = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(HERE, "icons")

# ---- Brand tokens (edit here to rebrand) -----------------------------------
BRAND = {
    "name": "Deloitte",
    "font": "Open Sans",
    "G": "86BC25",      # primary green
    "GD": "26890D",     # dark green
    "DK": "101214",     # near black
    "DK2": "2A2E31",    # dark panel
    "GREY": "5B6063",
    "TXT": "3A3F43",
    "MID": "D9DCD6",
    "TINT": "EEF5E0",
    "LIGHT": "F2F2F2",
}
B = BRAND
W, H = 13.333, 7.5
L, R = 0.75, 12.73
FW = R - L


def rgb(h):
    return RGBColor.from_string(h)


def nostyle(o):
    """Drop the theme style reference so no theme shadow/effects are applied."""
    st = o._element.find(qn("p:style"))
    if st is not None:
        o._element.remove(st)
    return o


# ---- Primitives --------------------------------------------------------------
def rect(s, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, dash=False):
    o = s.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        o.adjustments[0] = min(0.5, radius / max(0.01, min(w, h)))
    if fill:
        o.fill.solid(); o.fill.fore_color.rgb = rgb(fill)
    else:
        o.fill.background()
    if line:
        o.line.color.rgb = rgb(line); o.line.width = Pt(0.75)
        if dash:
            d = etree.SubElement(o.line._get_or_add_ln(), qn("a:prstDash")); d.set("val", "dash")
    else:
        o.line.fill.background()
    o.shadow.inherit = False
    return nostyle(o)


def oval(s, cx, cy, d, fill, line=None):
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, I(cx - d / 2), I(cy - d / 2), I(d), I(d))
    o.fill.solid(); o.fill.fore_color.rgb = rgb(fill)
    if line:
        o.line.color.rgb = rgb(line); o.line.width = Pt(1.25)
    else:
        o.line.fill.background()
    o.shadow.inherit = False
    return nostyle(o)


def text(s, runs, x, y, w, h, size=12, color=None, bold=False, italic=False, align="l", anchor="t", spacing=None):
    """runs: str, or list of paragraphs; each paragraph a str or list of (text, opts)."""
    tb = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        if spacing:
            p.line_spacing = spacing
        segs = para if isinstance(para, list) else [(para, {})]
        for t, o in segs:
            r = p.add_run(); r.text = t
            f = r.font; f.name = B["font"]
            f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold); f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color or B["TXT"]))
    return tb


def icon(s, name, tone, cx, cy, d):
    fn = ICON_FILES.get(name, name)
    path = os.path.join(ICON_DIR, f"{fn}_{tone}.png")
    if os.path.exists(path):
        s.shapes.add_picture(path, I(cx - d / 2), I(cy - d / 2), I(d), I(d))


def badge(s, cx, cy, d, fill, name, tone="w", ratio=0.52):
    oval(s, cx, cy, d, fill)
    icon(s, name, tone, cx, cy, d * ratio)


def line(s, x1, y1, x2, y2, color=None, width=1.5, head=False, dash=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    c.line.color.rgb = rgb(color or B["GD"]); c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    if head:
        t = etree.SubElement(ln, qn("a:tailEnd")); t.set("type", "triangle")
    return nostyle(c)


def arrow(s, x, y, w, h, fill=None):
    o = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, I(x), I(y), I(w), I(h))
    o.fill.solid(); o.fill.fore_color.rgb = rgb(fill or B["G"]); o.line.fill.background(); o.shadow.inherit = False; nostyle(o)


def chevron(s, x, y, w, h, fill, first=False):
    o = rect(s, x, y, w, h, fill, shape=MSO_SHAPE.PENTAGON if first else MSO_SHAPE.CHEVRON)
    o.adjustments[0] = 0.28
    return o


def tone_for(fill):
    return "d" if fill in (B["G"], B["TINT"], "FFFFFF", B["LIGHT"]) else "w"


def fit(t, base, limit):
    """Shrink font a little when text is longer than the space was designed for."""
    n = len(t or "")
    if n <= limit:
        return base
    return max(base - 1.5, base * limit / n)


# ---- Page furniture ------------------------------------------------------------
def content_page(prs, title, subtitle=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, title, L, 0.42, FW, 0.55, size=26, bold=True, color=B["DK"], anchor="m")
    if subtitle:
        text(s, subtitle, L, 0.98, FW, 0.32, size=fit(subtitle, 14, 120), color=B["GREY"], anchor="m")
    wordmark(s, L, 6.95, size=14, color=B["DK"])
    return s


def wordmark(s, x, y, size=20, color="FFFFFF"):
    text(s, [[(B["name"], {"bold": True, "size": size, "color": color}), (".", {"bold": True, "size": size, "color": B["G"]})]],
         x, y, 3, 0.4, anchor="m")


def grid_motif(s, x0, y0, cols, rows, cell, gap, prog, seed=7):
    rnd = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            p = (c / (cols - 1)) * 0.85 + prog + rnd.uniform(-0.25, 0.25)
            st = 2 if p > 0.75 else (1 if p > 0.45 else 0)
            rect(s, x0 + c * (cell + gap), y0 + r * (cell + gap), cell, cell, [None, B["GD"], B["G"]][st],
                 line=("4A4F53" if st == 0 else None), radius=0.04)


def dark_page(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, W, H, B["DK"], shape=MSO_SHAPE.RECTANGLE)
    return s


# ---- Layouts -------------------------------------------------------------------
def render_cover(prs, d):
    s = dark_page(prs)
    grid_motif(s, 7.35, 0.95, 11, 11, 0.38, 0.12, 0.0)
    if d.get("kicker"):
        text(s, d["kicker"], 0.85, 1.6, 6, 0.4, size=14, bold=True, color=B["G"], anchor="m")
    text(s, d["title"], 0.85, 2.1, 6.1, 2.2, size=fit(d["title"], 32, 60), bold=True, color="FFFFFF", spacing=0.95)
    if d.get("subtitle"):
        text(s, d["subtitle"], 0.85, 4.45, 5.8, 0.8, size=14, color="BFC3C5")
    rect(s, 0.85, 5.45, 0.9, 0.05, B["G"], radius=0)
    if d.get("date_line"):
        text(s, d["date_line"], 0.85, 5.6, 5.5, 0.3, size=11, color="BFC3C5", anchor="m")
    wordmark(s, 0.85, 6.4)


def render_closing(prs, d):
    s = dark_page(prs)
    grid_motif(s, 7.35, 0.95, 11, 11, 0.38, 0.12, 0.75)
    text(s, d.get("title") or "Thank you", 0.85, 2.75, 6, 1.2, size=54, bold=True, color="FFFFFF", anchor="m")
    wordmark(s, 0.85, 6.4)


def render_columns(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    cols = d["columns"]; n = len(cols); gap = 0.12
    cw = (FW - (n - 1) * gap) / n
    palette = {3: [B["DK"], B["GD"], B["G"]], 4: [B["DK"], B["GD"], B["GD"], B["G"]], 5: [B["DK"], B["GD"], B["GD"], B["G"], B["G"]]}[n]
    small = n >= 5
    for k, c in enumerate(cols):
        f = palette[k]; tc = "FFFFFF" if f != B["G"] else B["DK"]
        x = L + k * (cw + gap)
        chevron(s, x - (0 if k == 0 else 0.12), 1.38, cw + 0.24, 0.6, f, first=(k == 0))
        sub_col = B["G"] if f == B["DK"] else ("E3EFC8" if f == B["GD"] else B["DK"])
        text(s, [[(c["header"], {"bold": True, "size": fit(c["header"], 10 if not small else 9, 28), "color": tc})],
                 [(c.get("timing", ""), {"bold": True, "size": 8, "color": sub_col})]],
             x + (0.14 if k == 0 else 0.26), 1.38, cw - 0.42, 0.6, anchor="m")
        rect(s, x, 2.05, cw, 2.92, "FFFFFF", line=B["MID"])
        badge(s, x + 0.32, 2.35, 0.42, f, c["icon"], tone_for(f))
        text(s, c["tagline"], x + 0.6, 2.08, cw - 0.66, 0.55, size=fit(c["tagline"], 9.5 if not small else 8.5, 34), bold=True, color=B["GD"], anchor="m")
        text(s, c.get("items_label", "Key activities"), x + 0.14, 2.66, cw - 0.2, 0.2, size=7.5, bold=True, color=B["GREY"], anchor="m")
        items = c["items"]; m = len(items)
        pitch = 0.62 if m <= 2 else (0.44 if m == 3 else min(0.34, 1.3 / m))
        isz = 8.5 if not small else 7.5
        for j, it in enumerate(items):
            y = 2.88 + j * pitch
            rect(s, x + 0.16, y + 0.07, 0.08, 0.08, B["G"], radius=0)
            text(s, it, x + 0.3, y, cw - 0.38, pitch, size=fit(it, isz, 70 if not small else 50), color=B["DK"])
        rect(s, x + 0.08, 4.22, cw - 0.16, 0.7, B["TINT"], radius=0.06)
        text(s, c["panel_label"], x + 0.16, 4.24, cw - 0.3, 0.18, size=7, bold=True, color=B["GD"], anchor="m")
        pis = c["panel_items"]
        for j, it in enumerate(pis):
            vy = 4.44 + j * (0.46 / max(1, len(pis)))
            rect(s, x + 0.2, vy + 0.05, 0.06, 0.06, B["GD"], radius=0)
            text(s, it, x + 0.32, vy - 0.01, cw - 0.42, 0.16, size=7, color=B["DK"], anchor="m")
        rect(s, x, 5.05, cw, 0.5, "FFFFFF", line=f if f != B["G"] else B["GD"], radius=0.06)
        text(s, c["outcome"], x + 0.1, 5.05, cw - 0.2, 0.5, size=fit(c["outcome"], 7.5, 80), italic=True, bold=True, color=B["DK"], anchor="m")
        if d.get("sequential") and k < n - 1:
            arrow(s, x + cw + 0.005, 5.23, 0.11, 0.14)
        rect(s, x, 5.62, cw, 0.66, B["DK"] if k < n - 1 else B["DK2"], radius=0.06)
        text(s, [[(c["dark_label"], {"bold": True, "size": 7, "color": "BFC3C5"})],
                 [(c["dark_text"], {"bold": True, "size": fit(c["dark_text"], 9.5, 45), "color": B["G"] if k < n - 1 else "FFFFFF"})]],
             x + 0.12, 5.62, cw - 0.24, 0.66, anchor="m")
    banners(s, d.get("banner_left_label", "Business outcome"), d.get("banner_left", ""),
            d.get("banner_right_label", ""), d.get("banner_right", ""))


def banners(s, la, ta, lb, tb):
    if tb:
        rect(s, L, 6.35, 6.3, 0.55, B["G"], radius=0.06)
        text(s, [[(la + "   ", {"bold": True, "size": 8, "color": B["DK"]}), (ta, {"size": 7.5, "color": B["DK"]})]], L + 0.13, 6.35, 6.05, 0.55, anchor="m")
        rect(s, 7.15, 6.35, 5.58, 0.55, B["DK"], radius=0.06)
        text(s, [[(lb + "   ", {"bold": True, "size": 8, "color": B["G"]}), (tb, {"size": 7.5, "color": "FFFFFF"})]], 7.28, 6.35, 5.35, 0.55, anchor="m")
    elif ta:
        rect(s, L, 6.35, FW, 0.55, B["DK"], radius=0.06)
        text(s, [[(la + "   ", {"bold": True, "size": 9, "color": B["G"]}), (ta, {"size": 9, "color": "FFFFFF"})]], L + 0.25, 6.35, FW - 0.5, 0.55, anchor="m")


def render_timeline(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    per = d["periods"]; rows = d["rows"]; ms = d.get("milestones", []); boxes = d.get("side_boxes", [])
    right = 8.95 if boxes else R
    gx = L + 2.85
    gw = (right - gx) / len(per)
    for k, p in enumerate(per):
        rect(s, gx + k * gw + 0.02, 1.42, gw - 0.04, 0.3, B["DK"] if k % 2 == 0 else B["DK2"], radius=0.06)
        text(s, p, gx + k * gw, 1.42, gw, 0.3, size=8.5, bold=True, color="FFFFFF", align="c", anchor="m")
    rh = min(0.42, 3.4 / max(1, len(rows))); y0 = 1.85
    for k in range(1, len(per)):
        line(s, gx + k * gw, 1.8, gx + k * gw, y0 + len(rows) * rh, color="EDEDED", width=0.75)
    colors = [B["DK"], B["DK"], B["GD"], B["GD"], B["GD"], B["G"], B["G"], B["G"], B["G"]]
    for r, row in enumerate(rows):
        y = y0 + r * rh
        if r % 2 == 0:
            rect(s, L, y, right - L, rh - 0.04, "F7F7F7", radius=0.04)
        f = colors[min(r, len(colors) - 1)]
        badge(s, L + 0.2, y + (rh - 0.04) / 2, 0.28, f, row["icon"], tone_for(f), 0.55)
        text(s, row["name"], L + 0.42, y, 2.35, rh - 0.04, size=fit(row["name"], 8.5, 36), bold=True, color=B["DK"], anchor="m")
        a = max(0, min(row["start"], len(per) - 1)); b = max(a, min(row["end"], len(per) - 1))
        rect(s, gx + a * gw + 0.04, y + 0.08, (b - a + 1) * gw - 0.08, rh - 0.2, f, radius=0.11)
    if ms:
        my = y0 + len(rows) * rh + 0.05
        text(s, "Milestones", L, my, 2.8, 0.34, size=9, bold=True, color=B["GD"], anchor="m")
        stack = {}
        for i, m in enumerate(ms):
            p = max(0, min(m["period"], len(per) - 1))
            j = stack.get(p, 0); stack[p] = j + 1
            cx = gx + (p + 1) * gw - 0.18 - j * 0.24
            oval(s, cx, my + 0.17, 0.26, B["G"], line=B["DK"])
            text(s, str(i + 1), cx - 0.13, my + 0.04, 0.26, 0.26, size=8, bold=True, color=B["DK"], align="c", anchor="m")
        ly = my + 0.45
        half = (right - L) / 2
        for i, m in enumerate(ms):
            x = L + (i % 2) * half; y = ly + (i // 2) * 0.24
            oval(s, x + 0.1, y + 0.12, 0.2, B["G"])
            text(s, str(i + 1), x, y + 0.02, 0.2, 0.2, size=7, bold=True, color=B["DK"], align="c", anchor="m")
            text(s, m["label"], x + 0.27, y, half - 0.35, 0.24, size=8, color=B["DK"], anchor="m")
    if boxes:
        sx, sw = 9.2, R - 9.2
        heights = [2.6, 2.1][:len(boxes)] if len(boxes) == 2 else [4.8]
        y = 1.42
        for bi, bx in enumerate(boxes):
            h = heights[bi]; dark = bi == 0
            rect(s, sx, y, sw, h, B["DK"] if dark else B["TINT"], line=None if dark else B["G"])
            text(s, bx["title"], sx + 0.2, y + 0.06, sw - 0.4, 0.32, size=10.5, bold=True, color=B["G"] if dark else B["GD"], anchor="m")
            items = bx["items"]; pitch = min(0.42, (h - 0.5) / max(1, len(items)))
            for j, it in enumerate(items):
                iy = y + 0.45 + j * pitch
                icon(s, "check", "g", sx + 0.3, iy + pitch / 2 - 0.02, 0.16)
                text(s, it, sx + 0.48, iy, sw - 0.6, pitch - 0.02, size=fit(it, 8.5, 55), color="FFFFFF" if dark else B["DK"], anchor="m")
            y += h + 0.1
    if d.get("outcome"):
        banners(s, "Outcome", d["outcome"], "", "")


def render_grid(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    cards = d["cards"]; n = len(cards)
    cols = 3 if n in (3, 5, 6) else 2
    rows_ = (n + cols - 1) // cols
    gap = 0.15; top = 1.5; bottom = 6.15 if d.get("banner") else 6.7
    cw = (FW - (cols - 1) * gap) / cols; ch = (bottom - top - (rows_ - 1) * gap) / rows_
    ch = min(ch, 2.2)
    palette = [B["DK"], B["GD"], B["GD"], B["G"], B["G"], B["DK"]]
    for i, c in enumerate(cards):
        x = L + (i % cols) * (cw + gap); y = top + (i // cols) * (ch + gap)
        f = palette[i]
        rect(s, x, y, cw, ch, "FFFFFF", line=B["MID"])
        rect(s, x, y, cw, 0.07, f, radius=0)
        badge(s, x + 0.5, y + 0.6, 0.6, f, c["icon"], tone_for(f))
        text(s, c["title"], x + 0.95, y + 0.3, cw - 1.1, 0.6, size=fit(c["title"], 12, 32), bold=True, color=B["DK"], anchor="m")
        text(s, c["text"], x + 0.25, y + 1.05, cw - 0.5, ch - 1.15, size=fit(c["text"], 10.5, 140), color=B["GREY"])
    if d.get("banner"):
        banners(s, "Takeaway", d["banner"], "", "")


RENDERERS = {"cover": render_cover, "columns": render_columns, "timeline": render_timeline,
             "grid": render_grid, "closing": render_closing}


def render_deck(slides, path=None):
    """slides: list of dicts (each with a 'layout' key). Returns pptx bytes; also writes `path` if given."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = I(W), I(H)
    for d in slides:
        RENDERERS[d["layout"]](prs, d)
    buf = io.BytesIO(); prs.save(buf)
    data = buf.getvalue()
    if path:
        with open(path, "wb") as fh:
            fh.write(data)
    return data


if __name__ == "__main__":
    import json, sys
    slides = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "deck.pptx"
    render_deck(slides, out)
    print("wrote", out)
