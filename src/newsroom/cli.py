# ABOUTME: Argument parsing for the Newsroom CLI using argparse.
# ABOUTME: Defines pitch, draft, and qa subcommands with their flags.
"""CLI argument parsing for the Newsroom CLI.

Parsing only — command logic lives in commands.py.
"""

import argparse
import os
import sys

from newsroom import commands

# Truthy values that activate the $0 in-memory fake-LLM seam. Deliberately
# narrow: an unset var, "", "0", and "false" all leave the real
# AnthropicProvider path untouched, so the common "set to 0/false to
# disable" idiom can't accidentally flip the CLI into fake mode.
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def _fake_llm_enabled() -> bool:
    """Return True only when NEWSROOM_FAKE_LLM is set to a genuine truthy value."""
    return os.environ.get("NEWSROOM_FAKE_LLM", "").strip().lower() in _TRUTHY_ENV_VALUES


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

    # config-dir seam: mirrors the NEWSROOM_FAKE_LLM env idiom above. Unset
    # (the production default) leaves `config_dir=None`, and each command
    # resolves that to `config/` itself. Setting NEWSROOM_CONFIG_DIR points
    # every command at an alternate config directory instead — e.g. the
    # e2e suite points it at the committed `config.example/` so subprocess
    # runs never depend on the gitignored, developer-local `config/` dir.
    config_dir_env = os.environ.get("NEWSROOM_CONFIG_DIR")
    config_dir = Path(config_dir_env) if config_dir_env else None

    if args.command == "pitch":
        commands.pitch_cmd(
            beat=args.beat,
            since=args.since,
            now=args.now,
            out_dir=out_dir,
            source_override=args.source_override,
            verbose=args.verbose,
            config_dir=config_dir,
        )
    elif args.command == "draft":
        # $0 e2e seam: when NEWSROOM_FAKE_LLM is set to a truthy value,
        # inject the in-memory FakeLLMProvider instead of leaving `provider`
        # unset, so draft_cmd never falls through to constructing a real
        # (paid) AnthropicProvider. Unset (the production default) leaves
        # `provider=None` and the real provider path is untouched.
        provider = None
        if _fake_llm_enabled():
            from newsroom.draft.fake_provider import FakeLLMProvider

            provider = FakeLLMProvider()
        commands.draft_cmd(
            beat=args.beat,
            date=args.date,
            pitch_id=args.pitch_id,
            guidance_file=Path(args.guidance_file),
            now=args.now,
            out_dir=out_dir,
            verbose=args.verbose,
            config_dir=config_dir,
            provider=provider,
        )
    elif args.command == "qa":
        commands.qa_cmd(
            beat=args.beat,
            date=args.date,
            out_dir=out_dir,
            verbose=args.verbose,
            config_dir=config_dir,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
