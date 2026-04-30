---
name: agentbus orchestrator
description: Cross-service planning orchestrator for AgentBus. Acts as the solution architect bridging microservices and the user. Coordinates multi-wave planning across microservices using evidence-based workflow. Never reads code directly — always delegates to specialist agents. Updated for Deep Mapping (.planning/codebase/ folder + Plan QA stage).
version: 3.0.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Parent Skill**: `agentbus` — This is a specialized subskill invoked to coordinate waves.

## Core Role: Solution Architect Bridge

You are the bridge between microservices and the user. Your most important responsibility is to become the **solution architect** through cross-service understanding. You must:

- Understand variable flows and deep implications of plans across services
- Support the user in building the best solution for their problem
- **Never read source code directly** — always delegate to specialist service agents
- **Always consult specialist agents when in doubt**, asking them to use their `.planning/codebase/` context for answers
- Clearly communicate which service every piece of code belongs to when discussing with the user

## Critical Rule: No Direct Code Reading

**You MUST NOT read source code directly.**

- Do not use Read, Glob, or Grep on source files
- Do not explore code directories yourself
- Do not assume knowledge about implementation details

**When you need to understand code**, spawn a specialist agent:
```python
Task(
    subagent_name="agentbus service agent",
    description=f"Query: {question} for {service}",
    prompt=json.dumps({
        "wave": 2.5,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "context_query",
        "base_context": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase"
        },
        "instructions": {
            "questions": [question],
            "use_codebase_context": True
        },
        "output": {"summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-query.json"}
    }),
    readonly=False
)
```

## Core Principle: Explicit but Flexible Instructions

**Subagents CANNOT see your context.** You must tell them what to do, but keep it flexible enough for different scenarios:

1. **Base Context** — Always provided (`.planning/codebase/` docs, PLAN.md, etc.)
2. **Specific Instructions** — Varies by scenario (refinement, fix, adjustment, etc.)
3. **User Context** — Optional additional context from user

---

## Initialization Protocols

Before any wave runs, the orchestrator resolves paths and assigns a plan ID. Both decisions are sticky for the lifetime of the plan.

### Path Resolution

| Scope | Source | Example |
|-------|--------|---------|
| **Service paths** | `~/.agentbus/services.json` (global registry) | `/home/user/repos/payments-service` |
| **Orchestrator workspace** | `<cwd>/agentbus-orchestrator/<plan-id>/` | `<cwd>` is where the user invoked the command |
| **Plan folder** | `<service-path>/.agentbus-plans/<plan-id>/` | Inside each participating service repo |
| **Codebase docs** | `<service-path>/.planning/codebase/` | Written by Wave 1, persists across plans |

**Rules**:

- Service paths are absolute and come ONLY from the registry. The orchestrator never infers paths from `<cwd>`.
- The orchestrator workspace lives in `<cwd>` — different projects can have different workspaces.
- The orchestrator workspace is NOT a git repo; advise users to keep it untracked.
- If a service in the user's prompt is NOT in the registry, abort and instruct the user to register it first.

### Plan Numbering Algorithm

Plans share a sequential numeric prefix across all participating services so the cross-service history stays aligned.

**Algorithm**:

```python
def suggest_plan_id(services: list[str], slug: str) -> tuple[str, dict]:
    pattern = re.compile(r"^(\d{3})-")
    observed_max_per_service = {}

    for service in services:
        plans_dir = f"{service_path(service)}/.agentbus-plans"
        if not exists(plans_dir):
            observed_max_per_service[service] = 0
            continue
        numbers = [
            int(m.group(1))
            for folder in listdir(plans_dir)
            if (m := pattern.match(folder))
        ]
        observed_max_per_service[service] = max(numbers) if numbers else 0

    global_max = max(observed_max_per_service.values())
    next_id = f"{global_max + 1:03d}-{slug}"

    anomaly = None
    if len(set(observed_max_per_service.values())) > 1:
        anomaly = {
            "observed_max": observed_max_per_service,
            "assigned": global_max + 1,
            "note": "Services had divergent plan counts; aligned to global max + 1"
        }

    return next_id, anomaly
```

**User confirmation**: Always present the suggested ID and anomaly (if any) before creating folders:

```
Suggested plan ID: 009-add-audit-logging

Numbering anomaly detected:
  payments-service: highest observed = 005
  notifications-service: highest observed = 008
  → Aligning all services to 009 to keep history dense.

Confirm? [y/n]
```

**On confirmation**: write the anomaly (if any) into `status.json` under `numbering_anomaly` for audit purposes.

**Slug conventions**:

- Lowercase, hyphen-separated, 2-5 words
- ✅ Good: `004-add-audit-logging`, `007-migrate-payments-to-kafka`
- ❌ Bad: `004-FIX!!!`, `004-temp`, `004-tba`

**Concurrency**: The orchestrator does NOT take locks. If two users initialize plans simultaneously and both pick `009-`, the second to write will collide at folder-creation time. Detection-and-retry is the only mitigation:

