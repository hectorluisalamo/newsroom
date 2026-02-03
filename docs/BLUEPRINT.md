# Blueprint: "Newsroom" — Synthetic Newsroom CLI

## Overview

A Python CLI project ("newsroom") that produces Substack-ready opinion columns from beat-specific research briefs and writer voices. V0 covers the `science_tech` beat end-to-end.

**Stack**: Python 3.12+, uv, Ruff, pytest, Pydantic, feedparser, httpx, rich, anthropic SDK, scikit-learn, python-dotenv.

**Repo root**: Rename `crash_log/` → project lives at current working directory but the Python package is `newsroom`. No confusing package/folder collision.

---

## Resolved Design Decisions

Recorded in `docs/decisions.md` (ADR-style) during Phase 0.

1. **argparse over Click** — two commands, lean deps. Subparsers with `required=True`. Parsing centralized in `cli.py`; command modules receive typed args, stay testable.
2. **scikit-learn as required dependency** — TF-IDF clustering is core to pitches. Pinned alongside numpy in `pyproject.toml`. Clustering logic lives behind a `Clusterer` protocol so the rest of the codebase doesn't know/care about the implementation.
3. **Pitch generation is purely algorithmic** — no LLM. Different clusters → different pitches. When cluster count < 3, use angle templates ("incentives", "second-order effects", "language framing") to force meaningful differentiation. Pitches carry rich metadata so the draft step has real bones.
4. **Single `models.py`** — purely declarative, no business logic. Revisit if >300-400 LOC or circular imports appear.
5. **httpx over requests** — sync client only in V0 (determinism + simplicity). Explicit timeouts + retries on every request.
6. **Deterministic time control** — `--now <ISO8601>` flag and `NEWSROOM_NOW` env var override current time for all date-dependent operations. Fixtures and `verify_content.sh` always pass a fixed `--now`.
7. **UTC-aware datetimes everywhere** — all `published_at` and `generated_at` fields normalized to UTC on ingest. No naive datetimes.
8. **Inline citation markers** — drafts use `[src:N]` convention for inline source references. QA checks match stats to citation markers, not sentence proximity.
9. **LLM model from config/env** — model ID lives in env (`NEWSROOM_MODEL`) with a default, never hardcoded in provider code.
10. **python-dotenv for local dev** — `.env` file loaded explicitly on CLI startup so users don't need to manually export vars.

---

## Phase 0: Project Bootstrap (Scaffolding Only)

### Directory Structure

