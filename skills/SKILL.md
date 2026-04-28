---
name: agentbus
description: Cross-service planning system for LLM coding agents. Orchestrates multi-wave planning across microservices with evidence-based workflow. Updated for .planning/codebase/ output and Plan QA stage.
version: 3.0.0
triggers: [cross-service feature, multi-service planning, service architecture]
tools: [Read, Write, Bash, Task]
tags: [agentbus, orchestration, cross-service, planning]
---

# AgentBus Skills

Cross-service planning system that eliminates the "developer as messenger" problem when planning features that span multiple microservices.

## When to Use

Use AgentBus when you need to:

- **Plan a feature** that touches 2+ services (e.g., "migrate sync calls to async events")
- **Understand** how a feature works across services
- **Verify** cross-service consistency before implementation
- **Refactor** APIs or data models that affect multiple services

**Don't use AgentBus for:**
- Single-service changes → Use `gsd` or `spec-kit` instead
- Simple code exploration → Use `map-codebase` directly

## Core Philosophy: Evidence Over Communication

Instead of passing data through responses, AgentBus writes artifacts at each stage:

```
Wave 1:   Service Mapping          →  .planning/codebase/ (5 docs per service)
Wave 1.5: Design Alignment         →  Validated approach decisions
Wave 2:   Plan Refinement          →  PLAN.md (per service)
Wave 2.5: Plan QA & Concerns       →  QA-REPORT.md (per service) + user input
Wave 2.6: Plan Alignment           →  Cross-service consistency check
Wave 3:   Implementation           →  Modified code + CHANGES.md
Wave 3.5: Contract Validation      →  Deep implementation check (optional)
Wave 4:   Verification             →  TEST-RESULTS.md
Wave 4b:  Adjustments (opt)        →  Minor fixes + clarifications
Wave 5:   Wrap-up (opt)            →  Git commits
```

**Benefits:**
- **Context efficiency**: Orchestrator reads only what it needs
- **Auditability**: Complete history in version-controlled files
- **Resumability**: Failed waves can be retried independently
- **Reusability**: `.planning/codebase/` serves as living service documentation

## Quick Start Commands

### Step 1: Load the Skill (Required)

**First, you must initialize the AgentBus skill** so the LLM understands the system:

```
/agentbus
```

This provides context about the wave model, routing, and conventions.

### Step 2: Local Service Repositories (Required)

**All services to modify must be:**
- Cloned locally in your workspace
- Listed in `~/.agentbus/services.json`

The orchestrator needs local file access — it cannot work with remote repos.

### Step 3: Initialize a New Plan

```
/agentbus orchestrator "remove deprecated field from Tool model in tools and bot"
```

The orchestrator:
1. Detects services from your prompt ("tools" → exitus-agent-tools)
2. Suggests next plan ID (scans existing plans for sequential numbering)
3. Creates:
   - `agentbus-orchestrator/004-feature/status.json`
   - `agentbus-orchestrator/004-feature/SEED-PLAN.md`

### Continue Waves

```
/agentbus orchestrator --continue 004-feature
```

Runs the next wave based on `status.json`.

### Review Cross-Service Consistency

```
/agentbus review --feature-slug "004-feature"
```

## Wave Execution Model

### Wave 1: Service Mapping

**Purpose**: Create/update `.planning/codebase/` documentation in each service

**What happens:**
- Orchestrator spawns parallel subagents (one per service)
- Each subagent maps codebase: stack, architecture, APIs, DB, testing
- Writes 5 documents to `{service}/.planning/codebase/`:
  - STACK.md — Technology stack
  - ARCHITECTURE.md — Patterns and data flow
  - STRUCTURE.md — Directory layout
  - CONVENTIONS.md — Implementation patterns (CRITICAL)
  - CONCERNS.md — Tech debt and risks
- Writes summary JSON to orchestrator workspace

**Output**: `{service}/.planning/codebase/*.md`

### Wave 2a: Plan Refinement

**Purpose**: Create detailed implementation plan per service

**What happens:**
- Subagents read `.planning/codebase/` documents (especially CONVENTIONS.md)
- Read SEED-PLAN.md for context
- Explore relevant code files
- Write PLAN.md with specific changes

**Output**: `{service}/.agentbus-plans/{plan-id}/PLAN.md`

### Wave 2.5: Plan QA & Concerns — NEW

**Purpose**: Surface concerns, gaps, and doubts before implementation

**What happens:**
- Orchestrator spawns specialist agents in `plan_qa` mode
- Each agent reads their PLAN.md and `.planning/codebase/` docs
- Each agent writes QA-REPORT.md with concerns, gaps, and questions
- Orchestrator consolidates and presents to the user for input
- Plans are refined based on user answers

