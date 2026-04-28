---
name: agentbus
description: Cross-service planning system for multi-service features. Entry point that routes to orchestrator for all execution. Updated for Deep Mapping (.planning/codebase/ folder + Wave 2.5 Plan QA).
version: 3.0.0
triggers: [cross-service feature, multi-service planning]
tools: [Read, Task]
tags: [agentbus, orchestration, cross-service]
---

# AgentBus Skills

Cross-service planning system for features that touch **2+ microservices**.

---

## When to Use AgentBus?

✅ **YES — Use AgentBus:**
- Feature that modifies 2+ services (e.g., "migrate sync to async between payments and notifications")
- API refactor that affects producers and consumers
- Schema change that impacts multiple repos

❌ **NO — Use other skills:**
- Change in **a single service** → Use `gsd` or `spec-kit`
- Just exploring one codebase → Use `map-codebase` directly on the repo

---

## Architecture

```
┌─────────────────────────────────────┐
│  agentbus (base skill)              │  ← This file
│  └── Documents and routes only      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  agentbus orchestrator              │  ← Execution entry point
│  ├── Spawns map-codebase (Wave 1)   │
│  ├── Design Alignment (Wave 1.5)    │
│  ├── Plan QA & Concerns (Wave 2.5)  │
│  ├── Spawns service-agents          │
│  └── Coordinates waves              │
└─────────────────────────────────────┘
```

| Component | Role | Invocation |
|-----------|------|------------|
| `agentbus orchestrator` | Coordinates cross-service waves | `/agentbus orchestrator ...` |
| `agentbus map-codebase` | Deep mapping (5 documents) | Spawned in Wave 1 |
| `agentbus service agent` | Specialist per service | Spawned via Task (internal) |
| `agentbus review` | Verifies cross-service consistency | `/agentbus review ...` |

---

## Main Commands

### Discovery (read-only)
```
/agentbus orchestrator --ask "how does the payment flow work?" payments notifications
```

### Initialize Plan
```
/agentbus orchestrator "migrate to async events" payments notifications inventory
```
Creates: `agentbus-orchestrator/001-feature/status.json` + `SEED-PLAN.md`

### Continue Waves
```
/agentbus orchestrator --continue 001-feature
```
Executes the next wave based on `status.json`.

### Verify Consistency
```
/agentbus review --feature-slug 001-feature
```

---

## Wave Model (Deep Mapping + Plan QA)

| Wave | Name | Output | Description |
|------|------|--------|-------------|
| 1 | Service Mapping | `.planning/codebase/` (5 docs) | Deep mapping of the service |
| 1.5 | Design Alignment | Validated decisions | Approach checkpoint |
| 2 | Plan Refinement | `PLAN.md` | Detailed per-service plan |
| 2.5 | Plan QA & Concerns | `QA-REPORT.md` | Surface gaps and doubts for user input |
| 2.6 | Plan Alignment | Consistency report | Cross-service design check |
| 2b | Context Queries | Answers | Query adjacent services |
| 3 | Implementation | Code + `CHANGES.md` | Modify code (no commits) |
| 3.5 | Contract Validation | Validation report | Deep implementation check (optional) |
| 4 | Verification | `TEST-RESULTS.md` | Run tests |
| 4b | Adjustments (opt) | Fixes / explanations | Minor fixes and clarifications |
| 5 | Wrap-up (opt) | `COMMITS.md` | Post-verification commits |

**Important:** Run **one wave at a time**. Review results before continuing.

### Deep Mapping (Wave 1)

Instead of a single `AGENTS.md`, Wave 1 generates **5 specialized documents** in `.planning/codebase/`:

| Document | Content | Use |
|----------|---------|-----|
| `STACK.md` | Tech stack, dependencies | Which technologies to use |
| `ARCHITECTURE.md` | Patterns, layers, flow | How to structure changes |
| `STRUCTURE.md` | Directory layout | Where to create files |
| `CONVENTIONS.md` | Available patterns, when to use them | **Which approach to use** |
| `CONCERNS.md` | Tech debt, risks | What to avoid |

