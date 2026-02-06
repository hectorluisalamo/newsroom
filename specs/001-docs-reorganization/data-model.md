# Data Model: Documentation Reorganization

**Date**: 2026-02-05
**Feature**: 001-docs-reorganization

## Overview

This feature is a documentation-only reorganization. No code entities, database schemas, or data models are introduced or modified.

## Entities

### Documentation Files (Conceptual)

The "data model" for this feature is the set of documentation files and their roles:

| File | Role | Audience | Authority Level |
|------|------|----------|-----------------|
| `.specify/memory/constitution.md` | Supreme project principles | Agents, developers | #2 (below CI only) |
| `docs/architecture.md` | System design authority | Agents, developers | #3 |
| `docs/decisions.md` | Historical design choices | Agents, developers | #4 |
| `CLAUDE.md` | Operational rules for Claude | Claude Code agent | #5 |
| `README.md` | Public project entry point | External contributors | N/A (informational) |
| `docs/agent-notes.md` | Post-implementation summaries | Claude Code agent | N/A (working notes) |
| `docs/prd/*.md` | Feature specifications | Agents, developers | #6 |

### Authority Hierarchy (State Machine)

In case of conflict, higher-numbered authorities are overridden by lower-numbered ones:

```
CI / verification output (#1)
        ↓ overrides
constitution.md (#2)
        ↓ overrides
docs/architecture.md (#3)
        ↓ overrides
docs/decisions.md (#4)
        ↓ overrides
CLAUDE.md (#5)
        ↓ overrides
docs/prd/*.md (#6)
```

## No Code Changes

No Pydantic models, database schemas, API contracts, or source code entities are affected by this feature.
