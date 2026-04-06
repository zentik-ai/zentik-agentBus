# Refactor Plan: AgentBus Markdown-First Orchestrator

## 1. Goal

Refactor AgentBus to a markdown-first system where:

- Skills are the source of truth for behavior.
- Orchestration is driven by instructions and subagents, not local helper scripts.
- Cross-service planning stays coherent across microservices.
- Verification happens at the end in two layers:
  - service-level verification (owned by service subagents)
  - global verification (owned by orchestrator)

## 1.1 Key Design Decisions (Consolidated)

| Aspect | Decision |
|--------|----------|
| **Orchestrator Location** | Lives at workspace level (parent folder of service repos), not inside a service repo |
| **Subagent Tool** | Uses `Task` tool (pattern from GSD) to spawn parallel subagents per service |
| **Wave Execution** | Sequential waves (Wave 1 → Wave 2 → Wave 3), each wave = new orchestrator invocation with fresh context |
| **Parallelism** | Services within a wave run in parallel via `Task` tool |
| **Context Format** | JSON passed directly to subagent prompt |
| **State Management** | `status.json` tracks progress per plan, enables resume/retry |
| **Plan Storage** | Seed plan → `.agentbus-orchestrator/XXX/plan.md`; Refined plan → `<service>/.agentbus-plans/XXX.md` (overwritten) |
| **Service Detection** | Docs-first (AGENTS.md, README.md, API.md), then code-signals (endpoints, event names), NO confidence scoring |
| **User Confirmation** | Orchestrator writes proposal to temp file, user confirms/adjusts list |
| **Retry Strategy** | Re-run failed subagent; if fails again, report clearly for manual resolution; update status.json to track |
| **Cross-Service Tests** | Generated as TEST-PLAN.md, executed locally by developer (docker-compose), NOT automated by orchestrator |
| **Add Service Mid-Flight** | Update status.json → mark wave as "needs_update" → re-run orchestrator for that wave |

## 2. Core principles

- Markdown first: all behavior contracts live in `SKILL.md` files.
- No additional scripts: no new Python or shell helper scripts for orchestration logic.
- Orchestrator as control-plane: it owns global context, dispatch, sequencing, and final decision.
- Subagents as specialists: each service subagent receives enough context to do meaningful work.
- Verification as a final gate: no implementation start until service-level and global checks pass.

## 3. Scope

### In scope

- Redesign skill protocols (`agentbus-orchestrator`, `agentbus-expert`, `agentbus-review`).
- Add explicit subagent lifecycle in orchestrator instructions.
- Define context package contract passed to each subagent.
- Define final verification protocol split by service and global layers.
- Update docs (`README.md`, `agentBus_PRD`, `agentBus_details.md`) to match behavior.

### Out of scope

- New scripts/tools for orchestration.
- Automatic code implementation by default.
- Full autonomous conflict resolution without user confirmation.

## 4. Target architecture

### 4.1 Core Principle: Evidence Over Communication

**Files are the source of truth.** El orquestador NO acumula estado en memoria. Cada wave produce artefactos que el orquestador puede consultar cuando necesita saber el estado global.

```
Wave 1 (Mapping)    →  Crea/actualiza AGENTS.md en cada servicio
Wave 2 (Refinement) →  Lee AGENTS.md + escribe PLAN.md refinado
Wave 3 (Verification) → Lee PLAN.md + escribe IMPLEMENTATION-REPORT.md
```

### 4.2 Orchestrator responsibilities (global)

- Parse user goal and constraints
- Detect likely impacted services (docs-first, then code-signals)
- Confirm service list with user (writes proposal to temp file)
- Launch service subagents via `Task` with minimal context
- **Read** (not receive) outputs from written artifacts
- Run final global verification by reading service artifacts
- Report readiness based on evidence

### 4.3 Service subagent responsibilities (local)

**Wave 1 (Mapping):**
- Map codebase: structure, APIs, DB, conventions
- **Write** `AGENTS.md` in service repo (creates/upgrades documentation)
- **Write** brief summary to orchestrator output folder

