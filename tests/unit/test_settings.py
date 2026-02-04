# ABOUTME: Unit tests for configuration loading functions.
# ABOUTME: Validates YAML/Markdown parsing, error handling, and typed model output.
"""Tests for newsroom.settings."""

from pathlib import Path

import pytest

from newsroom.models import ClusterConfig, FeedSource, QAConfig, VoiceConstitution
from newsroom.settings import (
    ConfigError,
    load_cluster_config,
    load_qa_config,
    load_sources,
    load_voice,
)

# Path to committed example configs (golden-path tests)
_CONFIG_EXAMPLE = Path(__file__).resolve().parent.parent.parent / "config.example"

# Path to intentionally broken fixtures
_BAD_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "config"


# ---------------------------------------------------------------------------
# load_sources — golden path against config.example/
# ---------------------------------------------------------------------------


class TestLoadSourcesGolden:
    def test_loads_science_tech_from_config_example(self):
        sources = load_sources("science_tech", _CONFIG_EXAMPLE)
        assert len(sources) == 5
        assert all(isinstance(s, FeedSource) for s in sources)
        names = [s.name for s in sources]
        assert "Ars Technica" in names


# ---------------------------------------------------------------------------
# load_sources — controlled tests via tmp_path
# ---------------------------------------------------------------------------


class TestLoadSources:
    def test_returns_list_of_feed_source(self, tmp_path):
        (tmp_path / "sources.yaml").write_text(
            "test_beat:\n"
            "  rss:\n"
            '    - name: "Feed A"\n'
            '      url: "https://example.com/a"\n'
            '    - name: "Feed B"\n'
            '      url: "https://example.com/b"\n'
        )
        sources = load_sources("test_beat", tmp_path)
        assert len(sources) == 2
        assert sources[0].name == "Feed A"
        assert isinstance(sources[0], FeedSource)

    def test_nonexistent_directory_raises(self):
        missing = Path("/nonexistent/dir/that/does/not/exist")
        with pytest.raises(ConfigError, match=str(missing)):
            load_sources("science_tech", missing)

    def test_missing_file_in_existing_dir_raises(self, tmp_path):
        with pytest.raises(ConfigError, match="sources.yaml"):
            load_sources("science_tech", tmp_path)

    def test_missing_beat_key_raises(self, tmp_path):
        (tmp_path / "sources.yaml").write_text(
            "other_beat:\n  rss:\n    - name: X\n      url: https://x.com\n"
        )
        with pytest.raises(ConfigError, match="politics"):
            load_sources("politics", tmp_path)

    def test_missing_rss_key_raises(self, tmp_path):
        (tmp_path / "sources.yaml").write_text("science_tech:\n  social: []\n")
        with pytest.raises(ConfigError, match="rss"):
            load_sources("science_tech", tmp_path)

    def test_invalid_feed_entry_raises(self, tmp_path):
        (tmp_path / "sources.yaml").write_text(
            "beat:\n  rss:\n    - name: Bad\n      url: not-a-url\n"
        )
        with pytest.raises(ConfigError):
            load_sources("beat", tmp_path)

    def test_empty_yaml_raises(self, tmp_path):
        (tmp_path / "sources.yaml").write_text("")
        with pytest.raises(ConfigError):
            load_sources("beat", tmp_path)

    def test_social_key_ignored(self, tmp_path):
        (tmp_path / "sources.yaml").write_text(
            "beat:\n"
            "  rss:\n"
            '    - name: "Feed"\n'
            '      url: "https://example.com/feed"\n'
            "  social:\n"
            '    - name: "Twitter"\n'
            '      url: "https://twitter.com"\n'
        )
        sources = load_sources("beat", tmp_path)
        assert len(sources) == 1


# ---------------------------------------------------------------------------
# load_qa_config — golden path against config.example/
# ---------------------------------------------------------------------------


class TestLoadQAConfigGolden:
    def test_loads_from_config_example(self):
        cfg = load_qa_config(_CONFIG_EXAMPLE)
        assert isinstance(cfg, QAConfig)
        assert cfg.hedging.max_ratio == 0.15
        assert "arguably" in cfg.hedging.phrases
        assert cfg.source_attribution.require_citation_near_stats is True
        assert cfg.voice_drift.max_sentence_length == 60


