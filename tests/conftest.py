# ABOUTME: Shared test fixtures and configuration for the Newsroom test suite.
# ABOUTME: Enforces no-network policy for all tests.
"""Shared fixtures for the newsroom test suite."""

import socket

import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Prevent any test from making real network connections."""

    def _guard(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden in tests.")

    monkeypatch.setattr(socket, "socket", _guard)