**Wave 2 (Refinement):**
- Read `AGENTS.md` (from Wave 1)
- Read seed plan from orchestrator
- Refine implementation plan with local knowledge
- **Write** `PLAN.md` to `<service>/.agentbus-plans/XXX-feature.md`
- **Write** key decisions summary to orchestrator output folder

**Wave 3 (Verification):**
- Read refined `PLAN.md`
- Verify completeness and identify blockers
- **Write** `IMPLEMENTATION-REPORT.md` in service repo
- **Write** verification status to orchestrator output folder

### 4.4 Review responsibilities

- Service-level verification: lee `IMPLEMENTATION-REPORT.md` de cada servicio
- Global verification: orquestador lee todos los reports y verifica consistencia cross-service
- Final go/no-go: basado en evidencia escrita, no en memoria

## 5. Context Contract (Minimal)

El subagente recibe solo lo necesario para saber QUÉ hacer. El CÓMO lo saca de los archivos.

### Wave 1 (Mapping) Context
```json
{
  "wave": 1,
  "wave_name": "mapping",
  "service_name": "tools-service",
  "service_path": "/workspace/tools-service",
  "outputs": {
    "agents_md": "/workspace/tools-service/AGENTS.md",
    "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/tools-service.json"
  }
}
```

### Wave 2 (Refinement) Context
```json
{
  "wave": 2,
  "wave_name": "refinement",
  "service_name": "tools-service",
  "service_path": "/workspace/tools-service",
  "inputs": {
    "agents_md": "/workspace/tools-service/AGENTS.md",
    "seed_plan": "/workspace/agentbus-orchestrator/001-feature/SEED-PLAN.md"
  },
  "outputs": {
    "refined_plan": "/workspace/tools-service/.agentbus-plans/001-feature.md",
    "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/tools-service.json"
  }
}
```

### Wave 3 (Verification) Context
```json
{
  "wave": 3,
  "wave_name": "verification",
  "service_name": "tools-service",
  "service_path": "/workspace/tools-service",
  "inputs": {
    "refined_plan": "/workspace/tools-service/.agentbus-plans/001-feature.md",
    "other_service_plans": {
      "bot-service": "/workspace/bot-service/.agentbus-plans/001-feature.md"
    }
  },
  "outputs": {
    "implementation_report": "/workspace/tools-service/.agentbus-plans/001-feature-REPORT.md",
    "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/tools-service.json"
  }
}
```

### Subagent Summary JSON (mínimo, para status tracking)

El subagente escribe un JSON breve para que el orquestador pueda actualizar `status.json` sin leer archivos grandes:

```json
{
  "status": "completed|failed|needs_clarification",
  "artifacts_written": [
    "/workspace/tools-service/AGENTS.md",
    "/workspace/tools-service/.agentbus-plans/001-feature.md"
  ],
  "key_findings": ["Tool model has 3 consumers", "API v2 ready for breaking change"],
  "blockers": [],
  "unresolved_questions": []
}
```

## 6. End-to-end workflow (Evidence-Based)

### Phase 1: Intake & Discovery (Orchestrator)

1. **Parse request** - User provides feature description and candidate services
2. **Load service docs** - Read AGENTS.md, README.md, API.md from candidate services (si existen)
3. **Detect impact** - Docs-first analysis + code-signals (endpoints, events, imports)
4. **Propose service list** - Write to temp file for user review
5. **User confirmation** - User confirms/adjusts service list

### Phase 2: Seed Planning (Orchestrator)

6. **Create orchestrator workspace**:
   ```
   workspace/agentbus-orchestrator/001-feature/
   ├── status.json              # tracking
   ├── SEED-PLAN.md             # visión global inicial
   └── service-outputs/         # donde los subagentes escriben resúmenes
   ```
