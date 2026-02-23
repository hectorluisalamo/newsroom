# Architecture

This document describes the architecture of **Newsroom**: a lean, deterministic CLI that generates **algorithmic pitches** and **LLM-authored opinion drafts** for a single beat (V0: `science_tech`), with a human editor in control.

This repo is **public** and implements the core pipeline. Runtime configuration (sources, QA thresholds, voice constitutions) is **open-core**: example configs live in `config.example/`, while real configs are generated locally via `scripts/init_config.sh`.

---

## Operating Model

Newsroom is intentionally split into two editorial steps:

1. **Pitch step (deterministic, no LLM)**
   - Ingest sources for a beat
   - Normalize, dedupe, cluster, rank
   - Generate **3 distinct pitches** (topic + angle) using heuristics/templates
   - Output a brief pack and pitch set

2. **Draft step (LLM, editor-guided)**
   - Human selects a `pitch_id`
   - Human provides editorial guidance
   - Writer generates a ~700-word Substack-ready column using:
     - the selected pitch
     - relevant brief excerpts
     - the beat voice constitution
     - the editor guidance
   - Run QA gates and output a report

This keeps discovery fast and reliable, while preserving human authority over meaning and publication.

---

## Design Goals

- **Determinism first**: pitch outputs should be reproducible given the same inputs and the same `--now`.
- **No browsing for the writer**: LLM drafting is constrained to pre-collected sources and brief excerpts.
- **Minimal moving parts**: small modules with clear responsibilities and strong data models.
- **Testability**: unit/integration/e2e tests, with a strict **NO NETWORK** policy.
- **Auditability**: outputs are stored as dated artifacts; intermediate JSON is preserved.
- **Swap-friendly internals**: clustering and LLM providers are behind small interfaces.

---

## Non-Goals

- Real-time reporting, fact-checking, or original journalism.
- Automated publication to Substack (human publishes).
- A marketing/growth system.
- A web UI or persistent database in V0.
- Social ingestion (placeholders allowed, not implemented in V0).

---

## Repository Boundaries

### Open-Core Config Boundary

- `config/` is **gitignored** in the public repo.
- `config.example/` is committed and serves as canonical examples.
- Runtime config is generated locally via `scripts/init_config.sh`.

### Why
This keeps the public repo clean while allowing:
- evolving voice constitutions
- environment-specific thresholds
- API keys and secrets in `.env` (gitignored separately)

---

## High-Level Data Flow

### Pitch (`newsroom pitch`)

sources.yaml
↓
ingestion (RSS fetch + parse)
↓
normalize (canonical fields, timestamps, text cleanup)
↓
dedupe (exact + fuzzy)
↓
cluster (TF-IDF + cosine + deterministic ids)
↓
rank (recency + diversity + size)
↓
pitches (heuristic templates + angle differentiation)
↓
render (brief.json/brief.md, pitches.json/pitches.md)

### Draft (`newsroom draft`)

pitches.json + brief.json + voice.md + editor guidance
↓
writer prompt assembly (no browsing; only allowed context)
↓
LLM provider (Anthropic in V0; interface supports swapping)
↓
post-checks (word count, Sources section)
↓
QA checks (unsourced stats, hedging, taboo phrases, etc.)
↓
render (draft.md, draft.json, report.json)


---

## Core Modules

All Python code lives under `src/newsroom/`.

- `cli.py`  
  Argparse subcommands; parsing only. Delegates to command functions.

- `commands.py`  
  Orchestrates pipeline steps for `pitch`, `draft`, and (optionally) `qa`.

- `models.py`  
  Pydantic models (declarative only). This is the shared vocabulary for pipeline stages.

- `settings.py`  
  Loads runtime configuration from `config/` (or `config.example/` when appropriate). Fails fast on invalid config.

- `logging_config.py`  
  Standard library logging setup. No bespoke logging framework.

### Pipeline Packages

