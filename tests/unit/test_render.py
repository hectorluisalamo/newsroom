# ABOUTME: Unit tests for output rendering.
# ABOUTME: Validates JSON and Markdown output formatting and determinism.
"""Tests for newsroom.render."""

import json
from datetime import date, datetime, timezone

from newsroom.models import (
    BriefCluster,
    BriefPack,
    Draft,
    FeedItem,
    Pitch,
    PitchSet,
    QAFinding,
    QAReport,
)
from newsroom.render.render import (
    render_brief_json,
    render_brief_md,
    render_draft_json,
    render_draft_md,
    render_pitches_json,
    render_pitches_md,
    render_report_json,
)

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_feed_item(item_id: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=f"Story {item_id}",
        url=f"https://example.com/{item_id}",
        source_name="Example Source",
        source_feed_url="https://example.com/feed.xml",
        published_at=_NOW,
        summary="A short summary.",
        raw_tags=[],
        beat="science_tech",
    )


def _make_cluster(
    cluster_id: str, label: str, *, centroid_keywords: list[str]
) -> BriefCluster:
    items = [_make_feed_item(f"{cluster_id}-1")]
    return BriefCluster(
        cluster_id=cluster_id,
        label=label,
        items=items,
        centroid_keywords=centroid_keywords,
        recency_score=0.75,
        source_diversity=1,
        size=len(items),
    )


def _make_brief_pack(clusters: list[BriefCluster]) -> BriefPack:
    return BriefPack(
        beat="science_tech",
        date=date(2026, 1, 15),
        since="48h",
        total_items_ingested=10,
        total_items_after_dedupe=5,
        clusters=clusters,
        generated_at=_NOW,
    )


def _make_pitch(
    pitch_id: str,
    title: str,
    *,
    key_points: list[str],
    risk_flags: list[str],
    source_urls: list[str] | None = None,
) -> Pitch:
    return Pitch(
        pitch_id=pitch_id,
        title=title,
        thesis_angle="A thesis.",
        why_now="Because now.",
        key_points=key_points,
        source_urls=source_urls
        or [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ],
        risk_flags=risk_flags,
        cluster_id="cluster-1",
        angle="contrarian",
    )


def _make_pitch_set(pitches: list[Pitch]) -> PitchSet:
    return PitchSet(
        beat="science_tech",
        date=date(2026, 1, 15),
        pitches=pitches,
        brief_pack_ref="brief-ref-1",
        generated_at=_NOW,
    )


def _make_draft(
    *,
    title: str = "A Draft Title",
    body_md: str = "Body text with [src:1] and [src:2] citations.",
    sources: list[str] | None = None,
) -> Draft:
    return Draft(
        beat="science_tech",
        date=date(2026, 1, 15),
        pitch_id="p1",
        title=title,
        body_md=body_md,
        word_count=len(body_md.split()),
        sources=sources
        or [
            "https://example.com/a",
            "https://example.com/b",
        ],
        guidance_used="Keep it punchy.",
        model_id="fake-model-v1",
        generated_at=_NOW,
        token_usage={"input_tokens": 100, "output_tokens": 200},
    )


class TestRenderBriefJson:
    def test_round_trips_as_valid_json(self):
        brief = _make_brief_pack(
            [_make_cluster("c1", "Cluster One", centroid_keywords=["ai"])]
        )

        rendered = render_brief_json(brief)
        parsed = json.loads(rendered)

        assert parsed["beat"] == "science_tech"
        assert len(parsed["clusters"]) == 1

    def test_repeated_calls_are_byte_identical(self):
        brief = _make_brief_pack(
            [_make_cluster("c1", "Cluster One", centroid_keywords=["ai"])]
        )

        first = render_brief_json(brief)
        second = render_brief_json(brief)

        assert first == second


