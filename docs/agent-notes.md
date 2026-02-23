# Agent Notes

## Current State
- **Branch**: main
- **Tests**: 120 passing (unit + integration + e2e)
- **Verification**: clean (lint + format + tests)
- **Phases completed**: 0 (Bootstrap), 1 (Core Data Models), 2 (Settings Loading)

## What's Been Completed
- Repository scaffold with open-core config boundary (config.example/ committed, config/ gitignored)
- 8 pipeline Pydantic models + 11 config models in src/newsroom/models.py
- 4 config loaders in src/newsroom/settings.py (sources, qa, cluster, voice)
- Time anchor (resolve_now) in src/newsroom/time_anchor.py
- Migrated from speckit/constitution governance to conversation-driven workflow (ADR-012)

## Immediate Next Step
- **PRD 003: RSS Ingestion & Normalization** — Implement ingestion/rss.py and normalize/normalize.py. Depends on settings loaders and time anchor from PRD 002. See docs/architecture.md for module responsibilities.

## Known Issues
- None
