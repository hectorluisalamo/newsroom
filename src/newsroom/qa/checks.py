# ABOUTME: Quality assurance checks for generated drafts.
# ABOUTME: Validates source attribution, hedging, voice drift, and citations.
"""QA checks for the Newsroom pipeline.

All checks are pure, deterministic, and require no network or LLM calls.
"""

import re
from datetime import datetime, timezone

from newsroom.models import Draft, QAConfig, QAFinding, QAReport, VoiceConstitution

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\n+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<!\d)[.!?]+(?!\d)")
_STATS_RE = re.compile(
    r"\$\d[\d,]*(?:\.\d+)?|\d[\d,]*\.\d+%?|\d[\d,]*%|\d{1,3}(?:,\d{3})+"
)
_CITATION_MARKER_RE = re.compile(r"\[src:(\d+)\]")


def _split_paragraphs(body_md: str) -> list[str]:
    """Split draft body text into paragraphs on one-or-more blank lines."""
    return [p for p in _PARAGRAPH_SPLIT_RE.split(body_md.strip()) if p]


def _split_sentences(body_md: str) -> list[str]:
    """Split draft body text into sentences on terminal punctuation."""
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(body_md) if s.strip()]


def check_unsourced_stats(draft: Draft, qa_config: QAConfig) -> list[QAFinding]:
    """Check for statistics without nearby citation markers.

    Finds numbers, percentages, and dollar amounts in each paragraph
    and verifies a [src:N] marker is present in the same paragraph.
    """
    findings: list[QAFinding] = []
    if not qa_config.source_attribution.require_citation_near_stats:
        return findings

    citation_re = re.compile(qa_config.source_attribution.citation_pattern)
    for index, paragraph in enumerate(_split_paragraphs(draft.body_md), start=1):
        if _STATS_RE.search(paragraph) and not citation_re.search(paragraph):
            findings.append(
                QAFinding(
                    check_name="unsourced_stats",
                    severity="warning",
                    location=f"paragraph {index}",
                    message=(
                        "Paragraph contains a statistic without a nearby "
                        "[src:N] citation marker."
                    ),
                    details={"paragraph_index": index, "paragraph": paragraph},
                )
            )
    return findings


def check_hedging(draft: Draft, qa_config: QAConfig) -> list[QAFinding]:
    """Check for excessive hedging language.

    Counts sentences containing hedging phrases from qa.yaml and
    flags if the ratio exceeds max_ratio.
    """
    sentences = _split_sentences(draft.body_md)
    if not sentences:
        return []

    phrase_patterns = [
        re.compile(r"\b" + re.escape(phrase.lower()) + r"\b")
        for phrase in qa_config.hedging.phrases
    ]
    hedged_count = sum(
        1
        for sentence in sentences
        if any(pattern.search(sentence.lower()) for pattern in phrase_patterns)
    )
    ratio = hedged_count / len(sentences)

    if ratio > qa_config.hedging.max_ratio:
        return [
            QAFinding(
                check_name="hedging",
                severity="warning",
                location="body_md",
                message=(
                    f"Hedging ratio {ratio:.2f} exceeds max allowed "
                    f"{qa_config.hedging.max_ratio:.2f}."
                ),
                details={
                    "ratio": ratio,
                    "hedged_sentences": hedged_count,
                    "total_sentences": len(sentences),
                },
            )
        ]
    return []