7. **Write SEED-PLAN.md** - One sección por servicio confirmado
8. **Initialize status.json** with wave 1 ready
9. **Report** - "Wave 1 ready: Run orchestrator again to start mapping"

### Phase 3: Wave 1 - Service Mapping (Orchestrator + Subagents)

**Orchestrator actions:**
- Load status.json, verify wave 1 is next
- Build minimal context package for each service (solo paths y wave)
- Spawn parallel subagents via `Task` tool
- **Wait** for all subagents to complete
- **Read** summary JSON files from `service-outputs/`
- Update status.json (mark wave 1 complete, wave 2 ready)
- Report: "AGENTS.md created/updated in N services"

**Subagent responsibilities:**
- Map codebase: read structure, APIs, DB schemas, conventions
- **Write** `AGENTS.md` to service repo (or update if exists)
- **Write** brief summary JSON to `service-outputs/{service}.json`

**Artefactos producidos:**
- `{service}/AGENTS.md` - Documentación del servicio (actualizada)
- `agentbus-orchestrator/001-feature/service-outputs/{service}.json` - Resumen para tracking

### Phase 4: Wave 2 - Plan Refinement (Orchestrator + Subagents)

**Orchestrator actions:**
- Load status.json, verify wave 1 complete
- Read AGENTS.md summaries from Wave 1 outputs
- Build context package for each service (incluye paths a AGENTS.md y SEED-PLAN)
- Spawn parallel subagents via `Task`
- **Wait** for completion
- **Read** summary JSON files
- Update status.json (mark wave 2 complete, wave 3 ready)

**Subagent responsibilities:**
- **Read** `AGENTS.md` (su propio servicio, escrito en Wave 1)
- **Read** sección de SEED-PLAN.md para su servicio
- Refinar plan con detalles de implementación local
- **Write** `PLAN.md` to `<service>/.agentbus-plans/001-feature.md`
- **Write** summary JSON con cambios y riesgos identificados

**Artefactos producidos:**
- `{service}/.agentbus-plans/001-feature.md` - Plan refinado por servicio
- `agentbus-orchestrator/001-feature/service-outputs/{service}.json` - Actualizado

### Phase 5: Wave 3 - Verification (Orchestrator + Subagents)

**Orchestrator actions:**
- Load status.json, verify wave 2 complete
- Collect all refined plan paths from status
- Build context package (incluye paths a todos los PLAN.md)
- Spawn parallel subagents via `Task`
- **Wait** for completion
- **Read** IMPLEMENTATION-REPORT.md de cada servicio
- Run global verification (cross-service consistency check)
- Update status.json
- Generate final outputs leyendo los reports

**Subagent responsibilities:**
- **Read** refined `PLAN.md` (su propio servicio)
- **Read** PLAN.md de servicios relacionados (si hay dependencias)
- Verificar: ¿plan completo? ¿tests identificados? ¿blockers?
- **Write** `IMPLEMENTATION-REPORT.md` a `{service}/.agentbus-plans/001-feature-REPORT.md`
- **Write** verification status JSON

**Artefactos producidos:**
- `{service}/.agentbus-plans/001-feature-REPORT.md` - Reporte de implementación
- `agentbus-orchestrator/001-feature/service-outputs/{service}.json` - Final

### Phase 6: Final Report (Orchestrator)

Lee todos los IMPLEMENTATION-REPORT.md y genera:
- `PLAN.md` - Consolidated global view (síntesis de todos los planes)
- `TEST-PLAN.md` - Estrategia de tests cross-service
- `DEPLOY-ORDER.md` - Secuencia de rollout
- Readiness status basado en evidencia escrita

## 7. File Structure (Evidence-Based)