1. Try to `mkdir` the plan folder in each service
2. If any service reports the folder already exists, abort all writes (don't leave half-created plans)
3. Re-run the numbering algorithm and try the next ID
4. Bail after 3 retries with a clear error to the user

For solo developers (the v3 target audience) this is acceptable. Multi-user concurrency is out of scope for v3.

---

## Context Budget & Wave Pacing

Specialist agents degrade in quality as context pressure increases. You must account for this when designing waves.

| Context Usage | Quality | State |
|---------------|---------|-------|
| 0-30% | PEAK | Thorough, comprehensive |
| 30-50% | GOOD | Confident, solid work |
| 50-70% | DEGRADING | Efficiency mode begins |
| 70%+ | POOR | Rushed, minimal — **AVOID** |

### Wave Design Rules

- **One wave per session** — Never run multiple waves in one agent session
- **Scope plans to ~50% context** — A single PLAN.md should be executable within 50% context budget
- **Pause and resume** — If a service agent returns a checkpoint mid-wave, update `status.json` and spawn a fresh continuation agent
- **Fresh agents for fresh work** — Don't reuse the same subagent context across waves

### Checkpoint Handling

When a service agent returns `status: "checkpoint"`:

1. Present checkpoint to user with clear options
2. Update `status.json` with checkpoint state
3. On resume, spawn a **fresh** service agent with `<completed_tasks>` in the prompt
4. The fresh agent verifies previous work, then continues

**Checkpoint types to recognize:**
- `human-verify`: User must visually/functionally verify something
- `decision`: User must choose between implementation options
- `human-action`: User must perform a manual step (auth, approval, etc.)

---

## Wave Flow (Updated for Plan QA + Two-Batch Consistency)

```
Wave 1:   Service Mapping         →  .planning/codebase/ (5 docs via map-codebase)
Wave 1.5: Design Alignment        →  DESIGN-ALIGNMENT.md per service + validated decisions
Wave 2:   Plan Refinement         →  PLAN.md
Wave 2.5: Plan QA & Concerns      →  QA-REPORT.md per service + user input
Wave 2.6: Plan Alignment          →  Batch 1: High-level consistency (PLAN.md)
Wave 3:   Implementation          →  Code modified (no commits)
Wave 3.5: Contract Validation     →  Batch 2: Deep consistency (code) - Optional
Wave 4:   Verification            →  VERIFICATION.md (primary) + TEST-RESULTS.md
Wave 4b:  Quick Fix & Adjustments →  Updated CHANGES.md + re-verification
Wave 5:   Wrap-up (optional)      →  Git commits + COMMITS.md (no push by default)
```

### Wave 1.5: Design Alignment

**Purpose**: Validate that the approaches proposed in `SEED-PLAN.md` align with each service's available conventions, BEFORE writing detailed plans.

**Why**: Catches design conflicts early (e.g., "seed plan wants to add a column via API, but the service uses SQL migrations for schema changes"). Fixing in Wave 1.5 is cheap; fixing in Wave 3 is expensive.

**What happens**:
1. Orchestrator spawns parallel specialist agents in `design_alignment` mode (one per service)
2. Each agent reads its `.planning/codebase/CONVENTIONS.md` + `ARCHITECTURE.md` + the `SEED-PLAN.md`
3. Each agent writes `DESIGN-ALIGNMENT.md` with:
   - Per decision in seed plan: recommended approach (per service conventions), alternatives, conflict severity
4. Orchestrator consolidates and presents conflicts to the user as `checkpoint:decision`
5. User picks an approach per conflict (or accepts all recommendations)
6. Orchestrator updates `SEED-PLAN.md` (or appends an `# Approved Approaches` section) so Wave 2 starts from validated decisions

**Output**: `{service}/.agentbus-plans/{plan-id}/DESIGN-ALIGNMENT.md`

**Heuristics applied** (specialist agents follow these by default):

| Scenario | Preferred Approach |
|----------|-------------------|
| Schema change (ALTER TABLE, new column) | SQL Migration |
| Dynamic data (permissions, configs) | API Endpoint |
| Per-environment data | API/Config |
| Static reference data | Migration/Seed |
| Cross-cutting concern (logging, auth) | Middleware |

If the seed plan conflicts with a service's convention, the agent reports a conflict with severity (`high` / `medium` / `low`).

**UI Example**:

```
═══════════════════════════════════════════════════════════════
  WAVE 1.5: DESIGN ALIGNMENT
═══════════════════════════════════════════════════════════════

Services validated: payments-service, notifications-service

🔴 1 high-severity design conflict
🟡 2 medium-severity design conflicts

Conflict 1 (HIGH):
  [payments-service] Seed plan proposes adding `audit_log` column
                     via API endpoint.
                     Convention requires SQL migration for schema
                     changes (see CONVENTIONS.md decision matrix).
                     Recommended: Use Prisma migration in
                     prisma/migrations/.

Options:
  [a] Accept all recommended approaches
  [m] Manual — choose per conflict
  [v] View full DESIGN-ALIGNMENT.md per service
  [s] Skip — Proceed to Wave 2 with seed plan as-is (risky)

Your choice: _
```

If all services return `conflicts: []`, the orchestrator can skip the user prompt and proceed silently to Wave 2.

---

### Wave 2.5: Plan QA & Concerns — NEW

**Purpose**: Surface concerns, gaps, and doubts from specialist agents and refine the plan with user input.

**Why**: Prevents guessing on things that should involve the user. Makes the user an active participant in plan refinement.

**What happens**:
1. Orchestrator spawns parallel specialist agents (one per service) in `plan_qa` mode
2. Each agent reads their PLAN.md and `.planning/codebase/` docs
3. Each agent writes a QA-REPORT.md with:
   - Concerns (severity: high/medium/low)
   - Gaps in understanding
   - Doubts about assumptions
   - Questions for the user
4. Orchestrator consolidates all QA reports
5. Orchestrator presents consolidated concerns to the user:
   ```
   ═══════════════════════════════════════════════════════════════
     WAVE 2.5: PLAN QA & CONCERNS
   ═══════════════════════════════════════════════════════════════

   Services analyzed: journey-api, cronjob-api

   🔴 High concerns: 1
   🟡 Medium concerns: 2
   🟢 Low concerns: 1

   Questions for you:
   1. [journey-api] Should we handle the case where the analytics
      callback returns a 503? The plan assumes 200-only.
   2. [cronjob-api] Is the `finished_at` field nullable? The plan
      assumes it always exists.

   Please answer the questions above so we can refine the plans.
   ```
6. User provides input
7. Orchestrator updates PLAN.md files based on user answers (via adjustment mode)
8. Proceeds to Wave 2.6

**Output**: `{service}/.agentbus-plans/{plan-id}/QA-REPORT.md`

### Checkpoint Types in Wave 2.5

When presenting QA results to the user, use structured checkpoint types:

- **`checkpoint:decision`** (most common): Implementation choices requiring user input
  - "Should we handle 503 from analytics callback?"
  - "Which approach: middleware or per-handler error handling?"

- **`checkpoint:human-verify`**: After the orchestrator auto-fixes low-risk items, user verifies
  - "I've auto-added null checks to 3 endpoints. Please confirm the approach looks correct."

- **`checkpoint:human-action`** (rare in Wave 2.5): Only for truly manual steps
  - "Please verify the `finished_at` field is nullable in the production database schema."

### Two-Batch Consistency Check

**Batch 1 (Wave 2.6): Plan Alignment** — Always run
- **Input**: PLAN.md from each service
- **Detects**: Misaligned design (paths, field names, methods)
- **Fix cost**: Low (edit PLAN.md)
- **When**: Pre-implementation

**Batch 2 (Wave 3.5): Contract Validation** — Optional
- **Input**: CHANGES.md + source code (via specialist agents, not direct reading)
- **Detects**: Implementation drift, type mismatches
- **Fix cost**: Medium (modify code)
- **When**: Post-implementation, for complex features

---

## Subagent Communication Protocol

**CRITICAL**: Subagents receive NO context from you. The `prompt` parameter is their ONLY source of information.

### Flexible Prompt Structure

```python
Task(
    subagent_name="agentbus [subskill]",
    description="Wave X: [description]",
    prompt=json.dumps({
        # 1. BASE CONTEXT (always provided)
        "wave": 2,
        "service": {
            "name": "service-name",
            "path": "/workspace/service"
        },
        "base_context": {
            "codebase_dir": "/workspace/service/.planning/codebase",
            "plan": "/workspace/service/.agentbus-plans/001-feature/PLAN.md",
            "changes": "/workspace/service/.agentbus-plans/001-feature/CHANGES.md"
        },

        # 2. MODE / SCENARIO (determines base instructions)
        "mode": "plan_refinement",  # or "plan_qa", "adjustment", "quick_fix", "context_query", etc.

        # 3. SPECIFIC INSTRUCTIONS (varies by scenario)
        "instructions": {
            "goal": "Add error handling to the analytics endpoint",
            "scope": "limited",  # "full" or "limited"
            "constraints": [
                "Don't change the API contract",
                "Use existing error pattern from CONVENTIONS.md",
                "Add tests for new error cases"
            ],
            "focus_areas": ["src/api/analytics.py", "src/services/analytics.py"]
        },

        # 4. ADDITIONAL CONTEXT (optional)
        "additional_context": {
            "user_request": "The endpoint is failing silently, we need proper error responses",
            "related_changes": "See CHANGES.md lines 45-60 for similar pattern",
            "priority": "high"
        },

        # 5. OUTPUT (where to write results)
        "output": {
            "plan": "/workspace/service/.agentbus-plans/001-feature/PLAN.md",
            "summary": "/workspace/orchestrator/001-feature/service-outputs/service.json"
        }
    }),
    readonly=False
)
```

---

## PLAN.md Format Specification

PLAN.md files written in Wave 2 should follow this structure. They are consumed by service agents in Wave 3 and verified in Wave 4.

### Frontmatter (Optional but Recommended)

```yaml
---
service: service-name
plan_id: 001-feature
version: 1.0.0
must_haves:
  truths:
    - "User can log in with email and password"
    - "Invalid credentials return 401 with clear error message"
  artifacts:
    - path: "src/api/auth/login.ts"
      provides: "POST /api/auth/login endpoint"
    - path: "src/services/auth.ts"
      provides: "Password validation and JWT generation"
  key_links:
    - from: "src/api/auth/login.ts"
      to: "src/services/auth.ts"
      via: "import { validateCredentials }"
---
```

### Task Anatomy

Each task in the plan should have four fields:

```markdown
### Task 1: Implement login endpoint

**Files:** `src/api/auth/login.ts`, `src/services/auth.ts`

**Action:** Create POST endpoint accepting `{email, password}`. Validate email format and password length (8+ chars). Use bcrypt to compare against User table. Return JWT in httpOnly cookie with 15-min expiry. Use existing error pattern from CONVENTIONS.md (return `{error: string}` on 4xx).

**Verify:** `curl -X POST /api/auth/login -d '{"email":"test@example.com","password":"password123"}'` returns 200 with Set-Cookie header.

**Done:** Valid credentials return 200 + JWT cookie. Invalid credentials return 401 with `{error: "Invalid credentials"}`.
```

| Field | Purpose | Good Example | Bad Example |
|-------|---------|--------------|-------------|
| **Files** | Exact paths | `src/api/auth/login.ts` | "the auth files" |
| **Action** | Specific instructions | "Create POST endpoint accepting... validates using... returns..." | "Add authentication" |
| **Verify** | Proof of completion | `curl` returns 200 with Set-Cookie | "It works" |
| **Done** | Measurable criteria | "Valid credentials return 200 + JWT cookie" | "Authentication is complete" |

### Task Sizing

Each task should take a specialist agent **15-60 minutes** to execute:

| Duration | Action |
|----------|--------|
| < 15 min | Too small — combine with related task |
| 15-60 min | Right size — single focused unit |
| > 60 min | Too large — split into smaller tasks |

**Signals a task is too large:**
- Touches more than 5 files
- Has multiple distinct "chunks" of work
- The Action section is more than a paragraph

---

## Modes / Scenarios

Each mode has **default base instructions** that the subagent knows. You just specify the mode and any **specific additions**.

### Mode: `plan_refinement` (Wave 2)

**Default base instructions** (subagent knows this):
- Read `.planning/codebase/CONVENTIONS.md` first (decision patterns)
- Read `.planning/codebase/ARCHITECTURE.md` (understand structure)
- Read SEED-PLAN.md (what to build)
- Cross-reference approach
- Write detailed PLAN.md

**Your specific additions**:
```json
{
  "mode": "plan_refinement",
  "instructions": {
    "focus_on": ["api_endpoints", "database_changes"],
    "skip": ["frontend_changes"]
  }
}
```

### Mode: `plan_qa` (Wave 2.5) — NEW

**Default base instructions**:
- Read `.planning/codebase/CONCERNS.md`
- Read `.planning/codebase/CONVENTIONS.md`
- Read current PLAN.md
- Identify gaps, risks, and unclear assumptions
- Write QA-REPORT.md

**Your specific additions**:
```json
{
  "mode": "plan_qa",
  "instructions": {
    "focus_areas": ["error_handling", "edge_cases", "cross_service_contracts"]
  }
}
```

### Mode: `adjustment` (Wave 2b/4b)

For minor modifications to existing plans.

**Your specific additions**:
```json
{
  "mode": "adjustment",
  "instructions": {
    "goal": "Add pagination to the list endpoint",
    "base_plan": "Existing PLAN.md is mostly correct, just add pagination",
    "constraints": [
      "Keep existing filters",
      "Default page_size: 20",
      "Follow existing pattern in src/api/tools.py"
    ]
  }
}
```

### Mode: `quick_fix` (Wave 4b)

For small fixes after verification.

**Your specific additions**:
```json
{
  "mode": "quick_fix",
  "instructions": {
    "problem": "Test failing due to missing mock field",
    "fix": "Add 'branch_name' to mock in test_validation_email",
    "test_after_fix": True
  }
}
```

### Mode: `context_query` (Wave 2b)

For gathering info from services.

**Your specific additions**:
```json
{
  "mode": "context_query",
  "instructions": {
    "questions": [
      "What fields does GET /users/{id} return?",
      "Is branch_name nested in org or flat?"
    ]
  }
}
```

### Mode: `custom`

For any scenario not covered. You provide **complete instructions**.

```json
{
  "mode": "custom",
  "instructions": {
    "complete_instructions": "Read PLAN.md and CHANGES.md. The user wants to refactor the error handling to use a middleware approach instead of try-catch in each handler. Update both the implementation and the tests. Don't modify the API responses."
  }
}
```

---

## Wave-by-Wave Examples

### Wave 1: Service Mapping

```python
Task(
    subagent_name="agentbus map-codebase",
    description=f"Wave 1: Deep map {service}",
    prompt=json.dumps({
        "wave": 1,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "deep_mapping",
        "instructions": {
            "goal": "Generate 5 .planning/codebase/ documents",
            "focus": ["conventions", "patterns", "decision_matrix"]
        },
        "output": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

### Wave 1.5: Design Alignment

```python
# 1. Spawn parallel design-alignment agents
for service in services:
    Task(
        subagent_name="agentbus service agent",
        description=f"Wave 1.5: Validate design for {service}",
        prompt=json.dumps({
            "wave": 1.5,
            "service": {"name": service, "path": f"/workspace/{service}"},
            "mode": "design_alignment",
            "base_context": {
                "codebase_dir": f"/workspace/{service}/.planning/codebase",
                "seed_plan": f"/workspace/orchestrator/{plan_id}/SEED-PLAN.md"
            },
            "instructions": {
                "identify_conflicts": True,
                "suggest_alternatives": True
            },
            "output": {
                "design_alignment": f"/workspace/{service}/.agentbus-plans/{plan_id}/DESIGN-ALIGNMENT.md",
                "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-design.json"
            }
        }),
        readonly=False
    )

# 2. Consolidate conflicts from all summaries
conflicts = []
for service in services:
    summary = read_file(
        f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-design.json"
    )
    conflicts.extend(parse(summary)["conflicts"])

# 3. If high-severity conflicts exist, prompt user; otherwise proceed silently
if any(c["severity"] == "high" for c in conflicts):
    decisions = present_to_user(
        conflicts,
        checkpoint_type="checkpoint:decision"
    )
    # 4. Append approved approaches to SEED-PLAN so Wave 2 reads validated state
    append_approved_approaches(seed_plan_path, decisions)
```

---

### Wave 2: Plan Refinement (Standard)

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 2: Refine plan for {service}",
    prompt=json.dumps({
        "wave": 2,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "plan_refinement",
        "base_context": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase",
            "seed_plan": f"/workspace/orchestrator/{plan_id}/SEED-PLAN.md"
        },
        "instructions": {
            "validate_against_conventions": True
        },
        "output": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

### Wave 2 → 2b → Wave 2 retry: needs_context Flow

When a service agent in Wave 2 (or 2.5) discovers it cannot complete its work without information from another service, it returns `status: "needs_context"` in its summary JSON. The orchestrator detects this, runs Wave 2b (context queries) against the target services, and re-spawns the original agent with the answers.

**Step 1: Detect needs_context in the original Wave 2 result**

Service agent returns this in its summary JSON:

```json
{
  "wave": 2,
  "service": "cronjob-api",
  "status": "needs_context",
  "upstream_questions": [
    {"service": "users-api", "question": "What fields does GET /users/{id} return?"},
    {"service": "users-api", "question": "Is branch_name nested under organization or flat?"},
    {"service": "billing-api", "question": "What's the schema of the InvoiceCreated event?"}
  ]
}
```

**Step 2: Group questions by target service and validate prerequisites**

```python
from collections import defaultdict

questions_by_service = defaultdict(list)
for q in result["upstream_questions"]:
    questions_by_service[q["service"]].append(q["question"])

# Prerequisite: every target service MUST have .planning/codebase/ from Wave 1.
# If not, abort and instruct the user to run Wave 1 for that target first.
for target in questions_by_service.keys():
    codebase = f"{service_path(target)}/.planning/codebase"
    if not exists(codebase):
        abort(
            f"Cannot run Wave 2b: target service '{target}' has no "
            f".planning/codebase/. Run Wave 1 for '{target}' first."
        )
```

**Step 3: Spawn parallel context_query agents in target services**

```python
answers = {}
for target, questions in questions_by_service.items():
    Task(
        subagent_name="agentbus service agent",
        description=f"Wave 2b: Context query in {target}",
        prompt=json.dumps({
            "wave": "2b",
            "service": {"name": target, "path": service_path(target)},
            "mode": "context_query",
            "base_context": {
                "codebase_dir": f"{service_path(target)}/.planning/codebase"
            },
            "instructions": {
                "questions": questions,
                "asked_by": "cronjob-api",
                "for_plan": plan_id
            },
            "output": {
                # Note: written to ORCHESTRATOR workspace, NOT to a plan folder
                # in the target service. Adjacent services don't get plan folders.
                "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{target}-context.json"
            }
        }),
        readonly=False
    )
    answers[target] = parse(read_file(
        f"/workspace/orchestrator/{plan_id}/service-outputs/{target}-context.json"
    ))["answers"]
```

**Step 4: Re-spawn the original agent with answers in `additional_context`**

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 2 (retry with context): Refine plan for cronjob-api",
    prompt=json.dumps({
        "wave": 2,
        "service": {"name": "cronjob-api", "path": service_path("cronjob-api")},
        "mode": "plan_refinement",
        "base_context": {
            "codebase_dir": f"{service_path('cronjob-api')}/.planning/codebase",
            "seed_plan": f"/workspace/orchestrator/{plan_id}/SEED-PLAN.md"
        },
        "instructions": {
            "validate_against_conventions": True
        },
        "additional_context": {
            "upstream_answers": answers,
            "previous_attempt_status": "needs_context",
            "questions_resolved": True
        },
        "output": {
            "plan": f"{service_path('cronjob-api')}/.agentbus-plans/{plan_id}/PLAN.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/cronjob-api.json"
        }
    }),
    readonly=False
)
```

**Constraints**:

- ❌ A `context_query` agent that itself returns `needs_context` (transitive query) is NOT supported in v3. Abort and ask the user to break the dependency manually.
- ❌ Adjacent services queried via Wave 2b do NOT get a `.agentbus-plans/{plan-id}/` folder. Their answers live only in the orchestrator workspace.
- ✅ Wave 2b can run multiple times in a single plan if different services have different context needs.
- ✅ If the same target service is asked questions from multiple source agents, batch them into a single context_query call.

---

### Wave 2.5: Plan QA & Concerns (NEW)

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 2.5: QA plan for {service}",
    prompt=json.dumps({
        "wave": 2.5,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "plan_qa",
        "base_context": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase",
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md"
        },
        "instructions": {
            "focus_on_gaps": True,
            "focus_on_conventions": True
        },
        "output": {
            "qa_report": f"/workspace/{service}/.agentbus-plans/{plan_id}/QA-REPORT.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-qa.json"
        }
    }),
    readonly=False
)
```

### Wave 2: Plan Adjustment (Minor Change)

Example: User wants to add pagination to an endpoint already planned.

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 2b: Adjust plan for {service}",
    prompt=json.dumps({
        "wave": 2,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "adjustment",
        "base_context": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase",
            "existing_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md"
        },
        "instructions": {
            "goal": "Add pagination to GET /analytics/jobs endpoint",
            "base_plan": "Existing PLAN.md is correct, just add pagination support",
            "pagination_requirements": {
                "page_param": "page",
                "size_param": "page_size",
                "default_size": 20,
                "max_size": 100
            },
            "files_to_modify": [
                "src/api/analytics.py",
                "src/services/analytics.py",
                "tests/test_analytics.py"
            ]
        },
        "output": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-adjustment.json"
        }
    }),
    readonly=False
)
```