```
<repo-root>/                           # currently crash_log/, package is "newsroom"
├── pyproject.toml
├── README.md
├── CLAUDE.md                          # repo-local rules
├── .gitignore
├── .env.example                       # ANTHROPIC_API_KEY, NEWSROOM_MODEL, NEWSROOM_NOW
├── .python-version                    # 3.12
├── config/
│   ├── sources.yaml                   # RSS feeds per beat
│   ├── qa.yaml                        # QA thresholds
│   ├── cluster.yaml                   # TF-IDF + clustering params (treated as API)
│   └── voices/
│       └── science_tech.md            # voice constitution
├── docs/
│   ├── AGENTIC_DEV_PLAYBOOK.md        # already exists
│   ├── decisions.md                   # ADR log
│   ├── prd/
│   │   └── prd-template.md
│   ├── architecture.md
│   └── agent-notes.md
├── fixtures/                          # saved RSS XML + expected outputs for tests
│   └── science_tech/
│       ├── sample_feed.xml
│       ├── sample_feed_2.xml
│       ├── expected_brief.json
│       └── sample_draft_text.md
├── scripts/
│   ├── verify.sh                      # lint + typecheck + unit tests
│   └── verify_content.sh              # pitch/draft against fixtures with fixed --now
├── src/
│   └── newsroom/
│       ├── __init__.py
│       ├── __main__.py                # CLI entry point (loads dotenv)
│       ├── cli.py                     # argparse subparsers (parsing only)
│       ├── commands.py                # command implementations (pitch_cmd, draft_cmd, qa_cmd)
│       ├── settings.py                # config loader (sources, qa, cluster params, voices)
│       ├── logging_config.py          # stdlib logging setup
│       ├── models.py                  # all Pydantic models (declarative only)
│       ├── time_anchor.py             # --now / NEWSROOM_NOW resolution
│       ├── ingestion/
│       │   ├── __init__.py
│       │   └── rss.py                 # fetch + parse RSS feeds (sync httpx, timeouts, 1 retry)
│       ├── normalize/
│       │   ├── __init__.py
│       │   └── normalize.py           # clean raw feed items into FeedItems
│       ├── dedupe/
│       │   ├── __init__.py
│       │   └── dedupe.py              # fingerprint-based deduplication
│       ├── cluster/
│       │   ├── __init__.py
│       │   ├── protocol.py            # Clusterer protocol (interface)
│       │   └── tfidf.py               # TF-IDF + cosine implementation
│       ├── rank/
│       │   ├── __init__.py
│       │   └── rank.py                # score clusters by recency, source diversity, etc.
│       ├── pitches/
│       │   ├── __init__.py
│       │   ├── pitches.py             # algorithmic pitch generation from top clusters
│       │   └── angles.py              # angle templates for differentiation
│       ├── draft/
│       │   ├── __init__.py
│       │   ├── provider.py            # LLM provider ABC
│       │   ├── anthropic_provider.py  # Anthropic Claude implementation
│       │   └── writer.py              # prompt assembly + LLM call + citation enforcement
│       ├── qa/
│       │   ├── __init__.py
│       │   └── checks.py              # source attribution, hedging, voice drift checks
│       ├── render/
│       │   ├── __init__.py
│       │   └── render.py              # JSON + Markdown output formatting
│       └── utils/
│           ├── __init__.py
│           ├── time_utils.py          # "since 48h" parsing, timestamp normalization
│           └── text.py                # HTML stripping, whitespace normalization, shared helpers
├── tests/
│   ├── conftest.py                    # shared fixtures, NO NETWORK (enforced)
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_normalize.py
│   │   ├── test_dedupe.py
│   │   ├── test_cluster.py
│   │   ├── test_rank.py
│   │   ├── test_pitches.py
│   │   ├── test_qa.py
│   │   ├── test_render.py
│   │   └── test_time_utils.py
│   ├── integration/
│   │   ├── test_pitch_pipeline.py     # ingestion → pitches (fixture data, fixed --now)
│   │   └── test_draft_pipeline.py     # pitch → draft → QA (mocked LLM)
│   └── e2e/
│       └── test_cli.py                # CLI subprocess, --out-dir to tmp, verify files
└── out/                               # gitignored, default runtime output
```

### New/Changed from Prior Draft
- `time_anchor.py` — resolves `--now` / `NEWSROOM_NOW` into a single canonical "now" used everywhere
- `config/cluster.yaml` — TF-IDF params as config (max_features, ngram_range, stop_words, distance_threshold)
- `commands.py` now includes `qa_cmd` — standalone QA subcommand
- All CLI commands accept `--out-dir` (default `out/`) and `--now` (optional)
- `.env.example` includes `NEWSROOM_MODEL` and `NEWSROOM_NOW`

### Files Created in Phase 0
- `pyproject.toml` — metadata, pinned deps (scikit-learn, numpy explicit), dev-deps, Ruff config, pytest config
- `CLAUDE.md` — repo-local rules
- `docs/decisions.md` — the 10 design decisions above
- `.gitignore` — out/, .env, __pycache__, .ruff_cache, *.egg-info, etc.
- `.env.example` — `ANTHROPIC_API_KEY=`, `NEWSROOM_MODEL=claude-sonnet-4-20250514`, `NEWSROOM_NOW=`
- `.python-version` — `3.12`
- All `__init__.py` files
- `scripts/verify.sh` and `scripts/verify_content.sh`
- `docs/prd/prd-template.md` — canonical format with Sources & Data section
- `docs/architecture.md`
- `docs/agent-notes.md`
- Stub modules (signatures + docstrings, no logic)
- Initial commit: scaffolding only

---

## Phase 1: Pydantic Data Models

### Models (all in `src/newsroom/models.py`, purely declarative)

