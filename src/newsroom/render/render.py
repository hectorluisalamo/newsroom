# ABOUTME: Output rendering for briefs, pitches, drafts, and QA reports.
# ABOUTME: Produces deterministic JSON and Markdown with stable key ordering.
"""Output rendering for the Newsroom pipeline."""


def render_brief_json(brief: object) -> str:
    """Render a BriefPack as deterministic JSON."""
    raise NotImplementedError


def render_brief_md(brief: object) -> str:
    """Render a BriefPack as human-readable Markdown."""
    raise NotImplementedError


def render_pitches_json(pitches: object) -> str:
    """Render a PitchSet as deterministic JSON."""
    raise NotImplementedError


def render_pitches_md(pitches: object) -> str:
    """Render a PitchSet as formatted Markdown pitch cards."""
    raise NotImplementedError


def render_draft_md(draft: object) -> str:
    """Render a Draft as Substack-ready Markdown with a Sources section."""
    raise NotImplementedError


def render_draft_json(draft: object) -> str:
    """Render a Draft as deterministic JSON."""
    raise NotImplementedError


def render_report_json(report: object) -> str:
    """Render a QAReport as deterministic JSON."""
    raise NotImplementedError
