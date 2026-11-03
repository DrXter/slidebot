"""Slide schemas.

Each layout is a pydantic model. The JSON schema of the model is passed to
Ollama's `format` parameter, so the model can only answer with valid slide data.
The renderer (renderer.py) turns that data into a styled .pptx slide.
"""
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

# Friendly icon names the model may choose from (mapped to PNGs in icons/).
Icon = Literal[
    "brain", "check", "clock", "database", "warning", "document", "history",
    "inbox", "layers", "plug", "diagram", "robot", "search", "shield",
    "network", "refresh", "user-check", "user-shield", "executive", "team",
]
ICON_FILES = {
    "brain": "FaBrain", "check": "FaClipboardCheck", "clock": "FaClock",
    "database": "FaDatabase", "warning": "FaExclamationTriangle",
    "document": "FaFileAlt", "history": "FaHistory", "inbox": "FaInbox",
    "layers": "FaLayerGroup", "plug": "FaPlug", "diagram": "FaProjectDiagram",
    "robot": "FaRobot", "search": "FaSearch", "shield": "FaShieldAlt",
    "network": "FaSitemap", "refresh": "FaSyncAlt", "user-check": "FaUserCheck",
    "user-shield": "FaUserShield", "executive": "FaUserTie", "team": "FaUsers",
}

SHORT = "Short phrase, max 8 words, sentence case"


class CoverSlide(BaseModel):
    layout: Literal["cover"] = "cover"
    kicker: str = Field("", description="Small line above the title, e.g. 'Prepared for <client>'")
    title: str = Field(description="Deck title, max 10 words")
    subtitle: str = Field("", description="One sentence, max 20 words")
    date_line: str = Field("", description="e.g. 'Proposal for discussion, November 2026'")


class Column(BaseModel):
    header: str = Field(description="Column name, 2-5 words")
    timing: str = Field("", description="Optional timing or sub-label, e.g. 'Feb to Jun'")
    icon: Icon
    tagline: str = Field(description=SHORT)
    items_label: str = Field("Key activities", description="Label above the bullets")
    items: List[str] = Field(description="3-5 bullets, each max 10 words", min_length=2, max_length=5)
    panel_label: str = Field(description="Label of the light-green panel, e.g. 'Acceleration levers'")
    panel_items: List[str] = Field(description="2-3 short items, max 6 words each", min_length=1, max_length=3)
    outcome: str = Field(description="One italic line, max 14 words")
    dark_label: str = Field(description="Small label in the dark box, e.g. 'Milestone' or 'Example'")
    dark_text: str = Field(description="Bold text in the dark box, max 10 words")


class ColumnsSlide(BaseModel):
    """Phase-approach style: chevron headers over 3-5 columns."""
    layout: Literal["columns"] = "columns"
    title: str = Field(description="Slide title, max 10 words")
    subtitle: str = Field(description="One line, max 20 words")
    sequential: bool = Field(description="True if columns are steps in order (adds arrows), false if parallel")
    columns: List[Column] = Field(min_length=3, max_length=5)
    banner_left_label: str = Field("Business outcome")
    banner_left: str = Field(description="One sentence, max 30 words")
    banner_right_label: str = Field("Deloitte differentiator")
    banner_right: str = Field(description="One sentence, max 25 words")


class TimelineRow(BaseModel):
    name: str = Field(description="Workstream name, max 6 words")
    icon: Icon
    start: int = Field(description="Index of first period (0-based) in `periods`")
    end: int = Field(description="Index of last period (0-based), >= start")


class Milestone(BaseModel):
    label: str = Field(description="Milestone, max 10 words")
    period: int = Field(description="Index of the period it falls at the end of (0-based)")


class SideBox(BaseModel):
    title: str = Field(description="Box title, max 6 words")
    items: List[str] = Field(description="Up to 6 items, max 10 words each", max_length=6)


class TimelineSlide(BaseModel):
    """Gantt timeline with milestones and up to two side boxes."""
    layout: Literal["timeline"] = "timeline"
    title: str
    subtitle: str = ""
    periods: List[str] = Field(description="Column labels, e.g. months 'Nov','Dec'", min_length=3, max_length=12)
    rows: List[TimelineRow] = Field(min_length=1, max_length=9)
    milestones: List[Milestone] = Field(default_factory=list, max_length=6)
    side_boxes: List[SideBox] = Field(default_factory=list, max_length=2)
    outcome: str = Field("", description="One-sentence banner, max 30 words")


class Card(BaseModel):
    icon: Icon
    title: str = Field(description=SHORT)
    text: str = Field(description="One or two sentences, max 30 words")


class GridSlide(BaseModel):
    """Icon cards in a grid (3-6 cards), e.g. benefits, pillars, reasons."""
    layout: Literal["grid"] = "grid"
    title: str
    subtitle: str = ""
    cards: List[Card] = Field(min_length=3, max_length=6)
    banner: str = Field("", description="One-sentence takeaway, max 30 words")


class ClosingSlide(BaseModel):
    layout: Literal["closing"] = "closing"
    title: str = "Thank you"


Slide = Union[CoverSlide, ColumnsSlide, TimelineSlide, GridSlide, ClosingSlide]
LAYOUTS = {
    "cover": CoverSlide, "columns": ColumnsSlide, "timeline": TimelineSlide,
    "grid": GridSlide, "closing": ClosingSlide,
}


class Route(BaseModel):
    """What the assistant should do with the user's message."""
    action: Literal["add_slide", "edit_slide", "delete_slide", "answer"]
    layout: Optional[Literal["cover", "columns", "timeline", "grid", "closing"]] = Field(
        None, description="Layout for add_slide")
    slide_number: Optional[int] = Field(None, description="1-based slide number for edit/delete; for add_slide, where to insert (omit = end)")
    reply: str = Field(description="Short reply to the user, 1-2 sentences")