```python
class FeedItem(BaseModel):
    """A single normalized article from an RSS feed."""
    item_id: str                    # SHA256 of canonical URL
    title: str
    url: HttpUrl
    source_name: str                # e.g., "Ars Technica"
    source_feed_url: HttpUrl        # consistent HttpUrl typing
    published_at: datetime          # UTC-aware, always
    summary: str                    # cleaned: HTML stripped, whitespace normalized, then max 500 chars
    raw_tags: list[str] = []
    beat: str

class BriefCluster(BaseModel):
    """A cluster of related feed items representing a story thread."""
    cluster_id: str                 # SHA256 of sorted item_ids
    label: str                      # most representative title
    items: list[FeedItem]
    centroid_keywords: list[str]    # top 5 TF-IDF terms (stopword-filtered)
    recency_score: float            # 0-1
    source_diversity: int           # count of unique sources
    size: int                       # number of items

class BriefPack(BaseModel):
    """The full research brief for a beat on a given date."""
    beat: str
    date: date
    since: str                      # e.g., "48h"
    total_items_ingested: int
    total_items_after_dedupe: int
    clusters: list[BriefCluster]
    generated_at: datetime          # UTC-aware

class Pitch(BaseModel):
    """A single pitch candidate derived from the brief pack."""
    pitch_id: str                   # "{beat}-{date}-{index}"
    title: str
    thesis_angle: str               # 1-2 sentences
    why_now: str                    # 1-2 sentences
    key_points: list[str]           # 3-5 bullets (substantive, not headlines)
    source_urls: list[HttpUrl]      # min 3, max 10
    risk_flags: list[str]           # "single_source", "sensational", "missing_primary", "social_only"
    cluster_id: str
    angle: str                      # which angle template was used

    @field_validator("source_urls")
    @classmethod
    def at_least_three_sources(cls, v):
        if len(v) < 3:
            raise ValueError("Pitch requires at least 3 source URLs")
        return v[:10]

class PitchSet(BaseModel):
    """The set of 3 pitches produced for a beat on a date."""
    beat: str
    date: date
    pitches: list[Pitch]            # exactly 3
    brief_pack_ref: str             # path to brief.json
    generated_at: datetime

class Draft(BaseModel):
    """A generated opinion column draft."""
    beat: str
    date: date
    pitch_id: str
    title: str
    body_md: str                    # ~700-word column with [src:N] inline citations
    word_count: int
    sources: list[HttpUrl]          # numbered list matching [src:N] markers
    guidance_used: str
    model_id: str
    generated_at: datetime
    token_usage: dict[str, int] | None = None  # optional: {"input": N, "output": N}

class QAFinding(BaseModel):
    """A single QA check finding."""
    check_name: str
    severity: Literal["error", "warning", "info"]
    location: str                   # paragraph number or line range
    message: str
    details: dict[str, Any] = {}

class QAReport(BaseModel):
    """Quality gate results for a draft."""
    beat: str
    date: date
    pitch_id: str
    passed: bool
    findings: list[QAFinding]
    checks_run: list[str]
    generated_at: datetime
```

Key changes from prior draft:
- `source_feed_url` → `HttpUrl`
- All datetimes UTC-aware (enforced in normalize)
- `summary` truncation happens after HTML strip + whitespace normalization
- `Pitch.source_urls` min 3, max 10 (with validator)
- `Draft.token_usage` optional field for logging
- `Draft.body_md` uses `[src:N]` citation convention

---

## Phase 2: Config Files + Settings Loader

### `config/sources.yaml`
```yaml
science_tech:
  rss:
    - name: "Ars Technica"
      url: "https://feeds.arstechnica.com/arstechnica/index"
    - name: "MIT Technology Review"
      url: "https://www.technologyreview.com/feed/"
    - name: "Nature News"
      url: "https://www.nature.com/nature.rss"
    - name: "Hacker News (Best)"
      url: "https://hnrss.org/best"
    - name: "The Verge"
      url: "https://www.theverge.com/rss/index.xml"
  social: []  # placeholder, not implemented in V0
```

### `config/qa.yaml`
```yaml
hedging:
  max_ratio: 0.15
  phrases:
    - "it remains to be seen"
    - "only time will tell"
    - "it's unclear"
    - "some experts say"
    - "arguably"
    - "perhaps"

source_attribution:
  require_citation_near_stats: true
  citation_pattern: "\\[src:\\d+\\]"    # regex for [src:N] markers

voice_drift:
  max_avg_sentence_length: 35
  min_avg_sentence_length: 10
  max_sentence_length: 60
```

### `config/cluster.yaml` (new — treat as API)
```yaml
tfidf:
  max_features: 5000
  ngram_range: [1, 2]
  stop_words: "english"
  min_df: 2
  # custom stop words to add on top of sklearn's english list
  extra_stop_words: []

clustering:
  method: "agglomerative"
  distance_threshold: 0.7         # cosine distance cutoff
  linkage: "average"

keywords:
  top_n: 5
  # words too generic to be useful as centroid keywords
  generic_filter: ["AI", "data", "new", "technology", "tech", "report", "says"]
```

