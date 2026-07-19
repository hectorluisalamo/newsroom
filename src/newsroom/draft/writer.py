# ABOUTME: Draft writing logic for the Newsroom pipeline.
# ABOUTME: Assembles prompts and calls the LLM to produce opinion columns.
"""Draft writing and prompt assembly."""

from __future__ import annotations

import datetime as dt
import logging

from newsroom.draft.provider import LLMProvider
from newsroom.models import BriefPack, Draft, Pitch, VoiceConstitution

logger = logging.getLogger(__name__)

DEFAULT_TARGET_WORDS = 700
DEFAULT_TOLERANCE = 100
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_TOKENS = 1500


def _format_list_section(label: str, items: list[str]) -> str:
    """Render a labelled section from a list of strings, e.g. voice traits."""
    if not items:
        return f"{label}: (none)"
    lines = "\n".join(f"- {item}" for item in items)
    return f"{label}:\n{lines}"


def assemble_prompt(
    pitch: Pitch,
    brief: BriefPack,
    voice: VoiceConstitution,
    guidance: str,
    target_words: int = DEFAULT_TARGET_WORDS,
) -> tuple[str, str]:
    """Assemble system and user prompts for draft generation.

    Returns a (system_prompt, user_prompt) tuple. Pure and deterministic —
    no I/O, no randomness.
    """
    system_sections = [
        _format_list_section("Beliefs", voice.beliefs),
        _format_list_section("Tone", voice.tone),
        _format_list_section("Forbidden moves", voice.forbidden_moves),
        _format_list_section("Taboo phrases", voice.taboo_phrases),
        _format_list_section("Required habits", voice.required_habits),
    ]
    system_prompt = (
        "\n\n".join(system_sections)
        + "\n\n"
        + f"Write a column of approximately {target_words} words.\n\n"
        + "Cite every claim inline with `[src:N]` where N is the 1-based "
        "index into the numbered Sources list provided in the user prompt. "
        "Do not browse the web or introduce sources beyond the ones "
        "provided; use only the provided sources."
    )

    source_lines = [
        f"[src:{n}] {url}" for n, url in enumerate(pitch.source_urls, start=1)
    ]

    matching_cluster = next(
        (
            cluster
            for cluster in brief.clusters
            if cluster.cluster_id == pitch.cluster_id
        ),
        None,
    )
    if matching_cluster is not None and matching_cluster.items:
        excerpt_lines = [
            f"- {item.title} ({item.source_name}): {item.summary}"
            for item in matching_cluster.items
        ]
    else:
        # Fall back gracefully to pitch data if no matching brief cluster is
        # found (e.g. a stale brief_pack_ref) — never crash prompt assembly.
        excerpt_lines = [f"- {point}" for point in pitch.key_points]

    user_prompt = (
        "Pitch:\n"
        f"Title: {pitch.title}\n"
        f"Thesis/Angle: {pitch.thesis_angle}\n"
        f"Why now: {pitch.why_now}\n"
        "Key points:\n" + "\n".join(f"- {point}" for point in pitch.key_points) + "\n\n"
        "Sources:\n" + "\n".join(source_lines) + "\n\n"
        "Brief excerpts:\n" + "\n".join(excerpt_lines) + "\n\n"
        f"Editor guidance:\n{guidance}"
    )

    return system_prompt, user_prompt


def write_draft(
    pitch: Pitch,
    brief: BriefPack,
    voice: VoiceConstitution,
    guidance: str,
    provider: LLMProvider,
    *,
    now: dt.datetime,
    beat: str,
    date: dt.date,
    target_words: int = DEFAULT_TARGET_WORDS,
    tolerance: int = DEFAULT_TOLERANCE,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Draft:
    """Generate a draft column from a pitch using the LLM provider.

    Assembles the prompt, calls the provider, and — if the response's word
    count falls outside `target_words +/- tolerance` — retries with a
    corrective length instruction appended to the original user prompt, up
    to `max_retries` additional calls (hard cap: at most `1 + max_retries`
    total `generate()` calls). Each retry appends a single fresh correction
    to the original prompt rather than stacking onto the previous retry's
    prompt, so the model never sees conflicting length instructions. If the
    cap is exhausted without landing in tolerance, the last response is
    accepted and a warning is logged — word count is a post-check here, not
    a hard gate (that's QA, Night 4).
    """
    system_prompt, base_user_prompt = assemble_prompt(
        pitch, brief, voice, guidance, target_words=target_words
    )
    max_tokens = max(DEFAULT_MAX_TOKENS, int(target_words * 3))

    response = provider.generate(system_prompt, base_user_prompt, max_tokens=max_tokens)
    word_count = len(response.text.split())

    attempt = 0
    while abs(word_count - target_words) > tolerance and attempt < max_retries:
        attempt += 1
        direction = "shorter" if word_count > target_words else "longer"
        user_prompt = (
            f"{base_user_prompt}\n\n"
            f"Your previous draft was {word_count} words; the target is "
            f"{target_words} words (+/- {tolerance}). Revise to be "
            f"significantly {direction} and land within tolerance."
        )
        response = provider.generate(system_prompt, user_prompt, max_tokens=max_tokens)
        word_count = len(response.text.split())

    if abs(word_count - target_words) > tolerance:
        logger.warning(
            "write_draft: word count %d outside target %d +/- %d after %d "
            "retries; accepting last response (pitch_id=%s)",
            word_count,
            target_words,
            tolerance,
            attempt,
            pitch.pitch_id,
        )

    return Draft(
        beat=beat,
        date=date,
        pitch_id=pitch.pitch_id,
        title=pitch.title,
        body_md=response.text,
        word_count=word_count,
        sources=pitch.source_urls,
        guidance_used=guidance,
        model_id=provider.model_id,
        generated_at=now,
        token_usage=response.token_usage,
    )