```
workspace/                          # parent folder containing all service repos
├── agentbus-orchestrator/          # orchestrator workspace (NOT a git repo)
│   └── XXX-feature-slug/
│       ├── status.json             # state machine for resume/retry
│       ├── SEED-PLAN.md            # initial vision (written by orchestrator)
│       ├── PLAN.md                 # consolidated global view (síntesis final)
│       ├── TEST-PLAN.md            # cross-service test strategy
│       ├── DEPLOY-ORDER.md         # rollout sequence
│       └── service-outputs/        # minimal JSON summaries from subagents
│           ├── payments-service.json
│           └── notifications-service.json
│
├── payments-service/               # service repo
│   ├── AGENTS.md                   # ← CREADO/ACTUALIZADO en Wave 1
│   └── .agentbus-plans/
│       ├── XXX-feature-slug.md              # ← refined plan (Wave 2)
│       └── XXX-feature-slug-REPORT.md       # ← implementation report (Wave 3)
│
└── notifications-service/          # service repo
    ├── AGENTS.md                   # ← CREADO/ACTUALIZADO en Wave 1
    └── .agentbus-plans/
        ├── XXX-feature-slug.md
        └── XXX-feature-slug-REPORT.md
```

### Descripción de Artefactos

| Artefacto | Escrito por | Leído por | Propósito |
|-----------|-------------|-----------|-----------|
| `AGENTS.md` | Subagente Wave 1 | Subagente Waves 2-3 | Documentación del servicio (stack, arquitectura, convenciones) |
| `SEED-PLAN.md` | Orchestrator | Subagente Wave 2 | Visión inicial del feature por servicio |
| `XXX-feature.md` | Subagente Wave 2 | Subagente Wave 3, Orchestrator | Plan refinado con detalles de implementación |
| `XXX-feature-REPORT.md` | Subagente Wave 3 | Orchestrator | Verificación: tests, riesgos, blockers |
| `service-outputs/{service}.json` | Subagente (todas waves) | Orchestrator | Tracking mínimo para status.json |
| `status.json` | Orchestrator | Orchestrator | Estado del plan, permite resume/retry |

## 8. Status.json Schema (Tracking Only)

`status.json` NO contiene el contenido de los planes, solo tracks de dónde están los artefactos.

```json
{
  "plan_id": "001-remove-field",
  "feature_slug": "remove-field",
  "feature_description": "Remove deprecated field from Tool model",
  "created_at": "2026-04-06T12:00:00Z",
  "updated_at": "2026-04-06T14:30:00Z",
  "status": "in_progress|failed|completed|needs_retry",
  "services": ["tools-service", "bot-service"],
  
  "waves": {
    "wave_1_mapping": {
      "status": "completed",
      "started_at": "...",
      "completed_at": "...",
      "artifacts": {
        "tools-service": {
          "agents_md": "/workspace/tools-service/AGENTS.md",
          "summary_json": "/workspace/agentbus-orchestrator/001-remove-field/service-outputs/tools-service.json"
        },
        "bot-service": {
          "agents_md": "/workspace/bot-service/AGENTS.md",
          "summary_json": "..."
        }
      }
    },
    "wave_2_refinement": {
      "status": "in_progress",
      "started_at": "...",
      "artifacts": {
        "tools-service": {
          "refined_plan": "/workspace/tools-service/.agentbus-plans/001-remove-field.md",
          "summary_json": "..."
        },
        "bot-service": {
          "status": "failed",
          "error": "Unable to locate Tool client code",
          "retries": 1,
          "retry_at": "..."
        }
      }
    },
    "wave_3_verification": {
      "status": "pending",
      "artifacts": {}
    }
  },
  
  "global_decisions": [
    {"decision": "Remove field in v2 API only", "rationale": "...", "affects": [...]}
  ],
  "open_questions": [
    {"question": "...", "owner": "tools-service", "blocking": true}
  ]
}
```

## 9. Verification Model (Evidence-Based)

### 9.1 Service-level verification (subagent-owned)

Wave 3 subagent **escribe** IMPLEMENTATION-REPORT.md con estructura:

```markdown
# Implementation Report: 001-remove-field

## Service: tools-service

### Verification Status
- Status: ready|needs_work|blocked
- Blockers: []

### Implementation Summary
- Affected files: src/api/tools.ts, src/db/migrations/...
- API changes: Remove "deprecated" field from Tool response
- DB changes: Migration to drop column

### Tests Required
- Unit: test/tools.test.ts
- Integration: test/api.integration.test.ts
- E2E: None (covered by consumer tests)

### Local Risks
| Risk | Mitigation | Owner |
|------|------------|-------|
| Cache may have old format | Add cache invalidation on deploy | tools-service |

### Dependencies on Other Services
- bot-service: Must update client before field removal

### Rollback Plan
- Migration is reversible
- Feature flag to disable if needed
```

Service-level pass criteria:
- Status is "ready"
- IMPLEMENTATION-REPORT.md exists and is complete
- All blockers have mitigations assigned
- Tests are identified by file path

### 9.2 Global verification (orchestrator-owned)

Orchestrator **lee** todos los IMPLEMENTATION-REPORT.md y verifica:

1. **Plan completeness** - All services have REPORT.md
2. **Dependency mirroring** - Si Service A depende de B, el report de B menciona el cambio
3. **Contract consistency** - API changes documentadas en ambos lados (productor y consumidor)
4. **Question ownership** - Cada unresolved question tiene owner en algún report
5. **Sequencing coherence** - El orden de deploy es lógico (no hay "deploy A antes de B" y "deploy B antes de A")

Global pass criteria:
- Todos los service-level reports tienen status "ready"
- No hay contradicciones cross-service
- Las dependencias están documentadas en ambos servicios
- Hay un DEPLOY-ORDER.md coherente

Si falla:
- Update status.json con servicios que necesitan re-procesamiento
- User re-runs orchestrator para wave específica

## 10. File-by-file refactor tasks

### 10.1 `skills/agentbus-orchestrator/SKILL.md`

- Define workspace-level location (not inside service repo)
- Document **evidence-based** principle: orchestrator reads artifacts, doesn't accumulate state
- Document wave-based execution (Wave 1 → 2 → 3)
- Document `Task` tool usage for parallel subagent spawning
- Define **minimal** context package (only paths, no content)
- Define status.json schema (tracking only, no content)
- Document service detection (docs-first, code-signals)
- Document user confirmation flow (temp file → review → proceed)
- Document retry strategy and mid-flight service addition
- Document **artifact reading** protocol: orchestrator reads AGENTS.md, PLAN.md, REPORT.md
- Add final verification section (reads all REPORT.md, generates global view)
- Keep ask/discovery behavior but clarify it does not write plans

### 10.2 `skills/agentbus-service-agent/SKILL.md` (replaces agentbus-expert)

- New skill: service-level specialist subagent
- Document **evidence-based** output: writes files, doesn't return data
- Define per-wave behavior:
  - **Wave 1**: Read codebase → **Write** AGENTS.md → Write summary JSON
  - **Wave 2**: Read AGENTS.md + SEED-PLAN → **Write** PLAN.md → Write summary JSON  
  - **Wave 3**: Read PLAN.md + other service PLANs → **Write** REPORT.md → Write summary JSON
- Define AGENTS.md template (stack, architecture, components, testing, conventions)
- Define PLAN.md template (overview, changes, testing, dependencies, rollback)
- Define REPORT.md template (status, checklist, risks, cross-service impact)
- Ensure it never assumes global ownership
- Document: if AGENTS.md exists, update it; if not, create it

### 10.3 `skills/agentbus-review/SKILL.md`

- Convert to markdown-first review protocol
- Define review checklist for cross-service consistency
- Document reading of REPORT.md files (not JSON responses)
- Keep outputs structured so orchestrator can aggregate

### 10.4 `README.md`

- Update architecture section: orchestrator + wave-based subagent execution
- Document workspace-level orchestrator setup
- Document **AGENTS.md** as key artifact for knowledge sharing
- Add "How verification works" section
- Add "No helper scripts required for orchestration logic" note
- Keep installation and usage examples aligned with actual skills

### 10.5 `agentBus_PRD`

