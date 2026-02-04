# PRD 002: Settings Loading & Time Anchor

**PRD ID**: `002-settings-loading`
**Phase**: 2 + 3 (partial) per BLUEPRINT.md

## Goal

Implement the four configuration loaders in `src/newsroom/settings.py` and the
deterministic time resolver in `src/newsroom/time_anchor.py`. These replace the
current `NotImplementedError` stubs with typed, validated functions that
downstream pipeline phases depend on. This PRD also introduces the Pydantic
config models (`FeedSource`, `QAConfig`, `ClusterConfig`, `VoiceConstitution`)
that give the settings layer its type safety.

This PRD implements `resolve_now` but does **not** wire it into the CLI. CLI
integration occurs in a later PRD when the pipeline commands are connected.

## User Stories

- As a pipeline module author, I can call `load_sources("science_tech", config_dir)`
  and receive a validated `list[FeedSource]` without manually parsing YAML or
  guessing field names.
- As a QA check author, I can access `voice.taboo_phrases` as a typed `list[str]`
  instead of re-parsing the voice constitution markdown in every check.
- As a test author, I can call `resolve_now("2026-01-15T12:00:00Z")` and get a
  deterministic UTC-aware datetime, or set `NEWSROOM_NOW` in the environment to
  control time globally in fixtures.
- As a developer, I get a clear `ConfigError` with the file path and problem
  description when a config file is missing or malformed, rather than an opaque
  traceback.

## Non-Goals

- No RSS fetching, parsing, or normalization logic.
- No clustering, ranking, or pitch-generation logic.
- No CLI changes — current stubs and `--now` flag remain as-is. CLI wiring of
  `resolve_now` occurs in a later PRD.
- No changes to `config.example/` files (they are consumed, not modified).
- No runtime config generation (`scripts/init_config.sh` is unchanged).
- No new dependencies — `pyyaml` and `pydantic` are already in `pyproject.toml`.
- No business-logic methods on config models (ADR-004: purely declarative).

## Constraints

- **ADR-004**: All Pydantic models in `src/newsroom/models.py`. Config models
  (`FeedSource`, `QAConfig`, `ClusterConfig`, `VoiceConstitution` and their
  sub-models) are added to `models.py` in a clearly demarcated section above the
  existing pipeline models, kept free of business logic.
- **ADR-006**: `resolve_now` priority chain is `cli_now` arg > `NEWSROOM_NOW`
  env var > `datetime.now(UTC)`. No other sources.
- **ADR-007**: All outputs of `resolve_now` are timezone-aware UTC datetimes.
  Naive parsed datetimes have `tzinfo=timezone.utc` attached. Timezone-aware
  parsed datetimes are converted to UTC.
- **ISO 8601 `Z` suffix**: `resolve_now` must normalize a trailing `Z` to
  `+00:00` before calling `datetime.fromisoformat()`, because Python 3.12's
  `fromisoformat` does not reliably handle the `Z` suffix.
- **Fail fast**: All four loaders raise `ConfigError` on missing files, missing
  directories, invalid YAML structure, missing keys, or Pydantic validation
  failure. No silent defaults, no `None` returns. Error messages include the
  specific file path that caused the failure.
- **No new dependencies.**
- **No `TODO`, `FIXME`, or temporal comments.**
- **Preserve existing ABOUTME headers** in `settings.py`, `time_anchor.py`, and
  `models.py`.
- **`social` key in `sources.yaml`**: Ignored by `load_sources`. V0 loads only
  the `rss` list for a given beat. If the `rss` key is missing under the beat,
  raise `ConfigError`.

## Sources & Data

- Config file specifications: `docs/BLUEPRINT.md` §§ Phase 2.
- Design decisions: `docs/decisions.md` ADR-004, ADR-006, ADR-007.
- Example config files (consumed, not modified): `config.example/sources.yaml`,
  `config.example/qa.yaml`, `config.example/cluster.yaml`,
  `config.example/voices/science_tech.md`.
- QAConfig fields match the committed `config.example/qa.yaml` structure, which
  was specified in the Blueprint Phase 2 and implemented in PRD 000.
- No config file changes, no new output artifacts.

## Config Models to Add (in `models.py`)

