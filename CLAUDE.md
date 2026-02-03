## Governing Documents (Authoritative Order)

1. docs/BLUEPRINT.md — system blueprint and operating model
2. docs/architecture.md — structural and module-level design
3. docs/decisions.md — recorded design decisions (ADR-style)
4. docs/prd/*.md — scoped work specifications

Claude MUST:
- Read docs/BLUEPRINT.md before starting any PRD or implementation
- Treat the Blueprint as binding unless explicitly revised
- Propose changes to the Blueprint only via docs/decisions.md or an approved PRD
- Never bypass or reinterpret Blueprint constraints
