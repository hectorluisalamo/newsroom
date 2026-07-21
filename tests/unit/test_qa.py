# ABOUTME: Unit tests for QA checks on generated drafts.
# ABOUTME: Validates hedging, citation, voice drift, and stats attribution checks.
"""Tests for newsroom.qa."""

from datetime import date, datetime, timezone

from newsroom.models import (
    Draft,
    HedgingConfig,
    QAConfig,
    SourceAttributionConfig,
    VoiceConstitution,
    VoiceDriftConfig,
)
from newsroom.qa.checks import (
    _split_sentences,
    check_citation_integrity,
    check_hedging,
    check_unsourced_stats,
    check_voice_drift,
    run_all_checks,
)

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_qa_config(
    *,
    hedging: HedgingConfig | None = None,
    source_attribution: SourceAttributionConfig | None = None,
    voice_drift: VoiceDriftConfig | None = None,
) -> QAConfig:
    return QAConfig(
        hedging=hedging
        or HedgingConfig(
            max_ratio=0.15,
            phrases=["it's unclear", "some experts say", "arguably", "perhaps"],
        ),
        source_attribution=source_attribution
        or SourceAttributionConfig(
            require_citation_near_stats=True,
            citation_pattern=r"\[src:\d+\]",
        ),
        voice_drift=voice_drift
        or VoiceDriftConfig(
            max_avg_sentence_length=35,
            min_avg_sentence_length=10,
            max_sentence_length=60,
        ),
    )


def _make_voice(*, taboo_phrases: list[str] | None = None) -> VoiceConstitution:
    return VoiceConstitution(
        beliefs=["Technology is a tool shaped by human incentives."],
        tone=["Conversational but informed."],
        forbidden_moves=["Do not predict the future with certainty."],
        taboo_phrases=taboo_phrases if taboo_phrases is not None else ["revolutionary"],
        required_habits=["Every claim must trace to a source."],
    )


def _make_draft(*, body_md: str, sources: list[str] | None = None) -> Draft:
    return Draft(
        beat="science_tech",
        date=date(2026, 1, 15),
        pitch_id="p1",
        title="Test Draft",
        body_md=body_md,
        word_count=len(body_md.split()),
        sources=sources or ["https://example.com/a", "https://example.com/b"],
        guidance_used="Keep it punchy.",
        model_id="fake-model-v1",
        generated_at=_NOW,
    )


class TestCheckUnsourcedStats:
    def test_flags_paragraph_with_stat_and_no_citation(self):
        draft = _make_draft(
            body_md=(
                "Adoption grew by 42% last year.\n\n"
                "A second paragraph with no numbers at all."
            )
        )
        qa_config = _make_qa_config()

        findings = check_unsourced_stats(draft, qa_config)

        assert len(findings) == 1
        assert findings[0].check_name == "unsourced_stats"
        assert findings[0].severity == "warning"

    def test_no_finding_when_stat_has_citation_in_same_paragraph(self):
        draft = _make_draft(
            body_md=(
                "Adoption grew by 42% last year [src:1].\n\n"
                "A second paragraph with no numbers at all."
            )
        )
        qa_config = _make_qa_config()

        findings = check_unsourced_stats(draft, qa_config)

        assert findings == []

    def test_no_finding_when_require_citation_near_stats_disabled(self):
        draft = _make_draft(body_md="Adoption grew by 42% last year.")
        qa_config = _make_qa_config(
            source_attribution=SourceAttributionConfig(
                require_citation_near_stats=False,
                citation_pattern=r"\[src:\d+\]",
            )
        )

        findings = check_unsourced_stats(draft, qa_config)

        assert findings == []


class TestCheckHedging:
    def test_flags_when_hedging_ratio_exceeds_max(self):
        body = (
            "Arguably this matters. This is a clean sentence. "
            "Another clean sentence follows. A third clean one appears."
        )
        draft = _make_draft(body_md=body)
        qa_config = _make_qa_config()

        findings = check_hedging(draft, qa_config)

        assert len(findings) == 1
        assert findings[0].check_name == "hedging"
        assert findings[0].severity == "warning"

    def test_no_finding_when_hedging_ratio_within_max(self):
        body = (
            "This is sentence one. This is sentence two. "
            "This is sentence three. This is sentence four. "
            "This is sentence five. This is sentence six. "
            "Perhaps this one hedges."
        )
        draft = _make_draft(body_md=body)
        qa_config = _make_qa_config()

        findings = check_hedging(draft, qa_config)

        assert findings == []

    def test_hedging_phrase_as_substring_of_unrelated_word_does_not_count(self):
        body = (
            "Maybe you have heard of the park downtown. "
            "This is a clean sentence right here. "
            "Another clean sentence follows along nicely. "
            "A third clean sentence rounds things out."
        )
        draft = _make_draft(body_md=body)
        qa_config = _make_qa_config(
            hedging=HedgingConfig(max_ratio=0.15, phrases=["may"])
        )

        findings = check_hedging(draft, qa_config)

        assert findings == []

    def test_hedging_phrase_as_isolated_word_still_counts(self):
        body = (
            "This may or may not work out. "
            "This is a clean sentence right here. "
            "Another clean sentence follows along nicely. "
            "A third clean sentence rounds things out."
        )
        draft = _make_draft(body_md=body)
        qa_config = _make_qa_config(
            hedging=HedgingConfig(max_ratio=0.15, phrases=["may"])
        )

        findings = check_hedging(draft, qa_config)

        assert len(findings) == 1
        assert findings[0].details["hedged_sentences"] == 1


