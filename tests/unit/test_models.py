# ABOUTME: Unit tests for the Pydantic data models.
# ABOUTME: Validates model construction, serialization, and field constraints.
"""Tests for newsroom.models."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from newsroom.models import (
    BriefCluster,
    BriefPack,
    ClusterConfig,
    ClusteringMethodConfig,
    Draft,
    FeedItem,
    FeedSource,
    HedgingConfig,
    KeywordsConfig,
    Pitch,
    PitchSet,
    QAConfig,
    QAFinding,
    QAReport,
    SourceAttributionConfig,
    TfidfConfig,
    VoiceConstitution,
    VoiceDriftConfig,
)

# ---------------------------------------------------------------------------
# Helpers — reusable factory data
# ---------------------------------------------------------------------------

_NOW_UTC = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_NAIVE_DT = datetime(2025, 1, 15, 12, 0, 0)  # no tzinfo
_URL = "https://example.com/article"
_FEED_URL = "https://example.com/feed.xml"


def _make_feed_item(**overrides):
    defaults = {
        "item_id": "a" * 64,
        "title": "Test Article",
        "url": _URL,
        "source_name": "Example",
        "source_feed_url": _FEED_URL,
        "published_at": _NOW_UTC,
        "summary": "A short summary.",
        "raw_tags": ["science"],
        "beat": "science_tech",
    }
    defaults.update(overrides)
    return FeedItem(**defaults)


def _make_brief_cluster(**overrides):
    defaults = {
        "cluster_id": "b" * 64,
        "label": "AI regulation",
        "items": [_make_feed_item()],
        "centroid_keywords": ["ai", "regulation", "policy", "gov", "tech"],
        "recency_score": 0.85,
        "source_diversity": 1,
        "size": 1,
    }
    defaults.update(overrides)
    return BriefCluster(**defaults)


def _make_pitch(**overrides):
    urls = [f"https://example.com/{i}" for i in range(5)]
    defaults = {
        "pitch_id": "science_tech-2025-01-15-0",
        "title": "Test Pitch",
        "thesis_angle": "AI regulation is heating up.",
        "why_now": "Three bills introduced this week.",
        "key_points": ["Point A", "Point B", "Point C"],
        "source_urls": urls,
        "risk_flags": [],
        "cluster_id": "b" * 64,
        "angle": "trend_spotter",
    }
    defaults.update(overrides)
    return Pitch(**defaults)


def _make_pitch_set(**overrides):
    defaults = {
        "beat": "science_tech",
        "date": date(2025, 1, 15),
        "pitches": [
            _make_pitch(pitch_id=f"science_tech-2025-01-15-{i}") for i in range(3)
        ],
        "brief_pack_ref": "out/science_tech/2025-01-15/brief.json",
        "generated_at": _NOW_UTC,
    }
    defaults.update(overrides)
    return PitchSet(**defaults)


def _make_draft(**overrides):
    defaults = {
        "beat": "science_tech",
        "date": date(2025, 1, 15),
        "pitch_id": "science_tech-2025-01-15-0",
        "title": "Why AI Regulation Matters Now",
        "body_md": "Body text with [src:1] citation.",
        "word_count": 700,
        "sources": ["https://example.com/1", "https://example.com/2"],
        "guidance_used": "Focus on policy impact.",
        "model_id": "claude-sonnet-4-20250514",
        "generated_at": _NOW_UTC,
        "token_usage": {"input": 1000, "output": 500},
    }
    defaults.update(overrides)
    return Draft(**defaults)


def _make_qa_finding(**overrides):
    defaults = {
        "check_name": "hedging_ratio",
        "severity": "warning",
        "location": "paragraph 3",
        "message": "Hedging ratio 0.18 exceeds 0.15 threshold.",
        "details": {"ratio": 0.18, "threshold": 0.15},
    }
    defaults.update(overrides)
    return QAFinding(**defaults)


def _make_qa_report(**overrides):
    defaults = {
        "beat": "science_tech",
        "date": date(2025, 1, 15),
        "pitch_id": "science_tech-2025-01-15-0",
        "passed": True,
        "findings": [],
        "checks_run": ["hedging_ratio", "citation_check"],
        "generated_at": _NOW_UTC,
    }
    defaults.update(overrides)
    return QAReport(**defaults)


# ---------------------------------------------------------------------------
# AC-1: All models importable
# ---------------------------------------------------------------------------


class TestImports:
    """All eight models are importable from newsroom.models."""

    def test_all_models_importable(self):
        for cls in (
            FeedItem,
            BriefCluster,
            BriefPack,
            Draft,
            Pitch,
            PitchSet,
            QAFinding,
            QAReport,
        ):
            assert cls is not None


# ---------------------------------------------------------------------------
# AC-2: Each model instantiates with valid data
# ---------------------------------------------------------------------------


class TestValidConstruction:
    """Each model can be constructed with valid example data."""

    def test_feed_item(self):
        item = _make_feed_item()
        assert item.title == "Test Article"

    def test_brief_cluster(self):
        cluster = _make_brief_cluster()
        assert cluster.label == "AI regulation"

    def test_brief_pack(self):
        pack = BriefPack(
            beat="science_tech",
            date=date(2025, 1, 15),
            since="48h",
            total_items_ingested=100,
            total_items_after_dedupe=80,
            clusters=[_make_brief_cluster()],
            generated_at=_NOW_UTC,
        )
        assert pack.total_items_ingested == 100

    def test_pitch(self):
        pitch = _make_pitch()
        assert pitch.angle == "trend_spotter"

    def test_pitch_set(self):
        ps = _make_pitch_set()
        assert len(ps.pitches) == 3

    def test_draft(self):
        draft = _make_draft()
        assert draft.word_count == 700

    def test_qa_finding(self):
        finding = _make_qa_finding()
        assert finding.severity == "warning"

    def test_qa_report(self):
        report = _make_qa_report()
        assert report.passed is True


# ---------------------------------------------------------------------------
# AC-3: Round-trip serialization (model → JSON → model)
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Each model survives .model_dump_json() → Model.model_validate_json()."""

    @pytest.mark.parametrize(
        "factory",
        [
            _make_feed_item,
            _make_brief_cluster,
            lambda: BriefPack(
                beat="science_tech",
                date=date(2025, 1, 15),
                since="48h",
                total_items_ingested=50,
                total_items_after_dedupe=40,
                clusters=[_make_brief_cluster()],
                generated_at=_NOW_UTC,
            ),
            _make_pitch,
            _make_pitch_set,
            _make_draft,
            _make_qa_finding,
            _make_qa_report,
        ],
        ids=[
            "FeedItem",
            "BriefCluster",
            "BriefPack",
            "Pitch",
            "PitchSet",
            "Draft",
            "QAFinding",
            "QAReport",
        ],
    )
    def test_round_trip(self, factory):
        instance = factory()
        json_str = instance.model_dump_json()
        restored = type(instance).model_validate_json(json_str)
        assert restored == instance


