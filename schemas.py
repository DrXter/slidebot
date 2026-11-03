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


class FlowStep(BaseModel):
    icon: Icon
    title: str = Field(description="Step name, max 5 words")
    text: str = Field(description="What happens, max 16 words")
    label: str = Field("", description="Optional owner or timing, max 5 words, e.g. 'Owner: tower lead'")


class FlowSlide(BaseModel):
    """Numbered process steps on a connected line, with optional loop-back and branch."""
    layout: Literal["flow"] = "flow"
    title: str
    subtitle: str = ""
    steps: List[FlowStep] = Field(min_length=3, max_length=7)
    loop_note: str = Field("", description="Optional dashed loop-back label (e.g. 'Residual findings go back for another lever'); empty if none")
    loop_from: int = Field(0, description="1-based step the loop starts from (0 = none)")
    loop_to: int = Field(0, description="1-based step the loop returns to (0 = none)")
    branch_from: int = Field(0, description="1-based step that can branch off (0 = none)")
    branch_label: str = Field("", description="Condition for the branch, max 4 words, e.g. 'Constraint found'")
    branch_text: str = Field("", description="Where the branch goes, max 20 words")
    principles: List[str] = Field(default_factory=list, max_length=4, description="Up to 4 rules built into every step, max 7 words each")
    banner: str = Field("", description="One-sentence takeaway, max 30 words")


class Layer(BaseModel):
    kicker: str = Field(description="Small label above the layer name, max 5 words")
    title: str = Field(description="Layer name, max 5 words")
    chips: List[str] = Field(description="2-6 items in this layer, max 5 words each", min_length=2, max_length=6)
    icon: Icon
    dashed: bool = Field(False, description="True for a gap or risk layer shown dashed")


class StackSlide(BaseModel):
    """Layered stack: foundation at the bottom, what is added on top. Optional callout on the right."""
    layout: Literal["stack"] = "stack"
    title: str
    subtitle: str = ""
    layers: List[Layer] = Field(min_length=2, max_length=4, description="Ordered bottom (foundation) to top")
    side_title: str = Field("", description="Right panel title, max 6 words")
    side_pairs: List[List[str]] = Field(default_factory=list, max_length=5, description="Pairs [from, to], max 6 words each, e.g. ['Security and privacy','AI trust and safety']")
    side_left_label: str = Field("", description="Header over the 'from' column, max 3 words")
    side_right_label: str = Field("", description="Header over the 'to' column, max 3 words")
    callout: str = Field("", description="Optional big quote or question, max 10 words")
    banner: str = Field("", description="One-sentence takeaway, max 30 words")


class Spoke(BaseModel):
    icon: Icon
    title: str = Field(description="Max 5 words")
    items: List[str] = Field(description="2-4 items, max 7 words each", min_length=2, max_length=4)


class Stat(BaseModel):
    value: str = Field(description="Short figure from the source, e.g. '130+'")
    label: str = Field(description="Max 4 words")


class HubSlide(BaseModel):
    """A centre outcome with 4 spokes around it, plus an optional dark side panel of tiles and stats."""
    layout: Literal["hub"] = "hub"
    title: str
    subtitle: str = ""
    centre: str = Field(description="Centre label, max 5 words")
    spokes: List[Spoke] = Field(min_length=4, max_length=4)
    panel_title: str = Field("", description="Side panel title, max 5 words; empty for none")
    panel_tiles: List[List[str]] = Field(default_factory=list, max_length=6, description="Up to 6 tiles as [icon, label], icon from the allowed list")
    panel_stats: List[Stat] = Field(default_factory=list, max_length=3)
    panel_note: str = Field("", description="Max 25 words")
    banner: str = Field("", description="One-sentence takeaway, max 30 words")


class CompareRow(BaseModel):
    before: str = Field(description="Max 8 words")
    after: str = Field(description="Max 8 words")


class ComparisonSlide(BaseModel):
    """Before/after (or today/future, A vs B) rows with arrows, plus a highlight box."""
    layout: Literal["comparison"] = "comparison"
    title: str
    subtitle: str = ""
    left_label: str = Field(description="e.g. 'Today', max 4 words")
    right_label: str = Field(description="e.g. 'With the programme', max 4 words")
    left_icon: Icon
    right_icon: Icon
    rows: List[CompareRow] = Field(min_length=3, max_length=6)
    highlight_title: str = Field("", description="Max 6 words")
    highlight_text: str = Field("", description="Max 30 words")
    banner: str = Field("", description="One-sentence takeaway, max 30 words")


class QuadCard(BaseModel):
    icon: Icon
    title: str = Field(description="Max 5 words")
    text: str = Field(description="Max 20 words")


class QuadSlide(BaseModel):
    """'A + B = outcomes': two building blocks on the left feeding a 2x2 of outcomes around a centre."""
    layout: Literal["quad"] = "quad"
    title: str
    subtitle: str = ""
    block_a_title: str = Field(description="First contributor, max 4 words")
    block_a_text: str = Field(description="Max 22 words")
    block_b_title: str = Field(description="Second contributor, max 4 words")
    block_b_text: str = Field(description="Max 22 words")
    centre: str = Field(description="Centre label, max 4 words")
    cards: List[QuadCard] = Field(min_length=4, max_length=4)
    tagline: str = Field("", description="Closing line, max 16 words")


Slide = Union[CoverSlide, ColumnsSlide, TimelineSlide, GridSlide, FlowSlide, StackSlide, HubSlide, ComparisonSlide, QuadSlide, ClosingSlide]
LAYOUTS = {
    "cover": CoverSlide, "columns": ColumnsSlide, "timeline": TimelineSlide,
    "grid": GridSlide, "flow": FlowSlide, "stack": StackSlide, "hub": HubSlide,
    "comparison": ComparisonSlide, "quad": QuadSlide, "closing": ClosingSlide,
}
LayoutName = Literal["cover", "columns", "timeline", "grid", "flow", "stack", "hub", "comparison", "quad", "closing"]


class PlannedSlide(BaseModel):
    layout: LayoutName
    title: str = Field(description="Action title stating the takeaway, max 10 words")
    message: str = Field(description="The one point this slide must land, one sentence")
    content: str = Field(description="What goes on the slide and which source sections to use, max 40 words")


class DeckPlan(BaseModel):
    """Storyline for a deck: one entry per slide, in order."""
    storyline: str = Field(description="The narrative arc in 2-3 sentences")
    slides: List[PlannedSlide] = Field(min_length=2, max_length=14)


class Critique(BaseModel):
    score: int = Field(description="1 (poor) to 5 (ready for a partner review)")
    issues: List[str] = Field(default_factory=list, max_length=8, description="Specific, fixable problems naming the field, e.g. 'columns[2].tagline repeats the header'")


class Route(BaseModel):
    """What the assistant should do with the user's message."""
    action: Literal["add_slide", "edit_slide", "delete_slide", "plan_deck", "build_plan", "answer"]
    layout: Optional[LayoutName] = Field(None, description="Layout for add_slide")
    slide_number: Optional[int] = Field(None, description="1-based slide number for edit/delete; for add_slide, where to insert (omit = end)")
    reply: str = Field(description="Short reply to the user, 1-2 sentences")
