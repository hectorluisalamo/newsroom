# ABOUTME: Command implementations dispatched by the CLI parser.
# ABOUTME: Contains pitch_cmd, draft_cmd, and qa_cmd entry points.
"""Command implementations for the Newsroom CLI."""

import datetime as dt
import logging
from pathlib import Path

from newsroom import settings
from newsroom.cluster.tfidf import TfidfClusterer
from newsroom.dedupe.dedupe import dedupe_items
from newsroom.draft.anthropic_provider import AnthropicProvider
from newsroom.draft.provider import LLMProvider
from newsroom.draft.writer import write_draft
from newsroom.ingestion.rss import fetch_all_feeds, fetch_local_feeds
from newsroom.logging_config import setup_logging
from newsroom.models import BriefPack, PitchSet
from newsroom.normalize.normalize import normalize_all
from newsroom.pitches.pitches import generate_pitches
from newsroom.rank.rank import rank_clusters
from newsroom.render.render import (
    render_brief_json,
    render_brief_md,
    render_draft_json,
    render_draft_md,
    render_pitches_json,
    render_pitches_md,
)
from newsroom.time_anchor import resolve_now

logger = logging.getLogger(__name__)


def _validate_beat(beat: str) -> None:
    """Reject a `beat` value that could escape `out_dir` once joined into a path.

    `beat` comes from the caller-controlled `--beat` CLI flag and is joined
    directly into the output path (`out_dir / date / beat`), so it must be a
    single safe path component: not empty, not `.` or `..`, no path
    separators, and not an absolute path.
    """
    if not beat or beat in (".", ".."):
        msg = f"beat must be a non-empty path component, got {beat!r}"
        raise ValueError(msg)
    if "/" in beat or "\\" in beat:
        msg = f"beat must not contain path separators, got {beat!r}"
        raise ValueError(msg)
    if Path(beat).is_absolute():
        msg = f"beat must not be an absolute path, got {beat!r}"
        raise ValueError(msg)


def pitch_cmd(
    beat: str,
    since: str,
    now: str | None,
    out_dir: Path,
    source_override: str | None = None,
    verbose: bool = False,
    config_dir: Path | None = None,
) -> None:
    """Run the pitch pipeline: ingest, normalize, dedupe, cluster, rank, pitch.

    `config_dir` defaults to `config/` (the local, gitignored runtime
    config populated by `scripts/init_config.sh`). Tests pass an
    explicit `config_dir` (e.g. `config.example/`) so they never depend
    on that gitignored, developer-local state.
    """
    _validate_beat(beat)
    setup_logging(verbose)
    resolved_now = resolve_now(now)
    resolved_config_dir = config_dir if config_dir is not None else Path("config")

    if source_override:
        pairs = fetch_local_feeds(Path(source_override))
    else:
        sources = settings.load_sources(beat, resolved_config_dir)
        pairs = fetch_all_feeds(sources)

    entries = [entry for entry, _ in pairs]
    entry_sources = [source for _, source in pairs]
    total_ingested = len(entries)

    items = normalize_all(
        entries, entry_sources, beat=beat, since=since, now=resolved_now
    )

    deduped = dedupe_items(items)
    total_after_dedupe = len(deduped)

    cluster_config = settings.load_cluster_config(resolved_config_dir)
    clusterer = TfidfClusterer(cluster_config)
    ranked_clusters = rank_clusters(clusterer.cluster(deduped))

    brief = BriefPack(
        beat=beat,
        date=resolved_now.date(),
        since=since,
        total_items_ingested=total_ingested,
        total_items_after_dedupe=total_after_dedupe,
        clusters=ranked_clusters,
        generated_at=resolved_now,
    )

    pitch_set = generate_pitches(brief, n=3)

    beat_dir = out_dir / resolved_now.date().isoformat() / beat
    beat_dir.mkdir(parents=True, exist_ok=True)
    (beat_dir / "brief.json").write_text(render_brief_json(brief))
    (beat_dir / "brief.md").write_text(render_brief_md(brief))
    (beat_dir / "pitches.json").write_text(render_pitches_json(pitch_set))
    (beat_dir / "pitches.md").write_text(render_pitches_md(pitch_set))

    logger.info(
        "Wrote brief + %d pitches for beat=%s date=%s to %s",
        len(pitch_set.pitches),
        beat,
        resolved_now.date().isoformat(),
        beat_dir,
    )


def draft_cmd(
    beat: str,
    date: str,
    pitch_id: str,
    guidance_file: Path,
    now: str | None,
    out_dir: Path,
    verbose: bool = False,
    config_dir: Path | None = None,
    provider: LLMProvider | None = None,
) -> None:
    """Run the draft pipeline: load pitch, assemble prompt, generate draft, run QA.

    `config_dir` defaults to `config/`, mirroring `pitch_cmd`. `provider`
    defaults to a real `AnthropicProvider` (the money seam) so tests can
    inject a `FakeLLMProvider` instead of making a paid LLM call.
    """
    _validate_beat(beat)
    setup_logging(verbose)
    resolved_now = resolve_now(now)
    resolved_config_dir = config_dir if config_dir is not None else Path("config")

    try:
        selected_date = dt.date.fromisoformat(date)
    except ValueError as exc:
        msg = f"invalid --date {date!r}: expected ISO YYYY-MM-DD"
        raise ValueError(msg) from exc

    beat_dir = out_dir / selected_date.isoformat() / beat
    pitch_set = PitchSet.model_validate_json((beat_dir / "pitches.json").read_text())
    pitch = next((p for p in pitch_set.pitches if p.pitch_id == pitch_id), None)
    if pitch is None:
        msg = f"pitch_id {pitch_id!r} not found"
        raise ValueError(msg)

    brief = BriefPack.model_validate_json((beat_dir / "brief.json").read_text())

    if pitch_set.date != selected_date:
        msg = (
            f"pitch_set date {pitch_set.date.isoformat()!r} does not match "
            f"requested --date {selected_date.isoformat()!r}"
        )
        raise ValueError(msg)
    if brief.date != selected_date:
        msg = (
            f"brief_pack date {brief.date.isoformat()!r} does not match "
            f"requested --date {selected_date.isoformat()!r}"
        )
        raise ValueError(msg)

    voice = settings.load_voice(beat, resolved_config_dir)
    guidance = guidance_file.read_text()

    active_provider = provider if provider is not None else AnthropicProvider()

    draft = write_draft(
        pitch,
        brief,
        voice,
        guidance,
        active_provider,
        now=resolved_now,
        beat=beat,
        date=pitch_set.date,
    )

    (beat_dir / "draft.json").write_text(render_draft_json(draft))
    (beat_dir / "draft.md").write_text(render_draft_md(draft))

    logger.info(
        "Wrote draft for beat=%s date=%s pitch_id=%s to %s",
        beat,
        date,
        pitch_id,
        beat_dir,
    )


def qa_cmd(
    beat: str,
    date: str,
    out_dir: Path,
    verbose: bool = False,
) -> None:
    """Run QA checks on an existing draft and write a report."""
    raise NotImplementedError
