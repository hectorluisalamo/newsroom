# ABOUTME: Unit tests for command-level bookkeeping in newsroom.commands.
# ABOUTME: Verifies total_items_ingested reflects raw entries, not post-filter items.
"""Unit tests for newsroom.commands."""

import json
from datetime import datetime, timezone
from pathlib import Path

from newsroom import commands
from newsroom.models import BriefCluster, FeedItem

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXTURE_DIR = _REPO_ROOT / "fixtures" / "science_tech"
_CONFIG_EXAMPLE = _REPO_ROOT / "config.example"
_FIXED_NOW = "2026-01-15T12:00:00Z"
_NOW_UTC = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_item(item_id: str, url: str, title: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=title,
        url=url,
        source_name="Example",
        source_feed_url="https://example.com/feed.xml",
        published_at=_NOW_UTC,
        summary="A short summary.",
        raw_tags=["science"],
        beat="science_tech",
    )


class _FakeClusterer:
    """Groups items into fixed chunks of 3, bypassing real TF-IDF clustering
    so this test's outcome doesn't depend on vectorizer/threshold tuning."""

    def __init__(self, config) -> None:
        pass

    def cluster(self, items: list[FeedItem]) -> list[BriefCluster]:
        clusters = []
        for i in range(0, len(items), 3):
            chunk = items[i : i + 3]
            clusters.append(
                BriefCluster(
                    cluster_id=f"cluster-{i}",
                    label=chunk[0].title,
                    items=chunk,
                    centroid_keywords=["k1", "k2", "k3"],
                    recency_score=0.9,
                    source_diversity=len({str(item.url) for item in chunk}),
                    size=len(chunk),
                )
            )
        return clusters


def test_total_items_ingested_reflects_raw_entries_not_post_filter(
    tmp_path, monkeypatch
):
    """normalize_all filters raw entries (missing fields, out-of-window items),
    so total_items_ingested must count raw entries fetched, not the smaller
    post-filter set normalize_all returns."""
    raw_entry_count = len(list(_FIXTURE_DIR.glob("sample_feed*.xml"))) * 6

    crafted_items = (
        [
            _make_item(
                f"a-{i}", f"https://a.example.com/{i}", f"Chip export story #{i}"
            )
            for i in range(3)
        ]
        + [
            _make_item(
                f"b-{i}", f"https://b.example.com/{i}", f"Quantum computing story #{i}"
            )
            for i in range(3)
        ]
        + [
            _make_item(
                f"c-{i}", f"https://c.example.com/{i}", f"Satellite launch story #{i}"
            )
            for i in range(3)
        ]
    )
    assert len(crafted_items) == 9  # fewer than raw entries, proving filtering happened

    monkeypatch.setattr(commands, "normalize_all", lambda *a, **kw: crafted_items)
    monkeypatch.setattr(commands, "TfidfClusterer", _FakeClusterer)

    commands.pitch_cmd(
        beat="science_tech",
        since="48h",
        now=_FIXED_NOW,
        out_dir=tmp_path,
        source_override=str(_FIXTURE_DIR),
        verbose=False,
        config_dir=_CONFIG_EXAMPLE,
    )

    brief = json.loads(
        (tmp_path / "2026-01-15" / "science_tech" / "brief.json").read_text()
    )
    assert brief["total_items_ingested"] == raw_entry_count
    assert brief["total_items_after_dedupe"] == len(crafted_items)
    assert brief["total_items_ingested"] != brief["total_items_after_dedupe"]