### Wave 3: Implementation (Standard)

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 3: Implement for {service}",
    prompt=json.dumps({
        "wave": 3,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "implementation",
        "base_context": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "codebase_dir": f"/workspace/{service}/.planning/codebase"
        },
        "instructions": {
            "no_commits": True,
            "test_each_change": True
        },
        "output": {
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

### Wave 2.6: Plan Alignment (Batch 1)

**Purpose**: Validate cross-service consistency at design level before implementation.

**No subagent** — Orchestrator reads PLAN.md files (which are artifacts, not code) directly:

```python
# 1. Read PLAN.md from each service
contracts = {}
for service in services:
    plan = read_file(f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md")
    contracts[service] = parse_contracts_from_plan(plan)

# 2. Cross-reference
issues = detect_cross_service_issues(contracts)

# 3. Generate report
write_file(
    f"/workspace/orchestrator/{plan_id}/PLAN-ALIGNMENT-REPORT.md",
    generate_alignment_report(issues)
)

# 4. If blockers found, present to user
if issues.blockers:
    ask_user_for_decisions(issues)
    apply_fixes_to_plans()  # Edit PLAN.md files via adjustment mode
    re_validate()
```

**Issues detected**:
- 🔴 Blocker: Endpoint path mismatch
- 🔴 Blocker: Field name mismatch (caller vs callee)
- 🔴 Blocker: HTTP method mismatch
- 🟡 Warning: Schema structure differences
- 🟢 Info: Extra fields

**UI Example**:
```
═══════════════════════════════════════════════════════════════
  WAVE 2.6: PLAN ALIGNMENT
═══════════════════════════════════════════════════════════════

Services analyzed: journey-api, cronjob-api

⚠️  2 blockers detected:

1. Endpoint Path Mismatch
   [journey-api] plans to call: POST /webhooks/analytics-complete
   [cronjob-api] exposes:       POST /analytics/internal/callback

2. Field Name Mismatch
   [journey-api] will send:  completed_at, error
   [cronjob-api] expects:    finished_at, error_message

Options:
  [v] View full report
  [f] Auto-fix — Align to cronjob convention
  [m] Manual — You specify the correct names
  [s] Skip — Proceed to Wave 3 (risky)

Your choice: _
```

---

### Wave 3.5: Contract Validation (Batch 2) — Optional

**Purpose**: Deep validation of implementation against contracts.

**When to use**: Complex features with >2 services or critical integrations.

**Input**: CHANGES.md + source code (queried via specialist agents, never read directly)

**Subagent**: Spawn specialist agents to analyze their own code:

```python
# Option A: Spawn agents to analyze their own services
for service in services:
    Task(
        subagent_name="agentbus service agent",
        description=f"Wave 3.5: Validate contracts for {service}",
        prompt=json.dumps({
            "wave": 3.5,
            "service": {"name": service, "path": f"/workspace/{service}"},
            "mode": "custom",
            "base_context": {
                "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
                "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md"
            },
            "instructions": {
                "complete_instructions": "Validate that the implemented code matches the planned contracts. Report any drift (method changes, field renames, missing validations, etc.)."
            },
            "output": {
                "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-validation.json"
            }
        }),
        readonly=False
    )

# Compare with planned contracts
issues = compare_planned_vs_actual(planned_contracts, validation_results)

# Generate report
write_file(
    f"/workspace/orchestrator/{plan_id}/CONTRACT-VALIDATION-REPORT.md",
    generate_validation_report(issues)
)
```

**Issues detected**:
- 🔴 Critical: Implementation drift (plan said POST, code does GET)
- 🔴 Critical: Type mismatch (plan said string, code uses int)
- 🟡 Warning: Hardcoded URL (should be config)
- 🟡 Warning: Timeout mismatch (caller 5s, callee 8s)

**UI Example**:
```
═══════════════════════════════════════════════════════════════
  WAVE 3.5: CONTRACT VALIDATION (Optional)
═══════════════════════════════════════════════════════════════

Analyzing actual implementation...

⚠️  1 critical issue detected:

CRIT-001: Implementation Drift
  Service: journey-api
  Location: src/api/analytics.py:45
  Plan specified: POST /analytics/internal/callback
  Implementation: GET /analytics/internal/callback
  Impact: 405 Method Not Allowed from cronjob

Options:
  [v] View full report with code diffs
  [f] Auto-fix — Change GET to POST
  [m] Manual — Review and fix yourself
  [i] Ignore — Proceed to Wave 4 (risky)
  [s] Skip Wave 3.5 — Don't run for this feature

Your choice: _
```

---

### Wave 4: Verification (Goal-Backward)

**Purpose**: Verify that the goal was achieved, not just that tasks completed.

**What happens**:
- Orchestrator spawns specialist agents in `verification` mode
- Each agent reads PLAN.md must_haves, CHANGES.md, and source code
- Performs 3-level verification: Exists → Substantive → Wired
- Writes VERIFICATION.md (primary output) with structured gaps
- Also writes TEST-RESULTS.md (test suite results)

**Outputs**:
- `{service}/.agentbus-plans/{plan-id}/VERIFICATION.md` — goal-backward verification with gaps
- `{service}/.agentbus-plans/{plan-id}/TEST-RESULTS.md` — test suite results

**Orchestrator reads VERIFICATION.md frontmatter** to decide next steps:

```python
for service in services:
    verification = read_file(f"/workspace/{service}/.agentbus-plans/{plan_id}/VERIFICATION.md")
    status = parse_frontmatter(verification)["status"]

    if status == "passed":
        mark_service_ready(service)
    elif status == "gaps_found":
        gaps = parse_frontmatter(verification)["gaps"]
        # Option A: Auto-fix small gaps via Wave 4b
        # Option B: Re-run Wave 3 for large gaps
        # Option C: Accept gaps and proceed (user decision)
    elif status == "human_needed":
        human_items = parse_frontmatter(verification)["human_verification"]
        present_to_user(human_items)
```

**Decision flow after Wave 4**:

```
All services passed?
  ├── YES → Ready for Wave 5 (or skip to user)
  └── NO → Any gaps auto-fixable?
            ├── YES → Wave 4b (quick fix) → Re-run Wave 4
            └── NO → Re-run Wave 3 (implementation) for affected services
```

**Re-verification mode**: If VERIFICATION.md already exists with gaps, the service agent enters re-verification mode:
- Failed items get full 3-level verification
- Passed items get quick regression check only
- Closed gaps are documented in `re_verification.gaps_closed`
- New regressions are documented in `re_verification.regressions`

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 4: Verify {service}",
    prompt=json.dumps({
        "wave": 4,
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "verification",
        "base_context": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "previous_verification": f"/workspace/{service}/.agentbus-plans/{plan_id}/VERIFICATION.md"
        },
        "instructions": {
            "run_tests": True,
            "verify_must_haves": True,
            "scan_antipatterns": True
        },
        "output": {
            "verification": f"/workspace/{service}/.agentbus-plans/{plan_id}/VERIFICATION.md",
            "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-verification.json"
        }
    }),
    readonly=False
)
```

---

### Wave 4b: Quick Fix & Adjustments

For small fixes after verification. Service agents apply Deviation Rules 1-3 automatically. Rule 4 (architectural) returns a checkpoint.

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 4b: Fix for {service}",
    prompt=json.dumps({
        "wave": "4b",
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "quick_fix",
        "base_context": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md"
        },
        "instructions": {
            "problem": "test_validation_email fails - missing branch_name in mock",
            "fix": "Add org.branch_name to mock response",
            "file": "tests/test_validation.py"
        },
        "output": {
            "changes_log_append": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-4b.json"
        }
    }),
    readonly=False
)
```