- `ingestion/`  
  RSS fetching and parsing (sync `httpx`). Explicit timeouts and limited retries. Never crashes the full run for a single bad feed.

- `normalize/`  
  Converts raw entries into `FeedItem` objects: canonical URL handling, HTML stripping, text cleanup, timestamp normalization, `since` filtering.

- `dedupe/`  
  Exact dedupe by id + fuzzy dedupe by title similarity. Deterministic tie-breaking.

- `cluster/`  
  Clustering behind a protocol/interface. V0 uses TF-IDF + cosine similarity, producing stable cluster ids and keywords.

- `rank/`  
  Ranks clusters using a stable scoring function.

- `pitches/`  
  Algorithmic pitch generation from cluster metadata + angle templates. Produces exactly 3 pitches.

- `draft/`  
  Provider interface + writer orchestration. Writer is not allowed to browse; it only sees approved context.

- `qa/`  
  Pure, deterministic checks. No network. No LLM.

- `render/`  
  Deterministic JSON + Markdown rendering.

- `utils/`  
  Shared helpers (time parsing, text utilities). Kept small.

---

## Data Model Overview

All data models are defined as Pydantic models in `src/newsroom/models.py` (declarative only, no business logic). The code is the source of truth for field-level definitions; this section describes each model's purpose and key constraints.

- **FeedItem** — A single normalized article from an RSS feed. Identified by SHA256 of its canonical URL. Enforces UTC-aware timestamps and summary truncation after HTML stripping.

- **BriefCluster** — A group of related feed items representing a story thread. Cluster ID is a deterministic SHA256 of sorted item IDs. Carries TF-IDF centroid keywords, recency score, source diversity count, and cluster size.

- **BriefPack** — The complete research brief for a beat on a given date. Contains all clusters, ingestion/dedupe counts, and a UTC-aware generation timestamp.

- **Pitch** — A single pitch candidate derived from a brief pack. Requires a minimum of 3 source URLs (max 10). Carries a thesis angle, key points, risk flags, and the angle template used. Deterministic pitch ID: `{beat}-{date}-{index}`.

- **PitchSet** — The set of exactly 3 pitches produced for a beat on a date. References the brief pack it was generated from.

- **Draft** — A generated opinion column. Contains the markdown body with `[src:N]` inline citation markers, word count, numbered source URLs, editorial guidance used, model ID, and optional token usage.

- **QAFinding** — A single QA check result. Carries check name, severity (error/warning/info), location, and message.

- **QAReport** — Quality gate results for a draft. Aggregates all findings. Passes only if no error-severity findings exist.

---

## Resolved Design Decisions

Key design decisions recorded during project bootstrap. See `docs/decisions.md` for full ADR records.

1. **argparse over Click** — two commands, lean deps; parsing centralized in `cli.py`.
2. **scikit-learn as required dependency** — TF-IDF clustering is core; behind a `Clusterer` protocol.
3. **Pitch generation is purely algorithmic** — no LLM; angle templates force differentiation.
4. **Single `models.py`** — purely declarative, no business logic; revisit if >300-400 LOC.
5. **httpx over requests** — sync-only in V0; explicit timeouts and retries.
6. **Deterministic time control** — `--now` flag and `NEWSROOM_NOW` env var override current time.
7. **UTC-aware datetimes everywhere** — all timestamps normalized to UTC on ingest.
8. **Inline citation markers** — drafts use `[src:N]` convention; QA matches stats to markers.
9. **LLM model from config/env** — `NEWSROOM_MODEL` env var, never hardcoded.
10. **python-dotenv for local dev** — `.env` loaded on CLI startup.

---

## CLI Surface

### `pitch`
Produces the daily brief and 3 pitch candidates:

- Output:
  - `out/<YYYY-MM-DD>/<beat>/brief.json`
  - `out/<YYYY-MM-DD>/<beat>/brief.md`
  - `out/<YYYY-MM-DD>/<beat>/pitches.json`
  - `out/<YYYY-MM-DD>/<beat>/pitches.md`

