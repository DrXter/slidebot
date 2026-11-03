"""Code-level quality checks on slide JSON.

The model is asked to fix anything flagged here, so slides converge on the house style:
short parallel phrases, sentence case, no fluff, no invented numbers.
"""
import re

# field -> max words
LIMITS = {
    "title": 10, "subtitle": 22, "kicker": 8, "date_line": 10,
    "tagline": 8, "items": 11, "panel_items": 7, "outcome": 14, "dark_text": 10,
    "header": 5, "banner_left": 32, "banner_right": 26, "banner": 30,
    "card_title": 8, "card_text": 32, "row_name": 6, "milestone": 10, "side_item": 10, "side_title": 6,
}
FLUFF = ["leverage", "leveraging", "synergy", "synergies", "seamless", "seamlessly", "robust", "cutting-edge",
         "best-in-class", "world-class", "holistic", "game-changer", "game-changing", "unlock", "empower",
         "revolutionize", "revolutionise", "state-of-the-art", "next-generation", "paradigm", "utilize", "utilise"]
ACRONYM = re.compile(r"^[A-Z0-9][A-Z0-9&\-/+]+s?$")


def words(t):
    return len(re.findall(r"\S+", t or ""))


def title_case(t):
    toks = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", t or "") if not ACRONYM.match(w)]
    if len(toks) < 4:
        return False
    caps = sum(1 for w in toks[1:] if w[0].isupper())
    return caps / max(1, len(toks) - 1) > 0.6


def numbers(t):
    return {n.rstrip(".,") for n in re.findall(r"\d[\d,.]*%?", t or "")}


def texts(slide):
    """Yield (path, kind, text) for every text field in a slide."""
    lay = slide.get("layout")
    for k in ("title", "subtitle", "kicker", "date_line", "banner_left", "banner_right", "banner", "outcome"):
        if slide.get(k):
            yield k, k, slide[k]
    if lay == "columns":
        for i, c in enumerate(slide.get("columns", []), 1):
            for k in ("header", "tagline", "outcome", "dark_text"):
                yield f"columns[{i}].{k}", k, c.get(k, "")
            for j, it in enumerate(c.get("items", []), 1):
                yield f"columns[{i}].items[{j}]", "items", it
            for j, it in enumerate(c.get("panel_items", []), 1):
                yield f"columns[{i}].panel_items[{j}]", "panel_items", it
    elif lay == "grid":
        for i, c in enumerate(slide.get("cards", []), 1):
            yield f"cards[{i}].title", "card_title", c.get("title", "")
            yield f"cards[{i}].text", "card_text", c.get("text", "")
    elif lay == "timeline":
        for i, r in enumerate(slide.get("rows", []), 1):
            yield f"rows[{i}].name", "row_name", r.get("name", "")
        for i, m in enumerate(slide.get("milestones", []), 1):
            yield f"milestones[{i}].label", "milestone", m.get("label", "")
        for i, b in enumerate(slide.get("side_boxes", []), 1):
            yield f"side_boxes[{i}].title", "side_title", b.get("title", "")
            for j, it in enumerate(b.get("items", []), 1):
                yield f"side_boxes[{i}].items[{j}]", "side_item", it


def autofix(slide):
    """Cheap, safe fixes done in code: trim spaces, drop trailing full stops on short phrases."""
    def fix(v, short):
        if not isinstance(v, str):
            return v
        v = re.sub(r"\s+", " ", v).strip()
        if short and v.endswith(".") and not v.endswith("..."):
            v = v[:-1]
        return v
    lay = slide.get("layout")
    if lay == "columns":
        for c in slide.get("columns", []):
            for k in ("header", "tagline", "dark_text", "outcome"):
                c[k] = fix(c.get(k, ""), True)
            c["items"] = [fix(x, True) for x in c.get("items", [])]
            c["panel_items"] = [fix(x, True) for x in c.get("panel_items", [])]
    elif lay == "grid":
        for c in slide.get("cards", []):
            c["title"] = fix(c.get("title", ""), True)
    elif lay == "timeline":
        for r in slide.get("rows", []):
            r["name"] = fix(r.get("name", ""), True)
        for b in slide.get("side_boxes", []):
            b["items"] = [fix(x, True) for x in b.get("items", [])]
    for k in ("title", "subtitle"):
        if slide.get(k):
            slide[k] = fix(slide[k], k == "title")
    return slide


def check(slide, source=""):
    """Return a list of human-readable issues for the model to fix."""
    issues = []
    src_nums = numbers(source)
    seen = {}
    for path, kind, t in texts(slide):
        lim = LIMITS.get(kind)
        n = words(t)
        if lim and n > lim:
            issues.append(f"{path}: {n} words, max {lim}. Shorten: \"{t}\"")
        if kind in ("title", "tagline", "header", "card_title", "items", "panel_items", "row_name") and title_case(t):
            issues.append(f"{path}: use sentence case, not Title Case: \"{t}\"")
        low = t.lower()
        for f in FLUFF:
            if re.search(rf"\b{re.escape(f)}\b", low):
                issues.append(f"{path}: remove the buzzword '{f}': \"{t}\"")
        if source:
            for num in numbers(t) - src_nums:
                if len(num.strip(".,")) > 0 and not re.fullmatch(r"[1-9]", num):
                    issues.append(f"{path}: the number '{num}' is not in the source. Remove it or use a figure from the source.")
        key = low.strip()
        if key and kind in ("items", "panel_items", "card_title", "tagline") and key in seen:
            issues.append(f"{path}: duplicates {seen[key]}. Make each point distinct.")
        seen.setdefault(key, path)
    if slide.get("layout") == "columns":
        cols = slide.get("columns", [])
        counts = [len(c.get("items", [])) for c in cols]
        if counts and max(counts) - min(counts) > 2:
            issues.append(f"columns: bullet counts are uneven {counts}; aim for 3-5 per column and similar lengths.")
        if any(len(c.get("items", [])) < 3 for c in cols):
            issues.append("columns: give every column at least 3 bullets drawn from the source.")
    if slide.get("layout") == "timeline":
        p = len(slide.get("periods", []))
        for i, r in enumerate(slide.get("rows", []), 1):
            if not (0 <= r.get("start", 0) <= r.get("end", 0) < p):
                issues.append(f"rows[{i}]: start/end must be 0..{p - 1} with start <= end.")
    return issues
