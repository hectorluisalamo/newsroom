# TODO

## Phase 0: Bootstrap
- [x] Repository scaffolding, tooling, stubs, config boundary

## Phase 1: Core Data Models (PRD 001)
- [x] Pydantic models for pipeline data types

## Phase 2: Settings Loading & Time Anchor (PRD 002)
- [x] Config loaders, time anchor, config models

## Phase 3: RSS Ingestion & Normalization (PRD 003)
- [ ] Draft PRD 003
- [ ] Implement ingestion/rss.py
- [ ] Implement normalize/normalize.py
- [ ] Integration tests for ingest-to-normalize pipeline

## Phase 4: Deduplication
- [ ] Draft PRD
- [ ] Implement dedupe module

## Phase 5: Clustering
- [ ] Draft PRD
- [ ] Implement cluster module behind Clusterer protocol

## Phase 6: Ranking & Pitch Generation
- [ ] Draft PRD
- [ ] Implement rank and pitches modules

## Phase 7: Draft Generation
- [ ] Draft PRD
- [ ] Implement writer, provider interface, Anthropic provider
- [ ] Content verification via verify_content.sh

## Phase 8: QA Checks
- [ ] Draft PRD
- [ ] Implement QA check functions

## Phase 9: Rendering & CLI Wiring
- [ ] Draft PRD
- [ ] Implement render module
- [ ] Wire all pipeline steps through CLI commands