class TestCheckVoiceDrift:
    def test_flags_taboo_phrase_as_error(self):
        draft = _make_draft(body_md="This is truly revolutionary technology.")
        voice = _make_voice(taboo_phrases=["revolutionary"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert errors[0].check_name == "voice_drift"
        assert errors[0].details["phrase"] == "revolutionary"

    def test_no_finding_when_clean_and_sentence_lengths_in_range(self):
        draft = _make_draft(
            body_md=(
                "This is a normal sentence with a fairly reasonable overall "
                "length to it right now. "
                "Here is another sentence of quite similar reasonable length "
                "overall as well today."
            )
        )
        voice = _make_voice(taboo_phrases=["revolutionary", "game-changing"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        assert findings == []

    def test_flags_sentence_exceeding_max_length_as_warning(self):
        long_sentence = " ".join(["word"] * 61) + "."
        short_sentence = "This sentence has exactly ten plain words right here now."
        body = " ".join([long_sentence, short_sentence, short_sentence, short_sentence])
        draft = _make_draft(body_md=body)
        voice = _make_voice(taboo_phrases=["revolutionary"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        long_sentence_findings = [
            f
            for f in findings
            if f.severity == "warning" and f.details.get("length") == 61
        ]
        assert len(long_sentence_findings) == 1

    def test_flags_average_sentence_length_outside_range_as_warning(self):
        body = "Cats sleep. Dogs run. Birds fly. Fish swim. Ants march."
        draft = _make_draft(body_md=body)
        voice = _make_voice(taboo_phrases=["revolutionary"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        avg_findings = [
            f
            for f in findings
            if f.severity == "warning" and "average" in f.message.lower()
        ]
        assert len(avg_findings) == 1

    def test_no_finding_when_taboo_phrase_only_a_substring_of_other_word(self):
        draft = _make_draft(body_md="The retailer said detail matters most.")
        voice = _make_voice(taboo_phrases=["AI"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        errors = [f for f in findings if f.severity == "error"]
        assert errors == []

    def test_flags_taboo_phrase_when_standalone_word(self):
        draft = _make_draft(body_md="This is truly revolutionary technology.")
        voice = _make_voice(taboo_phrases=["revolutionary"])
        qa_config = _make_qa_config()

        findings = check_voice_drift(draft, voice, qa_config)

        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert errors[0].details["phrase"] == "revolutionary"

    def test_sentence_splitter_does_not_break_on_decimal_points(self):
        body = "Revenue grew 3.5 percent to $4.5 billion this year."

        sentences = _split_sentences(body)

        assert len(sentences) == 1
        assert sentences[0] == body.rstrip(".")


class TestCheckCitationIntegrity:
    def test_flags_orphaned_marker_as_error(self):
        draft = _make_draft(
            body_md="A claim with a bad citation [src:9].",
            sources=["https://example.com/a", "https://example.com/b"],
        )

        findings = check_citation_integrity(draft)

        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert errors[0].check_name == "citation_integrity"

    def test_flags_unused_source_as_warning(self):
        draft = _make_draft(
            body_md="A claim with a citation [src:1].",
            sources=["https://example.com/a", "https://example.com/b"],
        )

        findings = check_citation_integrity(draft)

        assert len(findings) == 1
        assert findings[0].severity == "warning"
        assert findings[0].check_name == "citation_integrity"

    def test_no_finding_when_all_sources_referenced_and_no_orphans(self):
        draft = _make_draft(
            body_md="First claim [src:1]. Second claim [src:2].",
            sources=["https://example.com/a", "https://example.com/b"],
        )

        findings = check_citation_integrity(draft)

        assert findings == []


class TestRunAllChecks:
    def test_builds_report_with_checks_run_and_metadata(self):
        draft = _make_draft(body_md="A clean sentence with a citation [src:1].")
        voice = _make_voice()
        qa_config = _make_qa_config()

        report = run_all_checks(draft, voice, qa_config)

        assert report.beat == draft.beat
        assert report.date == draft.date
        assert report.pitch_id == draft.pitch_id
        assert set(report.checks_run) == {
            "unsourced_stats",
            "hedging",
            "voice_drift",
            "citation_integrity",
        }
        assert report.generated_at.tzinfo is not None

    def test_passed_is_false_when_error_finding_present(self):
        draft = _make_draft(body_md="This is truly revolutionary technology [src:1].")
        voice = _make_voice(taboo_phrases=["revolutionary"])
        qa_config = _make_qa_config()

        report = run_all_checks(draft, voice, qa_config)

        assert report.passed is False
        assert any(f.severity == "error" for f in report.findings)

    def test_passed_is_true_when_only_warnings_present(self):
        body = (
            "Arguably this matters here today. This sentence is entirely "
            "clean. Another clean one follows now."
        )
        draft = _make_draft(body_md=body, sources=["https://example.com/a"])
        voice = _make_voice(taboo_phrases=["revolutionary", "game-changing"])
        qa_config = _make_qa_config(
            hedging=HedgingConfig(max_ratio=0.15, phrases=["arguably"])
        )

        report = run_all_checks(draft, voice, qa_config)

        assert report.passed is True
        assert len(report.findings) >= 1
        assert all(f.severity != "error" for f in report.findings)