class TestRenderBriefMd:
    def test_header_includes_beat_and_iso_date(self):
        brief = _make_brief_pack([])

        rendered = render_brief_md(brief)

        assert "science_tech" in rendered.splitlines()[0]
        assert "2026-01-15" in rendered.splitlines()[0]

    def test_includes_count_lines(self):
        brief = _make_brief_pack([])

        rendered = render_brief_md(brief)

        assert "- Items ingested: 10" in rendered
        assert "- Items after dedupe: 5" in rendered
        assert "- Clusters: 0" in rendered

    def test_one_section_per_cluster(self):
        brief = _make_brief_pack(
            [
                _make_cluster("c1", "Cluster One", centroid_keywords=[]),
                _make_cluster("c2", "Cluster Two", centroid_keywords=[]),
            ]
        )

        rendered = render_brief_md(brief)

        assert rendered.count("## Cluster One") == 1
        assert rendered.count("## Cluster Two") == 1

    def test_keywords_line_present_when_keywords_nonempty(self):
        brief = _make_brief_pack(
            [_make_cluster("c1", "Cluster One", centroid_keywords=["ai", "space"])]
        )

        rendered = render_brief_md(brief)

        assert "- Keywords: ai, space" in rendered

    def test_keywords_line_absent_when_keywords_empty(self):
        brief = _make_brief_pack(
            [_make_cluster("c1", "Cluster One", centroid_keywords=[])]
        )

        rendered = render_brief_md(brief)

        assert "- Keywords:" not in rendered

    def test_item_link_line_present_for_cluster_items(self):
        brief = _make_brief_pack(
            [_make_cluster("c1", "Cluster One", centroid_keywords=[])]
        )

        rendered = render_brief_md(brief)

        assert "  - [Story c1-1](https://example.com/c1-1) — Example Source" in rendered


