---
name: agentbus
description: Cross-service planning system for LLM coding agents. Orchestrates multi-wave planning across microservices with evidence-based workflow.
version: 1.0.0
triggers: [cross-service feature, multi-service planning, service architecture]
tools: [Read, Write, Bash, Task]
---

# AgentBus Skills

Cross-service planning system that eliminates the "developer as messenger" problem when planning features that span multiple microservices.

## When to Use

Use AgentBus when you need to:

- **Plan a feature** that touches multiple services (e.g., "migrate sync calls to async events")
- **Understand** how a feature works across services (discovery mode)
- **Verify** cross-service consistency before implementation
- **Refactor** APIs or data models that affect multiple services

## Core Philosophy: Evidence Over Communication

Instead of passing data through responses, AgentBus writes artifacts at each stage:

```
Wave 1: Service Mapping     →  AGENTS.md in each service
Wave 2: Plan Refinement     →  PLAN.md in each service  
Wave 3: Verification        →  REPORT.md in each service
Final:   Orchestrator reads REPORTs → Global synthesis
```

**Benefits:**
- **Context efficiency**: Orchestrator reads only what it needs
- **Auditability**: Complete history in version-controlled files
- **Resumability**: Failed waves can be retried independently
- **Reusability**: AGENTS.md serves as living service documentation

## Quick Start Commands

### Discover First (No Files Written)

Understand how something works across services without generating plans:

```
/agentbus-orchestrator --ask "how does user onboarding flow across services?" payments notifications
```

### Initialize a New Plan

Start planning a cross-service feature:

```
/agentbus-orchestrator "remove deprecated field from Tool model" tools-service bot-service
```

This creates:
- `agentbus-orchestrator/001-feature/status.json` — tracking
- `agentbus-orchestrator/001-feature/SEED-PLAN.md` — initial vision

### Continue Waves

After initialization, continue each wave:

```
/agentbus-orchestrator --continue 001-feature
```

This runs the next wave (1, 2, or 3 based on status.json).

### Review Before Implementation

Verify cross-service consistency:

```
/agentbus-review --feature-slug "001-feature"
```

## Wave Execution Model

### Wave 1: Service Mapping

**Purpose**: Create/update AGENTS.md in each service

What happens:
- Orchestrator spawns parallel subagents (one per service)
- Each subagent maps codebase: stack, architecture, APIs, DB, testing
- Writes AGENTS.md to service repo
- Writes summary JSON to orchestrator workspace

**Output**: `{service}/AGENTS.md`

### Wave 2: Plan Refinement

**Purpose**: Create detailed implementation plan per service

What happens:
- Subagents read AGENTS.md (their own service)
- Read SEED-PLAN.md for context
- Explore relevant code files
- Write PLAN.md with specific changes

**Output**: `{service}/.agentbus-plans/{feature}.md`

### Wave 3: Verification

**Purpose**: Verify plans are complete and consistent

What happens:
- Subagents read PLAN.md (own service)
- Read PLAN.md from related services
- Check for blockers, risks, dependencies
- Write REPORT.md with verification status

**Output**: `{service}/.agentbus-plans/{feature}-REPORT.md`

### Final: Global Synthesis

Orchestrator reads all REPORT.md and generates:
- `PLAN.md` — consolidated global view
- `TEST-PLAN.md` — cross-service test strategy
- `DEPLOY-ORDER.md` — rollout sequence

## Available Skills

| Skill | Purpose | Invocation |
|-------|---------|------------|
| **agentbus-orchestrator** | Coordinates waves, spawns subagents | `/agentbus-orchestrator "feature" svc1 svc2` |
| **agentbus-service-agent** | Per-service specialist (spawned by orchestrator) | Via Task tool only |
| **agentbus-review** | Verifies cross-service consistency | `/agentbus-review --feature-slug "xxx"` |
| **map-codebase** | Creates AGENTS.md for undocumented services | `/map-codebase` (auto-invoked) |

## Workspace Structure

```
workspace/                          # parent folder of all repos
├── agentbus-orchestrator/          # orchestrator workspace (not a git repo)
│   └── 001-feature-slug/
│       ├── status.json             # wave tracking, resume/retry
│       ├── SEED-PLAN.md            # initial vision
│       ├── PLAN.md                 # consolidated view (final)
│       ├── TEST-PLAN.md            # cross-service tests
│       ├── DEPLOY-ORDER.md         # rollout sequence
│       └── service-outputs/        # subagent summaries
│           └── {service}.json
│
├── payments-service/               # service repo
│   ├── AGENTS.md                   # ← Wave 1: service documentation
│   └── .agentbus-plans/
│       ├── 001-feature.md          # ← Wave 2: refined plan
│       └── 001-feature-REPORT.md   # ← Wave 3: verification
│
└── notifications-service/
    └── ... (same structure)
```

