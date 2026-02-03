# ABOUTME: Argument parsing for the Newsroom CLI using argparse.
# ABOUTME: Defines pitch, draft, and qa subcommands with their flags.
"""CLI argument parsing for the Newsroom CLI.

Parsing only — command logic lives in commands.py.
"""

import argparse
import sys

from newsroom import commands


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="newsroom",
        description=(
            "Synthetic newsroom CLI for producing opinion columns from research briefs."
        ),
    )

    # Global flags
    parser.add_argument(
        "--now",
        type=str,
        default=None,
        help="ISO 8601 timestamp to use as 'now' (overrides NEWSROOM_NOW env var).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="out/",
        help="Output directory for generated files (default: out/).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging output.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # pitch subcommand
    pitch_parser = subparsers.add_parser(
        "pitch",
        help="Generate pitches from RSS feeds for a beat.",
    )
    pitch_parser.add_argument(
        "--beat",
        type=str,
        required=True,
        help="Beat to generate pitches for (e.g., science_tech).",
    )
    pitch_parser.add_argument(
        "--since",
        type=str,
        default="48h",
        help="Time window for feed items (default: 48h).",
    )
    pitch_parser.add_argument(
        "--source-override",
        type=str,
        default=None,
        help="Path to fixture data directory (for testing).",
    )

    # draft subcommand
    draft_parser = subparsers.add_parser(
        "draft",
        help="Generate a draft column from a pitch.",
    )
    draft_parser.add_argument(
        "--beat",
        type=str,
        required=True,
        help="Beat the pitch belongs to.",
    )
    draft_parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date of the pitch set (YYYY-MM-DD).",
    )
    draft_parser.add_argument(
        "--pitch-id",
        type=str,
        required=True,
        help="ID of the pitch to draft.",
    )
    draft_parser.add_argument(
        "--guidance-file",
        type=str,
        required=True,
        help="Path to editorial guidance file.",
    )

    # qa subcommand
    qa_parser = subparsers.add_parser(
        "qa",
        help="Run QA checks on an existing draft.",
    )
    qa_parser.add_argument(
        "--beat",
        type=str,
        required=True,
        help="Beat the draft belongs to.",
    )
    qa_parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date of the draft (YYYY-MM-DD).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    from pathlib import Path

    out_dir = Path(args.out_dir)

    if args.command == "pitch":
        commands.pitch_cmd(
            beat=args.beat,
            since=args.since,
            now=args.now,
            out_dir=out_dir,
            source_override=args.source_override,
            verbose=args.verbose,
        )
    elif args.command == "draft":
        commands.draft_cmd(
            beat=args.beat,
            date=args.date,
            pitch_id=args.pitch_id,
            guidance_file=Path(args.guidance_file),
            now=args.now,
            out_dir=out_dir,
            verbose=args.verbose,
        )
    elif args.command == "qa":
        commands.qa_cmd(
            beat=args.beat,
            date=args.date,
            out_dir=out_dir,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