class TestRenderPitchesJson:
    def test_round_trips_as_valid_json(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch("p1", "Pitch One", key_points=["a"], risk_flags=[]),
                _make_pitch("p2", "Pitch Two", key_points=[], risk_flags=["risky"]),
                _make_pitch("p3", "Pitch Three", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_json(pitch_set)
        parsed = json.loads(rendered)

        assert parsed["beat"] == "science_tech"
        assert len(parsed["pitches"]) == 3

    def test_repeated_calls_are_byte_identical(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch("p1", "Pitch One", key_points=["a"], risk_flags=[]),
                _make_pitch("p2", "Pitch Two", key_points=[], risk_flags=["risky"]),
                _make_pitch("p3", "Pitch Three", key_points=[], risk_flags=[]),
            ]
        )

        first = render_pitches_json(pitch_set)
        second = render_pitches_json(pitch_set)

        assert first == second


class TestRenderPitchesMd:
    def test_one_card_per_pitch(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch("p1", "Pitch One", key_points=[], risk_flags=[]),
                _make_pitch("p2", "Pitch Two", key_points=[], risk_flags=[]),
                _make_pitch("p3", "Pitch Three", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_md(pitch_set)

        assert rendered.count("## Pitch One") == 1
        assert rendered.count("## Pitch Two") == 1
        assert rendered.count("## Pitch Three") == 1

    def test_scalar_fields_present_in_pitch_card(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch("p1", "Pitch One", key_points=[], risk_flags=[]),
                _make_pitch("p2", "Pitch Two", key_points=[], risk_flags=[]),
                _make_pitch("p3", "Pitch Three", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_md(pitch_set)

        assert "- Angle: contrarian" in rendered
        assert "- Thesis: A thesis." in rendered
        assert "- Why now: Because now." in rendered

    def test_key_points_block_present_only_when_nonempty(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch(
                    "p1",
                    "Has Points",
                    key_points=["point a", "point b"],
                    risk_flags=[],
                ),
                _make_pitch("p2", "No Points", key_points=[], risk_flags=[]),
                _make_pitch("p3", "Also No Points", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_md(pitch_set)

        lines = rendered.splitlines()
        assert "## Has Points" in lines, (
            "expected '## Has Points' section in rendered output"
        )
        assert "## No Points" in lines, (
            "expected '## No Points' section in rendered output"
        )
        has_points_idx = lines.index("## Has Points")
        no_points_idx = lines.index("## No Points")
        has_points_section = "\n".join(lines[has_points_idx:no_points_idx])
        assert "- Key points:" in has_points_section
        assert "  - point a" in has_points_section

        no_points_section = "\n".join(lines[no_points_idx:])
        assert "- Key points:" not in no_points_section

    def test_risk_flags_line_present_only_when_nonempty(self):
        pitch_set = _make_pitch_set(
            [
                _make_pitch(
                    "p1", "Risky Pitch", key_points=[], risk_flags=["speculative"]
                ),
                _make_pitch("p2", "Safe Pitch", key_points=[], risk_flags=[]),
                _make_pitch("p3", "Also Safe", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_md(pitch_set)

        lines = rendered.splitlines()
        assert "## Risky Pitch" in lines, (
            "expected '## Risky Pitch' section in rendered output"
        )
        assert "## Safe Pitch" in lines, (
            "expected '## Safe Pitch' section in rendered output"
        )
        risky_idx = lines.index("## Risky Pitch")
        safe_idx = lines.index("## Safe Pitch")
        risky_section = "\n".join(lines[risky_idx:safe_idx])
        assert "- Risk flags: speculative" in risky_section

        safe_section = "\n".join(lines[safe_idx:])
        assert "- Risk flags:" not in safe_section

    def test_all_source_urls_are_listed(self):
        urls = [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
            "https://example.com/d",
        ]
        pitch_set = _make_pitch_set(
            [
                _make_pitch(
                    "p1", "Pitch One", key_points=[], risk_flags=[], source_urls=urls
                ),
                _make_pitch("p2", "Pitch Two", key_points=[], risk_flags=[]),
                _make_pitch("p3", "Pitch Three", key_points=[], risk_flags=[]),
            ]
        )

        rendered = render_pitches_md(pitch_set)

        lines = rendered.splitlines()
        assert "## Pitch One" in lines, "expected '## Pitch One' section"
        assert "## Pitch Two" in lines, "expected '## Pitch Two' section"
        p1_start = lines.index("## Pitch One")
        p2_start = lines.index("## Pitch Two")
        p1_section = "\n".join(lines[p1_start:p2_start])
        for url in urls:
            assert f"  - {url}" in p1_section


def _make_report(
    *,
    passed: bool = True,
    findings: list[QAFinding] | None = None,
) -> QAReport:
    return QAReport(
        beat="science_tech",
        date=date(2026, 1, 15),
        pitch_id="p1",
        passed=passed,
        findings=findings
        if findings is not None
        else [
            QAFinding(
                check_name="check_hedging",
                severity="warning",
                location="paragraph-1",
                message="Hedging ratio exceeds threshold.",
                details={"ratio": 0.2},
            )
        ],
        checks_run=["check_hedging"],
        generated_at=_NOW,
    )


class TestRenderDraftJson:
    def test_round_trips_as_valid_json(self):
        draft = _make_draft()

        rendered = render_draft_json(draft)
        parsed = json.loads(rendered)

        assert parsed["title"] == "A Draft Title"
        assert parsed["word_count"] == draft.word_count
        assert parsed["sources"] == [
            "https://example.com/a",
            "https://example.com/b",
        ]

    def test_repeated_calls_are_byte_identical(self):
        draft = _make_draft()

        first = render_draft_json(draft)
        second = render_draft_json(draft)

        assert first == second


class TestRenderDraftMd:
    def test_includes_title_heading(self):
        draft = _make_draft(title="My Great Column")

        rendered = render_draft_md(draft)

        assert "# My Great Column" in rendered.splitlines()

    def test_includes_body(self):
        draft = _make_draft(body_md="Some body with [src:1] citation.")

        rendered = render_draft_md(draft)

        assert "Some body with [src:1] citation." in rendered

    def test_sources_section_is_numbered_list(self):
        draft = _make_draft(sources=["https://example.com/a", "https://example.com/b"])

        rendered = render_draft_md(draft)

        assert "## Sources" in rendered
        lines = rendered.splitlines()
        sources_idx = lines.index("## Sources")
        sources_section = "\n".join(lines[sources_idx:])
        assert "1. https://example.com/a" in sources_section
        assert "2. https://example.com/b" in sources_section


class TestRenderReportJson:
    def test_round_trips_as_valid_json(self):
        report = _make_report()

        rendered = render_report_json(report)
        parsed = json.loads(rendered)

        assert parsed["beat"] == "science_tech"
        assert parsed["pitch_id"] == "p1"
        assert parsed["passed"] is True
        assert parsed["checks_run"] == ["check_hedging"]
        assert len(parsed["findings"]) == 1
        assert parsed["findings"][0]["check_name"] == "check_hedging"

    def test_repeated_calls_are_byte_identical(self):
        report = _make_report()

        first = render_report_json(report)
        second = render_report_json(report)

        assert first == second
