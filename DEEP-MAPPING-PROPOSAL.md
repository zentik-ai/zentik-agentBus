# Deep Service Mapping + Design Alignment Checkpoint

## Resumen Ejecutivo

**Contexto que inspiró este cambio:**
Durante la implementación del plan `003-journey-analytics-dashboard`, detectamos que el approach propuesto en el SEED-PLAN (migración SQL para crear un permiso) no era el óptimo dado el contexto del servicio (existía un endpoint API que era más apropiado para datos dinámicos). El agente no detectó esta alternativa porque el AGENTS.md monolítico no estructura la información de "patterns disponibles" vs "cuándo usarlos".

**Principio general:**
El problema fundamental es que AGENTS.md acumula información de todo tipo (stack, arquitectura, convenciones, deuda técnica) en un solo documento, dificultando que los agentes tomen decisiones informadas sobre qué approach usar en situaciones donde hay múltiples opciones válidas.

**Solución:**
Separar el mapeo en 5 documentos especializados, donde CONVENTIONS.md capture explícitamente los patterns disponibles y cuándo usarlos. Agregar un Design Alignment Checkpoint entre el mapeo y la planificación para validar que el approach propuesto es el mejor disponible.

---

## Nuevo Modelo de Documentación

### Estructura de Archivos

```
{service}/
└── .agentbus/
    └── AGENTS/                    # Carpeta en lugar de archivo único
        ├── STACK.md              # Tecnología y dependencias
        ├── ARCHITECTURE.md       # Patrones y flujo de datos  
        ├── STRUCTURE.md          # Estructura de carpetas
        ├── CONVENTIONS.md        # Patterns de código y decisiones
        └── CONCERNS.md           # Deuda técnica y riesgos
```

### Propósito de cada Documento

| Documento | Contenido | Consume en | Decisiones que informa |
|-----------|-----------|------------|------------------------|
| STACK.md | Lenguajes, frameworks, versiones, dependencias externas | Todas las waves | Qué tecnologías son compatibles, versiones a usar |
| ARCHITECTURE.md | Patrones (MVC, hexagonal, etc), capas, flujo de datos | Wave 2, 3 | Cómo estructurar cambios, dónde ubicar código nuevo |
| STRUCTURE.md | Layout de directorios, naming conventions, dónde va qué | Wave 2, 3 | Dónde crear archivos, cómo nombrarlos |
| CONVENTIONS.md | Patterns de código disponibles, cuándo usarlos, ejemplos | Wave 1.5, 2, 3 | Qué approach usar cuando hay múltiples opciones |
| CONCERNS.md | Tech debt, bugs conocidos, limitaciones, riesgos | Wave 2, 3, 4b | Qué evitar, qué refactorizar primero, trampas |

---

## Template: CONVENTIONS.md

Este es el documento más crítico. Debe capturar los patterns disponibles en el codebase y proporcionar guía sobre cuándo usar cada uno.

```markdown
# Coding Conventions & Patterns

**Service:** [nombre-del-servicio]  
**Analysis Date:** [YYYY-MM-DD]

---

## Data Modification Patterns

### Pattern A: [Nombre del Pattern]

**When to use:**
- [Criterio 1]
- [Criterio 2]

**Implementation:**
- [Cómo se implementa]
- [Ubicación típica]
- [Ejemplos del codebase]

**Pros:**
- [Ventaja 1]
- [Ventaja 2]

**Cons:**
- [Desventaja 1]
- [Desventaja 2]

---

### Pattern B: [Nombre del Pattern]

**When to use:**
- [Criterio 1]
- [Criterio 2]

**Implementation:**
- [Cómo se implementa]
- [Ubicación típica]
- [Ejemplos del codebase]

**Pros:**
- [Ventaja 1]
- [Ventaja 2]

**Cons:**
- [Desventaja 1]
- [Desventaja 2]

---

### Decision Matrix

| Scenario | Preferred Approach | Reason |
|----------|-------------------|--------|
| [Situación 1] | Pattern A | [Justificación] |
| [Situación 2] | Pattern B | [Justificación] |
| [Situación 3] | Depends | [Criterio de decisión] |

---

## API Design Patterns

[Si aplica, documentar patterns para diseño de APIs]

---

## Error Handling Patterns

[Cómo se manejan errores en este servicio]

---

## Validation Patterns

[Cómo se validan inputs/requests]

---

## Testing Patterns

[Cómo se estructuran los tests, qué se mockea, etc]
```

