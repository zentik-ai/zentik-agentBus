---
name: agentbus orchestrator
description: Cross-service planning orchestrator for AgentBus. Coordinates multi-wave planning across microservices using evidence-based workflow. Updated for Deep Mapping (5-document AGENTS/ folder).
version: 2.0.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado para coordinar waves.

## Wave Flow (Updated for Deep Mapping)

```
Wave 1: Service Mapping    →  AGENTS/ (5 docs via map-codebase)
Wave 1.5: Design Alignment →  Validated approach decisions
Wave 2: Plan Refinement    →  PLAN.md
Wave 3: Implementation     →  Code modified (no commits yet)
Wave 4: Verification       →  TEST-RESULTS.md
Wave 5: Wrap-up (optional) →  Git commits + final deployment prep
```

## Service Detection & Fuzzy Matching

Uses fuzzy matching against `~/.agentbus/services.json`:
- Exact match: 100 puntos
- Substring match: 80 puntos
- Abreviatura match: 70 puntos

## Execution Model: Sequential Waves, Parallel Services

Each wave spawns N subagents in parallel, waits, reads summaries, updates status.

---

## End-to-End Workflow

### Phase 4: Wave 1 — Service Mapping (Deep Mapping)

Launch `agentbus map-codebase` for each service:

```python
Task(
    subagent_name="agentbus map-codebase",
    description=f"Wave 1: Deep map {service}",
    prompt=json.dumps({
        "service_name": service,
        "service_path": f"/workspace/{service}",
        "outputs": {
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

Generates 5 documents per service:
- STACK.md — Technology stack
- ARCHITECTURE.md — Patterns and data flow
- STRUCTURE.md — Directory layout
- CONVENTIONS.md — Implementation patterns (CRITICAL)
- CONCERNS.md — Tech debt and risks

### Phase 5: Wave 1.5 — Design Alignment Checkpoint

Validates that approaches in SEED-PLAN match patterns in CONVENTIONS.md.

**Heuristics applied:**
| Scenario | Preferred Approach |
|----------|-------------------|
| Schema change (ALTER TABLE) | Migration |
| Dynamic data (permissions) | API Endpoint |
| Environment-specific values | API/Config |
| Static reference data | Migration/Seed |

If conflicts detected, presents to user:
```
═══════════════════════════════════════════════════════════════
  DESIGN ALIGNMENT CHECKPOINT
═══════════════════════════════════════════════════════════════

Servicio: [service]
Cambio: [description]

Approach propuesto: [A]
Alternativa detectada: [B]
Sugerencia: [B]

Opciones:
  [A] Mantener approach propuesto
  [B] Usar alternativa (recomendado)
  [C] Otra: _

Tu elección: _
```

Records decision in `service-outputs/{service}-dac.json`

### Phase 6: Wave 2 — Plan Refinement

Launch `agentbus service agent` with inputs:
- `agents_dir` — Path to 5 AGENTS/ documents
- `seed_plan` — Original/adjusted plan
- `design_decisions` — Wave 1.5 decisions (optional)

### Phase 7: Wave 3 — Implementation

Launch `agentbus service agent` to modify code (no commits).

### Phase 8: Wave 4 — Verification

Launch `agentbus service agent` to run tests and verify.

### Phase 9: Wave 4b — Adjustments (Optional)

Explain mode or quick_fix mode for minor adjustments.

### Phase 10: Wave 5 — Wrap-up (Optional)

Create git commits after user confirmation.

---

## Status.json Schema (Updated)

```json
{
  "plan_id": "001-feature",
  "services": ["svc1", "svc2"],
  "current_wave": 2,
  "waves": {
    "wave_1_mapping": {
      "status": "completed",
      "artifacts": {
        "svc1": {
          "agents_dir": "/workspace/svc1/.agentbus/AGENTS",
          "documents": ["STACK.md", "ARCHITECTURE.md", "STRUCTURE.md", "CONVENTIONS.md", "CONCERNS.md"]
        }
      }
    },
    "wave_1_5_design_alignment": {
      "status": "completed",
      "decisions_made": 1
    },
    "wave_2_refinement": {"status": "in_progress"},
    "wave_3_implementation": {"status": "pending"},
    "wave_4_verification": {"status": "pending"},
    "wave_5_wrapup": {"status": "pending", "optional": true}
  }
}
```

## Anti-Patterns

- Don't skip Wave 1.5 without user explicit consent
- Don't spawn subagents without `readonly=False` if they need to write
- Don't accumulate state in context — read artifacts instead
