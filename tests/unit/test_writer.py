# ABOUTME: Unit tests for draft writing logic (prompt assembly + write_draft).
# ABOUTME: Uses an in-file fake LLMProvider — never calls a real/paid API.
"""Tests for newsroom.draft.writer."""

from datetime import date, datetime, timezone

from newsroom.draft.provider import LLMProvider, LLMResponse
from newsroom.draft.writer import assemble_prompt, write_draft
from newsroom.models import BriefCluster, BriefPack, FeedItem, Pitch, VoiceConstitution

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_feed_item(item_id: str, title: str, summary: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=title,
        url=f"https://example.com/{item_id}",
        source_name="Example Source",
        source_feed_url="https://example.com/feed.xml",
        published_at=_NOW,
        summary=summary,
        raw_tags=[],
        beat="science_tech",
    )


def _make_cluster(cluster_id: str) -> BriefCluster:
    items = [
        _make_feed_item(f"{cluster_id}-1", "Story One", "Summary of story one."),
        _make_feed_item(f"{cluster_id}-2", "Story Two", "Summary of story two."),
    ]
    return BriefCluster(
        cluster_id=cluster_id,
        label="Cluster label",
        items=items,
        centroid_keywords=["k1", "k2"],
        recency_score=0.8,
        source_diversity=2,
        size=len(items),
    )


def _make_brief(clusters: list[BriefCluster]) -> BriefPack:
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
    *,
    pitch_id: str = "pitch-1",
    cluster_id: str = "cluster-1",
    source_urls: list[str] | None = None,
) -> Pitch:
    return Pitch(
        pitch_id=pitch_id,
        title="AI Chip Export Controls Tighten",
        thesis_angle="Export controls reshape the chip market.",
        why_now="New rules just took effect.",
        key_points=["Point one.", "Point two.", "Point three."],
        source_urls=source_urls
        or [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ],
        risk_flags=[],
        cluster_id=cluster_id,
        angle="trend_analysis",
    )


def _make_voice() -> VoiceConstitution:
    return VoiceConstitution(
        beliefs=["Belief one.", "Belief two."],
        tone=["Direct.", "Skeptical."],
        forbidden_moves=["No both-sidesing."],
        taboo_phrases=["game changer"],
        required_habits=["Cite every claim."],
    )


class _FakeProvider(LLMProvider):
    """Returns canned text; records every call for assertions."""

    def __init__(self, texts: list[str]) -> None:
        self._texts = texts
        self.calls: list[tuple[str, str, int]] = []

    def generate(
        self, system_prompt: str, user_prompt: str, max_tokens: int
    ) -> LLMResponse:
        self.calls.append((system_prompt, user_prompt, max_tokens))
        idx = min(len(self.calls) - 1, len(self._texts) - 1)
        return LLMResponse(
            text=self._texts[idx], token_usage={"input": 10, "output": 20}
        )

    @property
    def model_id(self) -> str:
        return "fake-model-v1"


def _words(n: int, *, with_citation: bool = True) -> str:
    body = " ".join(f"word{i}" for i in range(n))
    if with_citation:
        body += " [src:1]"
    return body


class TestAssemblePrompt:
    def test_returns_two_tuple_of_strings(self):
        result = assemble_prompt(
            _make_pitch(),
            _make_brief([_make_cluster("cluster-1")]),
            _make_voice(),
            "Keep it punchy.",
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        system_prompt, user_prompt = result
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)

    def test_system_prompt_contains_voice_sections_and_citation_rule(self):
        voice = _make_voice()
        system_prompt, _ = assemble_prompt(
            _make_pitch(),
            _make_brief([_make_cluster("cluster-1")]),
            voice,
            "Keep it punchy.",
        )

        for belief in voice.beliefs:
            assert belief in system_prompt
        for tone in voice.tone:
            assert tone in system_prompt
        for forbidden in voice.forbidden_moves:
            assert forbidden in system_prompt
        for taboo in voice.taboo_phrases:
            assert taboo in system_prompt
        for habit in voice.required_habits:
            assert habit in system_prompt
        assert "[src:N]" in system_prompt

    def test_user_prompt_contains_one_src_line_per_source_url_and_guidance(self):
        pitch = _make_pitch(
            source_urls=[
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
                "https://example.com/d",
            ]
        )
        guidance = "Focus on the human impact angle."
        _, user_prompt = assemble_prompt(
            pitch, _make_brief([_make_cluster("cluster-1")]), _make_voice(), guidance
        )

        for n, url in enumerate(pitch.source_urls, start=1):
            assert f"[src:{n}] {url}" in user_prompt
        assert guidance in user_prompt

    def test_falls_back_to_pitch_key_points_when_cluster_not_found(self):
        pitch = _make_pitch(cluster_id="cluster-missing")
        brief = _make_brief([_make_cluster("cluster-1")])

        # Should not raise even though no cluster in `brief` matches pitch.cluster_id.
        _, user_prompt = assemble_prompt(pitch, brief, _make_voice(), "Guidance.")

        for point in pitch.key_points:
            assert point in user_prompt

    def test_custom_target_words_used_in_system_prompt_instead_of_default(self):
        # A configurable target_words must actually steer the model's
        # instructions, not just gate the post-generation retry check —
        # otherwise a custom target instructs toward the default and the
        # writer judges the result against a target it never asked for.
        system_prompt, _ = assemble_prompt(
            _make_pitch(),
            _make_brief([_make_cluster("cluster-1")]),
            _make_voice(),
            "Keep it punchy.",
            target_words=1200,
        )

        assert "1200" in system_prompt
        assert "approximately 1200 words" in system_prompt
        assert "700" not in system_prompt

    def test_default_target_words_used_when_not_specified(self):
        system_prompt, _ = assemble_prompt(
            _make_pitch(),
            _make_brief([_make_cluster("cluster-1")]),
            _make_voice(),
            "Keep it punchy.",
        )

        assert "approximately 700 words" in system_prompt


