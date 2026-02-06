# Feature Specification: Documentation Reorganization

**Feature Branch**: `001-docs-reorganization`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "Let's clean up and reorganize the documentation in this repo. I specifically want to make sure that: 1) CLAUDE.md is limited to laying out repo-specific operational commands for Claude; 2) the archictecture.md functions as a standard archictecture.md (laying out how the system works and how it is structured, etc.); and 3) that the README.md and BLUEPRINT.md are combined into a new README.md that functions as a proper README.md (giving an overview of the app and its codebase, etc.). I think we can get rid of AGENTIC_DEV_PLAYBOOK.md, as it merely rehashes the global AGENTIC_DEV_PLAYBOOK.md. Primarily I want to make sure we have the proper documention set up to carry out this project to completetion quickly, accurate, and with no confusion as to the end product"

**Clarification**: BLUEPRINT.md should be discarded entirely (not merged into README). Extract any critical information needed for architecture.md or decisions.md, then remove BLUEPRINT.md. README.md should be a proper, concise project README.

## Clarifications

### Session 2026-02-05

- Q: How much BLUEPRINT.md detail should architecture.md absorb? → A: Summary-level only; code is the source of truth for model definitions, config schemas, and function signatures.
- Q: What happens to docs/AGENTIC_DEV_PLAYBOOK.md? → A: Remove the repo-local copy. The global playbook in ~/.claude/ remains untouched (out of scope).
- Q: What happens to docs/agent-notes.md? → A: Keep it. Agent-notes.md is preserved as the post-implementation summary file where Claude records what was done and recommends next development steps.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Contributor Onboarding (Priority: P1)

A developer discovering the Newsroom repository for the first time visits the README.md to understand what the project does, how to get started, and where to find detailed documentation.

**Why this priority**: The README.md is the entry point for all external users and contributors. A proper, concise README following standard conventions makes the project approachable and professional. This directly affects the project's portfolio presentation and usability.

**Independent Test**: Can be fully tested by reading the new README.md and verifying it answers: "What does Newsroom do?", "How do I run it?", and "Where do I find more details?" in a concise, scannable format.

**Acceptance Scenarios**:

1. **Given** a developer visits the repository, **When** they read README.md, **Then** they understand the project's purpose (opinion column generator for Substack) and can run a quick start command within 5 minutes
2. **Given** a developer wants to understand the tech stack, **When** they scan README.md, **Then** they see a clear list of technologies (Python 3.12+, uv, Ruff, pytest, Pydantic, scikit-learn, Anthropic SDK)
3. **Given** a developer wants deeper architectural detail, **When** they read README.md, **Then** they find clear navigation pointers to docs/architecture.md and docs/decisions.md
4. **Given** a developer wants to contribute, **When** they read README.md, **Then** they know how to run verification scripts and where documentation standards are defined

---

### User Story 2 - AI Agent Configuration (Priority: P2)

Claude Code reads CLAUDE.md to understand repo-specific rules, verification commands, config boundaries, and operational constraints before beginning work.

**Why this priority**: Clear operational boundaries prevent Claude from making incorrect assumptions about the repo structure, config management, or verification requirements. This reduces errors and misaligned implementations.

**Independent Test**: Can be fully tested by examining CLAUDE.md and verifying it contains only: status (public repo), governing docs order, project conventions, file header rules, comment rules, config boundary rules, and verification commands. No architectural narrative or system overview should appear.

**Acceptance Scenarios**:

1. **Given** Claude starts work on a PRD, **When** it reads CLAUDE.md, **Then** it understands the authority hierarchy with constitution.md as supreme law, and knows docs/architecture.md is authoritative for system design
2. **Given** Claude encounters conflicting guidance, **When** it consults the authority hierarchy in CLAUDE.md, **Then** it knows constitution.md supersedes architecture.md, which supersedes CLAUDE.md, which supersedes PRDs
3. **Given** Claude needs to verify code, **When** it reads CLAUDE.md, **Then** it knows to run `bash scripts/verify.sh` and optionally `bash scripts/verify_content.sh`
4. **Given** Claude creates a new Python file, **When** it reads CLAUDE.md, **Then** it knows to add a two-line ABOUTME header and follow comment rules
5. **Given** Claude needs architectural context, **When** it reads CLAUDE.md, **Then** it is directed to docs/architecture.md instead of finding duplicated architectural content in CLAUDE.md

---

### User Story 3 - Understanding System Architecture (Priority: P3)

A developer or AI agent needs to understand how the Newsroom pipeline works, what modules exist, how data flows through the system, and the design constraints from the former BLUEPRINT.md.

**Why this priority**: Accurate implementation requires understanding the system's structure and design boundaries. The architecture doc is the authoritative source for system design and prevents reimplementation mistakes.

**Independent Test**: Can be fully tested by reading docs/architecture.md and verifying it contains summary-level architectural information (operating model, design goals, module responsibilities, data flow, CLI surface, testing strategy, provider abstraction) without reproducing code-level detail from the former BLUEPRINT.md.

**Acceptance Scenarios**:

1. **Given** a developer wants to modify the clustering logic, **When** they read docs/architecture.md, **Then** they understand clustering is behind a protocol in `cluster/`, TF-IDF is the V0 implementation, and config lives in cluster.yaml
2. **Given** an agent needs to add a new LLM provider, **When** they read docs/architecture.md, **Then** they understand the provider abstraction in `draft/provider.py` and how to implement the interface
3. **Given** a developer wants to understand QA checks, **When** they read docs/architecture.md, **Then** they know QA checks are pure, deterministic, no-network functions in `qa/checks.py`
4. **Given** a developer wants to understand the data models, **When** they read docs/architecture.md, **Then** they find conceptual descriptions of all 8 Pydantic models (FeedItem, BriefCluster, BriefPack, Pitch, PitchSet, Draft, QAFinding, QAReport) and their purpose, with the code as the source of truth for field-level detail

