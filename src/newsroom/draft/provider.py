# ABOUTME: Abstract LLM provider interface for draft generation.
# ABOUTME: Defines the LLMProvider ABC and LLMResponse model.
"""LLM provider abstraction for the Newsroom pipeline."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    text: str
    token_usage: dict[str, int] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> LLMResponse:
        """Generate a response from the LLM."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier string."""
