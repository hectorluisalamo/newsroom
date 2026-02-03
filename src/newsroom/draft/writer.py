# ABOUTME: Draft writing logic for the Newsroom pipeline.
# ABOUTME: Assembles prompts and calls the LLM to produce opinion columns.
"""Draft writing and prompt assembly."""

from newsroom.draft.provider import LLMProvider


def assemble_prompt(
    pitch: object,
    brief: object,
    voice: object,
    guidance: str,
) -> tuple[str, str]:
    """Assemble system and user prompts for draft generation.

    Returns a (system_prompt, user_prompt) tuple.
    """
    raise NotImplementedError


def write_draft(
    pitch: object,
    brief: object,
    voice: object,
    guidance: str,
    provider: LLMProvider,
) -> object:
    """Generate a draft column from a pitch using the LLM provider.

    Assembles the prompt, calls the provider, parses the response
    into a Draft model, and runs post-checks (word count, citations).
    """
    raise NotImplementedError
