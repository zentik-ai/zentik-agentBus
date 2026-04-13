# Two-Batch Consistency Check Proposal

## Overview

Dividir el consistency check en dos etapas:

```
Wave 2: Plan Refinement
    ↓
Wave 2.5: Plan Alignment (Batch 1) ← NUEVO: Alto nivel, desde PLAN.md
    ↓
Wave 3: Implementation
    ↓
Wave 3.5: Contract Validation (Batch 2) ← NUEVO: Duro, desde código
    ↓
Wave 4: Verification
```

---

## Batch 1: Wave 2.5 — Plan Alignment (Pre-Implementation)

### Propósito
Validar que los planes de cada servicio están **alineados a nivel de diseño** antes de escribir código.

### Input
- `PLAN.md` de cada servicio afectado
- `AGENTS/CONVENTIONS.md` (para contexto de patterns)

### Qué detecta

| Tipo | Ejemplo | Severidad |
|------|---------|-----------|
| **Endpoint mismatch** | Service A llama `/analytics/jobs`, Service B expone `/analytic/jobs` (typo) | 🔴 Blocker |
| **Field name mismatch** | A envía `completed_at`, B espera `finished_at` | 🔴 Blocker |
| **Method mismatch** | A hace POST, B espera GET | 🔴 Blocker |
| **Missing endpoint** | A planea llamar endpoint que B no expone | 🔴 Blocker |
| **Schema mismatch** | A envía objeto plano, B espera nested | 🟡 Warning |
| **Extra fields** | A envía campos que B no usa | 🟢 Info |

### Output

**PLAN-ALIGNMENT-REPORT.md**:
```markdown
# Plan Alignment Report

**Plan**: 003-feature
**Services**: journey-api, cronjob-api
**Generated**: 2024-01-15

## Summary

| Status | Count |
|--------|-------|
| 🔴 Blockers | 2 |
| 🟡 Warnings | 1 |
| 🟢 Info | 1 |

**Verdict**: ❌ Wave 3 blocked until blockers resolved

---

## Blockers (Must Fix)

### BLOCKER-001: Endpoint Path Mismatch

**Between**: journey-api → cronjob-api

| | Expected By | Planned By |
|---|-------------|------------|
| Endpoint | cronjob-api: `POST /analytics/internal/callback` | journey-api: `POST /webhooks/analytics-complete` |

**Issue**: Callback from journey nunca llegará a cronjob

**Fix Options**:
- Option A: journey cambia a `/analytics/internal/callback`
- Option B: cronjob agrega `/webhooks/analytics-complete`
- Option C: Ambos se alinean a nuevo path

**Decision Required**: Yes

---

### BLOCKER-002: Field Name Mismatch

**Between**: journey-api (caller) → cronjob-api (callee)

| Field | Journey Plans to Send | Cronjob Expects |
|-------|----------------------|-----------------|
| Timestamp | `completed_at` | `finished_at` |
| Error | `error` | `error_message` |

**Issue**: Cronjob no encontrará datos en campos esperados

**Fix**: Alinear nombres (recomendado: usar nombres de cronjob)

---

## Warnings (Should Fix)

### WARN-001: Schema Structure Mismatch

**Between**: journey-api → cronjob-api

- Journey envía: `{ user_id, branch_name, completed_at }`
- Cronjob espera: `{ user: { id, branch_name }, timestamp }`

**Impact**: Funcionará pero no es ideal

**Fix**: Recomendado alinear estructura

---

## Info (FYI)

### INFO-001: Extra Field

Journey envía `run_type`, cronjob no lo usa (lo ignora).

---

## Resolution

| Blocker | Selected Fix | Status |
|---------|--------------|--------|
| BLOCKER-001 | Option A (journey usa path de cronjob) | ⬜ Pending |
| BLOCKER-002 | journey usa `finished_at`, `error_message` | ⬜ Pending |

**After fixes**: Re-run Wave 2.5
```

### Proceso

**Paso 1**: Parse PLAN.md de cada servicio
```python
# Extraer contratos planificados
for service in services:
    plan = parse_plan(f"{service}/.agentbus-plans/{plan_id}/PLAN.md")
    contracts[service] = {
        "exposes": extract_endpoints(plan),      # Qué endpoints expone
        "calls": extract_api_calls(plan),        # A qué endpoints llama
        "sends": extract_payloads(plan),         # Qué payloads envía
        "expects": extract_expectations(plan)    # Qué payloads espera
    }
```

**Paso 2**: Cross-reference
```python
# Comparar llamadas vs exposiciones
for service_a in services:
    for call in contracts[service_a]["calls"]:
        target_service = call.target_service
        target_endpoint = call.endpoint
        
        # Buscar matching endpoint
        exposed = find_exposed_endpoint(contracts[target_service], target_endpoint)
        
        if not exposed:
            report_blocker("Missing endpoint", service_a, target_service)
        elif not paths_match(call.path, exposed.path):
            report_blocker("Path mismatch", service_a, target_service)
        elif not schemas_compatible(call.payload, exposed.expected_payload):
            report_warning("Schema mismatch", service_a, target_service)
```