# ---------------------------------------------------------------------------
# load_qa_config — controlled tests via tmp_path
# ---------------------------------------------------------------------------

_VALID_QA_YAML = (
    "hedging:\n"
    "  max_ratio: 0.2\n"
    "  phrases:\n"
    '    - "maybe"\n'
    "source_attribution:\n"
    "  require_citation_near_stats: false\n"
    '  citation_pattern: "\\\\[ref:\\\\d+\\\\]"\n'
    "voice_drift:\n"
    "  max_avg_sentence_length: 30\n"
    "  min_avg_sentence_length: 5\n"
    "  max_sentence_length: 50\n"
)


class TestLoadQAConfig:
    def test_returns_qa_config(self, tmp_path):
        (tmp_path / "qa.yaml").write_text(_VALID_QA_YAML)
        cfg = load_qa_config(tmp_path)
        assert isinstance(cfg, QAConfig)
        assert cfg.hedging.max_ratio == 0.2

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ConfigError, match="qa.yaml"):
            load_qa_config(tmp_path)

    def test_missing_dir_raises(self):
        with pytest.raises(ConfigError):
            load_qa_config(Path("/nonexistent/dir"))

    def test_invalid_yaml_raises(self, tmp_path):
        (tmp_path / "qa.yaml").write_text("hedging:\n  max_ratio: banana\n")
        with pytest.raises(ConfigError):
            load_qa_config(tmp_path)

    def test_empty_yaml_raises(self, tmp_path):
        (tmp_path / "qa.yaml").write_text("")
        with pytest.raises(ConfigError):
            load_qa_config(tmp_path)


# ---------------------------------------------------------------------------
# load_cluster_config — golden path against config.example/
# ---------------------------------------------------------------------------


class TestLoadClusterConfigGolden:
    def test_loads_from_config_example(self):
        cfg = load_cluster_config(_CONFIG_EXAMPLE)
        assert isinstance(cfg, ClusterConfig)
        assert cfg.tfidf.max_features == 5000
        assert cfg.tfidf.ngram_range == [1, 2]
        assert cfg.clustering.method == "agglomerative"
        assert cfg.keywords.top_n == 5


# ---------------------------------------------------------------------------
# load_cluster_config — controlled tests via tmp_path
# ---------------------------------------------------------------------------

_VALID_CLUSTER_YAML = (
    "tfidf:\n"
    "  max_features: 3000\n"
    "  ngram_range: [1, 1]\n"
    '  stop_words: "english"\n'
    "  min_df: 1\n"
    "clustering:\n"
    '  method: "agglomerative"\n'
    "  distance_threshold: 0.5\n"
    '  linkage: "ward"\n'
    "keywords:\n"
    "  top_n: 3\n"
)


class TestLoadClusterConfig:
    def test_returns_cluster_config(self, tmp_path):
        (tmp_path / "cluster.yaml").write_text(_VALID_CLUSTER_YAML)
        cfg = load_cluster_config(tmp_path)
        assert isinstance(cfg, ClusterConfig)
        assert cfg.tfidf.max_features == 3000

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ConfigError, match="cluster.yaml"):
            load_cluster_config(tmp_path)

    def test_invalid_ngram_range_raises(self, tmp_path):
        bad = _VALID_CLUSTER_YAML.replace("ngram_range: [1, 1]", "ngram_range: [2, 1]")
        (tmp_path / "cluster.yaml").write_text(bad)
        with pytest.raises(ConfigError):
            load_cluster_config(tmp_path)

    def test_empty_yaml_raises(self, tmp_path):
        (tmp_path / "cluster.yaml").write_text("")
        with pytest.raises(ConfigError):
            load_cluster_config(tmp_path)


# ---------------------------------------------------------------------------
# load_voice — golden path against config.example/
# ---------------------------------------------------------------------------


