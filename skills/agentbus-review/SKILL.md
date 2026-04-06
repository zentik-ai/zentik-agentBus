---
name: agentbus-review
description: Review existing cross-service plans for a feature slug and detect missing plans, inconsistent cross-service decisions, and potential conflicting open questions before implementation starts.
compatibility: Requires uv and local filesystem read access to registered repositories.
metadata:
  invocation: manual-only
---

# agentbus-review

Use this skill after plans exist and before implementation starts.

## Invocation

Review all registered services:

`/agentbus-review --feature-slug "<feature-slug>"`

Review selected services:

`/agentbus-review --feature-slug "<feature-slug>" --services <service1> <service2> ...`

## Protocol

1. Resolve `SCRIPTS_DIR=<agentbus-skills-root>/scripts`.
2. Run:
   - `uv run <SCRIPTS_DIR>/review_plans.py --feature-slug "<slug>"` or
   - `uv run <SCRIPTS_DIR>/review_plans.py --feature-slug "<slug>" --services ...`
3. Read output and summarize:
   - issues (must-fix)
   - warnings (should-review)
   - services missing plans
4. Propose concrete fixes:
   - run orchestrator for missing services
   - align `Decisions from other services`
   - reconcile contradictory open questions

## Output style

- Start with status (`ok` or `needs-attention`)
- Then a compact checklist:
  - [ ] missing plans
  - [ ] inconsistent decisions
  - [ ] question conflicts
- End with recommended next command(s)
