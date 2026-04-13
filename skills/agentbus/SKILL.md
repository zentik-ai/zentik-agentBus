---
name: agentbus
description: Cross-service planning system for multi-service features. Entry point that routes to orchestrator for all execution. Updated for Deep Mapping (AGENTS/ folder + Wave 1.5).
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
│  agentbus orchestrator              │  ← Entry point de ejecución
│  ├── Spawnea map-codebase (Wave 1)  │
│  ├── Design Alignment (Wave 1.5)    │
│  ├── Spawnea service-agents         │
│  └── Coordina waves                 │
└─────────────────────────────────────┘
```

| Componente | Rol | Invocación |
|------------|-----|------------|
| `agentbus orchestrator` | Coordina waves cross-service | `/agentbus orchestrator ...` |
| `agentbus map-codebase` | Deep mapping (5 documentos) | Spawned en Wave 1 |
| `agentbus service agent` | Especialista por servicio | Spawned vía Task (interno) |
| `agentbus review` | Verifica consistencia cross-service | `/agentbus review ...` |

---

## Comandos Principales

### Descubrimiento (solo lectura)
```
/agentbus orchestrator --ask "cómo funciona el flow de pagos?" payments notifications
```

### Inicializar Plan
```
/agentbus orchestrator "migrar a eventos async" payments notifications inventory
```
Crea: `agentbus-orchestrator/001-feature/status.json` + `SEED-PLAN.md`

### Continuar Waves
```
/agentbus orchestrator --continue 001-feature
```
Ejecuta la siguiente wave basada en `status.json`.

### Verificar Consistencia
```
/agentbus review --feature-slug 001-feature
```

---

## Modelo de Waves (Deep Mapping)

| Wave | Nombre | Output | Descripción |
|------|--------|--------|-------------|
| 1 | Service Mapping | `AGENTS/` (5 docs) | Deep mapping del servicio |
| 1.5 | Design Alignment | Decisiones validadas | Checkpoint de approach |
| 2 | Plan Refinement | `PLAN.md` | Plan detallado por servicio |
| 2b | Context Queries | Respuestas | Consulta servicios adyacentes |
| 3 | Implementation | Código + `CHANGES.md` | Modifica código (no commits) |
| 4 | Verification | `TEST-RESULTS.md` | Corre tests |
| 4b | Adjustments (opt) | Ajustes | Fixes menores y aclaraciones |
| 5 | Wrap-up (opt) | `COMMITS.md` | Commits post-verificación |

**Importante:** Corre **una wave a la vez**. Revisa resultados antes de continuar.

### Deep Mapping (Wave 1)

En lugar de un único `AGENTS.md`, Wave 1 genera **5 documentos especializados** en `.agentbus/AGENTS/`:

| Documento | Contenido | Uso |
|-----------|-----------|-----|
| `STACK.md` | Tech stack, dependencias | Qué tecnologías usar |
| `ARCHITECTURE.md` | Patrones, capas, flujo | Cómo estructurar cambios |
| `STRUCTURE.md` | Layout de carpetas | Dónde crear archivos |
| `CONVENTIONS.md` | Patterns disponibles, cuándo usarlos | **Qué approach usar** |
| `CONCERNS.md` | Tech debt, riesgos | Qué evitar |

**CONVENTIONS.md es crítico**: Captura los patterns disponibles en el codebase y ayuda a elegir el mejor approach cuando hay múltiples opciones.

### Design Alignment Checkpoint (Wave 1.5)

Nuevo checkpoint que valida que los approaches propuestos en `SEED-PLAN` son los mejores disponibles según `CONVENTIONS.md`.

**Heurísticas aplicadas:**
| Escenario | Preferencia |
|-----------|-------------|
| Schema change (ALTER TABLE) | Migración SQL |
| Datos dinámicos (permisos, configs) | API Endpoint |
| Datos por ambiente | API/Config |
| Datos estáticos de referencia | Migración/Seed |

Si se detecta conflicto, se presenta al usuario para decisión antes de continuar a Wave 2.

### Context Queries (Wave 2b)

Durante el planning, si un service-agent necesita información de otros servicios (ej: "¿qué devuelve el endpoint de users-api?"), puede solicitar **context queries**.

**Flujo**:
1. Service-agent detecta necesidad → Escribe PLAN provisional
2. Reporta `status: "needs_context"` con queries pendientes
3. Orchestrator spawnea **query-only agents** en servicios adyacentes
4. Re-ejecuta service-agent con el contexto obtenido
5. Completa PLAN.md final

**Ventaja**: No mapeas servicios que no modificas, pero obtienes contexto preciso cuando lo necesitas.

### Adjustments (Wave 4b)

Después de Wave 4 (tests), si hay fallos menores o necesitas aclaraciones:

**Modo Explain**:
- Pregunta: "¿Por qué falla este test?"
- Service-agent investiga y explica (read-only)

**Modo Quick Fix**:
- Ajuste menor: "Arregla el mock en el test"
- Fix de typo, validación, import faltante
- **No** cambios arquitectónicos grandes
- Se apenda a CHANGES.md
- Re-corre tests afectados

---

## Primeros Pasos

### 1. Verificar Service Registry
```bash
# Lee ~/.agentbus/services.json
# Debe contener los servicios que vas a usar
```

### 2. Plan ID Auto-Generado
El orchestrator escanea `.agentbus-plans/` en cada servicio para:
- Encontrar el número de plan más alto existente
- Sugerir el siguiente número secuencial (sin gaps)
- Validar consistencia entre todos los servicios

Ejemplo: Si existe `003-feature`, el nuevo será `004-nuevo-feature`.

### 3. Ejecutar Flujo
```
# Paso 1: Inicializar (auto-detecta número de plan)
/agentbus orchestrator "descripción del feature" svc1 svc2

# Paso 2: Wave 1 (Deep Mapping - 5 documentos)
/agentbus orchestrator --continue 004-feature-slug

# Paso 3: Wave 1.5 (Design Alignment Checkpoint)
#         Se ejecuta automáticamente, puede pedir input

# Paso 4-N: Continuar waves restantes
/agentbus orchestrator --continue 004-feature-slug
```

---

## Documentación Detallada

- **Protocolo completo**: `@skills/agentbus orchestrator/SKILL.md`
- **Map Codebase**: `@skills/agentbus map-codebase/SKILL.md`
- **Service agent**: `@skills/agentbus service agent/SKILL.md`
- **Review**: `@skills/agentbus review/SKILL.md`

---

## Version

AgentBus Skills v2.0.0 (Deep Mapping)
