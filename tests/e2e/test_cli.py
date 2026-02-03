# ABOUTME: End-to-end tests for the Newsroom CLI.
# ABOUTME: Runs CLI as a subprocess and verifies output files and exit codes.
"""End-to-end tests for the newsroom CLI."""

import subprocess
import sys


def test_cli_help_shows_subcommands():
    """The CLI --help flag exits 0 and lists all subcommands."""
    result = subprocess.run(
        [sys.executable, "-m", "newsroom", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pitch" in result.stdout
    assert "draft" in result.stdout
    assert "qa" in result.stdout