### FeedSource

| Field  | Type     | Constraint |
|--------|----------|------------|
| `name` | `str`    | —          |
| `url`  | `HttpUrl`| —          |

### QAConfig (with nested sub-models)

```
HedgingConfig
  max_ratio: float
  phrases: list[str]

SourceAttributionConfig
  require_citation_near_stats: bool
  citation_pattern: str

VoiceDriftConfig
  max_avg_sentence_length: int
  min_avg_sentence_length: int
  max_sentence_length: int

QAConfig
  hedging: HedgingConfig
  source_attribution: SourceAttributionConfig
  voice_drift: VoiceDriftConfig
```

### ClusterConfig (with nested sub-models)

```
TfidfConfig
  max_features: int
  ngram_range: list[int]       # must be exactly 2 elements; min <= max
  stop_words: str
  min_df: int
  extra_stop_words: list[str] = []

ClusteringMethodConfig
  method: str
  distance_threshold: float
  linkage: str

KeywordsConfig
  top_n: int
  generic_filter: list[str] = []

ClusterConfig
  tfidf: TfidfConfig
  clustering: ClusteringMethodConfig
  keywords: KeywordsConfig
```

`TfidfConfig.ngram_range` must contain exactly 2 integers where
`ngram_range[0] <= ngram_range[1]`. Enforced by a Pydantic validator.

### VoiceConstitution

| Field              | Type        | Source Section       |
|--------------------|-------------|----------------------|
| `beliefs`          | `list[str]` | `## Beliefs`         |
| `tone`             | `list[str]` | `## Tone`            |
| `forbidden_moves`  | `list[str]` | `## Forbidden Moves` |
| `taboo_phrases`    | `list[str]` | `## Taboo Phrases`   |
| `required_habits`  | `list[str]` | `## Required Habits` |

All five sections are required. `load_voice` raises `ConfigError` if any section
is missing from the markdown file.

## Functions to Implement

### `settings.py`

#### `ConfigError(Exception)`

Custom exception for all config loading failures. Raised on:
- Missing config file or directory
- Invalid YAML structure or missing keys
- Pydantic validation failure (wrapped with file path context)
- Missing beat key in `sources.yaml` (include available beats in message)
- Missing `rss` key under a beat in `sources.yaml`
- Missing required H2 section in voice markdown

All `ConfigError` messages must include the specific file path.

#### `load_sources(beat: str, config_dir: Path) -> list[FeedSource]`

1. Read `config_dir / "sources.yaml"`. Raise `ConfigError` if file or
   directory does not exist.
2. Parse YAML. Look up the `beat` key (e.g., `science_tech`). Raise
   `ConfigError` if beat key is missing (include available beats in message).
3. Extract the `rss` list. Raise `ConfigError` if `rss` key is missing.
   Ignore `social`.
4. Validate each entry as `FeedSource`.
5. Return `list[FeedSource]`.

#### `load_qa_config(config_dir: Path) -> QAConfig`

1. Read `config_dir / "qa.yaml"`. Raise `ConfigError` if missing.
2. Parse YAML.
3. Validate as `QAConfig` (Pydantic handles nested structure).
4. Wrap any `ValidationError` as `ConfigError` with file path context.

#### `load_cluster_config(config_dir: Path) -> ClusterConfig`

1. Read `config_dir / "cluster.yaml"`. Raise `ConfigError` if missing.
2. Parse YAML.
3. Validate as `ClusterConfig` (Pydantic handles nested structure).
4. Wrap any `ValidationError` as `ConfigError` with file path context.

#### `load_voice(beat: str, config_dir: Path) -> VoiceConstitution`

Deterministic markdown parsing rules:

1. Read `config_dir / "voices" / f"{beat}.md"`. Raise `ConfigError` if missing.
2. Split content on lines that start with `## ` (H2 headers). Section names
   are matched exactly: `Beliefs`, `Tone`, `Forbidden Moves`, `Taboo Phrases`,
   `Required Habits`.
3. Within each section, extract bullet items: lines whose stripped form starts
   with `- ` (hyphen-space). Strip the `- ` prefix and trim whitespace.
4. Blank lines are ignored. Non-bullet content inside a section (e.g., prose
   paragraphs) is ignored.