### `config/voices/science_tech.md`
Structured voice constitution with parseable H2 sections:
- `## Beliefs`
- `## Tone`
- `## Forbidden Moves`
- `## Taboo Phrases` — bullet list, each phrase on its own line (used by QA)
- `## Required Habits`

### `src/newsroom/settings.py`
- `load_sources(beat: str, config_dir: Path) -> list[FeedSource]`
- `load_qa_config(config_dir: Path) -> QAConfig` (typed Pydantic model)
- `load_cluster_config(config_dir: Path) -> ClusterConfig` (typed Pydantic model)
- `load_voice(beat: str, config_dir: Path) -> VoiceConstitution` (parses .md sections)
- Fail fast on missing/invalid config

---

## Phase 3: RSS Ingestion + Normalization

### `src/newsroom/ingestion/rss.py`
- `fetch_feed(url: str, timeout: int = 30) -> feedparser.FeedParserDict`
  - Sync httpx client, explicit timeout
  - 1 retry on transient failure (timeout, 5xx)
- `fetch_all_feeds(sources: list[FeedSource]) -> list[RawFeedEntry]`
  - Graceful per-feed failure: log warning, continue

### `src/newsroom/normalize/normalize.py`
- `normalize_entry(entry, source, beat, now) -> FeedItem | None`
  - `item_id` = SHA256 of canonical URL
  - HTML strip → whitespace normalize → collapse repeated newlines → truncate to 500 chars
  - Date parsing: try multiple formats, normalize to UTC-aware, fall back to `now`
- `normalize_all(entries, sources, since, now) -> list[FeedItem]`
  - `now` parameter from time_anchor (deterministic)
  - Filter by `since` window relative to `now`
  - Sort by `published_at` (stable)

### `src/newsroom/time_anchor.py`
- `resolve_now(cli_now: str | None = None) -> datetime`
  - Priority: `cli_now` arg > `NEWSROOM_NOW` env > `datetime.now(UTC)`
  - Always returns UTC-aware datetime
  - Used by all date-dependent operations

---

## Phase 4: Dedupe + Clustering

### `src/newsroom/dedupe/dedupe.py`
- `dedupe_items(items: list[FeedItem]) -> list[FeedItem]`
  - Phase 1: exact dedup by `item_id`
  - Phase 2: fuzzy dedup by title similarity (Jaccard on word sets, threshold 0.8)
  - Deterministic: keeps item with earliest `published_at` on ties

### `src/newsroom/cluster/protocol.py`
```python
class Clusterer(Protocol):
    def cluster(self, items: list[FeedItem]) -> list[BriefCluster]: ...
```

### `src/newsroom/cluster/tfidf.py`
- Implements `Clusterer` protocol
- All params from `config/cluster.yaml` (max_features, ngram_range, stop_words, distance_threshold, linkage)
- TF-IDF vectorization of title + summary
- Agglomerative clustering with explicit distance_threshold cutoff
- centroid_keywords: top 5 TF-IDF terms, filtered through generic_filter list
- Deterministic cluster_id: SHA256 of sorted item_ids
- Singletons kept as size-1 clusters

### `src/newsroom/rank/rank.py`
- `rank_clusters(clusters: list[BriefCluster]) -> list[BriefCluster]`
  - Score = recency(0.4) + source_diversity(0.3) + size(0.3)
  - Stable sort descending

---

## Phase 5: Pitch Generation (No LLM)

### `src/newsroom/pitches/angles.py`
Named angle templates:
- `"trend_analysis"` — trajectory and why it matters
- `"skeptics_take"` — what's overlooked or overhyped
- `"human_impact"` — who's affected and how
- `"incentives"` — follow the money/power
- `"second_order"` — what happens next that nobody's talking about
- `"language_framing"` — how the story is being told shapes belief

Each template: title pattern, thesis framing, key_points extraction strategy.

### `src/newsroom/pitches/pitches.py`
- `generate_pitches(brief: BriefPack, n: int = 3) -> PitchSet`
  - **≥3 clusters**: one pitch per top-3 cluster, default angle per cluster
  - **2 clusters**: one pitch each + second angle on top cluster
  - **1 cluster**: three different angle templates
  - **0 clusters**: raise error
  - Each pitch: key_points (3-5), source_urls (≥3, ≤10), risk_flags, angle
  - Deterministic pitch_id: `{beat}-{date}-{index}`

