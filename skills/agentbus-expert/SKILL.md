---
name: agentbus-expert
description: Refine a pending AgentBus service plan by analyzing the local codebase, resolving plan open questions, and updating the same plan file in place. Use when starting implementation for a cross-service feature.
compatibility: Requires uv and filesystem read/write access in current service repository.
metadata:
  invocation: manual-or-contextual
---

# agentbus-expert

Use this skill inside a single service repository.

## Protocol

0. Resolve the absolute scripts directory from this skill package:
   - `SCRIPTS_DIR=<agentbus-skills-root>/scripts`
1. Check for plans:
   - `uv run <SCRIPTS_DIR>/read_plan.py --list`
   - If none exist, report no plans and continue normal workflow.
2. Read plan:
   - `uv run <SCRIPTS_DIR>/read_plan.py` for latest
   - `uv run <SCRIPTS_DIR>/read_plan.py --plan <NNN>` if user specifies a plan
3. Analyze local impact:
   - affected modules/files
   - API/event/contract changes
   - dependencies on other services
   - risk and effort
4. Resolve open questions when possible.
5. Update the same plan in place:
   - update top-level `**Status:** refined — pending developer review`
   - add or update `## Expert Review` (do not duplicate section)
6. Report:
   - updated plan path
   - key decisions
   - unresolved questions
   - suggested next step

## Expert Review section

```markdown
## Expert Review
**Reviewed by:** <agent or CLI name>
**Date:** <ISO date>
**Status:** refined — pending developer review

### Local impact
<affected files/modules>

### Constraints
<constraints>

### Decisions
<decisions>

### Impact on other services
<contract/event/API implications>

### Resolved questions
- [x] <question> -> <answer>

### Still open
- [ ] <question>

### Implementation steps
1. <step>
2. <step>
```