5. Only `- ` (hyphen-space) bullets are recognized. Numbered lists (`1. `),
   asterisk bullets (`* `), and other formats are not supported and are ignored.
6. Validate as `VoiceConstitution`. Raise `ConfigError` if any required section
   is missing from the file.

### `time_anchor.py`

#### `resolve_now(cli_now: str | None = None) -> datetime`

All outputs are timezone-aware UTC datetimes (`tzinfo=timezone.utc`).

1. If `cli_now` is not `None`: normalize trailing `Z` to `+00:00`, then parse
   with `datetime.fromisoformat()`. If the result is naive, attach
   `timezone.utc`. If timezone-aware, convert to UTC via `.astimezone(timezone.utc)`.
2. Else if `NEWSROOM_NOW` env var is set and non-empty: parse identically to
   step 1.
3. Else: return `datetime.now(timezone.utc)`.
4. Invalid strings raise `ValueError` (natural `fromisoformat` behavior — not
   wrapped in `ConfigError` since this is not a config loader).

## Acceptance Criteria

1. `from newsroom.models import FeedSource, QAConfig, ClusterConfig, VoiceConstitution` succeeds.
2. `from newsroom.settings import load_sources, load_qa_config, load_cluster_config, load_voice, ConfigError` succeeds.
3. `from newsroom.time_anchor import resolve_now` succeeds.
4. `load_sources("science_tech", config_dir)` returns a `list[FeedSource]` with 5 entries when pointed at `config.example/`.
5. `load_sources("nonexistent", config_dir)` raises `ConfigError`.
6. `load_sources(beat, nonexistent_dir)` raises `ConfigError` (directory does not exist). `load_sources(beat, empty_dir)` raises `ConfigError` (file missing inside directory). Both error messages include the specific path.
7. `load_qa_config(config_dir)` returns a `QAConfig` with `hedging`, `source_attribution`, and `voice_drift` sub-models populated.
8. `load_cluster_config(config_dir)` returns a `ClusterConfig` with `tfidf`, `clustering`, and `keywords` sub-models populated.
9. `load_qa_config(missing_dir)` and `load_cluster_config(missing_dir)` raise `ConfigError`.
10. `load_voice("science_tech", config_dir)` returns a `VoiceConstitution` with all 5 sections populated as `list[str]`.
11. `load_voice("nonexistent", config_dir)` raises `ConfigError`.
12. Voice markdown missing a required section → `ConfigError`.
13. `resolve_now("2026-01-15T12:00:00Z")` returns `datetime(2026, 1, 15, 12, 0, tzinfo=UTC)`.
14. `resolve_now("2026-01-15T07:00:00-05:00")` returns `datetime(2026, 1, 15, 12, 0, tzinfo=UTC)`.
15. `resolve_now(None)` with `NEWSROOM_NOW=2026-01-15T12:00:00Z` returns the same as AC 13.
16. `resolve_now(None)` with no env var returns a UTC-aware datetime within ±2 seconds of `datetime.now(timezone.utc)` at test execution time.
17. `resolve_now("not-a-date")` raises `ValueError`.
18. `cli_now` takes precedence over `NEWSROOM_NOW` env var.
19. All config models round-trip through `.model_dump_json()` → `.model_validate_json()`.
20. Config models are grouped in a clearly marked section within `models.py` and kept free of business logic.
21. `TfidfConfig` rejects `ngram_range` with length != 2 or where `min > max`.
22. `load_sources` raises `ConfigError` when `rss` key is missing under the beat.
23. `bash scripts/verify.sh` passes (lint + format + tests).

## Definition of Done

- `scripts/verify.sh` passes.
- `tests/unit/test_settings.py` covers settings acceptance criteria (AC 1–2, 4–12, 19–20, 22).
- `tests/unit/test_time_anchor.py` covers time anchor acceptance criteria (AC 3, 13–18).
- `tests/unit/test_models.py` updated with config model tests (AC 1, 19, 21).
- No unrelated changes to other modules.
- Existing ABOUTME headers preserved in all modified files.
- `docs/agent-notes.md` updated with PRD 002 completion note.
- Single commit message drafted referencing PRD `002-settings-loading`.
