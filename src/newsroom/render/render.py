# ABOUTME: Output rendering for briefs, pitches, drafts, and QA reports.
# ABOUTME: Produces deterministic JSON and Markdown with stable key ordering.
"""Output rendering for the Newsroom pipeline."""

from newsroom.models import BriefPack, PitchSet


def render_brief_json(brief: BriefPack) -> str:
    """Render a BriefPack as deterministic JSON."""
    return brief.model_dump_json(indent=2)


def render_brief_md(brief: BriefPack) -> str:
    """Render a BriefPack as human-readable Markdown."""
    lines = [
        f"# Research Brief — {brief.beat} — {brief.date.isoformat()}",
        "",
        f"- Since: {brief.since}",
        f"- Items ingested: {brief.total_items_ingested}",
        f"- Items after dedupe: {brief.total_items_after_dedupe}",
        f"- Clusters: {len(brief.clusters)}",
        f"- Generated at: {brief.generated_at.isoformat()}",
        "",
    ]
    for cluster in brief.clusters:
        lines.append(f"## {cluster.label}")
        lines.append("")
        lines.append(
            f"- Cluster ID: `{cluster.cluster_id}` · Size: {cluster.size} · "
            f"Source diversity: {cluster.source_diversity} · "
            f"Recency score: {cluster.recency_score:.2f}"
        )
        if cluster.centroid_keywords:
            lines.append(f"- Keywords: {', '.join(cluster.centroid_keywords)}")
        lines.append("")
        for item in cluster.items:
            lines.append(f"  - [{item.title}]({item.url}) — {item.source_name}")
        lines.append("")
    return "\n".join(lines)


def render_pitches_json(pitches: PitchSet) -> str:
    """Render a PitchSet as deterministic JSON."""
    return pitches.model_dump_json(indent=2)


def render_pitches_md(pitches: PitchSet) -> str:
    """Render a PitchSet as formatted Markdown pitch cards."""
    lines = [
        f"# Pitches — {pitches.beat} — {pitches.date.isoformat()}",
        "",
    ]
    for pitch in pitches.pitches:
        lines.append(f"## {pitch.title}")
        lines.append("")
        lines.append(f"- Pitch ID: `{pitch.pitch_id}`")
        lines.append(f"- Angle: {pitch.angle}")
        lines.append(f"- Thesis: {pitch.thesis_angle}")
        lines.append(f"- Why now: {pitch.why_now}")
        if pitch.key_points:
            lines.append("- Key points:")
            for point in pitch.key_points:
                lines.append(f"  - {point}")
        lines.append("- Sources:")
        for url in pitch.source_urls:
            lines.append(f"  - {url}")
        if pitch.risk_flags:
            lines.append(f"- Risk flags: {', '.join(pitch.risk_flags)}")
        lines.append("")
    return "\n".join(lines)


def render_draft_md(draft: object) -> str:
    """Render a Draft as Substack-ready Markdown with a Sources section."""
    raise NotImplementedError


def render_draft_json(draft: object) -> str:
    """Render a Draft as deterministic JSON."""
    raise NotImplementedError


def render_report_json(report: object) -> str:
    """Render a QAReport as deterministic JSON."""
    raise NotImplementedError