**Paso 3**: Generar reporte y pedir decisiones

**Paso 4**: Aplicar fixes (editar PLAN.md)

**Paso 5**: Re-validar

---

## Batch 2: Wave 3.5 — Contract Validation (Post-Implementation)

### Propósite
Validar que la **implementación real** cumple los contratos y es consistente cross-service.

### Input
- `CHANGES.md` de cada servicio
- Código fuente implementado
- `PLAN.md` (para comparar)

### Qué detecta (más profundo que Batch 1)

| Tipo | Ejemplo | Severidad |
|------|---------|-----------|
| **Implementation drift** | Plan decía POST, código hace GET | 🔴 Critical |
| **Type mismatch** | Plan decía string, código usa int | 🔴 Critical |
| **Missing validation** | Código no valida campo requerido | 🔴 Critical |
| **URL hardcodeada** | Endpoint URL hardcodeada vs config | 🟡 Warning |
| **Timeout mismatch** | Caller timeout 5s, callee tarda 10s | 🟡 Warning |
| **Missing error handling** | No maneja error 500 del callee | 🟡 Warning |
| **Logging inconsistency** | Formatos de log diferentes | 🟢 Info |
| **Extra headers** | Headers enviados no esperados | 🟢 Info |

### Output

**CONTRACT-VALIDATION-REPORT.md**:
```markdown
# Contract Validation Report

**Plan**: 003-feature
**Services**: journey-api, cronjob-api
**Generated**: 2024-01-15

## Summary

| Status | Count |
|--------|-------|
| 🔴 Critical | 1 |
| 🟡 Warning | 2 |
| 🟢 Info | 2 |

**Verdict**: ❌ Wave 4 blocked until critical issues resolved

---

## Critical Issues

### CRIT-001: Implementation Drift - Wrong HTTP Method

**Location**: `journey-api/src/api/analytics.py:45`

**Plan Specified**: `POST /analytics/internal/callback`
**Implementation**: `GET /analytics/internal/callback`

**Impact**: cronjob-api espera POST, recibe GET → 405 Method Not Allowed

**Fix**: Cambiar a POST en journey-api

---

### CRIT-002: Type Mismatch in Payload

**Location**: `journey-api/src/services/analytics.py:78`

**Plan Specified**: `job_id: string (UUID)`
**Implementation**: `job_id: int`

**Impact**: cronjob-api espera string, recibe int → Validation error

**Fix**: Cambiar a string en journey-api

---

## Warnings

### WARN-001: Hardcoded URL

**Location**: `journey-api/src/config.py:12`

```python
CRONJOB_CALLBACK_URL = "http://cronjob-api:8080/analytics/internal/callback"
```

**Issue**: URL hardcodeada, debería venir de config/env

**Impact**: Difícil cambiar en producción

---

### WARN-002: Timeout Mismatch

**Caller (journey-api)**: timeout=5s
**Callee (cronjob-api)**: avg_response=8s

**Impact**: Timeouts frecuentes

**Fix**: Aumentar timeout en journey o optimizar cronjob

---

## Info

### INFO-001: Extra Header Sent

Journey envía `X-Request-ID`, cronjob no lo usa.

---

## Code Diffs (Implementation vs Plan)

### journey-api/src/api/analytics.py

```diff
# Plan specified:
#   requests.post(f"{CRONJOB_URL}/analytics/internal/callback", json=payload)

# Implementation:
- response = requests.get(f"{CRONJOB_URL}/analytics/internal/callback", params=payload)
+ response = requests.post(f"{CRONJOB_URL}/analytics/internal/callback", json=payload)
```

---

## Fixes Applied

| Issue | Fix | Status |
|-------|-----|--------|
| CRIT-001 | Changed GET to POST | ✅ Done |
| CRIT-002 | Changed int to str for job_id | ✅ Done |

**After fixes**: Re-run Wave 3.5
```

### Proceso

**Paso 1**: Extraer contratos reales del código
```python
for service in services:
    # Leer CHANGES.md para saber qué archivos cambiaron
    changes = read_changes(f"{service}/.agentbus-plans/{plan_id}/CHANGES.md")
    
    # Analizar código implementado
    for file in changes.modified_files:
        code = read_file(file)
        actual_contracts[service] = {
            "endpoints": extract_actual_endpoints(code),
            "calls": extract_actual_api_calls(code),
            "payloads": extract_actual_payloads(code),
            "types": extract_actual_types(code)
        }
```

**Paso 2**: Comparar Plan vs Implementation
```python
# Detectar drift
for service in services:
    plan = load_plan(service)
    actual = actual_contracts[service]
    
    for planned_endpoint in plan.endpoints:
        actual_endpoint = find_actual(actual.endpoints, planned_endpoint.name)
        
        if planned_endpoint.method != actual_endpoint.method:
            report_critical("Method drift", service, planned_endpoint, actual_endpoint)
        
        if not types_compatible(planned_endpoint.payload, actual_endpoint.payload):
            report_critical("Type drift", service, planned_endpoint, actual_endpoint)
```