---

## Nuevo Wave 1.5: Design Alignment Checkpoint

### Ubicación en el Flujo

```
Wave 1: Deep Service Mapping (5 documentos)
     ↓
Wave 1.5: Design Alignment Checkpoint  ← NUEVO
     ↓
Wave 2: Plan Refinement
```

### Responsabilidad

El Design Alignment Checkpoint valida que el approach propuesto en el SEED-PLAN es apropiado dado el contexto capturado en los 5 documentos de mapeo, particularmente CONVENTIONS.md.

### Proceso

**Paso 1: Análisis del SEED-PLAN**

El orchestrator (o un subagente especializado) lee el SEED-PLAN e identifica los approaches propuestos para cada cambio.

**Paso 2: Detección de Alternativas**

Para cada approach propuesto, el sistema:
- Lee CONVENTIONS.md del servicio afectado
- Identifica si existen múltiples patterns válidos para ese tipo de cambio
- Detecta si el approach propuesto es el recomendado o si hay alternativas

**Paso 3: Aplicación de Heurísticas**

Si hay múltiples approaches válidos, aplicar heurísticas predefinidas:

| Escenario | Heurística | Preferencia |
|-----------|------------|-------------|
| Modificación de schema de DB | Si es ALTER/CREATE TABLE | Migración SQL |
| Creación de datos dinámicos (permisos, configs) | Si existe endpoint CRUD | API Endpoint |
| Datos que varían por ambiente | Si difiere entre dev/prod | API Endpoint / Config |
| Datos estáticos de referencia | Si son seeds inmutables | Migración SQL / Seed file |
| Configuración temporal | Si cambia frecuentemente | API Endpoint / Feature flag |

**Paso 4: Presentación al Usuario (si hay conflicto)**

Si se detecta que el approach propuesto NO es el preferido por las heurísticas, o si hay ambigüedad:

```
═══════════════════════════════════════════════════════════════
  DESIGN ALIGNMENT CHECKPOINT: [nombre-del-servicio]
═══════════════════════════════════════════════════════════════

Detecté una decisión de diseño que necesita validación:

Cambio propuesto en SEED-PLAN:
  [Descripción del cambio]

Approach propuesto:
  [Approach A - descrito en SEED-PLAN]

Alternativa detectada en CONVENTIONS.md:
  [Approach B - disponible en el codebase]

Heurística aplicable:
  [Explicación de cuál heurística aplica y por qué]

Sugerencia del sistema:
  [Approach recomendado por las heurísticas]

Opciones:
  [A] Mantener approach propuesto en SEED-PLAN
  [B] Usar approach alternativo detectado
  [C] Híbrido: [describir si aplica]

Tu elección: _

Justificación (opcional): _
```

**Paso 5: Registro de Decisiones**

Las decisiones tomadas se registran en un archivo:

```json
{
  "checkpoint_id": "dac-[plan-id]-[servicio]",
  "service": "[nombre-servicio]",
  "timestamp": "[ISO-date]",
  "decisions": [
    {
      "change_description": "[descripción]",
      "proposed_approach": "[approach A]",
      "alternatives_found": ["[approach B]", "[approach C]"],
      "selected_approach": "[approach elegido]",
      "selection_reason": "[heurística o justificación del usuario]",
      "adjusted_from_seed_plan": [true|false]
    }
  ],
  "notes_for_wave_2": "[instrucciones para el plan refinement]"
}
```

### Cuándo se omite

Si no se detectan conflictos (el approach propuesto es el único disponible o el preferido por las heurísticas), el checkpoint puede completarse automáticamente sin intervención del usuario.

---

## Los Otros 4 Documentos (Resumen)

### STACK.md

```markdown
# Technology Stack

**Service:** [nombre-servicio]

## Core Stack
- **Language:** [Lenguaje] [Versión]
- **Framework:** [Framework] [Versión]
- **Database:** [DB] [Versión]
- **ORM/Client:** [ORM] [Versión]

## Key Dependencies
- **[Package]:** [Versión] - [Propósito]
- **[Package]:** [Versión] - [Propósito]

## External Services
- **[Service]:** [Propósito]
  - Endpoint: [URL base o endpoint clave]
  - Client: [Ubicación del cliente en el código]
  - Auth: [Método de autenticación]
```