# ---------------------------------------------------------------------------
# AC-4: FeedItem rejects naive datetime
# ---------------------------------------------------------------------------


class TestFeedItemNaiveDatetime:
    def test_rejects_naive_published_at(self):
        with pytest.raises(ValidationError, match="UTC"):
            _make_feed_item(published_at=_NAIVE_DT)


# ---------------------------------------------------------------------------
# AC-5: FeedItem rejects summary > 500 chars
# ---------------------------------------------------------------------------


class TestFeedItemSummaryLength:
    def test_rejects_long_summary(self):
        with pytest.raises(ValidationError):
            _make_feed_item(summary="x" * 501)

    def test_accepts_exactly_500(self):
        item = _make_feed_item(summary="x" * 500)
        assert len(item.summary) == 500


# ---------------------------------------------------------------------------
# AC-6: Pitch rejects < 3 source_urls
# ---------------------------------------------------------------------------


class TestPitchSourceUrlsMin:
    def test_rejects_fewer_than_3(self):
        with pytest.raises(ValidationError):
            _make_pitch(source_urls=["https://example.com/1", "https://example.com/2"])

    def test_accepts_exactly_3(self):
        urls = [f"https://example.com/{i}" for i in range(3)]
        pitch = _make_pitch(source_urls=urls)
        assert len(pitch.source_urls) == 3


# ---------------------------------------------------------------------------
# AC-7: Pitch truncates > 10 source_urls to first 10
# ---------------------------------------------------------------------------


class TestPitchSourceUrlsMax:
    def test_truncates_to_first_10(self):
        urls = [f"https://example.com/{i}" for i in range(15)]
        pitch = _make_pitch(source_urls=urls)
        assert len(pitch.source_urls) == 10
        # Verify order preserved — first 10 kept
        for i in range(10):
            assert str(pitch.source_urls[i]) == f"https://example.com/{i}"

    def test_accepts_exactly_10(self):
        urls = [f"https://example.com/{i}" for i in range(10)]
        pitch = _make_pitch(source_urls=urls)
        assert len(pitch.source_urls) == 10


# ---------------------------------------------------------------------------
# AC-8: PitchSet requires exactly 3 pitches
# ---------------------------------------------------------------------------


class TestPitchSetCount:
    def test_rejects_fewer_than_3(self):
        with pytest.raises(ValidationError):
            _make_pitch_set(pitches=[_make_pitch()])

    def test_rejects_more_than_3(self):
        with pytest.raises(ValidationError):
            _make_pitch_set(pitches=[_make_pitch(pitch_id=f"p-{i}") for i in range(4)])


