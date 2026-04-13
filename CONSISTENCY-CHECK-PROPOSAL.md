# Cross-Service Consistency Check Proposal

## Problema Identificado

Durante la implementación del plan `003-journey-analytics-dashboard`, se detectaron **5 issues críticos** entre `journey-api` y `cronjob-api` que habrían roto la integración:

| # | Issue | Journey-API | Cronjob-API | Impacto |
|---|-------|-------------|-------------|---------|
| 1 | Callback URL | `/webhooks/analytics-complete` | `/analytics/internal/callback` | Callback nunca llega |
| 2 | Timestamp field | `completed_at` | `finished_at` | Campo no reconocido |
| 3 | Error field | `error` | `error_message` | Error info perdida |
| 4 | Job ID format | nanoid (21 chars) | UUID format | Type mismatch |
| 5 | Date range | Computa `today` | Espera `since`/`until` | Ignora parámetros |

**Root cause**: No hay un paso formal en AgentBus que valide que los contratos entre servicios sean consistentes **antes** de la verificación.

---

## Solución: Wave 3.5 — Cross-Service Contract Validation

### Ubicación en el Flujo

```
Wave 1: Service Mapping           → AGENTS/ (5 docs)
Wave 1.5: Design Alignment        → Validated approaches
Wave 2: Plan Refinement           → PLAN.md
Wave 3: Implementation            → Code modified
Wave 3.5: Contract Validation  ←  NUEVO: Cross-service consistency check
     ↓
Wave 4: Verification              → Tests
Wave 5: Wrap-up                   → Commits
```

### Responsabilidad

Validar que los contratos entre servicios sean consistentes:
- API endpoints (paths, methods)
- Request/response schemas
- Field names and types
- Status values and enums
- Event payloads
- Database foreign key expectations

### Proceso

**Paso 1: Extract Contracts from CHANGES.md**

Para cada servicio, extraer:
- Nuevos endpoints expuestos (path, method, request, response)
- Endpoints consumidos (calls to other services)
- Eventos publicados (topic, payload schema)
- Eventos consumidos (subscription, expected payload)
- Cambios de DB que afectan contratos

**Paso 2: Cross-Service Matching**

Comparar contratos entre pares de servicios:

```
Servicio A expone:  POST /analytics/jobs
Servicio B consume: POST /analytic/jobs  ← typo detectado

Servicio A envía:   { "completed_at": "2024-01-15" }
Servicio B espera:  { "finished_at": "2024-01-15" }  ← field mismatch
```

**Paso 3: Issue Classification**

| Severity | Definition | Action |
|----------|------------|--------|
| 🔴 **Critical** | Rompe la integración (ej: URL equivocada, campo requerido faltante) | Bloquea Wave 4 |
| 🟡 **Warning** | Puede causar problemas (ej: campo extra, type coercion posible) | Reporta, no bloquea |
| 🟢 **Info** | Diferencia menor (ej: orden de campos, naming no estándar) | Documenta |

**Paso 4: Generate CONSISTENCY-REPORT.md**

```markdown
# Cross-Service Consistency Report

**Plan**: 003-journey-analytics-dashboard  
**Generated**: 2024-01-15T10:30:00Z

## Summary

| Status | Count |
|--------|-------|
| 🔴 Critical | 2 |
| 🟡 Warning | 3 |
| 🟢 Info | 1 |

**Verdict**: ❌ Wave 4 blocked until critical issues resolved

---

## Critical Issues (Blockers)

### CRIT-001: Callback URL Mismatch

**Between**: journey-api → cronjob-api

| | Expected By | Provided By |
|---|-------------|-------------|
| Endpoint | cronjob-api: `/analytics/internal/callback` | journey-api: `/webhooks/analytics-complete` |

**Impact**: Callback from journey never reaches cronjob

**Fix Options**:
- [ ] Option A: Change journey-api to call `/analytics/internal/callback`
- [ ] Option B: Change cronjob-api to expose `/webhooks/analytics-complete`

**Decision**: _

---

### CRIT-002: Response Field Name Mismatch

**Between**: journey-api (producer) → cronjob-api (consumer)

| Field | Journey Sends | Cronjob Expects |
|-------|---------------|-----------------|
| Timestamp | `completed_at` | `finished_at` |
| Error | `error` | `error_message` |

**Impact**: Cronjob won't find completion timestamp or error details

**Fix**: Align field names (recommend: use `finished_at`, `error_message`)

---

## Warnings

### WARN-001: Job ID Format Mismatch

**Between**: journey-api → cronjob-api

| Aspect | Journey | Cronjob |
|--------|---------|---------|
| Format | nanoid (21 chars) | UUID (36 chars) |

**Impact**: Type mismatch, may cause validation issues

**Note**: May work if cronjob treats ID as string, but inconsistent

---

## Info

### INFO-001: Extra Field in Payload

**Between**: journey-api → cronjob-api

- Journey sends: `run_type`
- Cronjob doesn't use this field

**Impact**: None (extra field ignored)

**Recommendation**: Document or remove

---

## Recommended Fix Order

1. **Fix CRIT-001** (callback URL) - Highest priority
2. **Fix CRIT-002** (field names) - Blocks data flow
3. Address WARN-001 if validation strict
4. Optional: Clean up INFO-001

---

## Sign-off

After fixes, re-run: `/agentbus orchestrator --continue 003-feature`
```

**Paso 5: User Decision**

Presentar reporte y opciones:

```
═══════════════════════════════════════════════════════════════
  WAVE 3.5: CROSS-SERVICE CONTRACT VALIDATION
═══════════════════════════════════════════════════════════════

Verificación completada entre servicios afectados:
• journey-api
• cronjob-api

Resultado: ❌ 2 CRITICAL issues encontrados

Issues críticos (bloquean Wave 4):
─────────────────────────────────────────────────────────────
1. Callback URL Mismatch
   Journey llama a: /webhooks/analytics-complete
   Cronjob espera:  /analytics/internal/callback

2. Field Name Mismatch en callback payload
   Journey envía:  completed_at, error
   Cronjob espera: finished_at, error_message

Opciones:
  [f] Ver reporte completo — Abre CONSISTENCY-REPORT.md
  [a] Auto-fix sugerido — Aplica fixes recomendados
  [m] Manual — Indica tú qué fix aplicar
  [s] Skip — Proceder a Wave 4 con inconsistencias (riesgoso)

Tu elección: _
```

**Paso 6: Apply Fixes (si se selecciona)**

Spawn service-agents en modo `contract_fix`:

```python
Task(
    subagent_name="agentbus service agent",
    description="Wave 3.5: Apply contract fixes",
    prompt=json.dumps({
        "wave": "3.5",
        "mode": "contract_fix",
        "service_name": "journey-api",
        "fixes": [
            {
                "type": "endpoint_url",
                "current": "/webhooks/analytics-complete",
                "target": "/analytics/internal/callback"
            },
            {
                "type": "field_rename",
                "current": "completed_at",
                "target": "finished_at"
            }
        ]
    })
)
```

**Paso 7: Re-validate**

Re-ejecutar validación hasta que no haya issues críticos.

---

## Heurísticas de Detección

### Endpoint Matching

```python
# Normalizar paths para comparación
def normalize_path(path):
    # Remove trailing slashes
    # Convert to lowercase
    # Remove version prefixes (/v1/, /api/)
    # Handle plurals (job/jobs)
    return normalized

# Calcular similitud
if similarity(producer_path, consumer_path) > 0.8:
    flag_potential_mismatch()
```

### Schema Matching

```python
# Comparar schemas recursivamente
def compare_schemas(producer, consumer, path=""):
    issues = []
    
    for field in producer.required:
        if field not in consumer.expected:
            issues.append({
                "severity": "critical",
                "type": "missing_field",
                "field": f"{path}.{field}",
                "message": f"Producer sends '{field}' but consumer doesn't expect it"
            })
    
    for field in consumer.expected:
        if field not in producer.provides:
            issues.append({
                "severity": "critical", 
                "type": "unexpected_field",
                "field": f"{path}.{field}",
                "message": f"Consumer expects '{field}' but producer doesn't send it"
            })
    
    # Check type compatibility
    for field in common_fields:
        if not types_compatible(producer[field], consumer[field]):
            issues.append({
                "severity": "warning",
                "type": "type_mismatch",
                "field": f"{path}.{field}",
                "producer_type": producer[field].type,
                "consumer_type": consumer[field].type
            })
    
    return issues
```

---

## Integración con Skills Existentes

### Update: `agentbus orchestrator`

- Agregar `wave_3_5_contract_validation` a status.json
- Implementar lógica de detección de contratos
- Generar CONSISTENCY-REPORT.md
- Spawnea `contract_fix` mode si es necesario

### Update: `agentbus service agent`

Nuevo modo: `contract_fix`
- Recibe lista de fixes a aplicar
- Modifica código para alinear contratos
- Actualiza CHANGES.md
- No commitea (como Wave 3)

### New: `agentbus contract-check` (subskill opcional)

Skill especializado solo en análisis de contratos:
- Input: Lista de CHANGES.md de servicios
- Output: CONSISTENCY-REPORT.md
- No modifica código (read-only analysis)

---

## Casos de Uso

### Caso 1: Event-Driven Architecture

Validar que eventos publicados por servicio A sean consumibles por servicio B:
- Topic names match
- Payload schema compatible
- Required fields present

### Caso 2: API Call Chain

Validar cadena de llamadas: A → B → C:
- A calls correct B endpoint
- B calls correct C endpoint  
- Response de C compatible con expectativa de B
- Response de B compatible con expectativa de A

### Caso 3: Database Shared Entities

Validar que múltiples servicios tengan visión consistente de entidades:
- Foreign key types match
- Enum values consistent
- Timestamp formats aligned

---

## Implementación

### Fase 1: Contract Extractor

Agregar a `agentbus service agent` Wave 3:
- Extraer contratos y escribir `CONTRACTS.json` junto a CHANGES.md

### Fase 2: Contract Validator

Update `agentbus orchestrator`:
- Leer CONTRACTS.json de todos los servicios
- Comparar y generar CONSISTENCY-REPORT.md
- Implementar lógica de decisión (bloquear/continuar)

### Fase 3: Contract Fix Mode

Update `agentbus service agent`:
- Nuevo modo `contract_fix` para aplicar correcciones
- Integrar con Wave 3.5

---

## Beneficios

1. **Detecta issues antes de tests**: Evita debug en Wave 4
2. **Automatiza validación**: No depende de revisión manual
3. **Documenta contratos**: CONTRACTS.json como source of truth
4. **Previene regresiones**: Checks en futuros cambios

---

## Alternativas Consideradas

| Alternativa | Pros | Cons |
|-------------|------|------|
| **Wave 3.5 (elegido)** | Antes de tests, tiempo de fix | Agrega paso al flujo |
| Integrar en Wave 4 | Un paso menos | Tests fallan, debug más lento |
| Post-implementation manual | Flexible | Propenso a olvidos |
| Schema registry externo | Muy robusto | Complejo de implementar |

---

## Notas

- No requiere retrocompatibilidad (nueva funcionalidad)
- CONTRACTS.json es artifact interno (no editar manualmente)
- CONSISTENCY-REPORT.md es para humanos (legible, actionable)
- Puede auto-skip si solo hay un servicio afectado
