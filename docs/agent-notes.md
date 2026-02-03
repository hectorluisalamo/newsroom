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

### Next Steps

- **PRD 001: Pydantic Models & Settings Loading** — Define all Pydantic data models in `models.py` and implement the settings loaders in `settings.py` and `time_anchor.py`. This corresponds to BLUEPRINT.md Phase 1 and gives subsequent phases their typed data foundation.