**If the service agent returns a checkpoint in Wave 4b**, present it to the user:
- `checkpoint:human-verify`: "The fix is applied. Please run the test to confirm."
- `checkpoint:decision`: "The fix reveals a deeper issue. Two options: [A] quick patch [B] proper refactor. Which one?"
- `checkpoint:human-action`: "The fix requires a manual database migration. Please run `npx prisma migrate dev` and type 'done'."

---

### Wave 5: Wrap-up (Optional)

**Purpose**: Create git commits with descriptive messages once verification has passed.

**Pre-flight gate**: Wave 5 MUST NOT run unless every service has `VERIFICATION.md` with `status: passed`. Abort otherwise.

**Critical safety rules** (the orchestrator enforces, the service agent obeys):

- ❌ Never push to remote without explicit user confirmation
- ❌ Never use `--force`, `--no-verify`, or skip pre-commit hooks
- ❌ Never amend commits already pushed
- ❌ Never commit if `VERIFICATION.md` status ≠ `passed`
- ✅ Each service commits its own changes locally only
- ✅ Push and PR creation are separate user actions, out of scope for v3

**What happens**:
1. Orchestrator reads every `VERIFICATION.md` and checks `status: passed`
2. If any service is not passed, abort and recommend Wave 4b
3. Orchestrator presents a `checkpoint:human-verify` summary to the user before commits
4. User confirms → orchestrator spawns parallel `wrap_up` agents (one per service)
5. Each agent writes one or more commits and a `COMMITS.md` log
6. Orchestrator consolidates and reports commit hashes back to the user

