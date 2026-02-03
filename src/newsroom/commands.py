# ABOUTME: Command implementations dispatched by the CLI parser.
# ABOUTME: Contains pitch_cmd, draft_cmd, and qa_cmd entry points.
"""Command implementations for the Newsroom CLI."""

from pathlib import Path


def pitch_cmd(
    beat: str,
    since: str,
    now: str | None,
    out_dir: Path,
    source_override: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the pitch pipeline: ingest, dedupe, cluster, rank, pitch."""
    raise NotImplementedError


def draft_cmd(
    beat: str,
    date: str,
    pitch_id: str,
    guidance_file: Path,
    now: str | None,
    out_dir: Path,
    verbose: bool = False,
) -> None:
    """Run the draft pipeline: load pitch, assemble prompt, generate draft, run QA."""
    raise NotImplementedError


def qa_cmd(
    beat: str,
    date: str,
    out_dir: Path,
    verbose: bool = False,
) -> None:
    """Run QA checks on an existing draft and write a report."""
    raise NotImplementedError
