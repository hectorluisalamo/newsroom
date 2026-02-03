# ABOUTME: Quality assurance checks for generated drafts.
# ABOUTME: Validates source attribution, hedging, voice drift, and citations.
"""QA checks for the Newsroom pipeline.

All checks are pure, deterministic, and require no network or LLM calls.
"""


def check_unsourced_stats(draft: object, qa_config: dict) -> list:
    """Check for statistics without nearby citation markers.

    Finds numbers, percentages, and dollar amounts in each paragraph
    and verifies a [src:N] marker is present in the same paragraph.
    """
    raise NotImplementedError


def check_hedging(draft: object, qa_config: dict) -> list:
    """Check for excessive hedging language.

    Counts sentences containing hedging phrases from qa.yaml and
    flags if the ratio exceeds max_ratio.
    """
    raise NotImplementedError


def check_voice_drift(
    draft: object,
    voice: object,
    qa_config: dict,
) -> list:
    """Check for voice drift against the voice constitution.

    Detects taboo phrases (error severity) and sentence length
    violations (warning severity).
    """
    raise NotImplementedError


def check_citation_integrity(draft: object) -> list:
    """Check that all [src:N] markers map to entries in draft.sources.

    Verifies no orphaned citations and no missing source entries.
    """
    raise NotImplementedError


def run_all_checks(
    draft: object,
    voice: object,
    qa_config: dict,
) -> object:
    """Run all QA checks and aggregate findings into a QAReport.

    The report passes iff no error-severity findings exist.
    """
    raise NotImplementedError