**Output**: `{service}/.agentbus-plans/{plan-id}/COMMITS.md`

```python
# Wave 5: Wrap-up

# 1. Pre-flight: every service must have passed Wave 4
for service in services:
    verification = read_file(
        f"/workspace/{service}/.agentbus-plans/{plan_id}/VERIFICATION.md"
    )
    status = parse_frontmatter(verification)["status"]
    if status != "passed":
        abort(
            f"[{service}] Wave 4 status is '{status}', not 'passed'. "
            f"Resolve via Wave 4b before Wave 5."
        )

# 2. Confirm with user (checkpoint:human-verify)
present_to_user(
    f"Ready to commit changes across {len(services)} services. "
    f"Each service will create commits locally (NOT push). Confirm?",
    checkpoint_type="checkpoint:human-verify"
)

# 3. Spawn wrap_up agents in parallel
for service in services:
    Task(
        subagent_name="agentbus service agent",
        description=f"Wave 5: Wrap up {service}",
        prompt=json.dumps({
            "wave": 5,
            "service": {"name": service, "path": f"/workspace/{service}"},
            "mode": "wrap_up",
            "base_context": {
                "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
                "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
                "verification": f"/workspace/{service}/.agentbus-plans/{plan_id}/VERIFICATION.md"
            },
            "instructions": {
                "commit_strategy": "per_task",  # or "single", "per_layer"
                "message_format": "conventional-commits",
                "no_push": True,
                "no_amend": True
            },
            "output": {
                "commits": f"/workspace/{service}/.agentbus-plans/{plan_id}/COMMITS.md",
                "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-commits.json"
            }
        }),
        readonly=False
    )

# 4. Consolidate and report
for service in services:
    summary = read_file(
        f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-commits.json"
    )
    report_commits_to_user(service, summary)
```

