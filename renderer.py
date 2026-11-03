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


RECORD = None   # when a list, every text box is logged for the overflow check


def text(s, runs, x, y, w, h, size=12, color=None, bold=False, italic=False, align="l", anchor="t", spacing=None):
    """runs: str, or list of paragraphs; each paragraph a str or list of (text, opts)."""
    tb = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    if RECORD is not None:
        paras_ = runs if isinstance(runs, list) else [runs]
        rec = []
        for para in paras_:
            segs = para if isinstance(para, list) else [(para, {})]
            rec.append([(t, o.get("size", size), o.get("bold", bold)) for t, o in segs])
        RECORD.append({"w": w, "h": h, "paras": rec, "spacing": spacing or 1.0})
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
        heights = [2.6, 2.1] if len(boxes) == 2 else [min(4.8, 0.65 + 0.42 * len(boxes[0]["items"]))]
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



# ---- More visual layouts ---------------------------------------------------------
import math


def block_arc(s, cx, cy, d, start, sweep, fill, thick=0.18):
    o = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(cx - d / 2), I(cy - d / 2), I(d), I(d))
    o.adjustments[0] = (start % 360) * 0.6; o.adjustments[1] = ((start + sweep) % 360) * 0.6; o.adjustments[2] = thick
    o.fill.solid(); o.fill.fore_color.rgb = rgb(fill); o.line.fill.background(); o.shadow.inherit = False
    return nostyle(o)


def square(s, x, y, c=None):
    rect(s, x, y, 0.09, 0.09, c or B["G"], radius=0)


def bottom_banner(s, label, t, y=6.2):
    if t:
        rect(s, L, y, FW, 0.5, B["G"], radius=0.08)
        text(s, [[(label + "   ", {"bold": True, "size": 9.5, "color": B["DK"]}), (t, {"size": 9.5, "bold": True, "color": B["DK"]})]], L + 0.25, y, FW - 0.5, 0.5, anchor="m")