**Paso 3**: Cross-service validation (similar a Batch 1 pero con datos reales)

**Paso 4**: Generar reporte con code diffs

**Paso 5**: Aplicar fixes (modificar código)

**Paso 6**: Re-validar

---

## Comparación: Batch 1 vs Batch 2

| Aspecto | Batch 1 (Wave 2.5) | Batch 2 (Wave 3.5) |
|---------|-------------------|-------------------|
| **Cuándo** | Pre-implementación | Post-implementación |
| **Input** | PLAN.md | CHANGES.md + código |
| **Qué detecta** | Errores de diseño | Errores de implementación |
| **Precisión** | ~80% (intención) | ~100% (realidad) |
| **Costo de fix** | Bajo (editar plan) | Medio (modificar código) |
| **Tiempo** | Rápido | Más lento (analiza código) |
| **Blockers típicos** | Paths, field names, métodos | Types, validation, drift |

---

## Cuándo usar cada uno

### Siempre usar Batch 1 (Wave 2.5)
- Detecta errores obvios de diseño
- Barato y rápido
- Previene rework costoso

### Usar Batch 2 (Wave 3.5) si:
- Hay muchos servicios involucrados (>2)
- Hay contratos complejos (payloads grandes)
- El feature es crítico (no puede fallar en prod)
- Historia de issues de integración

### Skip Batch 2 si:
- Solo 2 servicios simples
- Contratos ya validados en otros features
- Timeline muy ajustado (riesgo calculado)

---

## Implementación

### Fase 1: Batch 1 (Wave 2.5)

1. Agregar a orchestrator: `wave_2_5_plan_alignment`
2. Crear parser de PLAN.md para contratos
3. Implementar cross-reference logic
4. Generar PLAN-ALIGNMENT-REPORT.md
5. UI para presentar blockers y recibir decisiones

### Fase 2: Batch 2 (Wave 3.5) - Opcional

1. Agregar a orchestrator: `wave_3_5_contract_validation`
2. Crear analyzer de código (static analysis)
3. Comparador Plan vs Implementation
4. Generar CONTRACT-VALIDATION-REPORT.md con diffs
5. Integrar con Wave 4

---

## Ejemplo de Flujo Completo

```
# Wave 2: Plan Refinement completado
# PLAN.md creado para journey-api y cronjob-api

$ /agentbus orchestrator --continue 003-feature
→ Detecta Wave 2 completado
→ Ejecuta Wave 2.5: Plan Alignment

╔════════════════════════════════════════════════════════════╗
║  WAVE 2.5: PLAN ALIGNMENT                                  ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Analizando PLAN.md de:                                    ║
║  • journey-api                                             ║
║  • cronjob-api                                             ║
║                                                            ║
║  Resultado: ⚠️ 2 blockers detectados                       ║
║                                                            ║
║  BLOCKER 1: Endpoint mismatch                              ║
║    Journey llama a: /webhooks/analytics-complete           ║
║    Cronjob expone:  /analytics/internal/callback           ║
║                                                            ║
║  BLOCKER 2: Field name mismatch                            ║
║    Journey envía:  completed_at, error                     ║
║    Cronjob espera: finished_at, error_message              ║
║                                                            ║
║  Opciones:                                                 ║
║    [v] Ver reporte completo                                ║
║    [f] Fix automático - Alinear a convención de cronjob    ║
║    [m] Manual - Especificar tú los nombres correctos       ║
║    [s] Skip - Proceder con inconsistencias (riesgoso)      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

# Usuario elige [f] Fix automático
→ Actualiza PLAN.md de journey-api
→ Re-ejecuta Wave 2.5 para verificar
→ ✅ Alignment OK
→ Procede a Wave 3

# Wave 3: Implementation completado

$ /agentbus orchestrator --continue 003-feature
→ Detecta Wave 3 completado
→ Ejecuta Wave 3.5: Contract Validation (si habilitado)

╔════════════════════════════════════════════════════════════╗
║  WAVE 3.5: CONTRACT VALIDATION                             ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Analizando implementación real...                         ║
║                                                            ║
║  ✅ journey-api: Implementación coincide con PLAN          ║
║  ⚠️  cronjob-api: 1 warning                                ║
║                                                            ║
║  WARN: Timeout potencial                                   ║
║    Journey timeout: 5s                                     ║
║    Cronjob avg response: 8s                                ║
║                                                            ║
║  Recomendación: Aumentar timeout en journey a 10s          ║
║                                                            ║
║  [a] Aplicar fix sugerido                                  ║
║  [i] Ignorar - Proceder a Wave 4                           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

# Wave 4: Verification
→ Tests pasan
→ Listo para commit
```

---

## Conclusión

**Batch 1 (Wave 2.5) es obligatorio**: Detecta errores de diseño baratos.

**Batch 2 (Wave 3.5) es opcional pero recomendado**: Valida implementación real.

Juntos proveen defensa en profundidad:
- Batch 1: "Antes de escribir código, ¿estamos de acuerdo en el diseño?"
- Batch 2: "Después de escribir código, ¿implementamos lo acordado?"
