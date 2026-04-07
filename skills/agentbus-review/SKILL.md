---
name: agentbus-review
description: Review cross-service plans for consistency. Reads IMPLEMENTATION-REPORT.md files directly and detects missing plans, inconsistent decisions, and conflicting open questions.
version: 2.0.0
triggers: [agentbus review, plan verification, cross-service consistency check]
tools: [Read, Write, Glob]
---

# AgentBus Review

Markdown-first review protocol for cross-service plans. Reads IMPLEMENTATION-REPORT.md files directly—no scripts required.

## When to Use

Use this skill:
- After Wave 3 (Verification) completes
- Before implementation starts
- When adding a new service mid-flight
- To verify consistency after plan updates

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
- `{service}/.agentbus-plans/{feature-slug}-REPORT.md` — implementation reports

### 2. Read All Reports

For each service:
- Check if REPORT.md exists
- Read and parse:
  - Verification status (ready/needs_work/blocked)
  - Blockers
  - Cross-service dependencies
  - Open questions

### 3. Run Consistency Checks

#### Check 1: Report Completeness
- [ ] All services have REPORT.md
- [ ] All reports have status field
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

| Service | Status | Blockers | Open Questions |
|---------|--------|----------|----------------|
| svc1 | ✅ ready | None | 0 |
| svc2 | ⚠️ needs_work | Cache invalidation | 1 |
| svc3 | ❌ blocked | Missing migration | 0 |

## Consistency Checks

### Dependency Mirroring
- [x] svc1 → svc2: Both acknowledge
- [ ] svc2 → svc3: svc3 doesn't mention (⚠️ warning)

### API Contracts
- [x] Breaking change in svc1: Documented and acknowledged by svc2

### Deploy Order
- [x] Order is coherent: svc1 → svc2 → svc3

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
2. Read REPORTs from both services
3. Check consistency:
   - tools-service: ready
   - bot-service: ready
   - Dependencies: tools-service says bot-service consumes API
   - Check: bot-service acknowledges consumption ✓
   - API contract: Breaking change documented both sides ✓
4. Write REVIEW.md
5. Report: "✅ All clear. Both services ready. No blocking issues."

---

User: /agentbus-review --feature-slug "002-kafka-migration"

You:
1. Read reports
2. Find inconsistency:
   - payments-service: "notifications-service will consume events"
   - notifications-service: No mention of events (only REST API)
3. Write REVIEW.md with warning
4. Report: "⚠️ needs-attention. Dependency mirroring issue between payments and notifications."
```

## Error Handling

**If status.json doesn't exist**:
- Report: "No plan found. Run orchestrator first."

**If REPORT.md missing for a service**:
- Mark as error
- Recommend: "Re-run Wave 3 for {service}"

**If REPORT.md is empty/malformed**:
- Mark as error
- Recommend: "Check Wave 3 output for {service}"

## Anti-Patterns

❌ **Don't**: Use Python scripts to parse markdown
❌ **Don't**: Assume all services have REPORTs
❌ **Don't**: Report "ok" if any service is blocked
✅ **Do**: Read markdown files directly
✅ **Do**: Check cross-references between services
✅ **Do**: Write findings to REVIEW.md for audit trail