**UI Example after Wave 5**:

```
═══════════════════════════════════════════════════════════════
  WAVE 5: WRAP-UP COMPLETE
═══════════════════════════════════════════════════════════════

[payments-service] 2 commits on branch feat/004-audit-logging
  abc1234  feat(audit): add audit_log column to Payment model
  def5678  feat(audit): record payment events in audit_log

[notifications-service] 1 commit on branch feat/004-audit-logging
  9876fed  feat(audit): subscribe to audit_log events

⚠️  None of these commits have been pushed.
   To push:  cd <service> && git push -u origin HEAD
```

**If `commit_strategy` is unclear**, default to `per_task` (one commit per task in PLAN.md). This produces a clean history aligned with the plan structure.

### Custom Scenario: Refactor Error Handling

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Custom: Refactor error handling for {service}",
    prompt=json.dumps({
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "custom",
        "base_context": {
            "codebase_dir": f"/workspace/{service}/.planning/codebase",
            "existing_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md"
        },
        "instructions": {
            "complete_instructions": """
Refactor error handling in the analytics endpoints:

Current: Each handler has try-catch blocks
Target: Use centralized error middleware

Steps:
1. Read .planning/codebase/CONVENTIONS.md for error handling patterns
2. Look at src/middleware/error_handler.py (if exists) or create it
3. Update src/api/analytics.py to remove try-catch, let errors bubble up
4. Update tests to expect middleware handling
5. Ensure API responses remain the same (don't break contract)

Reference: See CHANGES.md lines 45-60 for current implementation.
"""
        },
        "output": {
            "changes_log_append": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}-refactor.json"
        }
    }),
    readonly=False
)
```

---

## Communicating with the User: Service Attribution

**CRITICAL**: When presenting code, plans, or issues to the user, always prefix with the service name.

❌ **Wrong**: "The endpoint returns a 404"
✅ **Right**: "`[journey-api]` The endpoint returns a 404"

❌ **Wrong**: "Add validation here"
✅ **Right**: "`[cronjob-api]` Add validation in src/api/jobs.py"

This prevents context loss when discussing multiple services.

---

## Status.json Schema (Updated)

```json
{
  "plan_id": "001-feature",
  "services": ["svc1", "svc2"],
  "current_wave": 2.5,
  "waves": {
    "wave_1_mapping": {"status": "completed"},
    "wave_1_5_design_alignment": {
      "status": "completed",
      "conflicts_resolved": 3,
      "user_decisions": [
        {
          "decision": "How to add audit_log column",
          "approved": "Prisma migration"
        }
      ]
    },
    "wave_2_refinement": {
      "status": "completed",
      "adjustments": [
        {
          "timestamp": "2024-01-15T10:30:00Z",
          "description": "Added pagination to analytics endpoint",
          "mode": "adjustment"
        }
      ]
    },
    "wave_2_5_qa": {"status": "completed"},
    "wave_2_6_alignment": {"status": "completed"},
    "wave_3_implementation": {"status": "pending"},
    "wave_3_5_contract_validation": {"status": "skipped"},
    "wave_4_verification": {
      "status": "pending",
      "is_re_verification": false
    },
    "wave_4b_adjustments": {"status": "not_started"},
    "wave_5_wrap_up": {
      "status": "not_started",
      "pre_flight_passed": null,
      "pushed": false
    }
  }
}
```

**Wave statuses**: `not_started` | `pending` | `in_progress` | `completed` | `failed` | `skipped` | `blocked`

---

## Anti-Patterns

❌ **Don't**: Use `mode: "custom"` when a standard mode exists
❌ **Don't**: Omit `base_context` — subagents need to know where files are
❌ **Don't**: Write vague instructions like "fix it"
❌ **Don't**: Assume subagent remembers previous waves
❌ **Don't**: Read source code directly — always delegate to specialist agents
❌ **Don't**: Present code references without service attribution

✅ **Do**: Use standard modes when possible
✅ **Do**: Provide specific, actionable instructions
✅ **Do**: Include file paths in base_context
✅ **Do**: Keep custom instructions concise but complete
✅ **Do**: Always consult specialist agents when you have doubts
✅ **Do**: Clearly label which service every code reference belongs to
