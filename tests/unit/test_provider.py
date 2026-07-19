# ABOUTME: Unit tests for the LLM provider abstraction and its test doubles.
# ABOUTME: Covers FakeLLMProvider behavior and AnthropicProvider model resolution.
"""Tests for newsroom.draft.provider and newsroom.draft.anthropic_provider."""

from conftest import FakeLLMProvider
from newsroom.draft.anthropic_provider import _DEFAULT_MODEL, AnthropicProvider
from newsroom.draft.provider import LLMResponse

# ---------------------------------------------------------------------------
# FakeLLMProvider
# ---------------------------------------------------------------------------


class TestFakeLLMProvider:
    def test_default_word_count_is_700(self):
        provider = FakeLLMProvider()
        response = provider.generate("system", "user", max_tokens=2000)
        assert isinstance(response, LLMResponse)
        assert len(response.text.split()) == 700

    def test_custom_word_count_respected(self):
        provider = FakeLLMProvider(word_count=150)
        response = provider.generate("system", "user", max_tokens=2000)
        assert len(response.text.split()) == 150

    def test_zero_word_count_returns_empty_text(self):
        provider = FakeLLMProvider(word_count=0)
        response = provider.generate("system", "user", max_tokens=2000)
        assert response.text == ""

    def test_src_markers_present_default(self):
        provider = FakeLLMProvider()
        response = provider.generate("system", "user", max_tokens=2000)
        assert "[src:1]" in response.text
        assert "[src:2]" in response.text

    def test_src_markers_present_short_body(self):
        # Even a short body (below the 40-word sprinkle interval) must carry
        # both markers so the writer's citation post-check has something to
        # find regardless of configured length.
        provider = FakeLLMProvider(word_count=5)
        response = provider.generate("system", "user", max_tokens=2000)
        assert "[src:1]" in response.text
        assert "[src:2]" in response.text

    def test_call_count_increments(self):
        provider = FakeLLMProvider(word_count=10)
        assert provider.call_count == 0
        provider.generate("system", "user", max_tokens=100)
        assert provider.call_count == 1
        provider.generate("system", "user", max_tokens=100)
        assert provider.call_count == 2

    def test_model_id_is_fixed(self):
        provider = FakeLLMProvider()
        assert provider.model_id == "fake-model-v1"

    def test_responses_queue_simulates_retry_drift(self):
        # Two off-target lengths followed by an on-target one — mirrors a
        # provider whose output misses the writer's word-count window twice
        # before landing, so the writer's retry-cap logic has something to
        # exercise.
        provider = FakeLLMProvider(word_count=700, responses=[400, 400, 700])
        first = provider.generate("system", "user", max_tokens=2000)
        second = provider.generate("system", "user", max_tokens=2000)
        third = provider.generate("system", "user", max_tokens=2000)
        assert len(first.text.split()) == 400
        assert len(second.text.split()) == 400
        assert len(third.text.split()) == 700
        assert provider.call_count == 3

    def test_responses_queue_falls_back_to_word_count_once_exhausted(self):
        provider = FakeLLMProvider(word_count=250, responses=[400])
        first = provider.generate("system", "user", max_tokens=2000)
        second = provider.generate("system", "user", max_tokens=2000)
        assert len(first.text.split()) == 400
        assert len(second.text.split()) == 250

    def test_token_usage_reports_output_tokens(self):
        provider = FakeLLMProvider(word_count=42)
        response = provider.generate("system", "user", max_tokens=2000)
        assert response.token_usage["output_tokens"] == 42


# ---------------------------------------------------------------------------
# AnthropicProvider — construction / model resolution only (no .generate())
# ---------------------------------------------------------------------------


class TestAnthropicProviderModelResolution:
    def test_explicit_model_arg_wins(self, monkeypatch):
        monkeypatch.delenv("NEWSROOM_MODEL", raising=False)
        provider = AnthropicProvider(model="claude-explicit-model")
        assert provider.model_id == "claude-explicit-model"

    def test_env_var_used_when_no_explicit_model(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_MODEL", "claude-from-env")
        provider = AnthropicProvider()
        assert provider.model_id == "claude-from-env"

    def test_explicit_model_wins_over_env_var(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_MODEL", "claude-from-env")
        provider = AnthropicProvider(model="claude-explicit-model")
        assert provider.model_id == "claude-explicit-model"

    def test_default_used_when_no_arg_and_no_env(self, monkeypatch):
        monkeypatch.delenv("NEWSROOM_MODEL", raising=False)
        provider = AnthropicProvider()
        assert provider.model_id == _DEFAULT_MODEL

    def test_model_id_property_returns_resolved_model(self, monkeypatch):
        monkeypatch.delenv("NEWSROOM_MODEL", raising=False)
        provider = AnthropicProvider(model="claude-explicit-model")
        assert provider.model_id == provider.model_id == "claude-explicit-model"