**CONVENTIONS.md is critical**: Captures the available patterns in the codebase and helps choose the best approach when multiple options exist.

### Design Alignment Checkpoint (Wave 1.5)

New checkpoint that validates the approaches proposed in `SEED-PLAN` are the best available according to `CONVENTIONS.md`.

**Heuristics applied:**
| Scenario | Preference |
|----------|------------|
| Schema change (ALTER TABLE) | SQL Migration |
| Dynamic data (permissions, configs) | API Endpoint |
| Per-environment data | API/Config |
| Static reference data | Migration/Seed |

If conflict is detected, present to the user for a decision before continuing to Wave 2.

### Plan QA & Concerns (Wave 2.5) — NEW

Before implementation, the orchestrator asks each specialist agent to identify:
- **Concerns**: Risks, convention violations, performance issues
- **Gaps**: Missing error handling, undefined edge cases
- **Doubts**: Unclear assumptions about data or behavior

The orchestrator consolidates these and **asks the user for input** to refine the plans. This prevents guessing on things that should involve human judgment.

**Flow**:
1. Orchestrator spawns specialist agents in `plan_qa` mode
2. Each agent writes `QA-REPORT.md`
3. Orchestrator consolidates and presents to user
4. User provides answers
5. Plans are refined before moving to alignment

### Context Queries (Wave 2b)

During planning, if a service agent needs information from other services (e.g., "what does users-api return?"), it can request **context queries**.

**Flow**:
1. Service agent detects need → Writes provisional PLAN
2. Reports `status: "needs_context"` with pending queries
3. Orchestrator spawns **query-only agents** in adjacent services
4. Re-runs service agent with obtained context
5. Completes final PLAN.md

**Advantage**: You don't map services you don't modify, but get precise context when needed.

### Adjustments (Wave 4b)

After Wave 4 (tests), if there are minor failures or you need clarifications:

**Explain Mode**:
- Question: "Why does this test fail?"
- Service agent investigates and explains (read-only)

**Quick Fix Mode**:
- Minor adjustment: "Fix the mock in the test"
- Typo fix, validation, missing import
- **No** large architectural changes
- Appended to CHANGES.md
- Re-runs affected tests

---

## First Steps

### 1. Verify Service Registry
```bash
# Read ~/.agentbus/services.json
# Must contain the services you will use
```

### 2. Auto-Generated Plan ID
The orchestrator scans `.agentbus-plans/` in each service to:
- Find the highest existing plan number
- Suggest the next sequential number (no gaps)
- Validate consistency across all services

Example: If `003-feature` exists, the new one will be `004-new-feature`.

### 3. Execute Flow
```
# Step 1: Initialize (auto-detects plan number)
/agentbus orchestrator "feature description" svc1 svc2

# Step 2: Wave 1 (Deep Mapping - 5 documents)
/agentbus orchestrator --continue 004-feature-slug

# Step 3: Wave 1.5 (Design Alignment Checkpoint)
#         Runs automatically, may ask for input

# Step 4: Wave 2 (Plan Refinement)
/agentbus orchestrator --continue 004-feature-slug

# Step 5: Wave 2.5 (Plan QA & Concerns — NEW)
/agentbus orchestrator --continue 004-feature-slug

# Step 6-N: Continue remaining waves
/agentbus orchestrator --continue 004-feature-slug
```

---

## Detailed Documentation

- **Complete protocol**: `@skills/agentbus orchestrator/SKILL.md`
- **Map Codebase**: `@skills/agentbus map-codebase/SKILL.md`
- **Service agent**: `@skills/agentbus service agent/SKILL.md`
- **Review**: `@skills/agentbus review/SKILL.md`

---

## Version

AgentBus Skills v3.0.0 (Deep Mapping + Plan QA)
