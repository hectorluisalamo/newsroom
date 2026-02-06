# Quickstart: Documentation Reorganization

**Date**: 2026-02-05
**Feature**: 001-docs-reorganization

## Overview

This is a documentation-only feature. No development environment setup, dependencies, or build steps are required beyond the standard repository tooling.

## Prerequisites

- Git (for `git rm` of deprecated files)
- Text editor (for markdown editing)
- Access to run `bash scripts/verify.sh` to confirm no regressions

## Execution

Follow the execution order defined in [plan.md](plan.md):

1. Update `docs/architecture.md` — absorb summary-level BLUEPRINT content
2. Rewrite `README.md` — concise project overview
3. Rewrite `CLAUDE.md` — operational rules + authority hierarchy
4. Update `.specify/memory/constitution.md` — fix governance sections
5. `git rm docs/BLUEPRINT.md`
6. `git rm docs/AGENTIC_DEV_PLAYBOOK.md`
7. Cross-reference validation
8. Run `bash scripts/verify.sh`

## Validation

After all changes:
- [ ] `README.md` is readable in under 5 minutes
- [ ] `CLAUDE.md` contains no architectural narrative
- [ ] `docs/architecture.md` covers system design at conceptual level
- [ ] No references to `BLUEPRINT.md` or `AGENTIC_DEV_PLAYBOOK.md` remain
- [ ] Authority hierarchy is consistent between `CLAUDE.md` and `constitution.md`
- [ ] `bash scripts/verify.sh` passes