## Prerequisites

1. **Register services** (one-time setup):
   ```bash
   # Optional: use legacy scripts
   uv run scripts/register_service.py payments-service /path/to/payments-service
   ```

2. **Verify services are known**:
   ```bash
   uv run scripts/list_services.py --json
   ```

## Typical Workflow

### 1. Understand the Feature

```
User: "We need to add audit logging to all user actions"

You: Run discovery
/agentbus-orchestrator --ask "which services handle user actions?" payments notifications auth

Review the answer to understand scope.
```

### 2. Initialize Plan

```
You: Initialize planning
/agentbus-orchestrator "add audit logging to user actions" auth payments notifications

This creates the orchestrator workspace and SEED-PLAN.md.
```

### 3. Run Wave 1 (Mapping)

```
You: Start mapping
/agentbus-orchestrator --continue 001-audit-logging

This spawns parallel subagents to create AGENTS.md in each service.
Wait for completion.
```

### 4. Run Wave 2 (Refinement)

```
You: Refine plans
/agentbus-orchestrator --continue 001-audit-logging

This spawns subagents to write PLAN.md in each service.
```

### 5. Run Wave 3 (Verification)

```
You: Verify plans
/agentbus-orchestrator --continue 001-audit-logging

This spawns subagents to write REPORT.md in each service.
Orchestrator performs global verification.
```

### 6. Review

```
You: Check consistency
/agentbus-review --feature-slug "001-audit-logging"

If issues found, fix and re-run relevant wave.
```

### 7. Final Output

Check generated files:
- `agentbus-orchestrator/001-audit-logging/PLAN.md` — consolidated view
- `agentbus-orchestrator/001-audit-logging/DEPLOY-ORDER.md` — rollout plan

## Error Handling & Recovery

### Subagent Fails

1. Check `status.json` for error details
2. Fix underlying issue
3. Re-run: `/agentbus-orchestrator --continue {plan-id}`
4. Failed subagent re-runs, others unchanged

### Add Service Mid-Flight

1. Update `status.json` to add service
2. Re-run current wave
3. New service gets processed, existing ones unchanged

### Resume After Interruption

1. Read `status.json` to see current wave
2. Run: `/agentbus-orchestrator --continue {plan-id}`
3. Continues from where it left off

## Key Concepts

### AGENTS.md

Living service documentation written by Wave 1. Includes:
- Technology stack
- Architecture and directory structure
- API endpoints
- Database schema
- Testing approach
- Conventions

**Reusable**: AGENTS.md is updated on each Wave 1, serving as documentation for future features.

### PLAN.md

Feature-specific implementation plan written by Wave 2. Includes:
- Overview of changes in this service
- Specific files to modify
- Testing strategy
- Dependencies on other services
- Rollback plan

### REPORT.md

Verification report written by Wave 3. Includes:
- Status: ready / needs_work / blocked
- Implementation checklist
- Local risks with mitigations
- Cross-service impact
- Open questions with owners

### status.json

Tracking file that enables resume/retry. Contains:
- Current wave
- Service statuses
- Artifact paths (not content)
- Retry counts

## Anti-Patterns to Avoid

❌ **Don't**: Run all waves in one session (context exhaustion)
✅ **Do**: Run one wave at a time, review, then continue

❌ **Don't**: Modify AGENTS.md manually during planning
✅ **Do**: Let Wave 1 subagent update it

❌ **Don't**: Skip Wave 3 (verification)
✅ **Do**: Always verify before implementation

❌ **Don't**: Add too many services (>5) without user confirmation
✅ **Do**: Propose list, let user confirm/adjust

## Getting Help

- **Orchestrator protocol**: `@skills/agentbus-orchestrator/SKILL.md`
- **Service agent protocol**: `@skills/agentbus-service-agent/SKILL.md`
- **Review protocol**: `@skills/agentbus-review/SKILL.md`
- **Full spec**: `agentBus_PRD`

## Version

AgentBus Skills v1.0.0 — Evidence-Based Wave Model
