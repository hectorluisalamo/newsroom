# Implementation Plan: Documentation Reorganization

**Branch**: `001-docs-reorganization` | **Date**: 2026-02-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-docs-reorganization/spec.md`

## Summary

Reorganize the Newsroom repository's documentation to eliminate duplication, establish a clear authority hierarchy with `constitution.md` as supreme law, and give each documentation file a single, distinct responsibility. The work is purely documentation — no source code changes.

**Approach**: Extract summary-level content from BLUEPRINT.md into architecture.md, rewrite README.md as a concise project overview, streamline CLAUDE.md to operational rules only, update constitution.md's governance sections, then delete deprecated files.

## Technical Context

**Language/Version**: N/A (documentation-only feature)
**Primary Dependencies**: N/A
**Storage**: N/A
**Testing**: Manual review — markdown files have no automated test coverage. `scripts/verify.sh` must still pass (no source changes, so existing tests remain green).
**Target Platform**: GitHub repository (markdown rendered by GitHub)
**Project Type**: Documentation reorganization
**Performance Goals**: N/A
**Constraints**: All content in public repo must be portfolio-safe. No secrets, no config files committed.
**Scale/Scope**: 6 files affected (4 modified, 2 deleted)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Determinism First | N/A | No pipeline code touched |
| II. Test-First Discipline | N/A | Documentation-only change; no testable code introduced. `verify.sh` must still pass to confirm no regressions. |
| III. Human Editorial Authority | N/A | No pipeline behavior changed |
| IV. Truth & Attribution | N/A | No generated content |
| V. Open-Core Boundary | PASS | No config/ or .env touched. All changes are to committed, public documentation. |
| VI. Simplicity & Minimal Moving Parts | PASS | Reducing doc count from 6 to 4. Eliminating duplication. Simplifying authority hierarchy. |

**Gate result**: PASS — no violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-docs-reorganization/
├── plan.md              # This file
├── research.md          # Phase 0 output (content mapping)
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Repository Files Affected

```text
README.md                              # REWRITE — concise project overview
CLAUDE.md                              # REWRITE — operational rules + authority hierarchy
docs/architecture.md                   # UPDATE — absorb summary-level BLUEPRINT content
docs/BLUEPRINT.md                      # DELETE (git rm)
docs/AGENTIC_DEV_PLAYBOOK.md           # DELETE (git rm)
.specify/memory/constitution.md        # UPDATE — fix authority hierarchy + dev workflow
docs/agent-notes.md                    # PRESERVE (no changes)
docs/decisions.md                      # PRESERVE (no changes)
docs/prd/                              # PRESERVE (no changes)
```

**Structure Decision**: No source code directories affected. All changes are to markdown documentation files at the repository root and in `docs/`.

## Content Mapping

This section defines exactly what content goes where, preventing duplication and information loss.

### README.md (Target: ~100 lines, <5 min read)

| Section | Source | Content |
|---------|--------|---------|
| Project title + one-liner | Current README L1-3 | "Newsroom — A Python CLI that produces Substack-ready opinion columns from beat-specific research briefs and writer voices." |
| Operating Model summary | BLUEPRINT "Operating Model" | 2-3 sentence summary of the two-step workflow (pitch → draft) |
| Quick Start | Current README "Quick Start" | `uv sync`, `init_config.sh`, `python -m newsroom --help` |
| Configuration | Current README "Configuration" | Open-core model, env vars, config.example/ |
| Project Structure | Current README "Project Structure" | Directory tree (keep concise) |
| Stack | Current README "Stack" | One-line tech list |
| Development | Current README "Development" | verify.sh, pytest commands |
| Documentation Pointers | New | Links to architecture.md, decisions.md, constitution.md |

**Excluded from README**: Data model details, module signatures, config YAML examples, implementation phases, testing strategy details — all belong in architecture.md or code.

### CLAUDE.md (Target: ~50 lines)

| Section | Source | Content |
|---------|--------|---------|
| Status line | Current CLAUDE.md L1 | "STATUS: PUBLIC REPOSITORY" |
| Authority Hierarchy | New (replaces "Governing Documents") | Numbered list: CI → constitution.md → architecture.md → decisions.md → CLAUDE.md → PRDs |
| Project Conventions | Current CLAUDE.md "Project Conventions" | Package, uv, Ruff, pytest/NO NETWORK |
| File Header Rule | Current CLAUDE.md "File Header Rule" | ABOUTME two-line comment |
| Comment Rules | Current CLAUDE.md "Comment Rules" | No TODO/FIXME/HACK, evergreen only |
| Config Boundary | Current CLAUDE.md "Config Boundary" | Never commit config/.env, only config.example/ |
| Verification | Current CLAUDE.md "Verification" | verify.sh + verify_content.sh commands |

**Excluded from CLAUDE.md**: All architectural narrative, operating model descriptions, system overviews, Blueprint references.

### docs/architecture.md (Target: ~350 lines)

| Section | Source | Content |
|---------|--------|---------|
| Overview + Operating Model | Current architecture.md L1-29 | Keep as-is (already well-written) |
| Design Goals | Current architecture.md L33-41 | Keep as-is |
| Non-Goals | Current architecture.md L45-51 | Keep as-is |
| Repository Boundaries | Current architecture.md L55-68 | Keep as-is |
| High-Level Data Flow | Current architecture.md L72-103 | Keep as-is |
| Core Modules | Current architecture.md L107-157 | Keep as-is |
| Data Model Overview | BLUEPRINT "Phase 1" (summarized) | Conceptual descriptions of FeedItem, BriefCluster, BriefPack, Pitch, PitchSet, Draft, QAFinding, QAReport — purpose and constraints, not field definitions |
| Resolved Design Decisions | BLUEPRINT "Resolved Design Decisions" | Brief list with pointers to decisions.md for full ADRs |
| CLI Surface | Current architecture.md L163-190 | Keep as-is |
| Data Model Invariants | Current architecture.md L194-202 | Keep as-is |
| Testing Strategy | Current architecture.md L206-220 | Keep as-is |
| Verification | Current architecture.md L224-232 | Keep as-is |
| Provider Abstraction | Current architecture.md L236-244 | Keep as-is |
| Safety & Trust Constraints | Current architecture.md L248-258 | Keep as-is |
| Extensibility | Current architecture.md L262-272 | Keep as-is |
| Dependencies | BLUEPRINT "Dependencies" (summarized) | Runtime + dev dependency lists (names only, no version pins — pyproject.toml is source of truth) |

**Excluded from architecture.md**: Full Pydantic model code, config YAML examples, function signatures, implementation phases — these belong in code.

### .specify/memory/constitution.md

| Section | Change |
|---------|--------|
| Governance → Authority hierarchy | Replace items 2-4 with: constitution.md (#2), architecture.md (#3), decisions.md (#4), CLAUDE.md (#5) |
| Governance → intro paragraph | Remove references to Blueprint and playbook |
| Development Workflow | Replace "The Blueprint (docs/BLUEPRINT.md) is binding" with "docs/architecture.md is the binding system design authority" |
| Version | Bump to 1.1.0 (MINOR: expanded governance guidance) |

## Execution Order

Operations ordered to prevent information loss:

1. **Update docs/architecture.md** — Absorb summary-level content from BLUEPRINT.md. Architecture must be complete before Blueprint is removed.
2. **Rewrite README.md** — Create concise project overview. Uses current README + BLUEPRINT overview as source.
3. **Rewrite CLAUDE.md** — Streamline to operational rules only. Establish new authority hierarchy.
4. **Update constitution.md** — Fix authority hierarchy and development workflow. Bump version to 1.1.0.
5. **Delete docs/BLUEPRINT.md** — `git rm` after all content extracted.
6. **Delete docs/AGENTIC_DEV_PLAYBOOK.md** — `git rm`.
7. **Cross-reference validation** — Verify no broken references, no content duplication, no information loss.
8. **Run verify.sh** — Confirm existing tests still pass (no source changes).

## Complexity Tracking

> No constitution violations. Table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
