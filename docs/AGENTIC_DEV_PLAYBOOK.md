# Agentic Dev Playbook (Crash Log Edition)

This playbook defines how work is executed using Claude Code.
It is binding for all agent-assisted development.

Claude writes code.
The system determines correctness.

Scope: Global Default

This playbook defines the default Agentic Development workflow across all repositories unless overridden by a repository-local `CLAUDE.md` or project documentation.

In case of conflict, repository-local rules take precedence.

---

## 1. Project Initialization

New projects MUST follow the Project Bootstrap Protocol:

- `PROJECT_BOOTSTRAP.md`

Claude MUST NOT invent repository structures or workflows outside of that protocol.

---

## 2. Canonical Work Unit: The PRD

All non-trivial work begins with a PRD.

PRDs are short, written specifications that define:
- intent
- constraints
- success conditions

PRDs live in:
- `docs/prd/`

Claude MUST NOT begin implementation without an active PRD unless explicitly authorized.

### Canonical PRD Format (Required)

Every PRD MUST follow this format.

**PRD Template**:

```md
# PRD: <Short, Descriptive Title>

## Goal
One paragraph describing what is being built and why.

## User Stories
- As a user, I can …
- As a user, I can …

## Non-Goals
Explicitly list what is NOT being done.

## Constraints
- Tech stack constraints
- Architectural constraints
- Performance, security, or compatibility constraints
- Explicit prohibitions (e.g., “no new dependencies”)

## Sources & Data
- source list changes (feeds added/removed)
- fixture updates
- caching assumptions
- expected output artifacts

## Acceptance Criteria
- Observable, testable conditions
- Each item must be objectively verifiable

## Definition of Done
- scripts/verify.sh passes
- Tests added or updated
- No unrelated changes
- Documentation updated if behavior changed
- `docs/agent-notes.md` updated with PRD completion note
- Single commit message drafted referencing PRD
```

Claude MUST:
- Follow this structure exactly
- Ask before deviating
- Treat Acceptance Criteria and Definition of Done as authoritative

Claude MUST NOT invent alternative PRD formats or expand the template without explicit approval.

---

## 3. Standard Task Flow

For each PRD:

1. Claude reads the PRD
2. Claude proposes a brief plan
3. Human approves or corrects plan
4. Claude implements in small, test-driven steps
5. Claude runs verification
6. Claude commits changes
   - Never include `Co-Authored-By` trailers in commit messages
7. Claude updates progress notes

No step may be skipped unless explicitly authorized.

---

## 4. Verification Is Mandatory

Verification is defined by:

- `scripts/verify.sh`
- `scripts/verify_content.sh` (or `scripts/verify_outputs.sh`) that runs:
    - `newsroom pitch …` and `newsroom draft …` against a fixture dataset
    - validates JSON schema
    - runs QA checks
    - asserts deterministic output formatting
- CI pipelines

Claude MUST:
- Run verification before marking work complete
- Treat failing verification as blocking

Claude MUST NOT claim success without pristine output.

---

## 5. Progress Tracking (Cross-Session Memory)

Claude MUST use:
- `docs/agent-notes.md`

This file is the agent’s memory between sessions.

Claude MUST update it with:
- What was changed
- Why it was changed
- Known issues
- Next steps: suggest the title and rough scope of the next PRD — but do NOT draft the next PRD

Claude MUST NOT rely on conversational memory.

---

## 6. Ralph Loop Usage

Ralph loops are authorized ONLY for:
- large refactors
- migrations
- multi-file mechanical fixes
- test-failure sweeps

Ralph loops MUST:
- be controlled by an external script
- cap iteration count
- rely on verification, not agent judgment

Claude MUST NOT implement self-directed infinite loops.

---

## 7. Scope Discipline

Claude MUST:
- Work only on the current PRD
- Document unrelated issues instead of fixing them
- Ask permission before expanding scope

---

## 8. Authority Hierarchy

In case of conflict:

1. CI / verification output
    - Editorial QA gates in scripts/qa.sh (or python -m newsroom qa …) are treated as verification output.
2. AGENTIC_DEV_PLAYBOOK.md
3. CLAUDE.md
4. Framework best practices
5. Claude’s judgment

Claude MUST surface conflicts explicitly.

---

## 9. Security & Safety Defaults

Claude operates under:
- sandboxed execution
- least privilege access
- no secret access

### Truth & Attribution

This project has a unique profile risk, reputational and legal, requiring that:
- No new factual claims beyond sources provided in the brief pack.
- Stats/numbers require inline attribution markers.
- No allegations about individuals unless sourced by reputable outlets and phrased cautiously.
- Social content is “signal only” unless independently corroborated.

Any request to bypass safeguards requires explicit human authorization.

--

## 10. Workflow Enforcement (Required)

### Small, Iterative Changes
Claude MUST:
- Work in small, testable increments
- Make the smallest reasonable changes to achieve the desired outcome
- Break work into small, iterable, testable chunks
- Discuss a plan before implementation unless explicitly told otherwise
    - For changes under ~15 lines that are purely mechanical (typo, import fix), the “plan” can be a one-liner.

### Tooling During Implementation
Claude SHOULD:
- Use `tldr` when figuring out syntax for a third-party tool or CLI

### CodeRabbit Review Gate
Claude MUST:
- Run `coderabbit review --plain` after completing code changes for a task
- Review all feedback carefully and address:
  - Bugs
  - Correctness issues
  - Performance concerns
  - Security or privacy risks
- For stylistic or nitpick suggestions:
  - Apply unless there is a clear reason not to
  - If intentionally declined, record the reason in code comments or the commit message
- Re-run `coderabbit review --plain` after changes
- Repeat until no material issues remain
- Treat this review as required before considering a task complete

