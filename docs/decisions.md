# Design Decisions

## ADR-001: argparse over Click

**Status:** Resolved

**Context:** The CLI has only two commands and we want lean dependencies.

**Decision:** Use argparse with subparsers (`required=True`). Parsing is centralized in `cli.py`; command modules receive typed args and stay testable.

**Consequences:** No Click dependency. Slightly more boilerplate for argument parsing but fewer moving parts.

---

## ADR-002: scikit-learn as required dependency

**Status:** Resolved

**Context:** TF-IDF clustering is core to pitch generation and needs a mature implementation.

**Decision:** Pin scikit-learn alongside numpy in `pyproject.toml`. Clustering logic lives behind a `Clusterer` protocol so the rest of the codebase is decoupled from the implementation.

**Consequences:** Heavier install footprint due to numpy/scipy. Justified by the centrality of clustering to the pipeline.

---

## ADR-003: Pitch generation is purely algorithmic

**Status:** Resolved

**Context:** Pitches need to be differentiated without relying on an LLM.

**Decision:** No LLM for pitches. Different clusters produce different pitches. When cluster count < 3, use angle templates ("incentives", "second-order effects", "language framing") to force differentiation. Pitches carry rich metadata so the draft step has real bones.

**Consequences:** Deterministic, testable pitch generation. LLM usage is confined to the draft step only.

---

## ADR-004: Single models.py

**Status:** Resolved

**Context:** Data models need a canonical home without circular import risk.

**Decision:** All Pydantic models live in a single `models.py`. Purely declarative, no business logic. Revisit if the file exceeds 300-400 LOC or circular imports appear.

**Consequences:** Simple import paths. One file to check for all data shapes.

---

## ADR-005: httpx over requests

**Status:** Resolved

**Context:** Need an HTTP client for RSS fetching with explicit timeout control.

**Decision:** Use httpx in sync-only mode for V0 (determinism + simplicity). Explicit timeouts and retries on every request.

**Consequences:** Modern API, consistent timeout behavior. Async upgrade path available if needed.

---

## ADR-006: Deterministic time control

**Status:** Resolved

**Context:** Date-dependent operations must be reproducible in tests and fixtures.

**Decision:** `--now <ISO8601>` flag and `NEWSROOM_NOW` env var override current time for all date-dependent operations. Fixtures and `verify_content.sh` always pass a fixed `--now`.

**Consequences:** Fully deterministic test runs. No flaky date-boundary failures.

---

## ADR-007: UTC-aware datetimes everywhere

**Status:** Resolved

**Context:** Mixing naive and aware datetimes causes subtle comparison bugs.

**Decision:** All `published_at` and `generated_at` fields are normalized to UTC on ingest. No naive datetimes anywhere in the pipeline.

**Consequences:** Consistent comparisons. Slightly more ceremony when creating test fixtures.

---

## ADR-008: Inline citation markers

**Status:** Resolved

**Context:** Drafts must attribute sources and QA must verify attribution.

**Decision:** Drafts use `[src:N]` convention for inline source references. QA checks match stats to citation markers, not sentence proximity.

**Consequences:** Machine-parseable citation format. Clean separation between the writer (inserts markers) and QA (validates them).

---

## ADR-009: LLM model from config/env

**Status:** Resolved

**Context:** The LLM model ID should not be hardcoded, to allow easy switching.

**Decision:** Model ID lives in env (`NEWSROOM_MODEL`) with a default. Never hardcoded in provider code.

**Consequences:** Easy to switch models without code changes. `.env.example` documents the default.

---

## ADR-010: python-dotenv for local dev

**Status:** Resolved

**Context:** Developers need API keys and config without manual export commands.

**Decision:** `.env` file is loaded explicitly on CLI startup via python-dotenv so users do not need to manually export vars.

**Consequences:** Seamless local dev experience. `.env` is gitignored; `.env.example` documents expected vars.

---

## ADR-011: Documentation reorganization and authority hierarchy

**Status:** Resolved

**Context:** `docs/BLUEPRINT.md` (650 lines) duplicated content already covered by `docs/architecture.md`, `docs/decisions.md`, and `README.md`. The repo-local `docs/AGENTIC_DEV_PLAYBOOK.md` duplicated the global playbook in `~/.claude/`. The authority hierarchy in `constitution.md` referenced both deprecated files and placed the constitution below them, inconsistent with its role as the supreme governing document.

**Decision:** Consolidate documentation into four files with distinct responsibilities: `README.md` (concise project overview), `CLAUDE.md` (operational rules only), `docs/architecture.md` (system design authority, absorbing summary-level BLUEPRINT content), and `.specify/memory/constitution.md` (supreme law). Remove `docs/BLUEPRINT.md` and `docs/AGENTIC_DEV_PLAYBOOK.md`. Establish a clear authority hierarchy: CI output > constitution > architecture > decisions > CLAUDE.md > PRDs.

**Consequences:** Two deprecated files removed. Constitution promoted to #2 authority (below CI only). Architecture.md is the binding system design authority. No content duplication between README, CLAUDE.md, and architecture.md. Each documentation file has a single, clear responsibility.