def check_voice_drift(
    draft: Draft,
    voice: VoiceConstitution,
    qa_config: QAConfig,
) -> list[QAFinding]:
    """Check for voice drift against the voice constitution.

    Detects taboo phrases (error severity) and sentence length
    violations (warning severity).
    """
    findings: list[QAFinding] = []
    body_lower = draft.body_md.lower()

    for phrase in voice.taboo_phrases:
        pattern = re.compile(r"\b" + re.escape(phrase.lower()) + r"\b")
        if pattern.search(body_lower):
            findings.append(
                QAFinding(
                    check_name="voice_drift",
                    severity="error",
                    location="body_md",
                    message=f"Taboo phrase found: '{phrase}'.",
                    details={"phrase": phrase},
                )
            )

    sentences = _split_sentences(draft.body_md)
    if sentences:
        lengths = [len(sentence.split()) for sentence in sentences]
        max_len = qa_config.voice_drift.max_sentence_length
        for sentence_index, length in enumerate(lengths, start=1):
            if length > max_len:
                findings.append(
                    QAFinding(
                        check_name="voice_drift",
                        severity="warning",
                        location=f"sentence {sentence_index}",
                        message=(
                            f"Sentence length {length} exceeds max allowed {max_len}."
                        ),
                        details={"sentence_index": sentence_index, "length": length},
                    )
                )

        avg_length = sum(lengths) / len(lengths)
        min_avg = qa_config.voice_drift.min_avg_sentence_length
        max_avg = qa_config.voice_drift.max_avg_sentence_length
        if not (min_avg <= avg_length <= max_avg):
            findings.append(
                QAFinding(
                    check_name="voice_drift",
                    severity="warning",
                    location="body_md",
                    message=(
                        f"Average sentence length {avg_length:.1f} outside "
                        f"allowed range [{min_avg}, {max_avg}]."
                    ),
                    details={"avg_sentence_length": avg_length},
                )
            )

    return findings


def check_citation_integrity(draft: Draft) -> list[QAFinding]:
    """Check that all [src:N] markers map to entries in draft.sources.

    Verifies no orphaned citations and no missing source entries.
    """
    findings: list[QAFinding] = []
    source_count = len(draft.sources)
    referenced: set[int] = set()
    seen_orphans: set[int] = set()

    for match in _CITATION_MARKER_RE.finditer(draft.body_md):
        marker_n = int(match.group(1))
        referenced.add(marker_n)
        if marker_n < 1 or marker_n > source_count:
            if marker_n in seen_orphans:
                continue
            seen_orphans.add(marker_n)
            findings.append(
                QAFinding(
                    check_name="citation_integrity",
                    severity="error",
                    location=f"marker [src:{marker_n}]",
                    message=(
                        f"Citation marker [src:{marker_n}] does not map to any "
                        f"source (draft has {source_count} source(s))."
                    ),
                    details={"marker": marker_n, "source_count": source_count},
                )
            )

    for source_index in range(1, source_count + 1):
        if source_index not in referenced:
            findings.append(
                QAFinding(
                    check_name="citation_integrity",
                    severity="warning",
                    location=f"source {source_index}",
                    message=(
                        f"Source {source_index} "
                        f"({draft.sources[source_index - 1]}) is never "
                        "referenced by a [src:N] marker."
                    ),
                    details={
                        "source_index": source_index,
                        "source_url": str(draft.sources[source_index - 1]),
                    },
                )
            )

    return findings


def _build_checks(draft, voice, qa_config):
    """Registry of (name, thunk) for every QA check run by run_all_checks.
    checks_run is derived from this list, so adding/removing a check here
    keeps the reported checks_run in sync automatically."""
    return [
        ("unsourced_stats", lambda: check_unsourced_stats(draft, qa_config)),
        ("hedging", lambda: check_hedging(draft, qa_config)),
        ("voice_drift", lambda: check_voice_drift(draft, voice, qa_config)),
        ("citation_integrity", lambda: check_citation_integrity(draft)),
    ]


def run_all_checks(
    draft: Draft,
    voice: VoiceConstitution,
    qa_config: QAConfig,
) -> QAReport:
    """Run all QA checks and aggregate findings into a QAReport.

    The report passes iff no error-severity findings exist.
    """
    checks = _build_checks(draft, voice, qa_config)
    checks_run = [name for name, _ in checks]

    findings: list[QAFinding] = []
    for _, thunk in checks:
        findings.extend(thunk())

    passed = not any(finding.severity == "error" for finding in findings)

    return QAReport(
        beat=draft.beat,
        date=draft.date,
        pitch_id=draft.pitch_id,
        passed=passed,
        findings=findings,
        checks_run=checks_run,
        generated_at=datetime.now(timezone.utc),
    )