### `draft`
Generates a Substack-ready draft from a selected pitch and editor guidance:

- Input:
  - `--date <YYYY-MM-DD>`
  - `--pitch-id <id>`
  - `--guidance-file <path>`
- Output:
  - `out/<YYYY-MM-DD>/<beat>/draft.md`
  - `out/<YYYY-MM-DD>/<beat>/draft.json`
  - `out/<YYYY-MM-DD>/<beat>/report.json`

### Deterministic Time (`--now`)
All commands support an optional `--now <ISO8601>` (or `NEWSROOM_NOW`) used for:
- computing the `--since` window
- stamping `generated_at`
- choosing output directory date

Tests and verification scripts always set `--now` to keep results reproducible.

---

## Data Model Invariants

Models enforce correctness constraints at the boundary:
- UTC-aware datetimes (naive datetimes rejected)
- bounded lists (e.g., pitch sources)
- numeric ranges (e.g., recency score)
- structural constraints (e.g., exactly 3 pitches)

Business logic (fetching, clustering math, ranking) lives outside models.

---

## Testing Strategy

### Hard Rule: No Network in Tests
All tests run on fixtures. Any network attempt is treated as a failure (enforced in `tests/conftest.py`).

### Test Layers
- **Unit tests**: individual modules, pure functions, validators
- **Integration tests**: pipeline slices using fixtures (ingestion→pitches, pitch→draft with mocked LLM)
- **E2E tests**: invoke CLI, assert outputs and schemas

Fixtures live under `fixtures/`:
- saved RSS XML
- expected rendered outputs
- sample draft text for QA regression

---

## Verification

- `scripts/verify.sh`  
  Lint + format check + tests.

- `scripts/verify_content.sh`  
  Runs `pitch`/`draft` against fixtures, validates JSON schemas, and asserts deterministic outputs. Uses fixed `--now` and an isolated `--out-dir`.

Verification output is authoritative.

---

## Provider Abstraction

LLM usage is confined to the draft step.

- `draft/provider.py` defines the provider interface.
- `draft/anthropic_provider.py` implements the interface in V0.
- Provider selection is configuration-driven (env/config), not hard-coded.

This makes it possible to add new providers without changing pipeline logic.

---

## Safety & Trust Constraints

- Writer cannot browse the web.
- Draft must include a **Sources** section with canonical URLs derived from the pitch/brief.
- QA checks flag:
  - unsourced statistics
  - taboo phrases (voice constitution)
  - excessive hedging
  - sentence-length drift (basic stylometry)
- Outputs preserve intermediate artifacts for audit and debugging.

This is an opinion column generator with guardrails, not an automated reporter.

---

## Extensibility

The system is designed to scale by adding beats, not complexity:

- Add a new beat by adding:
  - sources config for the beat
  - a voice constitution
  - optional beat-specific heuristics (later)

Social ingestion, richer credibility analysis, and memory/RAG layers are future phases that plug into the existing brief pack and pitch/draft boundary.

---

## Dependencies

`pyproject.toml` is the source of truth for version pins.

### Runtime

- **httpx** — sync HTTP client for RSS fetching (explicit timeouts + retries)
- **feedparser** — RSS/Atom feed parsing
- **pyyaml** — YAML config file loading
- **pydantic** — declarative data models and validation
- **rich** — CLI output formatting
- **anthropic** — Anthropic API client (draft step only)
- **scikit-learn** — TF-IDF vectorization and agglomerative clustering
- **numpy** — numerical operations (pinned alongside scikit-learn)
- **python-dotenv** — `.env` file loading for local development

### Dev

- **pytest** — test framework
- **ruff** — linter and formatter
- **pytest-mock** — test mocking utilities

---

## Operational Notes

- `out/` is gitignored; it is an artifact directory.
- Config and secrets are never committed.
- The human editor is the final authority on publication.


