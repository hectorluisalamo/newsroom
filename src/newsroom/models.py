# ABOUTME: Pydantic data models for the Newsroom pipeline.
# ABOUTME: Purely declarative — no business logic lives here.
"""Pydantic data models for the Newsroom pipeline.

All models are declarative. Business logic belongs in the modules that
consume these models, not here.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, HttpUrl, field_validator


def _require_utc(value: datetime) -> datetime:
    """Reject naive datetimes; require UTC-aware tzinfo."""
    if value.tzinfo is None:
        msg = "datetime must be UTC-aware; got naive datetime without tzinfo"
        raise ValueError(msg)
    return value


# ---------------------------------------------------------------------------
# FeedItem — a single normalized RSS article
# ---------------------------------------------------------------------------


class FeedItem(BaseModel):
    """A single normalized RSS article."""

    item_id: str
    title: str
    url: HttpUrl
    source_name: str
    source_feed_url: HttpUrl
    published_at: datetime
    summary: str
    raw_tags: list[str] = []
    beat: str

    @field_validator("published_at")
    @classmethod
    def _published_at_utc(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @field_validator("summary")
    @classmethod
    def _summary_max_length(cls, v: str) -> str:
        if len(v) > 500:
            msg = f"summary must be at most 500 characters, got {len(v)}"
            raise ValueError(msg)
        return v


# ---------------------------------------------------------------------------
# BriefCluster — a group of related FeedItems
# ---------------------------------------------------------------------------


class BriefCluster(BaseModel):
    """A cluster of related feed items forming a story thread."""

    cluster_id: str
    label: str
    items: list[FeedItem]
    centroid_keywords: list[str]
    recency_score: float
    source_diversity: int
    size: int

    @field_validator("recency_score")
    @classmethod
    def _recency_score_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            msg = f"recency_score must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


# ---------------------------------------------------------------------------
# BriefPack — a daily research brief
# ---------------------------------------------------------------------------


class BriefPack(BaseModel):
    """The full research brief for a beat and date."""

    beat: str
    date: date
    since: str
    total_items_ingested: int
    total_items_after_dedupe: int
    clusters: list[BriefCluster]
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _generated_at_utc(cls, v: datetime) -> datetime:
        return _require_utc(v)


# ---------------------------------------------------------------------------
# Pitch — a single story candidate
# ---------------------------------------------------------------------------


class Pitch(BaseModel):
    """A story pitch derived from a cluster."""

    pitch_id: str
    title: str
    thesis_angle: str
    why_now: str
    key_points: list[str]
    source_urls: list[HttpUrl]
    risk_flags: list[str]
    cluster_id: str
    angle: str

    @field_validator("source_urls")
    @classmethod
    def _source_urls_bounds(cls, v: list[HttpUrl]) -> list[HttpUrl]:
        if len(v) < 3:
            msg = f"source_urls must contain at least 3 URLs, got {len(v)}"
            raise ValueError(msg)
        if len(v) > 10:
            return v[:10]
        return v


# ---------------------------------------------------------------------------
# PitchSet — exactly 3 pitches for a beat/date
# ---------------------------------------------------------------------------


class PitchSet(BaseModel):
    """A set of exactly 3 pitches for a beat and date."""

    beat: str
    date: date
    pitches: list[Pitch]
    brief_pack_ref: str
    generated_at: datetime

    @field_validator("pitches")
    @classmethod
    def _exactly_three_pitches(cls, v: list[Pitch]) -> list[Pitch]:
        if len(v) != 3:
            msg = f"pitches must contain exactly 3 items, got {len(v)}"
            raise ValueError(msg)
        return v

    @field_validator("generated_at")
    @classmethod
    def _generated_at_utc(cls, v: datetime) -> datetime:
        return _require_utc(v)


# ---------------------------------------------------------------------------
# Draft — an LLM-generated column
# ---------------------------------------------------------------------------


class Draft(BaseModel):
    """A generated opinion column draft."""

    beat: str
    date: date
    pitch_id: str
    title: str
    body_md: str
    word_count: int
    sources: list[HttpUrl]
    guidance_used: str
    model_id: str
    generated_at: datetime
    token_usage: dict[str, int] | None = None

    @field_validator("generated_at")
    @classmethod
    def _generated_at_utc(cls, v: datetime) -> datetime:
        return _require_utc(v)


# ---------------------------------------------------------------------------
# QAFinding — a single QA check result
# ---------------------------------------------------------------------------


class QAFinding(BaseModel):
    """A single finding from a QA check."""

    check_name: str
    severity: Literal["error", "warning", "info"]
    location: str
    message: str
    details: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# QAReport — aggregated QA gate
# ---------------------------------------------------------------------------


class QAReport(BaseModel):
    """Aggregated QA report for a draft."""

    beat: str
    date: date
    pitch_id: str
    passed: bool
    findings: list[QAFinding]
    checks_run: list[str]
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _generated_at_utc(cls, v: datetime) -> datetime:
        return _require_utc(v)