- Update design section to evidence-based orchestration model
- Add explicit verification model and ownership split
- Document artifact-based communication (AGENTS.md → PLAN.md → REPORT.md)
- Add acceptance criteria for service/global verification flow
- Remove script-first assumptions from core orchestration behavior

### 10.6 `agentBus_details.md`

- Update implementation details to match evidence-based lifecycle
- Add AGENTS.md template and generation guidelines
- Add PLAN.md and REPORT.md templates
- Document status.json schema (tracking only)
- Remove contradictions with PRD and README
- Add section: "Why evidence-based?" (context efficiency, auditability, resume capability)

## 11. Migration strategy

### Phase 1: Protocol-first refactor

- Update `agentbus-orchestrator/SKILL.md` with **evidence-based** wave protocol
- Create new `agentbus-service-agent/SKILL.md` with AGENTS.md/PLAN.md/REPORT.md templates
- Update `agentbus-review/SKILL.md` for markdown-first review
- Keep existing scripts temporarily but mark as deprecated
- Confirm all docs are internally consistent

### Phase 2: AGENTS.md generation test

- Test Wave 1 on one service with NO existing AGENTS.md
- Verify subagent creates proper AGENTS.md structure
- Test Wave 1 on service WITH existing AGENTS.md
- Verify subagent updates/enriches AGENTS.md correctly
- Check status.json tracks artifact paths correctly

### Phase 3: Single-service full flow

- Test all 3 waves on single service
- Verify: AGENTS.md → PLAN.md → REPORT.md chain
- Orchestrator reads artifacts to build final view
- Validate resume/retry via status.json

### Phase 4: Multi-service dry-run

- Test full 3-wave flow on 2-service feature (e.g., "remove tool field")
- Validate parallel subagent spawning via `Task`
- Verify cross-service references in REPORT.md
- Test adding service mid-flight (update status.json, re-run wave)

### Phase 5: Verification hardening

- Enforce REPORT.md format
- Ensure orchestrator reads REPORT.md files (not JSON)
- Test global verification by reading cross-service artifacts
- Test retry: re-run Wave 2, verify PLAN.md gets overwritten

### Phase 6: Cleanup

- Remove script dependencies from skill instructions
- Archive/deprecate scripts not needed in markdown-first operation
- Update README with final usage examples
- Document AGENTS.md as ongoing service documentation

## 12. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Subagents receive incomplete context | Required context contract with hard-stop behavior; subagent must reject if missing fields |
| Orchestrator over/under-selects services | User confirmation loop (no auto-proceed); clear temp file with proposed services |
| Inconsistent plan formats across services | Strict output template in service-agent instructions; JSON schema validation |
| False confidence before implementation | Final verification gate with explicit pass/fail criteria; cross-service test plan generation |
| Wave fails mid-flight | status.json tracks progress; subagent-level retry; user can re-run specific wave |
| Adding service mid-flight breaks state | status.json supports dynamic service addition; re-run wave with updated service list |
| Parallel subagents conflict | Each subagent writes to own service repo only; no shared write locations |
| Context window exhaustion in subagent | Each wave gets fresh context; subagent only sees its service scope |

## 13. Definition of done

Refactor is complete when:

- [ ] orchestrator runs 3-wave subagent-driven flow end-to-end
- [ ] Wave 1: subagents create/update `AGENTS.md` in each service
- [ ] Wave 2: subagents read `AGENTS.md` + write `PLAN.md` in each service
- [ ] Wave 3: subagents read `PLAN.md` + write `REPORT.md` in each service
- [ ] orchestrator **reads** (not receives) artifacts to build global view
- [ ] orchestrator emits global verification result and readiness status
- [ ] status.json tracks artifact paths (not content)
- [ ] docs (`README.md`, `agentBus_PRD`, `agentBus_details.md`) match actual behavior
- [ ] no core orchestration step requires helper scripts
- [ ] dry-run on 2-service feature completes successfully
- [ ] AGENTS.md templates work for services with/without existing docs

