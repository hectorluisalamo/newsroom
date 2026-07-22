# ABOUTME: End-to-end tests for the Newsroom CLI.
# ABOUTME: Runs CLI as a subprocess and verifies output files and exit codes.
"""End-to-end tests for the newsroom CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXED_NOW = "2026-01-15T12:00:00Z"
_SUBPROCESS_TIMEOUT = 60


def test_cli_help_shows_subcommands():
    """The CLI --help flag exits 0 and lists all subcommands."""
    result = subprocess.run(
        [sys.executable, "-m", "newsroom", "--help"],
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0
    assert "pitch" in result.stdout
    assert "draft" in result.stdout
    assert "qa" in result.stdout


def _run_cli(args: list[str], extra_env: dict[str, str] | None = None):
    """Run `python -m newsroom <args>` as a real subprocess against the repo.

    cwd is the repo root. NEWSROOM_CONFIG_DIR defaults to `config.example/`
    (the committed reference config) so this suite runs identically on a
    fresh clone and in CI, where the gitignored, developer-local `config/`
    directory `scripts/init_config.sh` populates doesn't exist. `extra_env`
    layers onto a copy of the current environment (used to set
    NEWSROOM_FAKE_LLM=1 for `draft`, which is what keeps this test suite at
    $0 spend).
    """
    env = {
        **os.environ,
        "NEWSROOM_CONFIG_DIR": "config.example",
        **(extra_env or {}),
    }
    return subprocess.run(
        [sys.executable, "-m", "newsroom", *args],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
    )


class TestCliEndToEnd:
    """Real subprocess pitch -> draft -> qa flow over fixtures/science_tech.

    Chained through one temp --out-dir so each stage consumes the previous
    stage's real output files, exercising the CLI exactly as a human would
    run it. `draft` sets NEWSROOM_FAKE_LLM=1 so no AnthropicProvider is ever
    constructed and no real API key is used — this whole test class costs $0
    to run, repeatedly, in CI.
    """

    def test_pitch_writes_real_brief_and_pitches(self, tmp_path):
        out_dir = tmp_path / "out"
        result = _run_cli(
            [
                "--now",
                _FIXED_NOW,
                "--out-dir",
                str(out_dir),
                "pitch",
                "--beat",
                "science_tech",
                "--since",
                "48h",
                "--source-override",
                "fixtures/science_tech",
            ]
        )

        assert result.returncode == 0, result.stderr

        beat_dir = out_dir / "2026-01-15" / "science_tech"
        brief = json.loads((beat_dir / "brief.json").read_text())
        pitches = json.loads((beat_dir / "pitches.json").read_text())

        assert brief["beat"] == "science_tech"
        assert len(brief["clusters"]) > 0

        assert pitches["beat"] == "science_tech"
        assert len(pitches["pitches"]) == 3
        first_pitch = pitches["pitches"][0]
        assert first_pitch["pitch_id"]
        assert len(first_pitch["source_urls"]) >= 3

    def test_pitch_then_draft_then_qa_full_pipeline(self, tmp_path):
        out_dir = tmp_path / "out"

        pitch_result = _run_cli(
            [
                "--now",
                _FIXED_NOW,
                "--out-dir",
                str(out_dir),
                "pitch",
                "--beat",
                "science_tech",
                "--since",
                "48h",
                "--source-override",
                "fixtures/science_tech",
            ]
        )
        assert pitch_result.returncode == 0, pitch_result.stderr

        beat_dir = out_dir / "2026-01-15" / "science_tech"
        pitches = json.loads((beat_dir / "pitches.json").read_text())
        pitch_id = pitches["pitches"][0]["pitch_id"]

        guidance_file = tmp_path / "guidance.md"
        guidance_file.write_text("Keep it sharp and cite every claim.")

        draft_result = _run_cli(
            [
                "--now",
                _FIXED_NOW,
                "--out-dir",
                str(out_dir),
                "draft",
                "--beat",
                "science_tech",
                "--date",
                "2026-01-15",
                "--pitch-id",
                pitch_id,
                "--guidance-file",
                str(guidance_file),
            ],
            extra_env={"NEWSROOM_FAKE_LLM": "1"},
        )
        assert draft_result.returncode == 0, draft_result.stderr

        draft = json.loads((beat_dir / "draft.json").read_text())
        draft_md = (beat_dir / "draft.md").read_text()

        assert draft["pitch_id"] == pitch_id
        assert draft["model_id"] == "fake-model-v1"
        assert 600 <= draft["word_count"] <= 800
        assert "[src:1]" in draft["body_md"]
        assert "[src:" in draft_md

        qa_result = _run_cli(
            [
                "--now",
                _FIXED_NOW,
                "--out-dir",
                str(out_dir),
                "qa",
                "--beat",
                "science_tech",
                "--date",
                "2026-01-15",
            ]
        )
        assert qa_result.returncode == 0, qa_result.stderr

        report = json.loads((beat_dir / "report.json").read_text())
        assert report["beat"] == "science_tech"
        assert report["pitch_id"] == pitch_id
        assert isinstance(report["passed"], bool)
        assert len(report["checks_run"]) > 0