**Output**: `{service}/.agentbus-plans/{plan-id}/QA-REPORT.md`

### Wave 2b: Context Queries (Optional)

**Purpose**: Get information from adjacent services without mapping them

**What happens:**
- Service agent detects need for external info (e.g., "what does users-api return?")
- Reports `status: "needs_context"`
- Orchestrator spawns query-only agents in target services
- Re-runs service agent with answers
- Completes PLAN.md

**Output**: Answers integrated into PLAN.md

### Wave 3: Implementation

**⚠️ Destructive** — Modifies source code but does NOT commit

**Purpose**: Execute the plan

**What happens:**
- Subagents read PLAN.md
- Modify code files
- Run tests locally
- Write CHANGES.md log

**Output**: Modified code + `{service}/.agentbus-plans/{plan-id}/CHANGES.md`

### Wave 4: Verification

**Purpose**: Verify implementation works

**What happens:**
- Subagents read CHANGES.md
- Run full test suite
- Check cross-service compatibility
- Write TEST-RESULTS.md

**Output**: `{service}/.agentbus-plans/{plan-id}/TEST-RESULTS.md`

### Wave 4b: Adjustments & Clarifications (Optional)

**Purpose**: Minor fixes and explanations after verification

**Modes:**
- **Explain**: Answer questions ("Why does this test fail?")
- **Quick Fix**: Small adjustments (fix mocks, typos, validations)

**What happens:**
- User asks questions or requests small fixes
- Service agent investigates or makes minor changes
- Appends to CHANGES.md
- Re-runs affected tests

**Not for:** Major architectural changes (needs new plan)

### Wave 5: Wrap-up (Optional)

**Purpose**: Create git commits

**⚠️ Only after user confirmation**

**What happens:**
- Subagents stage changes
- Create commits with descriptive messages
- Write COMMITS.md log

**Output**: Git commits + `{service}/.agentbus-plans/{plan-id}/COMMITS.md`

## Available Skills

| Skill | Purpose | Invocation |
|-------|---------|------------|
| **agentbus orchestrator** | Coordinates waves, spawns subagents | `/agentbus orchestrator "feature"` |
| **agentbus service agent** | Per-service specialist | Via Task tool only |
| **agentbus review** | Verifies cross-service consistency | `/agentbus review --feature-slug "xxx"` |

## Workspace Structure

```
workspace/                          # parent folder of all repos
├── agentbus-orchestrator/          # orchestrator workspace (not a git repo)
│   └── 004-feature-slug/
│       ├── status.json             # wave tracking, resume/retry
│       ├── SEED-PLAN.md            # initial vision
│       ├── PLAN.md                 # consolidated view (final)
│       ├── TEST-PLAN.md            # cross-service tests
│       ├── DEPLOY-ORDER.md         # rollout sequence
│       └── service-outputs/        # subagent summaries
│           └── {service}.json
│
├── payments-service/               # service repo
│   └── .planning/
│       └── codebase/               # ← Wave 1: 5 service documents
│           ├── STACK.md
│           ├── ARCHITECTURE.md
│           ├── STRUCTURE.md
│           ├── CONVENTIONS.md
│           └── CONCERNS.md
│   └── .agentbus-plans/
│       └── 004-feature/            # ← Wave 2-5: plan folder
│           ├── PLAN.md             # ← Wave 2: refined plan
│           ├── QA-REPORT.md        # ← Wave 2.5: QA concerns
│           ├── CHANGES.md          # ← Wave 3: implementation log
│           ├── TEST-RESULTS.md     # ← Wave 4: test results
│           └── COMMITS.md          # ← Wave 5: commit log (optional)
│
└── notifications-service/
    └── ... (same structure)
```

## Service Registry

Global registry file: `~/.agentbus/services.json`

```json
{
  "payments-service": "/home/user/workspace/payments-service",
  "notifications-service": "/home/user/workspace/notifications-service"
}
```

**To register a service**: Read `~/.agentbus/services.json`, add entry, write back.

**To list services**: Read `~/.agentbus/services.json` and parse.

## Typical Workflow

### 1. Initialize Plan

```
User: "We need to add audit logging to user actions"

You: Initialize planning
/agentbus orchestrator "add audit logging to user actions" auth payments notifications

This creates the orchestrator workspace with sequential plan ID.
```

### 2. Run Wave 1 (Mapping)

```
You: Start mapping
/agentbus orchestrator --continue 004-audit-logging

This spawns parallel subagents to create .planning/codebase/ documents in each service.
Wait for completion.
```

### 3. Run Wave 2a (Refinement)

```
You: Refine plans
/agentbus orchestrator --continue 004-audit-logging

This spawns subagents to write PLAN.md in each service.
```