## 14. Suggested execution order (practical)

1. **Refactor `agentbus-orchestrator/SKILL.md`** - Wave-based protocol, Task tool usage, status.json
2. **Create `agentbus-service-agent/SKILL.md`** - New subagent skill (replaces agentbus-expert)
3. **Update `agentbus-review/SKILL.md`** - Markdown-first review protocol
4. **Sync PRD/details/README** - Ensure consistency
5. **Phase 2 dry-run** - Single service, Wave 1 only
6. **Phase 3 dry-run** - Two services, all 3 waves
7. **Adjust templates** - Fix gaps observed in dry-runs
8. **Phase 4-5** - Verification hardening and cleanup

---

## Appendix A: Artefact Examples

### AGENTS.md (produced by Wave 1)

```markdown
# tools-service — Agent Guide

Generated: 2026-04-06

## Technology Stack
- Node.js 20, Express
- PostgreSQL 15 with Drizzle ORM
- Redis for caching

## Architecture
- Layered: routes → controllers → services → repositories
- API versioning: /v1/, /v2/

## Key Components
| Component | Path | Purpose |
|-----------|------|---------|
| Tool API | src/api/tools.ts | CRUD for Tool model |
| Tool Service | src/services/toolService.ts | Business logic |
| Tool Repository | src/repositories/toolRepo.ts | DB access |

## API Endpoints
- GET /v1/tools — List all tools
- GET /v1/tools/:id — Get single tool
- POST /v1/tools — Create tool

## Database
- Table: tools (id, name, description, deprecated, created_at)
- deprecated: boolean, nullable, flagged for removal

## Testing
- Unit: vitest, files in test/unit/
- Integration: test/integration/
- E2E: Not implemented

## Conventions
- Use repository pattern for DB access
- Controllers handle HTTP only, no business logic
```

### PLAN.md (produced by Wave 2)

```markdown
# Plan: Remove deprecated field from Tool (001-remove-field)

## Service: tools-service

### Overview
Remove the "deprecated" boolean field from the Tool model and API responses.

### Changes Required

#### 1. Database Migration
- File: `migrations/20260406_remove_deprecated.sql`
- Action: ALTER TABLE tools DROP COLUMN deprecated
- Rollback: ADD COLUMN deprecated BOOLEAN NULL

#### 2. API Changes
- Files: `src/api/tools.ts`, `src/services/toolService.ts`
- Remove "deprecated" from response DTOs
- Keep v1 compatibility: return null instead of field

#### 3. Code Updates
- Remove from TypeScript interfaces: `src/types/tool.ts`
- Update repository queries: `src/repositories/toolRepo.ts`

### Testing Strategy
- Unit: Update toolService.test.ts
- Integration: Update api.integration.test.ts
- Migration test: Verify rollback works

### Dependencies
- bot-service consumes this API — coordinate deploy order

### Rollback Plan
1. Re-run migration (reversible)
2. Deploy previous code version
```

### IMPLEMENTATION-REPORT.md (produced by Wave 3)

```markdown
# Implementation Report: 001-remove-field

## Service: tools-service

### Verification Status
✅ **Status: ready**
- No blockers identified
- All tests identified

### Implementation Checklist
- [x] Migration script created and tested
- [x] API changes documented
- [x] Unit tests updated
- [x] Integration tests identified

### Files to Modify
| File | Change Type | Test Coverage |
|------|-------------|---------------|
| migrations/20260406_remove_deprecated.sql | New | Migration test |
| src/types/tool.ts | Remove field | Unit |
| src/api/tools.ts | Remove from DTO | Integration |

### Local Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| Cache inconsistency | Add TTL=0 on deploy | Mitigated |

### Cross-Service Impact
- bot-service: Must deploy client update BEFORE this change
- Deploy order: bot-service → tools-service

### Estimated Effort
- 2 hours implementation
- 1 hour testing

### Open Questions
- None
```