### Risk Flag Detection
- `single_source`: cluster items from only 1 feed
- `sensational`: exclamation marks, ALL CAPS words, "BREAKING"
- `missing_primary`: no source matches primary-source allowlist (arxiv.org, doi.org, sec.gov, company newsroom patterns, standards bodies, court docs, regulator reports, .gov, .edu). Warning severity, not blocker.
- `social_only`: placeholder for V0

Primary source allowlist maintained in `pitches.py` as a constant (domains + URL patterns).

---

## Phase 6: Draft Generation (LLM — Only Place LLM Is Used)

### `src/newsroom/draft/provider.py`
```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int) -> LLMResponse: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    text: str
    token_usage: dict[str, int] | None = None  # {"input": N, "output": N}
```

### `src/newsroom/draft/anthropic_provider.py`
- `AnthropicProvider(model: str | None = None, api_key: str | None = None)`
  - model from arg > `NEWSROOM_MODEL` env > default `claude-sonnet-4-20250514`
  - api_key from arg > `ANTHROPIC_API_KEY` env
  - Explicit timeout, raises `DraftGenerationError` on failure
  - Returns `LLMResponse` with token_usage populated

### `src/newsroom/draft/writer.py`
- `assemble_prompt(pitch, brief, voice, guidance) -> tuple[str, str]`
  - System prompt: voice constitution + writing rules + citation format instructions
  - User prompt: pitch + relevant cluster excerpts + guidance
  - Citation instruction: "Use [src:1], [src:2], etc. for inline citations. The Sources section at the end must list URLs in matching order."
  - Constraints: "only cite provided URLs", "mark uncertainty", "~700 words", "no web browsing"
- `write_draft(pitch, brief, voice, guidance, provider) -> Draft`
  - assemble_prompt → provider.generate → parse into Draft
  - Post-checks: word count, sources section present, citation markers exist

---

## Phase 7: QA Checks

### `src/newsroom/qa/checks.py`

All checks pure, deterministic, no network, no LLM.

1. **`check_unsourced_stats(draft, qa_config) -> list[QAFinding]`**
   - Regex: numbers, percentages, dollar amounts in each paragraph
   - Check: paragraph containing stat also contains `[src:N]` marker
   - Severity: warning

2. **`check_hedging(draft, qa_config) -> list[QAFinding]`**
   - Count sentences with hedging phrases from qa.yaml
   - Flag if ratio > `max_ratio`
   - Severity: warning

3. **`check_voice_drift(draft, voice, qa_config) -> list[QAFinding]`**
   - Taboo phrases from voice constitution → severity: error
   - Avg sentence length outside bands → severity: warning
   - Individual sentences exceeding max → severity: warning

4. **`check_citation_integrity(draft) -> list[QAFinding]`** (new)
   - Every `[src:N]` in body maps to an entry in `draft.sources`
   - No orphaned citations, no missing sources
   - Severity: error

5. **`run_all_checks(draft, voice, qa_config) -> QAReport`**
   - Aggregates all findings
   - `passed = True` iff no error-severity findings

---

## Phase 8: Render / Output

### `src/newsroom/render/render.py`
All output deterministic: stable templates, sorted keys, no random ordering.

- `render_brief_json(brief) -> str`
- `render_brief_md(brief) -> str`
- `render_pitches_json(pitches) -> str`
- `render_pitches_md(pitches) -> str` — formatted pitch cards
- `render_draft_md(draft) -> str` — Substack-ready with Sources section
- `render_draft_json(draft) -> str`
- `render_report_json(report) -> str`

### Output Directory
```
<out-dir>/<date>/<beat>/
  brief.json, brief.md, pitches.json, pitches.md
  draft.json, draft.md, report.json  (draft command only)
```
`<out-dir>` defaults to `out/`, overridable via `--out-dir`.

---

## Phase 9: CLI

### Three subcommands (argparse with subparsers, `required=True`)

**`pitch`**:
```
python -m newsroom pitch --beat science_tech --since 48h [--now ISO8601] [--out-dir DIR]
```

**`draft`**:
```
python -m newsroom draft --beat science_tech --date YYYY-MM-DD --pitch-id ID --guidance-file PATH [--now ISO8601] [--out-dir DIR]
```

**`qa`** (new):
```
python -m newsroom qa --beat science_tech --date YYYY-MM-DD [--out-dir DIR]
```
Loads draft from output dir, runs all QA checks, writes report.json.

### `src/newsroom/cli.py`
- Parsing only, calls `commands.py`
- Global flags: `--now`, `--out-dir`, `--verbose`