---

### Edge Cases

- What happens when CLAUDE.md references docs/BLUEPRINT.md but BLUEPRINT.md has been removed?
- How does README.md stay concise while still providing enough context for portfolio viewers to understand the project's value?
- What if critical architectural information from BLUEPRINT.md is lost during extraction? (Mitigated: code is the source of truth for implementation detail; only summary-level content needs extraction)
- What if architecture.md accidentally duplicates content from the new README.md?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a concise, standard README.md that includes: project overview, purpose statement, quick start instructions, configuration basics, project structure overview, tech stack list, and navigation pointers to detailed documentation
- **FR-002**: System MUST extract summary-level architectural content from docs/BLUEPRINT.md and incorporate it into docs/architecture.md, including: conceptual data model descriptions, module responsibilities, data flow descriptions, testing strategy, provider abstractions, and design constraints. Code is the source of truth for model field definitions, config schemas, and function signatures — architecture.md summarizes these at a conceptual level, not at code-level detail
- **FR-003**: System MUST remove docs/BLUEPRINT.md after extracting critical content to appropriate documentation files
- **FR-004**: System MUST update CLAUDE.md to remove all architectural narrative, operating model descriptions, and system overviews, retaining only: repo status, governing documents order, project conventions, file header rules, comment rules, config boundary, and verification commands
- **FR-005**: System MUST remove docs/AGENTIC_DEV_PLAYBOOK.md since it duplicates the global playbook (the global playbook in ~/.claude/ is out of scope and remains untouched)
- **FR-006**: System MUST update CLAUDE.md's "Governing Documents" section to establish clear authority hierarchy with constitution.md as supreme law:
  1. CI / verification output (objective truth)
  2. `.specify/memory/constitution.md` (supreme constitutional authority)
  3. `docs/architecture.md` (system design authority)
  4. `docs/decisions.md` (ADR-style design decisions)
  5. `CLAUDE.md` (operational rules and conventions)
  6. `docs/prd/*.md` (feature specifications)
- **FR-007**: System MUST ensure docs/architecture.md contains summary-level architectural and structural content: operating model, design goals, data flow, core modules, CLI surface, conceptual data model descriptions and invariants, testing strategy, provider abstraction, safety constraints, and extensibility patterns. Implementation-level detail (field types, config YAML examples, function signatures) belongs in the code
- **FR-007a**: System MUST preserve docs/agent-notes.md as the post-implementation summary file where Claude records what was done and recommends next development steps
- **FR-008**: README.md MUST remain concise (target: readable in under 5 minutes) while providing clear navigation pointers to docs/architecture.md, docs/decisions.md, and docs/prd/ for readers seeking deeper detail
- **FR-009**: System MUST update all references to docs/BLUEPRINT.md in CLAUDE.md to point to docs/architecture.md or README.md as appropriate
- **FR-010**: System MUST update the "Authority hierarchy" section in `.specify/memory/constitution.md` to remove references to deprecated files (docs/BLUEPRINT.md, AGENTIC_DEV_PLAYBOOK.md) and establish constitution.md as supreme authority below CI/verification output
- **FR-011**: System MUST update the "Development Workflow" section in `.specify/memory/constitution.md` to remove references to BLUEPRINT.md and establish docs/architecture.md as the binding architectural authority

### Key Entities

- **Documentation File**: Represents a markdown file in the repo (README.md, CLAUDE.md, docs/architecture.md, .specify/memory/constitution.md) with specific roles, audiences, and content boundaries
- **Deprecated Documentation File**: Files to be removed (docs/BLUEPRINT.md, docs/AGENTIC_DEV_PLAYBOOK.md) after extracting critical content
- **Authority Hierarchy**: Ordered list of governing documents by precedence:
  1. CI / verification output (objective truth)
  2. `.specify/memory/constitution.md` (supreme constitutional authority - core principles, technical constraints, non-negotiable rules)
  3. `docs/architecture.md` (system design authority - how the system is structured)
  4. `docs/decisions.md` (ADR-style design decisions - why choices were made)
  5. `CLAUDE.md` (operational rules and conventions - how Claude should work)
  6. `docs/prd/*.md` (feature specifications - what to build)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new contributor can read README.md (target: under 5 minutes) and understand the project's purpose, run a quick start command, and locate detailed documentation
- **SC-002**: Claude Code can read CLAUDE.md and identify all repo-specific operational constraints (config boundary, verification commands, file header rules) without encountering architectural narrative
- **SC-003**: A developer can read docs/architecture.md and understand the full system architecture at a conceptual level (modules, data flow, data model purposes, testing strategy) without needing the former BLUEPRINT.md; code is the source of truth for implementation detail
- **SC-004**: Documentation contains no duplicated content between README.md, CLAUDE.md, and docs/architecture.md (each file has a single, clear responsibility)
- **SC-005**: docs/BLUEPRINT.md and docs/AGENTIC_DEV_PLAYBOOK.md no longer exist in the repository
- **SC-006**: All references to docs/BLUEPRINT.md in CLAUDE.md and constitution.md are updated to point to docs/architecture.md or README.md as appropriate
- **SC-007**: Authority hierarchy is clearly defined in both CLAUDE.md and constitution.md with constitution.md as supreme law (below CI/verification output only)
- **SC-008**: Claude Code can read CLAUDE.md and understand that constitution.md supersedes architecture.md, which supersedes CLAUDE.md itself
