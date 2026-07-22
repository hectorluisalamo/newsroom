# ABOUTME: Unit tests for newsroom.cli's env-var seams.
# ABOUTME: Verifies NEWSROOM_FAKE_LLM truthy parsing and NEWSROOM_CONFIG_DIR resolution.
"""Unit tests for newsroom.cli."""

from pathlib import Path

import pytest

from newsroom import cli, commands
from newsroom.draft.fake_provider import FakeLLMProvider

_DRAFT_ARGV = [
    "draft",
    "--beat",
    "science_tech",
    "--date",
    "2026-01-15",
    "--pitch-id",
    "pitch-1",
    "--guidance-file",
    "guidance.md",
]


@pytest.fixture
def _capture_draft_cmd(monkeypatch):
    """Stub commands.draft_cmd and capture the kwargs it was called with."""
    calls: list[dict] = []

    def _fake_draft_cmd(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(commands, "draft_cmd", _fake_draft_cmd)
    return calls


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " 1 "])
def test_fake_llm_env_truthy_values_activate_fake_provider(
    monkeypatch, _capture_draft_cmd, value
):
    """Genuine truthy NEWSROOM_FAKE_LLM values inject a FakeLLMProvider."""
    monkeypatch.setenv("NEWSROOM_FAKE_LLM", value)

    cli.main(_DRAFT_ARGV)

    assert len(_capture_draft_cmd) == 1
    assert isinstance(_capture_draft_cmd[0]["provider"], FakeLLMProvider)


@pytest.mark.parametrize("value", ["0", "false", "False", "", "no", "off", "nope"])
def test_fake_llm_env_falsy_values_leave_provider_unset(
    monkeypatch, _capture_draft_cmd, value
):
    """Falsy-looking NEWSROOM_FAKE_LLM values (incl. '0'/'false') do NOT
    activate the fake path — draft_cmd falls through to the real provider."""
    monkeypatch.setenv("NEWSROOM_FAKE_LLM", value)

    cli.main(_DRAFT_ARGV)

    assert len(_capture_draft_cmd) == 1
    assert _capture_draft_cmd[0]["provider"] is None


def test_fake_llm_env_unset_leaves_provider_unset(monkeypatch, _capture_draft_cmd):
    """Unset NEWSROOM_FAKE_LLM (the production default) leaves provider=None."""
    monkeypatch.delenv("NEWSROOM_FAKE_LLM", raising=False)

    cli.main(_DRAFT_ARGV)

    assert len(_capture_draft_cmd) == 1
    assert _capture_draft_cmd[0]["provider"] is None


def test_config_dir_env_unset_passes_none(monkeypatch, _capture_draft_cmd):
    """Unset NEWSROOM_CONFIG_DIR (the production default) passes config_dir=None,
    so each command falls back to its own `config/` default."""
    monkeypatch.delenv("NEWSROOM_CONFIG_DIR", raising=False)

    cli.main(_DRAFT_ARGV)

    assert _capture_draft_cmd[0]["config_dir"] is None


def test_config_dir_env_set_overrides_default(monkeypatch, _capture_draft_cmd):
    """Setting NEWSROOM_CONFIG_DIR points every command at that directory instead."""
    monkeypatch.setenv("NEWSROOM_CONFIG_DIR", "config.example")

    cli.main(_DRAFT_ARGV)

    assert _capture_draft_cmd[0]["config_dir"] == Path("config.example")