def render_flow(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    steps = d["steps"]; n = len(steps); cw = FW / n; cy = 2.55
    xs = [L + k * cw + cw / 2 for k in range(n)]
    pal = [B["DK"]] + [B["GD"]] * max(0, n - 3) + [B["G"], B["G"]]
    pal = pal[:n] if len(pal) >= n else pal + [B["G"]] * (n - len(pal))
    for k in range(n - 1):
        line(s, xs[k] + 0.36, cy, xs[k + 1] - 0.36, cy, color=B["G"], width=2.5, head=True)
    for k, st in enumerate(steps):
        x = L + k * cw; f = pal[k]
        badge(s, xs[k], cy, 0.66, f, st["icon"], tone_for(f), 0.5)
        oval(s, xs[k] - 0.29, cy - 0.29, 0.26, "FFFFFF", line=B["DK"])
        text(s, str(k + 1), xs[k] - 0.42, cy - 0.42, 0.26, 0.26, size=8, bold=True, color=B["DK"], align="c", anchor="m")
        rect(s, x + 0.07, 3.0, cw - 0.14, 1.4, "FFFFFF", line=B["MID"])
        rect(s, x + 0.07, 3.0, cw - 0.14, 0.06, f, radius=0)
        text(s, st["title"], x + 0.15, 3.08, cw - 0.3, 0.36, size=fit(st["title"], 10, 22), bold=True, color=B["DK"], anchor="m")
        text(s, st["text"], x + 0.15, 3.44, cw - 0.3, 0.62, size=fit(st["text"], 8.5, 80), color=B["GREY"])
        if st.get("label"):
            text(s, st["label"], x + 0.15, 4.1, cw - 0.3, 0.24, size=7.5, bold=True, color=B["GD"], anchor="m")
    lf, lt = d.get("loop_from", 0), d.get("loop_to", 0)
    if d.get("loop_note") and 1 <= lt < lf <= n:
        ly = 1.98
        line(s, xs[lf - 1], cy - 0.34, xs[lf - 1], ly, color=B["GD"], width=1.5, dash=True)
        line(s, xs[lf - 1], ly, xs[lt - 1], ly, color=B["GD"], width=1.5, dash=True)
        line(s, xs[lt - 1], ly, xs[lt - 1], cy - 0.34, color=B["GD"], width=1.5, dash=True, head=True)
        mid = (xs[lf - 1] + xs[lt - 1]) / 2
        rect(s, mid - 1.6, ly - 0.12, 3.2, 0.24, "FFFFFF", radius=0)
        text(s, d["loop_note"], mid - 1.6, ly - 0.12, 3.2, 0.24, size=8, italic=True, color=B["GD"], align="c", anchor="m")
    bf = d.get("branch_from", 0)
    if d.get("branch_text") and 1 <= bf <= n:
        bx = xs[bf - 1]
        line(s, bx, 4.4, bx, 4.62, color=B["DK"], width=1.5)
        line(s, bx, 4.62, bx + 0.6, 4.62, color=B["DK"], width=1.5, head=True)
        if d.get("branch_label"):
            text(s, d["branch_label"], bx - 1.45, 4.44, 1.4, 0.22, size=8, bold=True, color=B["DK"], align="r", anchor="m")
        rect(s, bx + 0.62, 4.45, R - bx - 0.62, 0.36, B["TINT"], line=B["GD"], radius=0.18)
        text(s, d["branch_text"], bx + 0.8, 4.45, R - bx - 1.0, 0.36, size=8.5, color=B["DK"], anchor="m")
    pr = d.get("principles", [])
    if pr:
        text(s, "Built into every step", L, 4.98, 6, 0.3, size=11, bold=True, color=B["GD"], anchor="m")
        ow = (FW - (len(pr) - 1) * 0.12) / len(pr)
        for j, o in enumerate(pr):
            x = L + j * (ow + 0.12)
            rect(s, x, 5.33, ow, 0.5, B["DK"], radius=0.08)
            badge(s, x + 0.3, 5.58, 0.32, B["G"], "check", "d", 0.55)
            text(s, o, x + 0.55, 5.33, ow - 0.62, 0.5, size=fit(o, 9, 40), bold=True, color="FFFFFF", anchor="m")
    bottom_banner(s, "Business outcome", d.get("banner", ""), y=6.0)


def render_stack(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    layers = list(d["layers"]); n = len(layers)
    has_side = bool(d.get("side_pairs") or d.get("callout"))
    x0, w0 = L, (6.9 if has_side else FW - 0.5)
    top, bottom = 1.5, 5.65 if d.get("banner") else 6.6
    lh = (bottom - top - (n - 1) * 0.15) / n
    for idx, ly in enumerate(reversed(layers)):          # draw top layer first
        level = n - 1 - idx                              # 0 = foundation
        inset = 0.25 * level
        x, w = x0 + inset, w0 - 2 * inset
        y = top + idx * (lh + 0.15)
        if ly.get("dashed"):
            fill, tc, kc = "FFFFFF", B["GD"], B["GREY"]
            rect(s, x, y, w, lh, fill, line=B["GD"], dash=True)
        else:
            fill = B["DK"] if level == 0 else (B["G"] if level == n - 1 else B["GD"])
            tc = "FFFFFF" if fill != B["G"] else B["DK"]; kc = B["G"] if fill == B["DK"] else ("E3EFC8" if fill == B["GD"] else B["DK"])
            rect(s, x, y, w, lh, fill)
        text(s, [[(ly["kicker"], {"bold": True, "size": 8.5, "color": kc})], [(ly["title"], {"bold": True, "size": 14, "color": tc})]], x + 0.2, y + 0.05, w - 1.0, 0.62)
        icon(s, ly["icon"], "g" if fill == B["DK"] else ("d" if fill in (B["G"], "FFFFFF") else "w"), x + w - 0.45, y + 0.35, 0.38)
        chips = ly["chips"]; per = 3 if len(chips) > 4 else len(chips)
        cw = (w - 0.4 - (per - 1) * 0.1) / per
        rows = (len(chips) + per - 1) // per
        chh = min(0.3, (lh - 0.75) / max(1, rows) - 0.05)
        for j, c in enumerate(chips):
            cx = x + 0.2 + (j % per) * (cw + 0.1); cy = y + 0.72 + (j // per) * (chh + 0.05)
            if ly.get("dashed"):
                icon(s, "warning", "g", cx + 0.08, cy + chh / 2, 0.13)
                text(s, c, cx + 0.22, cy, cw - 0.22, chh, size=8, color=B["DK"], anchor="m")
            else:
                rect(s, cx, cy, cw, chh, "FFFFFF" if fill != B["DK"] else B["DK2"], line=None if fill != B["DK"] else B["G"], radius=0.12)
                text(s, c, cx, cy, cw, chh, size=fit(c, 7.5, 26), bold=True, color=B["DK"] if fill != B["DK"] else "FFFFFF", align="c", anchor="m")
    line(s, x0 + w0 + 0.25, bottom - 0.2, x0 + w0 + 0.25, top + 0.2, color=B["G"], width=3, head=True)
    if has_side:
        rx = 8.2; rw = R - rx; y = 1.42
        if d.get("side_title"):
            text(s, d["side_title"], rx, y, rw, 0.3, size=11, bold=True, color=B["GD"], anchor="m"); y += 0.36
        pairs = d.get("side_pairs", [])
        if pairs:
            bw = (rw - 0.6) / 2
            text(s, d.get("side_left_label", ""), rx, y, bw, 0.26, size=9, bold=True, color=B["GREY"], align="c", anchor="m")
            text(s, d.get("side_right_label", ""), rx + bw + 0.6, y, bw, 0.26, size=9, bold=True, color=B["GD"], align="c", anchor="m")
            y += 0.32
            for a, b in [(p + ["", ""])[:2] for p in pairs]:
                rect(s, rx, y, bw, 0.52, B["LIGHT"], radius=0.08); text(s, a, rx + 0.08, y, bw - 0.16, 0.52, size=8.5, color=B["DK"], align="c", anchor="m")
                arrow(s, rx + bw + 0.08, y + 0.16, 0.44, 0.2)
                rect(s, rx + bw + 0.6, y, bw, 0.52, B["TINT"], line=B["G"], radius=0.08); text(s, b, rx + bw + 0.68, y, bw - 0.16, 0.52, size=8.5, bold=True, color=B["DK"], align="c", anchor="m")
                y += 0.62
        if d.get("callout"):
            cy_ = max(y + 0.1, bottom - 0.95)
            rect(s, rx, cy_, rw, 0.95, B["DK"], radius=0.08)
            text(s, d["callout"], rx + 0.25, cy_, rw - 0.4, 0.95, size=fit(d["callout"], 15, 30), bold=True, color="FFFFFF", anchor="m")
    bottom_banner(s, "Takeaway", d.get("banner", ""), y=5.95)


def render_hub(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    has_panel = bool(d.get("panel_title"))
    right = 7.45 if has_panel else R
    cx = (L + right) / 2; cy = 3.75; D = 2.0
    cwid = (right - L - D - 0.5) / 2
    pos = [(L, 1.5), (right - cwid, 1.5), (right - cwid, 3.95), (L, 3.95)]
    pal = [B["DK"], B["GD"], B["GD"], B["G"]]
    starts = [180, 270, 0, 90]
    for k, sp in enumerate(d["spokes"][:4]):
        f = pal[k]; x, y = pos[k]; h = 2.05
        block_arc(s, cx, cy, D, starts[k] + 3, 84, f)
        rect(s, x, y, cwid, h, "FFFFFF", line=B["MID"])
        rect(s, x, y, cwid, 0.07, f, radius=0)
        badge(s, x + 0.35, y + 0.42, 0.44, f, sp["icon"], tone_for(f))
        text(s, [[(str(k + 1), {"bold": True, "size": 8, "color": B["GD"]})], [(sp["title"], {"bold": True, "size": fit(sp["title"], 11, 22), "color": B["DK"]})]], x + 0.66, y + 0.12, cwid - 0.7, 0.6)
        for j, it in enumerate(sp["items"][:4]):
            yy = y + 0.8 + j * 0.3
            square(s, x + 0.15, yy + 0.09)
            text(s, it, x + 0.3, yy, cwid - 0.38, 0.28, size=fit(it, 8.5, 34), color=B["DK"], anchor="m")
    oval(s, cx, cy, 1.36, B["TINT"])
    text(s, d["centre"], cx - 0.6, cy - 0.45, 1.2, 0.9, size=fit(d["centre"], 10.5, 20), bold=True, color=B["DK"], align="c", anchor="m")
    if has_panel:
        rx = 7.85; rw = R - rx; ph = 4.5 if d.get("banner") else 5.0
        rect(s, rx, 1.5, rw, ph, B["DK"])
        text(s, d["panel_title"], rx + 0.25, 1.58, rw - 0.5, 0.32, size=11, bold=True, color=B["G"], anchor="m")
        tiles = d.get("panel_tiles", [])[:6]; tw = (rw - 0.7) / 3
        for j, t in enumerate(tiles):
            ic, lab = (t + ["check", ""])[:2] if len(t) >= 2 else ("check", t[0] if t else "")
            ic = ic if ic in ICON_FILES else "check"
            xx = rx + 0.25 + (j % 3) * (tw + 0.1); yy = 2.0 + (j // 3) * 0.95
            rect(s, xx, yy, tw, 0.85, B["DK2"], line=B["G"])
            badge(s, xx + tw / 2, yy + 0.3, 0.38, B["G"], ic, "d", 0.55)
            text(s, lab, xx, yy + 0.52, tw, 0.28, size=fit(lab, 8.5, 16), bold=True, color="FFFFFF", align="c", anchor="m")
        y = 2.0 + ((len(tiles) + 2) // 3) * 0.95 + 0.05
        stats = d.get("panel_stats", [])[:3]
        for j, st in enumerate(stats):
            xx = rx + 0.25 + j * (tw + 0.1)
            text(s, [[(st["value"], {"bold": True, "size": 20, "color": B["G"]})], [(st["label"], {"size": 8, "color": "BFC3C5"})]], xx, y, tw, 0.75, align="c", anchor="m")
        if d.get("panel_note"):
            ny = y + (0.85 if stats else 0)
            line(s, rx + 0.25, ny, rx + rw - 0.25, ny, color="4A4F53", width=0.75)
            text(s, d["panel_note"], rx + 0.25, ny + 0.06, rw - 0.5, max(0.4, 1.5 + ph - ny - 0.15), size=8.5, color="BFC3C5")
    bottom_banner(s, "Key benefit", d.get("banner", ""), y=6.2)


def render_comparison(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    has_hl = bool(d.get("highlight_text"))
    right = 8.6 if has_hl else R
    bw = (right - L - 0.9) / 2
    for side, (lab, ic, x, f) in enumerate([(d["left_label"], d["left_icon"], L, B["DK"]), (d["right_label"], d["right_icon"], L + bw + 0.9, B["G"])]):
        rect(s, x, 1.45, bw, 0.6, f)
        badge(s, x + 0.35, 1.75, 0.4, "FFFFFF" if f == B["DK"] else B["DK"], ic, "d" if f == B["DK"] else "w", 0.55)
        text(s, lab, x + 0.65, 1.45, bw - 0.75, 0.6, size=13, bold=True, color="FFFFFF" if f == B["DK"] else B["DK"], anchor="m")
    rows = d["rows"]; top = 2.2; bottom = 5.95 if d.get("banner") else 6.6
    rh = min(0.72, (bottom - top) / len(rows))
    for j, r in enumerate(rows):
        y = top + j * rh
        rect(s, L, y, bw, rh - 0.1, B["LIGHT"])
        text(s, r["before"], L + 0.2, y, bw - 0.4, rh - 0.1, size=fit(r["before"], 10, 50), color=B["GREY"], anchor="m")
        arrow(s, L + bw + 0.2, y + (rh - 0.1) / 2 - 0.12, 0.5, 0.24)
        rect(s, L + bw + 0.9, y, bw, rh - 0.1, B["TINT"], line=B["G"])
        text(s, r["after"], L + bw + 1.1, y, bw - 0.4, rh - 0.1, size=fit(r["after"], 10, 50), bold=True, color=B["DK"], anchor="m")
    if has_hl:
        rx = 8.9; rw = R - rx
        hh = min(bottom - 1.55, 1.0 + 0.32 * math.ceil(len(d["highlight_text"]) / 34))
        rect(s, rx, 1.45, rw, hh, B["DK"])
        text(s, [[(d.get("highlight_title", ""), {"bold": True, "size": 12, "color": B["G"]})], [("", {"size": 6})], [(d["highlight_text"], {"size": 11, "color": "FFFFFF"})]],
             rx + 0.3, 1.65, rw - 0.6, hh - 0.35, anchor="t")
    bottom_banner(s, "Takeaway", d.get("banner", ""), y=6.05)


def render_quad(prs, d):
    s = content_page(prs, d["title"], d.get("subtitle", ""))
    rect(s, L, 1.55, 3.3, 1.75, B["DK"])
    text(s, [[(d["block_a_title"], {"bold": True, "size": 15, "color": "FFFFFF"})], [(d["block_a_text"], {"size": 9.5, "color": "BFC3C5"})]], L + 0.25, 1.62, 2.85, 1.6)
    oval(s, L + 1.65, 3.6, 0.44, B["G"]); text(s, "+", L + 1.43, 3.38, 0.44, 0.44, size=18, bold=True, color=B["DK"], align="c", anchor="m")
    rect(s, L, 3.9, 3.3, 1.45, B["G"])
    text(s, [[(d["block_b_title"], {"bold": True, "size": 15, "color": B["DK"]})], [(d["block_b_text"], {"size": 9.5, "color": B["DK"]})]], L + 0.25, 3.97, 2.85, 1.3)
    arrow(s, 4.2, 3.3, 0.55, 0.42)
    mx, my, mw, mh = 4.95, 1.55, R - 4.95, 3.8
    tw, th = (mw - 0.15) / 2, (mh - 0.15) / 2
    pal = [B["DK"], B["GD"], B["GD"], B["G"]]
    for j, c in enumerate(d["cards"][:4]):
        x = mx + (j % 2) * (tw + 0.15); y = my + (j // 2) * (th + 0.15); left = j % 2 == 0
        rect(s, x, y, tw, th, "F7F7F7")
        badge(s, x + (0.45 if left else tw - 0.45), y + 0.45, 0.56, pal[j], c["icon"], tone_for(pal[j]))
        text(s, c["title"], x + 0.85 if left else x + 0.2, y + 0.2, tw - 1.05, 0.5, size=fit(c["title"], 12.5, 26), bold=True, color=B["DK"], align="l" if left else "r", anchor="m")
        text(s, c["text"], x + 0.25 if left else x + 0.85, y + 0.85, tw - 1.1, 0.8, size=fit(c["text"], 9.5, 90), color=B["GREY"], align="l" if left else "r")
    oval(s, mx + mw / 2, my + mh / 2, 1.6, B["DK"], line="FFFFFF")
    text(s, d["centre"], mx + mw / 2 - 0.7, my + mh / 2 - 0.35, 1.4, 0.7, size=fit(d["centre"], 11, 18), bold=True, color=B["G"], align="c", anchor="m")
    if d.get("tagline"):
        rect(s, L, 5.6, FW, 0.62, B["DK"])
        text(s, d["tagline"], L + 0.25, 5.6, FW - 0.5, 0.62, size=fit(d["tagline"], 13, 90), bold=True, color="FFFFFF", align="c", anchor="m")


# ---- Overflow check ------------------------------------------------------------------
def estimate_overflow(slide):
    """Render one slide off-screen, log every text box, and estimate which ones overflow.
    Open Sans averages ~0.53 em per character; line height ~1.2 em."""
    global RECORD
    RECORD = []
    try:
        prs = Presentation(); prs.slide_width, prs.slide_height = I(W), I(H)
        RENDERERS[slide["layout"]](prs, slide)
        boxes = RECORD
    finally:
        RECORD = None
    problems = []
    for b in boxes:
        need = 0.0
        for para in b["paras"]:
            size = max((sz for _, sz, _ in para), default=10)
            chars = sum(len(t) * (1.06 if bold else 1.0) for t, _, bold in para)
            if not chars:
                need += size * 1.2 / 72
                continue
            per_line = max(1, int(b["w"] / (size * 0.53 / 72)))
            lines = math.ceil(chars / per_line)
            need += lines * size * 1.2 * b["spacing"] / 72
        if need > b["h"] + 0.02:
            txt = " ".join(t for para in b["paras"] for t, _, _ in para).strip()
            if txt:
                cut = int(100 * (1 - b["h"] / need))
                problems.append(f'Text overflows its box; cut it by about {max(cut, 15)}%: "{txt[:90]}"')
    return problems


RENDERERS = {"cover": render_cover, "columns": render_columns, "timeline": render_timeline,
             "grid": render_grid, "flow": render_flow, "stack": render_stack, "hub": render_hub,
             "comparison": render_comparison, "quad": render_quad, "closing": render_closing}


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
