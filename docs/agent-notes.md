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

### Next Steps

- **PRD 002: Settings Loading & Time Anchor** — Implement `settings.py` (YAML + Markdown config loaders) and `time_anchor.py` (`--now` / `NEWSROOM_NOW` resolution). Completes the typed data foundation for subsequent pipeline phases.
