<!--
  Sync Impact Report
  ==================
  Version change: N/A → 1.0.0 (initial creation)

  Modified principles: None (all new)
  Added principles:
    - I. Determinism First
    - II. Test-First Discipline
    - III. Human Editorial Authority
    - IV. Truth & Attribution
    - V. Open-Core Boundary
    - VI. Simplicity & Minimal Moving Parts
  Added sections:
    - Technical Constraints
    - Development Workflow
  Removed sections: None

  Templates requiring updates:
    - .specify/templates/plan-template.md        ✅ No update needed
    - .specify/templates/spec-template.md         ✅ No update needed
    - .specify/templates/tasks-template.md        ✅ No update needed
    - .specify/templates/checklist-template.md    ✅ No update needed
    - .specify/templates/agent-file-template.md   ✅ No update needed
    - README.md                                   ✅ Already aligned

  Follow-up TODOs: None
-->

# Newsroom Constitution

## Core Principles

### I. Determinism First

All pipeline outputs MUST be reproducible given the same inputs and the
same `--now` timestamp. This is the foundational guarantee that makes
testing, debugging, and auditing possible.

- No naive datetimes anywhere in the pipeline; all timestamps MUST be
  UTC-aware (normalized on ingest).
- Cluster IDs MUST be computed as SHA256 of sorted item IDs.
- Pitch IDs MUST follow the `{beat}-{date}-{index}` format.
- Rendered output MUST use stable templates, sorted keys, and no random
  ordering.
- Tests and verification scripts MUST always supply a fixed `--now`
  value.

### II. Test-First Discipline

TDD is mandatory. No implementation code is written before a failing
test defines the expected behavior. This applies to all feature work
without exception.

- Red-Green-Refactor cycle strictly enforced: write a failing test,
  write minimal code to pass, refactor while green.
- Unit, integration, AND e2e tests are required for every feature.
- NO NETWORK in any test. All RSS data comes from fixtures. All LLM
  calls are mocked. This is enforced by `tests/conftest.py`.
- `scripts/verify.sh` MUST pass (lint + format check + tests) before
  any work is considered complete.
- Test output MUST be pristine — no warnings or errors treated as
  acceptable noise.

### III. Human Editorial Authority

The human editor is the final authority on content selection and
publication. The system is a tool, not an autonomous publisher.

- LLM usage is confined to the draft step only; pitch generation is
  purely algorithmic.
- The writer (LLM) MUST NOT browse the web or access any sources beyond
  the pre-collected brief pack.
- Pitch selection, editorial guidance, and publish decisions are
  exclusively human actions.
- The system produces artifacts; the human decides what to do with them.

### IV. Truth & Attribution

This project carries reputational and legal risk. All generated content
MUST be traceable to its sources.

- No new factual claims beyond sources provided in the brief pack.
- Statistics and numbers MUST carry inline `[src:N]` citation markers
  linking to canonical URLs.
- QA gates MUST enforce: unsourced stats detection, hedging ratio
  limits, citation integrity checks, and voice drift analysis.
- No allegations about individuals unless sourced by reputable outlets
  and phrased cautiously.
- Social content is signal only unless independently corroborated.

### V. Open-Core Boundary

The public repository MUST be portfolio-safe, auditable, and publishable.
Private strategy and secrets stay out.

- `config/` and `.env` MUST NEVER be committed to the public repo.
- `config.example/` is the canonical public reference and MUST be
  committed with representative (non-sensitive) values.
- Runtime configuration is generated locally via `scripts/init_config.sh`
  or overlaid from a private repo via `scripts/sync_private_config.sh`.
- No secrets, proprietary source lists, or production voice constitutions
  in the public repo.

### VI. Simplicity & Minimal Moving Parts

Lean dependencies, small modules, clear responsibilities. Complexity
MUST be justified; the default is the simpler option.

- Prefer standard-library and lightweight dependencies over heavyweight
  frameworks (e.g., argparse over Click).
- No abstractions for one-time operations; avoid premature generalization.
- Interfaces (protocols) are used only at explicit swap boundaries
  (e.g., `Clusterer`, `LLMProvider`).
- Single `models.py` for all Pydantic models; revisit only if the file
  exceeds ~400 LOC or circular imports appear.
- Sync-only I/O in V0. Async is a future upgrade, not a current concern.

## Technical Constraints

Stack and boundary rules that apply to all implementation work:

- **Language**: Python 3.12+
- **Package manager**: `uv`
- **Linter/formatter**: Ruff (py312, E/F/I/W rules)
- **Tests**: pytest with NO NETWORK policy
- **Data models**: Pydantic (declarative only, no business logic in
  model classes)
- **HTTP client**: httpx in sync-only mode with explicit timeouts and
  limited retries
- **Clustering**: scikit-learn behind the `Clusterer` protocol
- **LLM model ID**: sourced from `NEWSROOM_MODEL` env var, MUST NOT
  be hardcoded in provider code
- **File headers**: every new Python file MUST start with a two-line
  `ABOUTME:` comment describing what the file does
- **Comments**: no `TODO`, `FIXME`, or `HACK` comments; all comments
  MUST be evergreen and describe the code as it is

## Development Workflow

All work follows a PRD-driven, verification-gated process:

- All non-trivial work begins with a PRD in `docs/prd/`.
- The Blueprint (`docs/BLUEPRINT.md`) is binding unless explicitly
  revised via `docs/decisions.md` (ADR-style).
- `scripts/verify.sh` (lint + format check + tests) MUST pass before
  any task is considered complete.
- CodeRabbit review gate is required before task completion; material
  issues MUST be resolved before merging.
- Work proceeds in small, iterative, test-driven increments.
- Scope discipline: work only on the current PRD, document unrelated
  issues instead of fixing them.

## Governance

This constitution captures the distilled, non-negotiable principles of
the Newsroom project. It is the speckit-level expression of rules that
originate in the Blueprint, architecture docs, and development playbook.

**Authority hierarchy** (in case of conflict):
1. CI / verification output (`scripts/verify.sh`, QA gates)
2. `docs/BLUEPRINT.md`
3. `AGENTIC_DEV_PLAYBOOK.md`
4. This constitution
5. `CLAUDE.md`

**Amendment procedure**:
- Amendments require a pull request with rationale.
- Material changes MUST be recorded in `docs/decisions.md`.
- Version bump follows semver: MAJOR for principle removals or
  redefinitions, MINOR for new principles or expanded guidance,
  PATCH for clarifications and wording fixes.

**Compliance**:
- Plan-phase constitution checks (in `plan-template.md`) MUST verify
  alignment with active principles before implementation begins.
- Violations MUST be justified in the plan's Complexity Tracking table
  or resolved before proceeding.

**Version**: 1.0.0 | **Ratified**: 2026-02-04 | **Last Amended**: 2026-02-04
