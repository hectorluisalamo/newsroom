# ABOUTME: Shared test fixtures and configuration for the Newsroom test suite.
# ABOUTME: Enforces no-network policy for all tests.
"""Shared fixtures for the newsroom test suite."""

import socket

import pytest

# Re-exported so existing `from conftest import FakeLLMProvider` test imports
# keep working. The canonical implementation lives in the production package
# (newsroom.draft.fake_provider) so newsroom.cli's $0 e2e seam can import it
# too — tests/ is never importable from production code.
from newsroom.draft.fake_provider import FakeLLMProvider

__all__ = ["FakeLLMProvider"]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Prevent any test from making real network connections."""

    def _guard(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden in tests.")

    monkeypatch.setattr(socket, "socket", _guard)
