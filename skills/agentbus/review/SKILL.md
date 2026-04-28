---
name: agentbus review
description: Review cross-service plans for consistency. Reads PLAN.md, CHANGES.md, and QA reports directly and detects missing plans, inconsistent decisions, and conflicting open questions.
version: 3.0.0
triggers: [agentbus review, plan verification, cross-service consistency check]
tools: [Read, Write, Glob]
tags: [agentbus, review, consistency, verification, cross-service]
---

# AgentBus Review

Markdown-first review protocol for cross-service plans. Reads artifacts directly — no scripts required.

**Parent Skill**: `agentbus` — This is a specialized subskill for post-planning verification.

## When to Use

Use this skill:
- After Wave 2.6 (Plan Alignment) completes
- After Wave 3 (Implementation) completes
- Before implementation starts
- When adding a new service mid-flight
- To verify consistency after plan updates

## Limitations

- **Read-only artifacts**: Do not modify REPORT.md or PLAN.md. Only read and report inconsistencies.
- **No automatic correction**: Identify problems but do not fix them. Recommend re-running waves.
- **Dependency on prior waves**: Requires that PLAN.md and QA reports exist. If they don't exist, recommend re-executing the prior wave.
- **No code execution**: Do not run tests or automatic verifications. Review is documentation-based.
- **No implementation quality check**: Only verifies plan consistency, not the quality of proposed implementation.

## Invocation

```
/agentbus-review --feature-slug "001-feature-slug"
```

Or for specific services:

```
/agentbus-review --feature-slug "001-feature-slug" --services payments notifications
```

## Protocol

### 1. Locate Artifacts

Read from orchestrator workspace:
- `agentbus-orchestrator/{feature-slug}/status.json` — to find which services participate
- `{service}/.agentbus-plans/{feature-slug}/PLAN.md` — implementation plans
- `{service}/.agentbus-plans/{feature-slug}/QA-REPORT.md` — Wave 2.5 QA reports

### 2. Read All Reports

For each service:
- Check if PLAN.md exists
- Check if QA-REPORT.md exists
- Read and parse:
  - Verification status (ready/needs_work/blocked)
  - Blockers
  - Cross-service dependencies
  - Open questions

### 3. Run Consistency Checks

#### Check 1: Report Completeness
- [ ] All services have PLAN.md
- [ ] All services have QA-REPORT.md (Wave 2.5)
- [ ] No empty reports

#### Check 2: Status Consistency
- [ ] All reports are "ready" (warn if any "needs_work")
- [ ] No reports are "blocked" (error)

#### Check 3: Dependency Mirroring
For each cross-service dependency mentioned:
- [ ] If Service A says "depends on Service B", Service B should mention interaction with A
- [ ] If Service A says "required by Service B", Service B should confirm

#### Check 4: API Contract Consistency
For API changes:
- [ ] Producer service documents breaking change
- [ ] Consumer service acknowledges breaking change
- [ ] Migration path documented on both sides

#### Check 5: Deploy Order Coherence
- [ ] No circular dependencies (A before B, B before A)
- [ ] Order is logically consistent
- [ ] Database migrations come before code changes

#### Check 6: Question Ownership
- [ ] Every open question has an owner
- [ ] Every open question has blocking/non-blocking status
- [ ] No duplicate questions across services

#### Check 7: QA Concerns Resolution (Wave 2.5)
- [ ] High-severity concerns from QA-REPORT.md are addressed in PLAN.md
- [ ] No unresolved gaps that should block implementation
- [ ] User input requested where appropriate

### 4. Write Review Report

Create `agentbus-orchestrator/{feature-slug}/REVIEW.md`:

```markdown
# Cross-Service Review: {feature-slug}

Review Date: YYYY-MM-DD

## Summary
- Status: ok|needs-attention|blocked
- Services reviewed: N
- Issues found: N critical, N warnings

## Service Status

| Service | Plan Status | QA Status | Blockers | Open Questions |
|---------|-------------|-----------|----------|----------------|
| svc1 | ✅ ready | ✅ clear | None | 0 |
| svc2 | ⚠️ needs_work | ⚠️ concerns | Cache invalidation | 1 |
| svc3 | ❌ blocked | ❌ gaps | Missing migration | 0 |

## Consistency Checks

### Dependency Mirroring
- [x] svc1 → svc2: Both acknowledge
- [ ] svc2 → svc3: svc3 doesn't mention (⚠️ warning)

### API Contracts
- [x] Breaking change in svc1: Documented and acknowledged by svc2

### Deploy Order
- [x] Order is coherent: svc1 → svc2 → svc3

### QA Concerns (Wave 2.5)
- [ ] svc2: High-severity concern about race condition not addressed in PLAN.md
- [x] svc1: All concerns resolved or accepted

## Critical Issues
1. **svc3 blocked**: Missing database migration plan
   - Recommended action: Re-run Wave 2 for svc3

## Warnings
1. **svc2 needs clarification**: Cache invalidation approach unclear
   - Recommended action: Add note to svc2 plan

## Recommended Next Steps
1. Re-run Wave 2 for: svc3
2. Update svc2 plan with cache strategy
3. Re-run review after fixes
```

### 5. Output to User

Present concise summary:
- Overall status (emoji + text)
- Number of issues by severity
- List of services needing attention
- Recommended next command(s)

## Example Workflow

```
User: /agentbus-review --feature-slug "001-remove-field"

You:
1. Read status.json → finds services: [tools-service, bot-service]
2. Read PLAN.md and QA-REPORT.md from both services
3. Check consistency:
   - tools-service: ready, QA clear
   - bot-service: ready, QA clear
   - Dependencies: tools-service says bot-service consumes API
   - Check: bot-service acknowledges consumption ✓
   - API contract: Breaking change documented both sides ✓
4. Write REVIEW.md
5. Report: "✅ All clear. Both services ready. No blocking issues."
```

---

User: /agentbus-review --feature-slug "002-kafka-migration"

You:
1. Read reports
2. Find inconsistency:
   - payments-service: "notifications-service will consume events"
   - notifications-service: No mention of events (only REST API)
3. Find QA concern:
   - notifications-service QA-REPORT: "Unclear how to handle event deserialization failures"
   - Not addressed in PLAN.md
4. Write REVIEW.md with warning
5. Report: "⚠️ needs-attention. Dependency mirroring issue between payments and notifications. QA concern unresolved in notifications."
```

## Error Handling

**If status.json doesn't exist**:
- Report: "No plan found. Run orchestrator first."

**If PLAN.md missing for a service**:
- Mark as error
- Recommend: "Re-run Wave 2 for {service}"

**If QA-REPORT.md missing for a service**:
- Mark as warning
- Recommend: "Re-run Wave 2.5 for {service}"

**If PLAN.md is empty/malformed**:
- Mark as error
- Recommend: "Check Wave 2 output for {service}"

## Anti-Patterns

❌ **Don't**: Use Python scripts to parse markdown
❌ **Don't**: Assume all services have reports
❌ **Don't**: Report "ok" if any service is blocked
❌ **Don't**: Modify the plans you're reviewing
✅ **Do**: Read markdown files directly
✅ **Do**: Check cross-references between services
✅ **Do**: Write findings to REVIEW.md for audit trail
