---
name: agentbus orchestrator
description: Cross-service planning orchestrator for AgentBus. Coordinates multi-wave planning across microservices using evidence-based workflow. Updated for Deep Mapping (5-document AGENTS/ folder).
version: 2.2.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado para coordinar waves.

## Core Principle: Explicit but Flexible Instructions

**Subagents CANNOT see your context.** You must tell them what to do, but keep it flexible enough for different scenarios:

1. **Base Context** — Always provided (AGENTS/ docs, PLAN.md, etc.)
2. **Specific Instructions** — Varies by scenario (refinement, fix, adjustment, etc.)
3. **User Context** — Optional additional context from user

---

## Wave Flow (Updated for Deep Mapping + Two-Batch Consistency)

```
Wave 1: Service Mapping         →  AGENTS/ (5 docs via map-codebase)
Wave 1.5: Design Alignment      →  Validated approach decisions
Wave 2: Plan Refinement         →  PLAN.md
Wave 2.5: Plan Alignment        →  Batch 1: High-level consistency (PLAN.md)
Wave 3: Implementation          →  Code modified (no commits)
Wave 3.5: Contract Validation   →  Batch 2: Deep consistency (code) - Optional
Wave 4: Verification            →  TEST-RESULTS.md
Wave 5: Wrap-up (optional)      →  Git commits + final deployment prep
```

### Two-Batch Consistency Check

**Batch 1 (Wave 2.5): Plan Alignment** — Always run
- **Input**: PLAN.md de cada servicio
- **Detecta**: Diseño desalineado (paths, field names, métodos)
- **Costo de fix**: Bajo (editar PLAN.md)
- **Cuándo**: Pre-implementación

**Batch 2 (Wave 3.5): Contract Validation** — Optional
- **Input**: CHANGES.md + código implementado
- **Detecta**: Drift de implementación, type mismatches
- **Costo de fix**: Medio (modificar código)
- **Cuándo**: Post-implementación, para features complejos

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
            "agents_dir": "/workspace/service/.agentbus/AGENTS",
            "plan": "/workspace/service/.agentbus-plans/001-feature/PLAN.md",
            "changes": "/workspace/service/.agentbus-plans/001-feature/CHANGES.md"
        },
        
        # 2. MODE / SCENARIO (determines base instructions)
        "mode": "plan_refinement",  # or "adjustment", "quick_fix", "context_query", etc.
        
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

## Modes / Scenarios

Each mode has **default base instructions** that the subagent knows. You just specify the mode and any **specific additions**.

### Mode: `plan_refinement` (Wave 2)

**Default base instructions** (subagent knows this):
- Read CONVENTIONS.md first (decision patterns)
- Read ARCHITECTURE.md (understand structure)
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

For gathering info from other services.

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
            "goal": "Generate 5 AGENTS/ documents",
            "focus": ["conventions", "patterns", "decision_matrix"]
        },
        "output": {
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "summary": f"/workspace/orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

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
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
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
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
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
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",  # Update in place
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
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS"
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


### Wave 2.5: Plan Alignment (Batch 1)

**Purpose**: Validate cross-service consistency at design level before implementation.

**No subagent** — Orchestrator does this directly by reading PLAN.md files:

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
    apply_fixes_to_plans()  # Edit PLAN.md files
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
  WAVE 2.5: PLAN ALIGNMENT
═══════════════════════════════════════════════════════════════

Servicios analizados: journey-api, cronjob-api

⚠️  2 blockers detectados:

1. Endpoint Path Mismatch
   Journey planea llamar: POST /webhooks/analytics-complete
   Cronjob expone:        POST /analytics/internal/callback

2. Field Name Mismatch
   Journey enviará:  completed_at, error
   Cronjob espera:   finished_at, error_message

Opciones:
  [v] Ver reporte completo
  [f] Auto-fix — Alinear a convención de cronjob
  [m] Manual — Especificar tú los nombres correctos
  [s] Skip — Proceder a Wave 3 (riesgoso)

Tu elección: _
```

---


### Wave 3.5: Contract Validation (Batch 2) — Optional

**Purpose**: Deep validation of implementation against contracts.

**When to use**: Complex features with >2 services or critical integrations.

**Input**: CHANGES.md + source code

**Subagent**: Specialized contract validator or orchestrator analysis:

```python
# Option A: Orchestrator does analysis directly
for service in services:
    changes = read_file(f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md")
    actual_contracts = analyze_source_code(service, changes)
    
# Compare with planned contracts
issues = compare_planned_vs_actual(planned_contracts, actual_contracts)

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

Análisis de implementación real...

⚠️  1 critical issue detectado:

CRIT-001: Implementation Drift
  Location: journey-api/src/api/analytics.py:45
  Plan specified: POST /analytics/internal/callback
  Implementation: GET /analytics/internal/callback
  Impact: 405 Method Not Allowed from cronjob

Opciones:
  [v] Ver reporte completo con code diffs
  [f] Auto-fix — Cambiar GET a POST
  [m] Manual — Revisar y fixear tú
  [i] Ignorar — Proceder a Wave 4 (riesgoso)
  [s] Skip Wave 3.5 — No ejecutar para este feature

Tu elección: _
```

---

### Wave 4b: Quick Fix

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

### Custom Scenario: Refactor Error Handling

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Custom: Refactor error handling for {service}",
    prompt=json.dumps({
        "service": {"name": service, "path": f"/workspace/{service}"},
        "mode": "custom",
        "base_context": {
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "existing_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md"
        },
        "instructions": {
            "complete_instructions": """
Refactor error handling in the analytics endpoints:

Current: Each handler has try-catch blocks
Target: Use centralized error middleware

Steps:
1. Read CONVENTIONS.md for error handling patterns
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

## Status.json Schema (Updated)

```json
{
  "plan_id": "001-feature",
  "services": ["svc1", "svc2"],
  "current_wave": 2,
  "waves": {
    "wave_1_mapping": {"status": "completed"},
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
    "wave_3_implementation": {"status": "pending"}
  }
}
```

---

## Anti-Patterns

❌ **Don't**: Use `mode: "custom"` when a standard mode exists
❌ **Don't**: Omit `base_context` — subagents need to know where files are
❌ **Don't**: Write vague instructions like "fix it"
❌ **Don't**: Assume subagent remembers previous waves

✅ **Do**: Use standard modes when possible
✅ **Do**: Provide specific, actionable instructions
✅ **Do**: Include file paths in base_context
✅ **Do**: Keep custom instructions concise but complete