### ARCHITECTURE.md

```markdown
# Architecture

**Service:** [nombre-servicio]

## Pattern Overview

**Overall:** [Patrón arquitectónico principal]

**Key Characteristics:**
- [Característica 1]
- [Característica 2]

## Layers

**[Layer Name]:**
- Purpose: [Qué hace esta capa]
- Location: `[path]`
- Contains: [Tipos de código que contiene]
- Depends on: [Qué otras capas usa]
- Used by: [Qué otras capas la usan]

## Data Flow

**[Flow Name]:**
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]
```

### STRUCTURE.md

```markdown
# Codebase Structure

**Service:** [nombre-servicio]

## Directory Layout

```
[project-root]/
├── [dir]/          # [Propósito]
├── [dir]/          # [Propósito]
└── [file]          # [Propósito]
```

## Where to Add New Code

**New Feature:**
- Primary code: `[path]`
- Tests: `[path]`

**New API Endpoint:**
- Handler: `[path]`
- Service logic: `[path]`
- Tests: `[path]`
```

### CONCERNS.md

```markdown
# Codebase Concerns & Tech Debt

**Service:** [nombre-servicio]

## Critical Issues

**[ID]: [Título]**
- **Files:** `[file paths]`
- **Issue:** [Descripción del problema]
- **Impact:** [Qué se rompe o degrada]
- **Fix approach:** [Cómo abordarlo]

## Known Limitations

**[ID]: [Título]**
- **Current:** [Estado actual]
- **Limitation:** [Qué no se puede hacer]
- **Workaround:** [Solución temporal si existe]
```

---

## Implementación

### Fase 1: Subskill map-codebase

Agregar `agentbus map-codebase` como subskill de AgentBus. Este skill:

1. Recibe un service_path como input
2. Explora el codebase según foco (tech, arch, structure, conventions, concerns)
3. Escribe los 5 documentos en `.agentbus/AGENTS/`
4. Es invocado por el orchestrator durante Wave 1

**Integración con orchestrator:**

El orchestrator en Wave 1 spawnea el `agentbus map-codebase` para cada servicio:

```
/agentbus orchestrator "feature description" svc1 svc2

→ Orchestrator detecta servicios
→ Para cada servicio:
  → Spawnea: /agentbus map-codebase [service_path]
  → Escribe: STACK.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, CONCERNS.md
→ Continúa a Wave 1.5
```

### Fase 2: Design Alignment Checkpoint

Implementar la lógica del checkpoint en el orchestrador:

**Input:**
- SEED-PLAN.md
- CONVENTIONS.md de cada servicio afectado

**Proceso:**
1. Parsear SEED-PLAN para extraer approaches propuestos
2. Para cada approach, consultar CONVENTIONS.md
3. Detectar si hay alternativas
4. Aplicar heurísticas
5. Presentar al usuario si hay conflicto
6. Registrar decisiones

**Output:**
- Decisiones registradas (JSON)
- SEED-PLAN ajustado (si aplica)
- Status actualizado

### Fase 3: Revisión de Consistencia

Actualizar todos los skills para usar el nuevo patrón:

- `agentbus orchestrator`: Leer de `.agentbus/AGENTS/` en lugar de `AGENTS.md`
- `agentbus service-agent`: Crear/modificar archivos en `.agentbus/AGENTS/`
- `agentbus review`: Usar información de los 5 documentos para consistencia
- Documentación: Actualizar todas las referencias al viejo `AGENTS.md`

---

## Beneficios

1. **Decisiones informadas:** Los agentes conocen qué patterns están disponibles y cuándo usarlos
2. **Menos rework:** Se detectan problemas de approach antes de la implementación
3. **Documentación viva:** Cada documento tiene un propósito específico y se mantiene enfocado
4. **Trazabilidad:** Las decisiones de diseño quedan registradas con su justificación

---

## Notas de Implementación

- No se requiere retrocompatibilidad con el viejo AGENTS.md
- El subskill `map-codebase` puede reutilizar lógica del skill `map-codebase` existente si aplica
- Las heurísticas deben ser configurables o extensibles por servicio
- El Design Alignment Checkpoint es opcional en el flujo (puede auto-completarse si no hay conflictos)
