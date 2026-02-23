# TODO

## Phase 0: Bootstrap
- [x] Repository scaffolding, tooling, stubs, config boundary

## Phase 1: Core Data Models (PRD 001)
- [x] Pydantic models for pipeline data types

## Phase 2: Settings Loading & Time Anchor (PRD 002)
- [x] Config loaders, time anchor, config models

## Phase 3: RSS Ingestion & Normalization
- [ ] Define requirements for ingestion and normalization (conversation)
- [ ] Implement ingestion/rss.py
- [ ] Implement normalize/normalize.py
- [ ] Integration tests for ingest-to-normalize pipeline

## Phase 4: Deduplication
- [ ] Implement dedupe module

## Phase 5: Clustering
- [ ] Implement cluster module behind Clusterer protocol

## Phase 6: Ranking & Pitch Generation
- [ ] Implement rank and pitches modules

## Phase 7: Draft Generation
- [ ] Implement writer, provider interface, Anthropic provider
- [ ] Content verification via verify_content.sh

## Phase 8: QA Checks
- [ ] Implement QA check functions

## Phase 9: Rendering & CLI Wiring
- [ ] Implement render module
- [ ] Wire all pipeline steps through CLI commands
