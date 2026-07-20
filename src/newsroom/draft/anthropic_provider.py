# ABOUTME: Anthropic Claude LLM provider implementation.
# ABOUTME: Wraps the Anthropic SDK for draft generation with timeout and retry.
"""Anthropic Claude provider for the Newsroom pipeline."""

import os

import anthropic

from newsroom.draft.provider import LLMProvider, LLMResponse

# Default model per ADR-009 resolution order (constructor arg > NEWSROOM_MODEL
# env > this default). Claude Sonnet 5 — successor to the retired
# claude-sonnet-4-20250514 alias, current as of the anthropic SDK 0.77.1 line.
# claude-sonnet-5 is the current Sonnet model ID (verified 2026-07 via the
# claude-api reference); do not "downgrade" to sonnet-4-6.
_DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider(LLMProvider):
    """LLM provider using the Anthropic Claude API.

    Model is resolved from: constructor arg > NEWSROOM_MODEL env var >
    default. API key from: constructor arg > ANTHROPIC_API_KEY env var.
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Anthropic provider."""
        self._model = model or os.environ.get("NEWSROOM_MODEL") or _DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = anthropic.Anthropic(api_key=self._api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> LLMResponse:
        """Generate a response using the Anthropic Claude API."""
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            # anthropic.APIError is the SDK's base exception, covering HTTP,
            # timeout, and rate-limit failures (auth, retry, and timeout are
            # handled by the SDK client itself via max_retries). Re-raise
            # with model context so callers see something actionable instead
            # of a raw SDK traceback. Never include the API key here.
            msg = f"Anthropic API call failed for model {self._model!r}: {exc}"
            raise RuntimeError(msg) from exc
        text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        )
        if not text:
            msg = "no text block in Anthropic response"
            raise RuntimeError(msg)
        return LLMResponse(
            text=text,
            token_usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    @property
    def model_id(self) -> str:
        """Return the configured model identifier."""
        return self._model