class TestWriteDraft:
    def test_happy_path_returns_valid_draft(self):
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        body_text = _words(700)
        provider = _FakeProvider([body_text])

        draft = write_draft(
            pitch,
            brief,
            voice,
            "Keep it punchy.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
        )

        assert len(provider.calls) == 1
        assert draft.body_md == body_text
        assert draft.word_count == len(body_text.split())
        assert draft.sources == pitch.source_urls
        assert draft.model_id == provider.model_id
        assert draft.guidance_used == "Keep it punchy."
        assert draft.pitch_id == pitch.pitch_id
        assert draft.beat == "science_tech"
        assert draft.date == date(2026, 1, 15)
        assert draft.generated_at.tzinfo is not None
        assert draft.generated_at == _NOW
        assert draft.token_usage == {"input": 10, "output": 20}

    def test_retry_cap_enforced_and_draft_still_returned(self):
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        # Always way off-target (50 words vs. 700 target) so every attempt retries.
        off_target_text = _words(50)
        provider = _FakeProvider([off_target_text])

        draft = write_draft(
            pitch,
            brief,
            voice,
            "Guidance.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
            max_retries=2,
        )

        assert len(provider.calls) == 3
        assert draft.body_md == off_target_text
        assert draft.word_count == 51  # 50 "wordN" tokens + the [src:1] marker

    def test_retry_corrections_are_not_stacked_across_attempts(self):
        # Each retry must append a single fresh correction to the *original*
        # user prompt, not to the previous retry's already-corrected prompt.
        # Otherwise attempt 2's prompt carries both attempt 1's and attempt
        # 2's correction, and the model sees conflicting length guidance.
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        off_target_text = _words(50)
        provider = _FakeProvider([off_target_text])

        write_draft(
            pitch,
            brief,
            voice,
            "Guidance.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
            max_retries=2,
        )

        assert len(provider.calls) == 3
        _, first_user_prompt, _ = provider.calls[0]
        _, second_user_prompt, _ = provider.calls[1]
        _, third_user_prompt, _ = provider.calls[2]

        correction_marker = "Your previous draft was"
        assert first_user_prompt.count(correction_marker) == 0
        assert second_user_prompt.count(correction_marker) == 1
        assert third_user_prompt.count(correction_marker) == 1

        # The final retry's prompt must still be built on top of the
        # original prompt (guidance intact), not on top of attempt 2's
        # already-corrected prompt.
        assert second_user_prompt.startswith(first_user_prompt)
        assert third_user_prompt.startswith(first_user_prompt)

    def test_forwards_custom_target_words_into_assembled_system_prompt(self):
        # write_draft's target_words must reach assemble_prompt, not just
        # the retry-tolerance check, so the model is instructed toward the
        # same target it's judged against.
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        provider = _FakeProvider([_words(1200)])

        write_draft(
            pitch,
            brief,
            voice,
            "Keep it punchy.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
            target_words=1200,
        )

        assert len(provider.calls) == 1
        system_prompt, _user_prompt, _max_tokens = provider.calls[0]
        assert "approximately 1200 words" in system_prompt

    def test_max_tokens_scales_with_custom_target_words(self):
        # A large custom target must not be truncated by a hardcoded
        # max_tokens cap sized for the default 700-word target.
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        provider = _FakeProvider([_words(3000)])

        write_draft(
            pitch,
            brief,
            voice,
            "Keep it punchy.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
            target_words=3000,
        )

        _system_prompt, _user_prompt, max_tokens = provider.calls[0]
        assert max_tokens > 1500

    def test_max_tokens_at_least_default_for_default_target_words(self):
        pitch = _make_pitch()
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        provider = _FakeProvider([_words(700)])

        write_draft(
            pitch,
            brief,
            voice,
            "Keep it punchy.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
        )

        _system_prompt, _user_prompt, max_tokens = provider.calls[0]
        assert max_tokens >= 1500

    def test_src_n_order_preserved_into_draft_sources(self):
        expected_urls = [
            "https://example.com/first",
            "https://example.com/second",
            "https://example.com/third",
        ]
        pitch = _make_pitch(source_urls=expected_urls)
        brief = _make_brief([_make_cluster("cluster-1")])
        voice = _make_voice()
        provider = _FakeProvider([_words(700)])

        # Confirm the numbered [src:N] list in the prompt matches source order.
        _, user_prompt = assemble_prompt(pitch, brief, voice, "Guidance.")
        for n, url in enumerate(expected_urls, start=1):
            assert f"[src:{n}] {url}" in user_prompt

        draft = write_draft(
            pitch,
            brief,
            voice,
            "Guidance.",
            provider,
            now=_NOW,
            beat="science_tech",
            date=date(2026, 1, 15),
        )

        assert [str(url) for url in draft.sources] == expected_urls
