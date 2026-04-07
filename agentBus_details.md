# AgentBus Skills — Implementation Plan (v0.4)

**Para usar junto con el PRD v0.4**
**Fecha:** Abril 2026

---

## Principio Clave: Evidencia sobre Comunicación

En lugar de acumular estado en el contexto del orquestador, cada wave produce artefactos que pueden ser leídos cuando se necesiten.

```
Wave 1 (Mapeo)      →  AGENTS.md en cada servicio
Wave 2 (Refinamiento) →  PLAN.md en cada servicio
Wave 3 (Verificación) →  REPORT.md en cada servicio
Final: Orquestador lee REPORTs → Vista global
```

Beneficios:
- **Eficiencia de contexto**: El orquestador solo lee lo que necesita
- **Auditabilidad**: Historial completo en archivos versionables
- **Resumibilidad**: Waves fallidas pueden reintentarse independientemente
- **Reusabilidad**: AGENTS.md sirve como documentación continua del servicio

---

## Estructura del Workspace

```
workspace/                          # folder padre
├── agentbus-orchestrator/          # workspace del orquestador (NO es git repo)
│   └── 001-feature-slug/
│       ├── status.json             # tracking de estado
│       ├── SEED-PLAN.md            # visión inicial
│       ├── PLAN.md                 # vista consolidada
│       ├── TEST-PLAN.md            # tests cross-service
│       ├── DEPLOY-ORDER.md         # secuencia de rollout
│       └── service-outputs/        # resúmenes JSON de subagentes
│           ├── payments-service.json
│           └── notifications-service.json
│
├── payments-service/               # repo de servicio
│   ├── AGENTS.md                   # ← escrito en Wave 1
│   └── .agentbus-plans/
│       ├── 001-feature-slug.md         # ← escrito en Wave 2
│       └── 001-feature-slug-REPORT.md  # ← escrito en Wave 3
│
└── notifications-service/
    └── ... (misma estructura)
```

---

## Flujo de Waves

### Wave 1: Mapeo de Servicio

**Input**: Contexto mínimo (paths, wave number)
**Tareas del subagente**:
1. Explorar estructura del codebase
2. Identificar: stack, arquitectura, componentes, APIs, DB, testing
3. **Escribir** AGENTS.md (crear o actualizar si existe)
4. **Escribir** resumen JSON

**Output**:
- `{service}/AGENTS.md` — Documentación del servicio
- `service-outputs/{service}.json` — Para tracking

### Wave 2: Refinamiento del Plan

**Input**: Paths a AGENTS.md (propio) y SEED-PLAN.md
**Tareas del subagente**:
1. **Leer** AGENTS.md para entender el servicio
2. **Leer** SEED-PLAN.md para contexto
3. Explorar archivos relevantes
4. Crear plan de implementación detallado
5. **Escribir** PLAN.md al repo del servicio
6. **Escribir** resumen JSON

**Output**:
- `{service}/.agentbus-plans/{feature}.md` — Plan refinado
- `service-outputs/{service}.json` — Actualizado

### Wave 3: Verificación

**Input**: Paths a PLAN.md (propio) y PLANs de servicios relacionados
**Tareas del subagente**:
1. **Leer** PLAN.md del servicio
2. **Leer** PLANs de servicios dependientes
3. Verificar completitud e identificar bloqueos
4. **Escribir** IMPLEMENTATION-REPORT.md
5. **Escribir** resumen JSON

**Output**:
- `{service}/.agentbus-plans/{feature}-REPORT.md` — Reporte de verificación
- `service-outputs/{service}.json` — Actualizado

---

## Templates de Artefactos

### AGENTS.md Template

```markdown
# {service-name} — Agent Guide

Generated: YYYY-MM-DD

## Technology Stack
- Language: [e.g., Node.js 20, Python 3.11]
- Framework: [e.g., Express, FastAPI]
- Database: [e.g., PostgreSQL 15]
- Cache: [e.g., Redis]
- Key Dependencies: [list]

## Architecture
- Pattern: [e.g., Layered, Hexagonal]
- Directory Structure:
  ```
  src/
  ├── api/          # HTTP routes/controllers
  ├── services/     # Business logic
  └── ...
  ```

## Key Components
| Component | Path | Purpose |
|-----------|------|---------|
| [Name] | `[path]` | [What it does] |

## API Endpoints
- `METHOD /path` — [description]

## Database Schema
- Table: [name] ([fields])

## Testing
- Framework: [e.g., vitest, pytest]
- Unit: [location]
- Integration: [location]

## Conventions
- [Code style, naming conventions]

## External Integrations
- [Other services this one calls]
```

### PLAN.md Template

```markdown
# Plan: {feature-name} ({plan-id})

## Service: {service-name}

### Overview
[What this feature does in this service]

### Changes Required

#### 1. [Category]
- Files: `[path1]`, `[path2]`
- Action: [Specific change]
- Rollback: [How to undo]

### Testing Strategy
- Unit: [files]
- Integration: [files]

### Dependencies
- Other services: [list]
- Order: [e.g., "Deploy after X"]

### Rollback Plan
[Steps to revert]
```

### REPORT.md Template

```markdown
# Implementation Report: {plan-id}

## Service: {service-name}

### Verification Status
- Status: ready|needs_work|blocked
- Blockers: [list or "None"]

### Implementation Checklist
- [x] All files identified
- [x] Steps documented
- [ ] Tests identified

### Files to Modify
| File | Change Type | Test Coverage |
|------|-------------|---------------|
| `src/api.ts` | Modify | Integration |

### Local Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| [Description] | [Action] | Mitigated |

### Cross-Service Impact
- Depends on: [services]
- Required by: [services]
- Deploy order: [sequence]

### Open Questions
- [Question, owner, blocking status]
```

---

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

---

## Estrategia de Reintento

1. **Subagente falla**:
   - Escribir error en status.json
   - Reportar al usuario

2. **Reintentar**:
   - Re-ejecutar orchestrator para la wave
   - Subagente sobreescribe sus artefactos
   - Otros servicios no se modifican

3. **Agregar servicio mid-flight**:
   - Actualizar status.json con nuevo servicio
   - Marcar servicio como "pending" para wave actual
   - Re-ejecutar orchestrator
   - Solo el nuevo servicio se procesa

---

## Scripts Legacy (Opcional)

Los scripts Python existen para registro de servicios pero NO son necesarios para la orquestación core:

```bash
# Registro de servicios (legacy, opcional)
uv run scripts/register_service.py payments-service /path/to/service
uv run scripts/list_services.py --json
```

El flujo evidence-based NO requiere scripts:
- Orchestrator usa `Task` tool para subagentes
- Subagentes escriben archivos directamente
- Orchestrator lee archivos directamente

---

## ¿Por qué Evidence-Based?

| Problema | Solución |
|----------|----------|
| Contexto del orquestador crece con N servicios | Orquestador solo lee resúmenes JSON |
| No hay historial de decisiones | AGENTS.md → PLAN.md → REPORT.md es audit trail |
| Fallo en un servicio requiere empezar de cero | status.json permite reanudar wave específica |
| Documentación del servicio es estática | AGENTS.md se actualiza en cada Wave 1 |
| Comunicación orquestador-subagente es compleja | Solo se pasan paths, no datos |
