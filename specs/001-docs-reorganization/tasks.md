# Tasks: Documentation Reorganization

**Input**: Design documents from `/specs/001-docs-reorganization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md

**Tests**: Not applicable — documentation-only feature with no testable code. `scripts/verify.sh` run as final validation to confirm no regressions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- All paths are relative to repository root
- Documentation files: `README.md`, `CLAUDE.md`, `docs/`, `.specify/memory/`

---

## Phase 1: Setup

**Purpose**: No setup required — documentation-only feature. All tools (Git, text editor) are already available.

*(No tasks in this phase)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update `docs/architecture.md` to absorb summary-level content from BLUEPRINT.md. This MUST complete before US1 (README links to architecture.md) and US2 (CLAUDE.md references architecture.md in the authority hierarchy). This phase also directly satisfies US3 acceptance scenarios.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Add "Data Model Overview" section to docs/architecture.md — extract conceptual descriptions of all 8 Pydantic models (FeedItem, BriefCluster, BriefPack, Pitch, PitchSet, Draft, QAFinding, QAReport) from docs/BLUEPRINT.md Phase 1. Describe each model's purpose and key constraints (e.g., "UTC-aware datetimes", "min 3 source URLs", "exactly 3 pitches") at summary level. Do NOT reproduce field-level definitions — code is source of truth. Insert after the "Core Modules" section in docs/architecture.md.
- [x] T002 Add "Resolved Design Decisions" section to docs/architecture.md — extract the 10 design decisions from docs/BLUEPRINT.md as a brief numbered list with one-line summaries. Add pointer: "See docs/decisions.md for full ADR records." Insert after the new "Data Model Overview" section.
- [x] T003 Add "Dependencies" section to docs/architecture.md — extract runtime and dev dependency lists from docs/BLUEPRINT.md. List names only (no version pins) with one-line purpose for each. Note: "pyproject.toml is the source of truth for versions." Insert before the "Operational Notes" section at the end of docs/architecture.md.

**Checkpoint**: docs/architecture.md is the comprehensive system design authority, containing all critical content that needs to survive BLUEPRINT.md removal. US3 acceptance scenarios are satisfied.

---

## Phase 3: User Story 1 - New Contributor Onboarding (Priority: P1) 🎯 MVP

**Goal**: Create a concise, standard README.md that gives new contributors a clear understanding of the project, quick start instructions, and navigation to detailed documentation.

**Independent Test**: Read README.md and verify it answers "What does Newsroom do?", "How do I run it?", and "Where do I find more details?" in under 5 minutes.

### Implementation for User Story 1

- [x] T004 [US1] Rewrite README.md as a concise project overview (~100 lines). Include sections per plan.md Content Mapping: project title + one-liner, operating model summary (2-3 sentences from BLUEPRINT overview), quick start (uv sync, init_config.sh, --help), configuration (open-core model, env vars), project structure (directory tree), stack (one-line tech list), development (verify.sh, pytest), and documentation pointers (links to docs/architecture.md, docs/decisions.md). Exclude: data model details, module signatures, config YAML examples, implementation phases.

**Checkpoint**: README.md is a proper, concise project README. New contributors can understand the project and get started within 5 minutes.

---

## Phase 4: User Story 2 - AI Agent Configuration (Priority: P2)

**Goal**: Streamline CLAUDE.md to operational rules only and establish constitution.md as supreme authority in a clear hierarchy.

**Independent Test**: Read CLAUDE.md and verify it contains only: status, authority hierarchy, project conventions, file header rules, comment rules, config boundary, and verification commands. No architectural narrative. Authority hierarchy is consistent with constitution.md.

### Implementation for User Story 2

- [x] T005 [P] [US2] Rewrite CLAUDE.md as streamlined operational rules (~50 lines). Replace "Governing Documents (Authoritative Order)" with "Authority Hierarchy (In Case of Conflict)" using the 6-level hierarchy from FR-006. Remove all Blueprint references and "Claude MUST" rules about reading Blueprint. Remove the "Active Technologies" and "Recent Changes" sections added by the agent context script. Retain: status line, project conventions, file header rule, comment rules, config boundary, verification commands. No architectural narrative.
- [x] T006 [P] [US2] Update .specify/memory/constitution.md governance sections. In "Governance" intro paragraph: remove references to Blueprint and playbook origins. In "Authority hierarchy": replace items 2-5 with constitution.md (#2), architecture.md (#3), decisions.md (#4), CLAUDE.md (#5). In "Development Workflow": replace "The Blueprint (docs/BLUEPRINT.md) is binding unless explicitly revised via docs/decisions.md" with "docs/architecture.md is the binding system design authority; changes require an ADR in docs/decisions.md". Bump version to 1.1.0 and update Last Amended date to 2026-02-05.

**Checkpoint**: CLAUDE.md and constitution.md both define a consistent authority hierarchy. Constitution.md is clearly the supreme law below CI output.

---

## Phase 5: Cleanup & Validation

**Purpose**: Remove deprecated files, validate cross-references, confirm no regressions.

- [x] T007 [US2] Record ADR in docs/decisions.md for the documentation reorganization and authority hierarchy restructuring. Add "ADR-011: Documentation reorganization and authority hierarchy" with Status: Resolved, Context (BLUEPRINT.md and playbook created duplication; authority hierarchy was outdated), Decision (consolidate into README/architecture/CLAUDE with constitution as supreme law), and Consequences (BLUEPRINT.md and AGENTIC_DEV_PLAYBOOK.md removed; constitution promoted to #2 authority). Required by constitution amendment procedure.
- [x] T008 [P] Delete docs/BLUEPRINT.md via git rm docs/BLUEPRINT.md
- [x] T009 [P] Delete docs/AGENTIC_DEV_PLAYBOOK.md via git rm docs/AGENTIC_DEV_PLAYBOOK.md
- [x] T010 Cross-reference validation — scan all modified files (README.md, CLAUDE.md, docs/architecture.md, .specify/memory/constitution.md, docs/decisions.md) for any remaining references to "BLUEPRINT.md" or "AGENTIC_DEV_PLAYBOOK.md". Verify no broken links. Verify no content duplication between README.md, CLAUDE.md, and docs/architecture.md. Verify docs/agent-notes.md is untouched.
- [x] T011 Run bash scripts/verify.sh to confirm existing tests still pass (no source code was changed, so all tests should remain green).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Empty — no setup required
- **Foundational (Phase 2)**: T001 → T002 → T003 (sequential edits to same file: docs/architecture.md)
- **User Stories (Phase 3-4)**: All depend on Phase 2 completion
  - US1 (T004) and US2 (T005, T006) can proceed in parallel (different files)
- **Cleanup (Phase 5)**: Depends on all user stories being complete
  - T007 (ADR) should complete before deletions (records rationale while files still exist)
  - T008 and T009 can run in parallel (different files)
  - T010 depends on T008 and T009 (must validate after deletions)
  - T011 depends on T010 (final verification)

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 completion (README links to architecture.md). No dependencies on US2.
- **User Story 2 (P2)**: Depends on Phase 2 completion (CLAUDE.md references architecture.md). No dependencies on US1.
- **User Story 3 (P3)**: Satisfied by Phase 2 (Foundational). architecture.md update IS the US3 deliverable.

### Within Each Phase

- Phase 2: Sequential (T001 → T002 → T003) — all edit docs/architecture.md
- Phase 3: Single task (T004)
- Phase 4: T005 and T006 can run in parallel (different files)
- Phase 5: T007 (ADR), then T008 ∥ T009 (deletions), then T010, then T011

### Parallel Opportunities

- **After Phase 2 completes**: T004 (README), T005 (CLAUDE.md), and T006 (constitution.md) can ALL run in parallel — three different files with no cross-dependencies
- **Phase 5 deletions**: T008 and T009 can run in parallel after T007 (ADR) completes

---

## Parallel Example: After Phase 2

```bash
# Launch US1 and US2 tasks together (all different files):
Task: "Rewrite README.md" (T004)
Task: "Rewrite CLAUDE.md" (T005)
Task: "Update constitution.md" (T006)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T003) — architecture.md is the system design authority
2. Complete Phase 3: User Story 1 (T004) — README.md is a proper project overview
3. **STOP and VALIDATE**: Read README.md, verify it's concise and answers key questions
4. This is a deliverable increment: the public-facing README is professional

### Incremental Delivery

1. Complete Foundational → architecture.md is authoritative (US3 satisfied)
2. Add US1 (T004) → README.md is a proper project overview
3. Add US2 (T005-T006) → CLAUDE.md is streamlined, authority hierarchy established
4. Cleanup (T007-T010) → deprecated files removed, all references validated
5. Each increment adds value without breaking previous work

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US3 (architecture.md) is delivered as Phase 2 Foundational work because US1 and US2 both depend on it
- No test tasks included — documentation-only feature with no testable code
- Commit after each phase completion for clean git history
- Stop at any checkpoint to validate story independently
