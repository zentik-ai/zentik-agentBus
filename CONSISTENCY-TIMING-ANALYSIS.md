# Consistency Check Timing Analysis

## Opciones Comparadas

### OPCIÓN A: Wave 2.5 (Antes de implementación)

```
Wave 2: Plan Refinement
    ↓
Wave 2.5: Contract Validation ← Desde PLAN.md
    ↓
Wave 3: Implementation (con contratos ya validados)
    ↓
Wave 4: Verification
```

**Input**: PLAN.md de cada servicio (cambios propuestos)

**Pros**:
- ✅ Detecta issues antes de escribir código (más barato)
- ✅ Evita rework de implementación
- ✅ Puede influir en approach de Wave 3
- ✅ Plans son "intención declarada" (fácil de parsear)

**Cons**:
- ❌ PLAN.md puede ser menos detallado que código real
- ❌ Algunos detalles de contrato emergen durante implementación
- ❌ Falso negativo: plan parece consistente, código no lo es

---

### OPCIÓN B: Wave 3.5 (Después de implementación)

```
Wave 2: Plan Refinement
    ↓
Wave 3: Implementation
    ↓
Wave 3.5: Contract Validation ← Desde CHANGES.md + código
    ↓
Wave 4: Verification
```

**Input**: CHANGES.md + código implementado

**Pros**:
- ✅ Contratos extraídos de código real (más preciso)
- ✅ Detecta inconsistencias reales, no solo planeadas
- ✅ Valida que la implementación cumpla el contrato

**Cons**:
- ❌ Más caro arreglar (modificar código ya escrito)
- ❌ Puede requerir re-hacer Wave 3 parcialmente
- ❌ Delay: descubres el problema tarde

---

### OPCIÓN C: Ambos (Wave 2.5 ligero + Wave 3.5 completo)

```
Wave 2: Plan Refinement
    ↓
Wave 2.5: Static Validation ← Desde PLAN.md (rápido)
    ↓
Wave 3: Implementation
    ↓
Wave 3.5: Deep Validation ← Desde código (completo)
    ↓
Wave 4: Verification
```

**Wave 2.5**: Check de alto nivel desde PLAN.md
- Endpoint paths
- Field names principales
- Event topics

**Wave 3.5**: Check detallado desde código
- Types exactos
- Validaciones
- Edge cases

**Pros**:
- ✅ Catch temprano de errores obvios
- ✅ Validación final precisa
- ✅ Defensa en profundidad

**Cons**:
- ❌ Dos pasos en lugar de uno
- ❌ Overhead de ejecución

---

## Análisis del Caso journey/cronjob

Los 5 issues encontrados:

| Issue | Se detectaría en Wave 2.5? | Se detectaría en Wave 3.5? |
|-------|---------------------------|---------------------------|
| Callback URL mismatch | ✅ Sí (PLAN.md tendría endpoint) | ✅ Sí (código tiene URL) |
| Field name mismatch (completed_at vs finished_at) | ✅ Sí (PLAN.md describe payload) | ✅ Sí (código tiene schema) |
| Job ID format | ⚠️ Tal vez (PLAN.md puede no especificar) | ✅ Sí (código revela types) |
| Date range params | ✅ Sí (PLAN.md describe parámetros) | ✅ Sí (código tiene signature) |
| Extra field run_type | ⚠️ Tal vez | ✅ Sí |

**Conclusión**: La mayoría se detectarían en Wave 2.5 desde PLAN.md.

---

## Recomendación

### Opción C simplificada: Wave 2.5 como "fail-fast"

Implementar **Wave 2.5: Static Contract Check** (ligero, desde PLAN.md):

```
Wave 2: Plan Refinement → PLAN.md
    ↓
Wave 2.5: Static Contract Check ← Parse PLAN.md, detecta obvios
    ↓ [Si pasa]
Wave 3: Implementation
    ↓
Wave 4: Verification (incluye validación implícita via tests)
```

**Wave 2.5 hace**:
- Extrae endpoints de PLAN.md
- Compara paths entre servicios
- Detecta field name mismatches obvios
- **Rápido**: No analiza código, solo texto de PLAN.md

**Si Wave 2.5 pasa**: Procedemos con confianza a Wave 3

**Si Wave 2.5 falla**: Fix en PLAN.md (más barato), luego Wave 3

---

## Implementación Recomendada

### Wave 2.5: Static Contract Check (nuevo)

**Input**: PLAN.md de cada servicio
**Output**: 
- `STATIC-CONTRACT-CHECK.md` (reporte)
- Actualización a PLAN.md si se encuentran issues

**Proceso**:
1. Parse PLAN.md de cada servicio
2. Extraer:
   - "Will call endpoint X" → contrato consumido
   - "Will expose endpoint Y" → contrato expuesto
   - "Payload will contain Z" → schema parcial
3. Cross-reference entre servicios
4. Generar reporte con mismatches

**Ejemplo de detección**:
```
PLAN.md (journey-api):
  "Call cronjob-api POST /analytics/internal/callback"
  "Payload: { completed_at, error }"

PLAN.md (cronjob-api):
  "Expose POST /webhooks/analytics-complete"
  "Expect: { finished_at, error_message }"

🔴 MISMATCH: Endpoint path diferente
🔴 MISMATCH: Field names diferentes
```

**Interacción**:
```
═══════════════════════════════════════════════════════════════
  WAVE 2.5: STATIC CONTRACT CHECK
═══════════════════════════════════════════════════════════════

Servicios analizados: journey-api, cronjob-api

⚠️  2 inconsistencias detectadas en PLAN.md:

1. Endpoint Mismatch
   Journey planea llamar: POST /analytics/internal/callback
   Cronjob expone:        POST /webhooks/analytics-complete
   
   Fix sugerido: Alinear endpoint paths

2. Field Name Mismatch
   Journey enviará:  completed_at, error
   Cronjob espera:   finished_at, error_message
   
   Fix sugerido: Renombrar campos para consistencia

Opciones:
  [f] Ver reporte completo
  [a] Auto-fix — Actualizar PLAN.md con nombres consistentes
  [m] Manual — Indica tú los nombres correctos
  [i] Ignorar — Proceder a Wave 3 (no recomendado)

Tu elección: _
```

---

## Ventajas de Wave 2.5

1. **Fail-fast**: Detecta errores de diseño antes de código
2. **Barato**: Solo parsea texto, no analiza código
3. **Accionable**: Fix es editar PLAN.md, no refactorizar
4. **Educativo**: Equipos aprenden a alinear contratos en planning

## Cuándo usar Wave 3.5 también

Si necesitamos validación más profunda:
- Types exactos (PLAN.md puede no especificar)
- Validaciones de rangos
- Edge cases

Pero para la mayoría de casos, Wave 2.5 es suficiente.

---

## Decisión

¿Implementamos:
- **A**: Solo Wave 2.5 (antes de implementación)
- **B**: Solo Wave 3.5 (después de implementación) 
- **C**: Wave 2.5 primero, Wave 3.5 opcional si se necesita

Mi recomendación: **A o C** (antes o ambos). 
**No B** (después es tarde para journey/cronjob).