# ---------------------------------------------------------------------------
# AC-9: BriefCluster.recency_score bounds
# ---------------------------------------------------------------------------


class TestRecencyScoreBounds:
    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            _make_brief_cluster(recency_score=-0.1)

    def test_rejects_above_one(self):
        with pytest.raises(ValidationError):
            _make_brief_cluster(recency_score=1.1)

    def test_accepts_zero(self):
        cluster = _make_brief_cluster(recency_score=0.0)
        assert cluster.recency_score == 0.0

    def test_accepts_one(self):
        cluster = _make_brief_cluster(recency_score=1.0)
        assert cluster.recency_score == 1.0


# ---------------------------------------------------------------------------
# AC-10: All datetime fields across all models reject naive datetimes
# ---------------------------------------------------------------------------


class TestNaiveDatetimeRejection:
    """Every model with a datetime field rejects naive datetimes."""

    def test_brief_pack_generated_at(self):
        with pytest.raises(ValidationError, match="UTC"):
            BriefPack(
                beat="science_tech",
                date=date(2025, 1, 15),
                since="48h",
                total_items_ingested=50,
                total_items_after_dedupe=40,
                clusters=[],
                generated_at=_NAIVE_DT,
            )

    def test_pitch_set_generated_at(self):
        with pytest.raises(ValidationError, match="UTC"):
            _make_pitch_set(generated_at=_NAIVE_DT)

    def test_draft_generated_at(self):
        with pytest.raises(ValidationError, match="UTC"):
            _make_draft(generated_at=_NAIVE_DT)

    def test_qa_report_generated_at(self):
        with pytest.raises(ValidationError, match="UTC"):
            _make_qa_report(generated_at=_NAIVE_DT)


# ---------------------------------------------------------------------------
# AC-11: QAFinding.severity rejects invalid values
# ---------------------------------------------------------------------------


class TestQAFindingSeverity:
    def test_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            _make_qa_finding(severity="critical")

    @pytest.mark.parametrize("level", ["error", "warning", "info"])
    def test_accepts_valid_severity(self, level):
        finding = _make_qa_finding(severity=level)
        assert finding.severity == level


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


class TestDefaults:
    """Fields with defaults produce expected values when omitted."""

    def test_feed_item_raw_tags_default(self):
        item = FeedItem(
            item_id="a" * 64,
            title="T",
            url=_URL,
            source_name="S",
            source_feed_url=_FEED_URL,
            published_at=_NOW_UTC,
            summary="S",
            beat="science_tech",
        )
        assert item.raw_tags == []

    def test_qa_finding_details_default(self):
        finding = QAFinding(
            check_name="test",
            severity="info",
            location="p1",
            message="ok",
        )
        assert finding.details == {}

    def test_draft_token_usage_default(self):
        draft = _make_draft(token_usage=None)
        assert draft.token_usage is None


# ---------------------------------------------------------------------------
# Config models — FeedSource
# ---------------------------------------------------------------------------


class TestFeedSource:
    def test_valid_construction(self):
        source = FeedSource(
            name="Ars Technica", url="https://feeds.arstechnica.com/feed"
        )
        assert source.name == "Ars Technica"

    def test_round_trip(self):
        source = FeedSource(
            name="Ars Technica", url="https://feeds.arstechnica.com/feed"
        )
        json_str = source.model_dump_json()
        restored = FeedSource.model_validate_json(json_str)
        assert restored == source

    def test_rejects_invalid_url(self):
        with pytest.raises(ValidationError):
            FeedSource(name="Bad", url="not-a-url")


# ---------------------------------------------------------------------------
# Config models — VoiceConstitution
# ---------------------------------------------------------------------------


def _make_voice_constitution(**overrides):
    defaults = {
        "beliefs": ["Tech is shaped by incentives."],
        "tone": ["Conversational but informed."],
        "forbidden_moves": ["Do not predict the future."],
        "taboo_phrases": ["It remains to be seen"],
        "required_habits": ["Every claim must trace to a source."],
    }
    defaults.update(overrides)
    return VoiceConstitution(**defaults)


class TestVoiceConstitution:
    def test_valid_construction(self):
        voice = _make_voice_constitution()
        assert voice.beliefs == ["Tech is shaped by incentives."]
        assert voice.taboo_phrases == ["It remains to be seen"]

    def test_round_trip(self):
        voice = _make_voice_constitution()
        json_str = voice.model_dump_json()
        restored = VoiceConstitution.model_validate_json(json_str)
        assert restored == voice

    def test_multiple_items_per_section(self):
        voice = _make_voice_constitution(
            taboo_phrases=["phrase one", "phrase two", "phrase three"],
        )
        assert len(voice.taboo_phrases) == 3

    def test_empty_section_allowed(self):
        voice = _make_voice_constitution(beliefs=[])
        assert voice.beliefs == []


