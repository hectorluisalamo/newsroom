# ABOUTME: Anthropic Claude LLM provider implementation.
# ABOUTME: Wraps the Anthropic SDK for draft generation with timeout and retry.
"""Anthropic Claude provider for the Newsroom pipeline."""

from newsroom.draft.provider import LLMProvider, LLMResponse


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
        raise NotImplementedError

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> LLMResponse:
        """Generate a response using the Anthropic Claude API."""
        raise NotImplementedError

    @property
    def model_id(self) -> str:
        """Return the configured model identifier."""
        raise NotImplementedError