### `src/newsroom/commands.py`
- `pitch_cmd(beat, since, now, out_dir, source_override=None)`
- `draft_cmd(beat, date, pitch_id, guidance_file, now, out_dir)`
- `qa_cmd(beat, date, out_dir)`

### `src/newsroom/__main__.py`
- Loads dotenv via `python-dotenv`
- Calls `cli.main()`

---

## Implementation Order

| Step | What | Depends On | Test Strategy |
|------|------|-----------|---------------|
| 0 | Bootstrap scaffolding + decisions.md | — | verify.sh runs clean |
| 1 | Pydantic models + time_anchor | — | Unit: validation, serialization, UTC enforcement, time resolution |
| 2 | Config/settings loader | Models | Unit: fixture YAML/MD parsing, fail-fast on bad config |
| 3 | RSS ingestion + normalization | Models, Settings, time_anchor | Unit: fixture XML, no network, deterministic with fixed now |
| 4 | Dedupe + clustering | Models, Normalize | Unit: fixture FeedItems, deterministic output |
| 5 | Rank + pitch generation + angles | Models, Cluster | Unit: fixture clusters, differentiation assertions, min 3 sources |
| 6 | Render (JSON + MD) | Models | Unit: compare against expected output strings |
| 7 | CLI pitch command (end-to-end) | Steps 2-6 | Integration: fixtures + fixed --now. E2E: CLI subprocess + --out-dir to tmp |
| 8 | LLM provider interface + Anthropic | Models | Unit: mocked API, token_usage populated |
| 9 | Draft writer + citation enforcement | Provider, Models, Settings | Unit: mocked provider, citation markers verified |
| 10 | QA checks (incl. citation integrity) | Models, Settings | Unit: crafted drafts with known issues |
| 11 | CLI draft + qa commands (end-to-end) | Steps 8-10 | Integration: mocked LLM. E2E: CLI + --out-dir + file checks |
| 12 | Content verification script | All | Run against fixtures with fixed --now, validate all outputs |

---

## Testing Strategy

### Hard Rules
- **No network calls in any test.** All RSS data from fixtures. (Repo-local playbook rule.)
- **LLM calls always mocked** in unit and integration tests.
- **Deterministic fixtures** in `fixtures/science_tech/`.
- **All time-dependent tests use fixed `--now`.**

### Fixtures
- `sample_feed.xml` — 5-10 items, realistic RSS with dates relative to a known anchor
- `sample_feed_2.xml` — second feed for source diversity
- `expected_brief.json` — regression baseline
- `sample_draft_text.md` — pre-written draft with [src:N] markers for QA testing

### Test Types
- **Unit**: every module in isolation
- **Integration**: pitch pipeline (ingestion→pitches), draft pipeline (pitch→draft→QA)
- **E2E**: CLI subprocess with `--out-dir` to temp dir, `--now` fixed, verify files + schemas

---

## Verification

### `scripts/verify.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
ruff check src/ tests/
ruff format --check src/ tests/
pytest tests/ -v
```

### `scripts/verify_content.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
NOW="2026-01-15T12:00:00Z"
OUT_DIR=$(mktemp -d)
trap "rm -rf $OUT_DIR" EXIT

# Pitch pipeline against fixtures
python -m newsroom pitch --beat science_tech --since 48h \
  --now "$NOW" --out-dir "$OUT_DIR" --source-override fixtures/science_tech/

# Validate JSON schemas
python -c "
from newsroom.models import BriefPack, PitchSet
import json
BriefPack.model_validate_json(open('$OUT_DIR/2026-01-15/science_tech/brief.json').read())
PitchSet.model_validate_json(open('$OUT_DIR/2026-01-15/science_tech/pitches.json').read())
"

# QA on fixture draft
python -m newsroom qa --beat science_tech --date 2026-01-15 --out-dir "$OUT_DIR"
```

---

## Dependencies (pinned in pyproject.toml)

### Runtime
- `httpx` — sync HTTP client (explicit timeouts + retries)
- `feedparser` — RSS/Atom parsing
- `pyyaml` — YAML config
- `pydantic` — data models
- `rich` — CLI formatting
- `anthropic` — Anthropic API client
- `scikit-learn` — TF-IDF + clustering (pinned)
- `numpy` — pinned explicitly alongside scikit-learn
- `python-dotenv` — .env loading for local dev

### Dev
- `pytest` — test framework
- `ruff` — linter + formatter
- `pytest-mock` — mocking