# ---------------------------------------------------------------------------
# Config models — QAConfig family
# ---------------------------------------------------------------------------


def _make_qa_config(**overrides):
    defaults = {
        "hedging": {"max_ratio": 0.15, "phrases": ["arguably", "perhaps"]},
        "source_attribution": {
            "require_citation_near_stats": True,
            "citation_pattern": r"\[src:\d+\]",
        },
        "voice_drift": {
            "max_avg_sentence_length": 35,
            "min_avg_sentence_length": 10,
            "max_sentence_length": 60,
        },
    }
    defaults.update(overrides)
    return QAConfig(**defaults)


class TestQAConfig:
    def test_valid_construction(self):
        cfg = _make_qa_config()
        assert cfg.hedging.max_ratio == 0.15
        assert cfg.hedging.phrases == ["arguably", "perhaps"]
        assert cfg.source_attribution.require_citation_near_stats is True
        assert cfg.voice_drift.max_avg_sentence_length == 35

    def test_round_trip(self):
        cfg = _make_qa_config()
        json_str = cfg.model_dump_json()
        restored = QAConfig.model_validate_json(json_str)
        assert restored == cfg

    def test_nested_hedging_config(self):
        hc = HedgingConfig(max_ratio=0.2, phrases=["maybe"])
        assert hc.max_ratio == 0.2

    def test_nested_source_attribution_config(self):
        sa = SourceAttributionConfig(
            require_citation_near_stats=False,
            citation_pattern=r"\[ref:\d+\]",
        )
        assert sa.require_citation_near_stats is False

    def test_nested_voice_drift_config(self):
        vd = VoiceDriftConfig(
            max_avg_sentence_length=40,
            min_avg_sentence_length=8,
            max_sentence_length=70,
        )
        assert vd.min_avg_sentence_length == 8


# ---------------------------------------------------------------------------
# Config models — ClusterConfig family
# ---------------------------------------------------------------------------


def _make_cluster_config(**overrides):
    defaults = {
        "tfidf": {
            "max_features": 5000,
            "ngram_range": [1, 2],
            "stop_words": "english",
            "min_df": 2,
            "extra_stop_words": [],
        },
        "clustering": {
            "method": "agglomerative",
            "distance_threshold": 0.7,
            "linkage": "average",
        },
        "keywords": {
            "top_n": 5,
            "generic_filter": ["AI", "data"],
        },
    }
    defaults.update(overrides)
    return ClusterConfig(**defaults)


class TestClusterConfig:
    def test_valid_construction(self):
        cfg = _make_cluster_config()
        assert cfg.tfidf.max_features == 5000
        assert cfg.tfidf.ngram_range == [1, 2]
        assert cfg.clustering.method == "agglomerative"
        assert cfg.keywords.top_n == 5

    def test_round_trip(self):
        cfg = _make_cluster_config()
        json_str = cfg.model_dump_json()
        restored = ClusterConfig.model_validate_json(json_str)
        assert restored == cfg

    def test_extra_stop_words_default(self):
        tfidf = TfidfConfig(
            max_features=1000,
            ngram_range=[1, 1],
            stop_words="english",
            min_df=1,
        )
        assert tfidf.extra_stop_words == []

    def test_generic_filter_default(self):
        kw = KeywordsConfig(top_n=3)
        assert kw.generic_filter == []

    def test_clustering_method_config(self):
        cm = ClusteringMethodConfig(
            method="agglomerative",
            distance_threshold=0.5,
            linkage="ward",
        )
        assert cm.linkage == "ward"


class TestNgramRangeValidation:
    def test_rejects_length_one(self):
        with pytest.raises(ValidationError, match="ngram_range"):
            TfidfConfig(
                max_features=5000,
                ngram_range=[1],
                stop_words="english",
                min_df=2,
            )

    def test_rejects_length_three(self):
        with pytest.raises(ValidationError, match="ngram_range"):
            TfidfConfig(
                max_features=5000,
                ngram_range=[1, 2, 3],
                stop_words="english",
                min_df=2,
            )

    def test_rejects_min_greater_than_max(self):
        with pytest.raises(ValidationError, match="ngram_range"):
            TfidfConfig(
                max_features=5000,
                ngram_range=[2, 1],
                stop_words="english",
                min_df=2,
            )

    def test_accepts_equal_min_max(self):
        tfidf = TfidfConfig(
            max_features=5000,
            ngram_range=[1, 1],
            stop_words="english",
            min_df=2,
        )
        assert tfidf.ngram_range == [1, 1]
