# Research: Documentation Reorganization

**Date**: 2026-02-05
**Feature**: 001-docs-reorganization

## Context

This feature is a documentation-only reorganization. No technology decisions or dependency research required. The research phase focused on auditing existing documentation to identify content ownership, duplication, and extraction targets.

## Research 1: Current Documentation Inventory

### Decision

Six documentation files exist, four of which have overlapping content:

| File | Lines | Primary Role | Overlap With |
|------|-------|-------------|--------------|
| README.md | 62 | Project entry point | BLUEPRINT (overview, structure, stack) |
| docs/BLUEPRINT.md | 650 | System blueprint + implementation spec | architecture.md, README, decisions.md |
| docs/architecture.md | 282 | System architecture | BLUEPRINT (operating model, modules, data flow) |
| CLAUDE.md | 53 | Agent operational rules | BLUEPRINT (governing docs reference) |
| docs/AGENTIC_DEV_PLAYBOOK.md | 240 | Development workflow | Global ~/.claude/ playbook |
| .specify/memory/constitution.md | 181 | Project principles + governance | BLUEPRINT, playbook (authority hierarchy) |
| docs/decisions.md | 120 | ADR log | BLUEPRINT (design decisions) |
| docs/agent-notes.md | 42 | Cross-session agent memory | None |

### Rationale

BLUEPRINT.md is the primary source of duplication — it contains content that belongs in architecture.md (system design), decisions.md (design decisions), and README.md (overview). The playbook duplicates global Claude configuration.

### Alternatives Considered

- Merge BLUEPRINT into README: Rejected — would make README 700+ lines, not a standard project README.
- Keep BLUEPRINT alongside architecture.md: Rejected — creates two competing sources of truth for system design.

## Research 2: BLUEPRINT Content Triage

### Decision

BLUEPRINT.md content categorized by destination:

**→ docs/architecture.md** (summary-level extraction):
- Data Model Overview (Phase 1 models) — conceptual descriptions only, not field definitions
- Resolved Design Decisions — brief list pointing to decisions.md for full ADRs
- Dependencies list — names only, pyproject.toml is source of truth for versions

**→ Already covered** (no extraction needed):
- Operating Model — already in architecture.md (L1-29)
- Design Goals — already in architecture.md (L33-41)
- Non-Goals — already in architecture.md (L45-51)
- Data Flow — already in architecture.md (L72-103)
- Core Modules — already in architecture.md (L107-157)
- CLI Surface — already in architecture.md (L163-190)
- Testing Strategy — already in architecture.md (L206-220)
- Provider Abstraction — already in architecture.md (L236-244)

**→ Discarded** (code is source of truth):
- Full Pydantic model definitions with field types (Phase 1)
- Config file YAML examples (Phase 2)
- Function signatures for every module
- Implementation phase descriptions (Phase 0-12)
- Detailed directory structure with inline comments

### Rationale

Architecture.md already covers most of the BLUEPRINT's architectural content. Only three sections need extraction: data model overview (conceptual), design decisions reference, and dependency list. The vast majority of BLUEPRINT detail is implementation-level content that belongs in the code itself.

## Research 3: Authority Hierarchy Conflict Resolution

### Decision

The current constitution.md authority hierarchy is outdated:
1. CI / verification output
2. docs/BLUEPRINT.md ← being removed
3. AGENTIC_DEV_PLAYBOOK.md ← being removed
4. This constitution ← should be #2
5. CLAUDE.md

New hierarchy (per spec FR-006):
1. CI / verification output (objective truth)
2. .specify/memory/constitution.md (supreme constitutional authority)
3. docs/architecture.md (system design authority)
4. docs/decisions.md (ADR-style design decisions)
5. CLAUDE.md (operational rules and conventions)
6. docs/prd/*.md (feature specifications)

### Rationale

The constitution captures the project's non-negotiable principles. It should be the highest human-authored authority, superseded only by CI output (which is objective truth). Architecture.md describes the system design; decisions.md records historical choices; CLAUDE.md provides operational rules; PRDs define feature work.

### Alternatives Considered

- Keep constitution at #4 (current position): Rejected — constitution is described as "non-negotiable principles" and should have corresponding authority.
- Put CLAUDE.md above decisions.md: Rejected — design decisions are more durable than operational conventions.
