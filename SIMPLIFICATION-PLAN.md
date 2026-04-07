# Plan de Simplificación: AgentBus Skill Base

## Objetivo
Convertir `skills/agentbus/SKILL.md` en un **router/documentador ligero** (~80 líneas) que delegue todo flujo de ejecución al orchestrator. Eliminar redundancia con `orchestrator/SKILL.md`.

## Cambios a Realizar

### 1. `skills/agentbus/SKILL.md` — Simplificación Mayor

**ESTRUCTURA FINAL:**
```yaml
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
| `agentbus/orchestrator` | Coordina waves cross-service | `/agentbus-orchestrator ...` |
| `agentbus/service-agent` | Especialista por servicio | Spawned vía Task (interno) |
| `agentbus/review` | Verifica consistencia cross-service | `/agentbus-review ...` |

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

- **Protocolo completo**: `@skills/agentbus/orchestrator/SKILL.md`
- **Service agent**: `@skills/agentbus/service-agent/SKILL.md`
- **Review**: `@skills/agentbus/review/SKILL.md`

---

## Version

AgentBus Skills v1.0.0
```

---

**CONTENIDO A ELIMINAR de agentbus/SKILL.md:**

- ❌ Sección "Core Philosophy" detallada (ya está en orchestrator)
- ❌ Sección "Delegación" con explicaciones largas
- ❌ "Quick Start Commands" detallado (se reduce a tabla simple)
- ❌ "Wave Execution Model" completo (solo tabla resumen)
- ❌ "Limitaciones" (mover a orchestrator)
- ❌ "Workspace Structure" completo (solo referencia)
- ❌ "Prerequisites" con instrucciones detalladas (solo link)
- ❌ "Typical Workflow" paso a paso de 7 fases (eliminar)
- ❌ "Error Handling & Recovery" detallado (mover a orchestrator)
- ❌ "Key Concepts" de AGENTS.md/PLAN.md/etc (mover a orchestrator)
- ❌ "Anti-Patterns to Avoid" duplicado (ya está en orchestrator)

---

### 2. `skills/agentbus/orchestrator/SKILL.md` — Cambios Mínimos

**AGREGAR al inicio:**
```markdown
## Skill Base vs Orchestrator

- **Skill Base** (`agentbus/SKILL.md`): Router/documentador. Decide si tu caso aplica para AgentBus.
- **Este archivo (orchestrator)**: Protocolo completo de ejecución. Toda la lógica de waves, spawn de subagentes, y manejo de errores.
```

**VERIFICAR que contenga:**
- ✅ Explicación de cuándo NO usar agentbus (single-service)
- ✅ Referencia a skills alternativas (gsd, spec-kit)
- ✅ Toda la documentación de waves, status.json, etc.

---

### 3. Archivos a Modificar

| Archivo | Cambio | Líneas Aprox |
|---------|--------|--------------|
| `skills/agentbus/SKILL.md` | Reescribir completamente | 80 líneas (de 384) |
| `skills/agentbus/orchestrator/SKILL.md` | Agregar nota skill base vs orchestrator | +5 líneas |

---

## Criterios de Éxito

- [ ] `agentbus/SKILL.md` tiene < 100 líneas
- [ ] Skill base claramente diferenciado de orchestrator
- [ ] Usuario sabe cuándo usar agentbus vs otras skills
- [ ] No hay información duplicada entre skill base y orchestrator
- [ ] Links funcionan entre documentos

---

## Notas de Implementación

1. Mantener mismo YAML frontmatter en skill base
2. Preservar versión (1.0.0)
3. No modificar service-agent ni review (están bien)
4. README.md del proyecto puede necesitar ajustes menores si referenciaba secciones específicas del skill base antiguo