### 4. Wave 2.5 (Plan QA & Concerns) — NEW

```
You: Run QA
/agentbus orchestrator --continue 004-audit-logging

This spawns specialist agents to identify concerns and gaps.
The orchestrator will present consolidated questions for your input.
```

### 5. Wave 2b (Context Queries - if needed)

If a service agent needs info from adjacent services:

```
Orchestrator: cronjob-api needs context from users-api
Run context queries? (yes/no): yes

This queries users-api without adding it to the plan.
```

### 6. Run Wave 3 (Implementation)

```
You: Implement changes
/agentbus orchestrator --continue 004-audit-logging

⚠️ This modifies source code but does NOT commit.
```

### 7. Run Wave 4 (Verification)

```
You: Verify implementation
/agentbus orchestrator --continue 004-audit-logging

This runs tests and creates TEST-RESULTS.md.
```

### 8. Wave 4b (Adjustments - if needed)

```
Orchestrator: 2 tests failed in cronjob-api
Adjustments or questions? (yes/no): yes

You: "Fix the mock in test_validation_email"
→ Quick fix applied
→ Tests re-run
→ ✅ PASS
```

### 9. Wave 5 (Wrap-up)

```
You: Create commits
/agentbus orchestrator --continue 004-audit-logging

⚠️ Only after confirming everything looks good.
```

## Error Handling & Recovery

### Subagent Fails

1. Check `status.json` for error details
2. Fix underlying issue
3. Re-run: `/agentbus orchestrator --continue {plan-id}`
4. Failed subagent re-runs, others unchanged

### Add Service Mid-Flight

1. Update `status.json` to add service
2. Re-run current wave
3. New service gets processed, existing ones unchanged

### Resume After Interruption

1. Read `status.json` to see current wave
2. Run: `/agentbus orchestrator --continue {plan-id}`
3. Continues from where it left off

## Key Concepts

### .planning/codebase/ (5 Documents)

Living service documentation written by Wave 1. Located at `{service}/.planning/codebase/`:

| Document | Content | Purpose |
|----------|---------|---------|
| STACK.md | Technology stack | Know what technologies to use |
| ARCHITECTURE.md | Patterns, layers, data flow | Structure changes correctly |
| STRUCTURE.md | Directory layout | Know where to place files |
| CONVENTIONS.md | Implementation patterns | **Choose the right approach** |
| CONCERNS.md | Tech debt, risks | Avoid pitfalls |

**Reusable**: `.planning/codebase/` is updated on each Wave 1, serving as documentation for future features.

**CRITICAL**: Always read CONVENTIONS.md first — it contains decision patterns for choosing approaches.

### PLAN.md

Feature-specific implementation plan written by Wave 2. Includes:
- Overview of changes in this service
- Specific files to modify
- Testing strategy
- Dependencies on other services
- Rollback plan

### QA-REPORT.md

Quality assurance report written by Wave 2.5. Includes:
- Concerns identified by the specialist agent
- Gaps in the plan
- Questions for the user
- Recommendations for refinement

### CHANGES.md

Log of files modified during Wave 3. Used for:
- Tracking what changed
- Creating commits in Wave 5
- Audit trail

### TEST-RESULTS.md

Test results from Wave 4. Includes:
- Test summary (passed/failed)
- Coverage metrics
- Cross-service compatibility checks

### status.json

Tracking file that enables resume/retry. Contains:
- Current wave
- Service statuses
- Artifact paths (not content)
- Retry counts

## Anti-Patterns to Avoid

❌ **Don't**: Run all waves in one session (context exhaustion)
✅ **Do**: Run one wave at a time, review, then continue

❌ **Don't**: Modify `.planning/codebase/` documents manually during planning
✅ **Do**: Let Wave 1 subagent update them

❌ **Don't**: Skip Wave 2.5 (Plan QA) — user input prevents bad assumptions
✅ **Do**: Always run Plan QA and address concerns before implementation

❌ **Don't**: Skip Wave 4 (verification)
✅ **Do**: Always verify before committing

❌ **Don't**: Add too many services (>5) without user confirmation
✅ **Do**: Propose list, let user confirm/adjust

❌ **Don't**: Use Wave 4b for major architectural changes
✅ **Do**: Create new plan if architecture needs to change

## Getting Help

- **Orchestrator protocol**: `@skills/agentbus orchestrator/SKILL.md`
- **Service agent protocol**: `@skills/agentbus service agent/SKILL.md`
- **Review protocol**: `@skills/agentbus review/SKILL.md`

## Version

AgentBus Skills v3.0.0 — Evidence-Based Wave Model with Plan QA (Deep Mapping)