class TestLoadVoiceGolden:
    def test_loads_science_tech_from_config_example(self):
        voice = load_voice("science_tech", _CONFIG_EXAMPLE)
        assert isinstance(voice, VoiceConstitution)
        assert len(voice.beliefs) > 0
        assert len(voice.taboo_phrases) > 0
        # Voice file uses quoted phrases: - "It remains to be seen"
        assert '"It remains to be seen"' in voice.taboo_phrases


# ---------------------------------------------------------------------------
# load_voice — controlled tests via tmp_path
# ---------------------------------------------------------------------------

_VALID_VOICE_MD = """\
# Test Voice Constitution

## Beliefs
- Belief one.
- Belief two.

## Tone
- Conversational but informed.

## Forbidden Moves
- Do not predict the future.
- Do not use hype words.

## Taboo Phrases
- It remains to be seen
- Only time will tell

## Required Habits
- Every claim must trace to a source.
"""


class TestLoadVoice:
    def test_returns_voice_constitution(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        (voices / "test.md").write_text(_VALID_VOICE_MD)
        voice = load_voice("test", tmp_path)
        assert isinstance(voice, VoiceConstitution)
        assert voice.beliefs == ["Belief one.", "Belief two."]
        assert voice.taboo_phrases == ["It remains to be seen", "Only time will tell"]

    def test_preserves_bullet_order(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        (voices / "b.md").write_text(_VALID_VOICE_MD)
        voice = load_voice("b", tmp_path)
        assert voice.forbidden_moves == [
            "Do not predict the future.",
            "Do not use hype words.",
        ]

    def test_nonexistent_beat_raises(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        with pytest.raises(ConfigError, match="nonexistent"):
            load_voice("nonexistent", tmp_path)

    def test_missing_voices_dir_raises(self, tmp_path):
        with pytest.raises(ConfigError):
            load_voice("test", tmp_path)

    def test_missing_section_raises(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        # Missing "Required Habits" section
        incomplete = (
            "## Beliefs\n- B\n\n"
            "## Tone\n- T\n\n"
            "## Forbidden Moves\n- F\n\n"
            "## Taboo Phrases\n- P\n"
        )
        (voices / "bad.md").write_text(incomplete)
        with pytest.raises(ConfigError, match="Required Habits"):
            load_voice("bad", tmp_path)

    def test_ignores_non_bullet_content(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        md = (
            "## Beliefs\n"
            "Some prose paragraph that is not a bullet.\n"
            "- Actual belief.\n"
            "More prose.\n"
            "\n"
            "## Tone\n- Tone item.\n"
            "## Forbidden Moves\n- Forbidden item.\n"
            "## Taboo Phrases\n- Taboo item.\n"
            "## Required Habits\n- Habit item.\n"
        )
        (voices / "t.md").write_text(md)
        voice = load_voice("t", tmp_path)
        assert voice.beliefs == ["Actual belief."]

    def test_ignores_asterisk_bullets(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        md = (
            "## Beliefs\n* Star bullet.\n- Dash bullet.\n"
            "## Tone\n- T.\n"
            "## Forbidden Moves\n- F.\n"
            "## Taboo Phrases\n- P.\n"
            "## Required Habits\n- H.\n"
        )
        (voices / "t.md").write_text(md)
        voice = load_voice("t", tmp_path)
        assert voice.beliefs == ["Dash bullet."]

    def test_ignores_numbered_lists(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        md = (
            "## Beliefs\n1. Numbered item.\n- Dash item.\n"
            "## Tone\n- T.\n"
            "## Forbidden Moves\n- F.\n"
            "## Taboo Phrases\n- P.\n"
            "## Required Habits\n- H.\n"
        )
        (voices / "t.md").write_text(md)
        voice = load_voice("t", tmp_path)
        assert voice.beliefs == ["Dash item."]

    def test_blank_lines_ignored(self, tmp_path):
        voices = tmp_path / "voices"
        voices.mkdir()
        md = (
            "## Beliefs\n\n- B1.\n\n- B2.\n\n"
            "## Tone\n- T.\n"
            "## Forbidden Moves\n- F.\n"
            "## Taboo Phrases\n- P.\n"
            "## Required Habits\n- H.\n"
        )
        (voices / "t.md").write_text(md)
        voice = load_voice("t", tmp_path)
        assert voice.beliefs == ["B1.", "B2."]
