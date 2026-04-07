---
name: agentbus/orchestrator
description: Cross-service planning orchestrator for AgentBus. Coordinates multi-wave planning across microservices using evidence-based workflow.
version: 1.0.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado para coordinar waves.

## Core Principle: Evidence Over Communication

**Files are the source of truth.** You don't accumulate state—you read artifacts when you need to know the status.

```
Wave 1: Subagents write AGENTS.md       ← Mapping (understand service)
Wave 2: Subagents write PLAN.md         ← Refinement (plan the change)
Wave 3: Subagents modify code + commits ← Implementation (execute plan) ⚠️ DESTRUCTIVE
Wave 4: Subagents run tests             ← Verification (verify it works)
```

**⚠️ Wave 3 Warning**: Wave 3 modifies source code and makes git commits. Ensure services are on feature branches before running.

## When to Use

User invokes: `/agentbus-orchestrator "feature description" service1 service2 ...`

Or: `/agentbus-orchestrator --continue 001-feature` (resume from status.json)

## Limitaciones

- **Solo coordina, no implementa detalles de servicio**: La implementación específica va en `agentbus/service-agent`.
- **No acumula estado en contexto**: Debe leer artefactos, no mantener estado en memoria.
- **Requiere `agentbus/service-agent` disponible**: El subskill debe estar accesible para invocación vía Task tool.
- **Wave 3 modifica código**: Asegúrate de que los servicios estén en feature branches antes de ejecutar Wave 3.
- **Confirma Wave 3 con usuario**: Wave 3 es destructiva. Pide confirmación explícita antes de ejecutar.
- **No toma decisiones de arquitectura**: Presenta opciones, el usuario decide.

## Execution Model: Sequential Waves, Parallel Services

```
Wave 1 (Mapping)
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 2 (Refinement)
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 3 (Implementation) ⚠️ DESTRUCTIVE
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 4 (Verification)
  └─► Spawn N subagents in parallel ──► Wait ──► Read reports ──► Global verify
```

Each wave is a separate invocation. You run Wave 1, wait for user to continue, then run Wave 2, etc.

## End-to-End Workflow

### Phase 1: Intake & Discovery

1. **Parse request**
   - Feature description (what to build)
   - Candidate services (from user or registry)

2. **Detect service impact** (docs-first)
   - Read existing AGENTS.md from candidate services (if exists)
   - Read README.md, API.md, CLAUDE.md
   - Search for code-signals: endpoints, event names, imports between services
   - Propose list of affected services

3. **User confirmation**
   - Write proposed services to temp file: `/tmp/agentbus-XXX-proposed-services.txt`
   - Ask user to confirm/adjust
   - Finalize service list

### Phase 2: Initialize Plan

4. **Create orchestrator workspace**:
   ```
   agentbus-orchestrator/001-feature-slug/
   ├── status.json
   ├── SEED-PLAN.md
   └── service-outputs/
   ```

5. **Write SEED-PLAN.md** with:
   - Feature description
   - One section per service with initial understanding
   - Cross-service interactions (guessed)

6. **Initialize status.json**:
   ```json
   {
     "plan_id": "001-remove-field",
     "feature_slug": "remove-field",
     "services": ["tools-service", "bot-service"],
     "status": "initialized",
     "current_wave": null,
     "waves": {
       "wave_1_mapping": {"status": "ready"},
       "wave_2_refinement": {"status": "pending"},
       "wave_3_implementation": {"status": "pending", "destructive": true},
       "wave_4_verification": {"status": "pending"}
     }
   }
   ```

7. **Report to user**: "Wave 1 ready. Run orchestrator again to start mapping."

### Phase 3: Wave 1 — Service Mapping

8. **Check status.json**: Verify wave 1 is "ready"

9. **Launch parallel subagents** via `Task` tool:
   ```python
   for service in services:
       Task(
           subagent_name="agentbus/service-agent",
           description=f"Wave 1: Map {service}",
           prompt=json.dumps({
               "wave": 1,
               "service_name": service,
               "service_path": f"/workspace/{service}",
               "outputs": {
                   "agents_md": f"/workspace/{service}/AGENTS.md",
                   "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
               }
           })
       )
   ```

10. **Wait** for all subagents to complete

11. **Read** summary JSON files from `service-outputs/`

12. **Update status.json**:
    - Mark wave 1 as "completed"
    - Record artifact paths
    - Mark wave 2 as "ready"

13. **Report**: Summary of AGENTS.md created/updated

### Phase 4: Wave 2 — Plan Refinement

14. **Check status.json**: Verify wave 1 is "completed"

15. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 2: Refine plan for {service}",
        prompt=json.dumps({
            "wave": 2,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "agents_md": f"/workspace/{service}/AGENTS.md",
                "seed_plan": f"/workspace/agentbus-orchestrator/{plan_id}/SEED-PLAN.md"
            },
            "outputs": {
                "refined_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        })
    )
    ```

16. **Wait**, **read** summaries, **update** status.json

17. **Report**: Summary of plans refined

### Phase 5: Wave 3 — Implementation ⚠️ DESTRUCTIVE

18. **⚠️ CONFIRM WITH USER BEFORE PROCEEDING**:
    - Warn: "Wave 3 will modify source code and make git commits."
    - Verify: "Ensure all services are on feature branches, not main/master."
    - Ask: "¿Proceder con Wave 3? (yes/no)"

19. **Check status.json**: Verify wave 2 is "completed"

20. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 3: Implement changes for {service}",
        prompt=json.dumps({
            "wave": 3,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}.md",
                "agents_md": f"/workspace/{service}/AGENTS.md"
            },
            "outputs": {
                "commit_log": f"/workspace/{service}/.agentbus-plans/{plan_id}-COMMITS.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        })
    )
    ```

21. **Wait**, **read** summaries, **update** status.json

22. **Report**: Summary of commits made per service

### Phase 6: Wave 4 — Verification

23. **Check status.json**: Verify wave 3 is "completed"

24. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 4: Verify implementation for {service}",
        prompt=json.dumps({
            "wave": 4,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "commit_log": f"/workspace/{service}/.agentbus-plans/{plan_id}-COMMITS.md",
                "other_services": [s for s in services if s != service]
            },
            "outputs": {
                "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}-TEST-RESULTS.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        })
    )
    ```

25. **Wait**, **read** summaries

26. **Read** all TEST-RESULTS.md files for global verification

27. **Run Global Verification**:
    - All services pass tests
    - Cross-service dependencies work
    - API contracts are respected

28. **Write Final Artifacts**:
    - `DEPLOY-ORDER.md` — Rollout sequence with verified commits

29. **Update status.json**: Mark as "completed"

30. **Final Report**:
    - Implementation status per service
    - Test results summary
    - Deploy readiness
    - Recommended next step: deploy to staging/production

## Error Handling & Retries

### If a subagent fails

1. Read its summary JSON for error details
2. Update status.json:
   ```json
   {
     "services": {
       "bot-service": {
         "status": "failed",
         "error": "...",
         "retries": 1
       }
     }
   }
   ```
3. Report failure to user
4. On retry: Re-run orchestrator for same wave (subagent will overwrite artifacts)

### If user wants to add service mid-flight

1. Update status.json to add service
2. Mark current wave as "needs_update" for that service
3. Re-run orchestrator for that wave
4. Only the new service gets processed

### If you need to resume

1. Read status.json
2. Determine current wave from status
3. Continue from there

## Status.json Schema

```json
{
  "plan_id": "001-feature",
  "feature_slug": "feature",
  "feature_description": "...",
  "services": ["svc1", "svc2"],
  "status": "in_progress",
  "current_wave": 2,
  "waves": {
    "wave_1_mapping": {
      "status": "completed",
      "artifacts": {
        "svc1": {
          "agents_md": "/workspace/svc1/AGENTS.md",
          "summary_json": ".../svc1.json"
        }
      }
    },
    "wave_2_refinement": {
      "status": "in_progress",
      "artifacts": {}
    },
    "wave_3_verification": {
      "status": "pending"
    }
  }
}
```

## Discovery: Code-Signals

When AGENTS.md doesn't exist, detect service impact by searching:

1. **Endpoint patterns**: Look for route definitions
   ```bash
   grep -r "app\.(get|post|put|delete)" --include="*.ts" --include="*.js"
   ```

2. **Event/topic names**: Look for message queue usage
   ```bash
   grep -r "kafka\|rabbitmq\|event\|emit" --include="*.ts" --include="*.py"
   ```

3. **Inter-service imports**: Look for client libraries
   ```bash
   grep -r "from.*payments\|import.*notifications" --include="*.ts"
   ```

4. **API clients**: Look for HTTP client usage
   ```bash
   grep -r "axios\|fetch\|requests" --include="*.ts" --include="*.py"
   ```

Document findings in proposed services list.

## Global Verification Checklist

After Wave 3, read all REPORT.md and verify:

- [ ] All services have REPORT.md with status "ready"
- [ ] Dependencies: If Service A lists dependency on B, Service B mentions A
- [ ] API contracts: Breaking changes documented by producer AND consumer
- [ ] Deploy order: No circular dependencies
- [ ] Open questions: All have owners assigned
- [ ] Rollback plans: Present for risky changes

If any check fails, report which services need re-processing.

## Output Artifacts

You produce:
1. **status.json** — Tracking for resume/retry
2. **SEED-PLAN.md** — Initial vision
3. **PLAN.md** — Consolidated view (synthesis of service plans)
4. **TEST-PLAN.md** — Cross-service test strategy
5. **DEPLOY-ORDER.md** — Rollout sequence

## Anti-Patterns

❌ **Don't**: Accumulate detailed knowledge in your context
❌ **Don't**: Ask subagents to return data in response text
❌ **Don't**: Write implementation details in status.json
❌ **Don't**: Assume services without AGENTS.md are unimportant
✅ **Do**: Read artifacts when you need to know something
✅ **Do**: Write clear, actionable final reports
✅ **Do**: Let subagents own service-level details
