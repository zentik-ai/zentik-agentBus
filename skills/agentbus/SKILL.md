---
name: agentbus
description: Cross-service planning system for multi-service features. Entry point that routes to orchestrator for all execution.
triggers: [cross-service feature, multi-service planning]
tools: [Read, Task]
tags: [agentbus, orchestration, cross-service]
---

# AgentBus Skills

Sistema de planificación cross-service para features que tocan **2+ microservicios**.

---

## ¿Cuándo USAR AgentBus?

✅ **SÍ - Usa AgentBus:**
- Feature que modifica 2+ servicios (ej: "migrar sync a async entre payments y notifications")
- Refactor de API que afecta productores y consumidores
- Cambio de schema que impacta múltiples repos

❌ **NO - Usa otras skills:**
- Cambio en **un solo servicio** → Usa `gsd` o `spec-kit`
- Solo explorar un codebase → Usa `map-codebase` directo en el repo

---

## Arquitectura

```
┌─────────────────────────────────────┐
│  agentbus (skill base)              │  ← Este archivo
│  └── Solo documenta y routea        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  agentbus/orchestrator              │  ← Entry point de ejecución
│  ├── Spawnea service-agents         │
│  ├── Coordina waves                 │
│  └── Maneja status.json             │
└─────────────────────────────────────┘
```

| Componente | Rol | Invocación |
|------------|-----|------------|
| `agentbus-orchestrator` | Coordina waves cross-service | `/agentbus-orchestrator ...` |
| `agentbus/service-agent` | Especialista por servicio | Spawned vía Task (interno) |
| `agentbus-review` | Verifica consistencia cross-service | `/agentbus-review ...` |

---

## Comandos Principales

### Descubrimiento (solo lectura)
```
/agentbus-orchestrator --ask "cómo funciona el flow de pagos?" payments notifications
```

### Inicializar Plan
```
/agentbus-orchestrator "migrar a eventos async" payments notifications inventory
```
Crea: `agentbus-orchestrator/001-feature/status.json` + `SEED-PLAN.md`

### Continuar Waves
```
/agentbus-orchestrator --continue 001-feature
```
Ejecuta la siguiente wave basada en `status.json`.

### Verificar Consistencia
```
/agentbus-review --feature-slug 001-feature
```

---

## Modelo de 5 Waves

| Wave | Nombre | Output | Descripción |
|------|--------|--------|-------------|
| 1 | Service Mapping | `AGENTS.md` | Entiende cada servicio |
| 2 | Plan Refinement | `PLAN.md` | Plan detallado por servicio |
| 3 | Implementation | Código + `CHANGES.md` | Modifica código (no commits) |
| 4 | Verification | `TEST-RESULTS.md` | Corre tests |
| 5 | Wrap-up (opt) | `COMMITS.md` | Commits post-verificación |

**Importante:** Corre **una wave a la vez**. Revisa resultados antes de continuar.

---

## Primeros Pasos

### 1. Verificar Service Registry
```bash
# Lee ~/.agentbus/services.json
# Debe contener los servicios que vas a usar
```

### 2. Ejecutar Flujo
```
# Paso 1: Inicializar
/agentbus-orchestrator "descripción del feature" svc1 svc2

# Paso 2: Wave 1 (Mapping)
/agentbus-orchestrator --continue 001-feature-slug

# Paso 3: Revisar AGENTS.md generados
# (Opcional: /agentbus-review --feature-slug ...)

# Paso 4-N: Continuar waves restantes
/agentbus-orchestrator --continue 001-feature-slug
```

---

## Documentación Detallada

- **Protocolo completo**: `@skills/agentbus-orchestrator/SKILL.md`
- **Service agent**: `@skills/agentbus-service-agent/SKILL.md`
- **Review**: `@skills/agentbus-review/SKILL.md`

---

## Version

AgentBus Skills v1.0.0
