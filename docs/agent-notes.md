# Agent Notes

## Phase 0: Bootstrap

- Scaffolded repository structure per BLUEPRINT.md Phase 0 and PRD 000-bootstrap.
- All modules stubbed with ABOUTME headers and function signatures.
- Open-core config boundary: `config.example/` committed, `config/` gitignored.
- `scripts/init_config.sh` copies examples into runtime config.
- `scripts/sync_private_config.sh` overlays private config if available.
- `verify.sh` passes: Ruff lint, Ruff format, pytest (13 tests).
- CLI `--help` works with pitch/draft/qa subcommands.
- All 24 Acceptance Criteria from PRD 000-bootstrap verified.
- CodeRabbit review clean (no material findings).
- Known issues: none.

## Phase 1: Core Data Models (PRD 001)

- Implemented 8 Pydantic v2 models in `src/newsroom/models.py`: FeedItem, BriefCluster, BriefPack, Pitch, PitchSet, Draft, QAFinding, QAReport.
- Centralized UTC-aware datetime validator (`_require_utc`) shared across all models with datetime fields.
- Validators: summary max 500 chars, recency_score 0.0–1.0, source_urls min 3 / truncate-to-first-10, pitches exactly 3.
- `Draft.word_count` left informational (no model-level validation).
- 41 tests in `tests/unit/test_models.py` covering all 13 acceptance criteria.
- `verify.sh` passes: Ruff lint, Ruff format, pytest (53 tests).
- Known issues: none.

## Phase 2: Settings Loading & Time Anchor (PRD 002)

- Added 11 config Pydantic models to `src/newsroom/models.py`: FeedSource, HedgingConfig, SourceAttributionConfig, VoiceDriftConfig, QAConfig, TfidfConfig, ClusteringMethodConfig, KeywordsConfig, ClusterConfig, VoiceConstitution. Grouped in a clearly marked section above pipeline models.
- `TfidfConfig.ngram_range` validated: exactly 2 elements, min <= max.
- Implemented `resolve_now` in `src/newsroom/time_anchor.py`: cli_now > NEWSROOM_NOW env > datetime.now(UTC). Normalizes `Z` suffix to `+00:00` for `fromisoformat` compatibility. Naive strings treated as UTC; aware strings converted to UTC.
- Implemented 4 config loaders in `src/newsroom/settings.py`: `load_sources`, `load_qa_config`, `load_cluster_config`, `load_voice`, plus `ConfigError` exception.
- `load_voice` uses deterministic markdown parsing: exact H2 header matching, hyphen-space bullets only, non-bullet content ignored.
- All loaders fail fast with `ConfigError` including file paths in messages.
- 63 new tests across 3 files: `test_models.py` (14 new), `test_settings.py` (30), `test_time_anchor.py` (12). Golden-path tests use `config.example/`; error-path tests use `tmp_path`.
- `verify.sh` passes: Ruff lint, Ruff format, pytest (116 tests).
- CLI wiring of `resolve_now` deferred to a later PRD.
- Known issues: none.

### Next Steps

- **PRD 003**: RSS Ingestion + Normalization — Implement `ingestion/rss.py` and `normalize/normalize.py`. Depends on settings loaders and time anchor from PRD 002.
