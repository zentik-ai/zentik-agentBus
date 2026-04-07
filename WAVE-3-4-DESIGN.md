# Diseño Wave 3 (Implementation) y Wave 4 (Verification)

## Secuencia Corregida

| Wave | Nombre | Input | Output | Responsabilidad |
|------|--------|-------|--------|-----------------|
| 1 | Mapping | Código del servicio | AGENTS.md | Entender el servicio |
| 2 | Refinement | AGENTS.md + requerimiento | PLAN.md | Planificar el cambio |
| 3 | Implementation | PLAN.md | Código modificado + COMMIT-LOG.md | Ejecutar el plan |
| 4 | Verification | Código modificado + tests | TEST-RESULTS.md | Verificar que funciona |

---

## Wave 3: Implementation

### Input Context
```json
{
  "wave": 3,
  "wave_name": "implementation",
  "service_name": "tools-service",
  "service_path": "/workspace/tools-service",
  "inputs": {
    "plan": "/workspace/tools-service/.agentbus-plans/001-feature.md",
    "agents_md": "/workspace/tools-service/AGENTS.md"
  },
  "outputs": {
    "commit_log": "/workspace/tools-service/.agentbus-plans/001-feature-COMMITS.md",
    "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/tools-service.json"
  },
  "constraints": {
    "atomic_commits": true,
    "test_on_change": true,
    "stop_on_failure": true
  }
}
```

### Tareas del Subagente

1. **Leer PLAN.md** - Entender qué cambios hay que hacer
2. **Leer AGENTS.md** - Recordar convenciones del proyecto
3. **Ejecutar cambios en orden**:
   - Por cada ítem en el plan:
     a. Modificar archivo
     b. Ejecutar tests relevantes (unit/integration)
     c. Si pasa: `git add && git commit`
     d. Si falla: detener y reportar
4. **Escribir COMMIT-LOG.md** - Resumen de commits realizados
5. **Escribir summary JSON** - Estado de la implementación

### COMMIT-LOG.md Template

```markdown
# Implementation Log: 001-feature

## Service: tools-service

### Commits Realizados

| Commit | Archivos | Descripción | Tests |
|--------|----------|-------------|-------|
| `a1b2c3d` | `src/api/tools.ts` | Remove deprecated field from response | ✅ unit, ✅ integration |
| `e4f5g6h` | `src/db/migration.sql` | Add migration to drop column | ✅ migration test |

### Estado
- ✅ Implementación completa
- ✅ Todos los tests pasan
- 📋 Pendiente: deploy en dev

### Rollback
```bash
# Revertir todos los cambios:
git revert a1b2c3d --no-commit
git revert e4f5g6h --no-commit
```

### Notas
- [Cualquier observación importante]
```

### Summary JSON Output
```json
{
  "wave": 3,
  "status": "completed|failed|partial",
  "commits": [
    {"hash": "a1b2c3d", "files": ["src/api/tools.ts"], "tests_passed": true}
  ],
  "tests": {
    "unit": {"run": 5, "passed": 5},
    "integration": {"run": 2, "passed": 2}
  },
  "blockers": [],
  "artifacts_written": [
    "/workspace/tools-service/.agentbus-plans/001-feature-COMMITS.md"
  ]
}
```

---

## Wave 4: Verification

### Input Context
```json
{
  "wave": 4,
  "wave_name": "verification",
  "service_name": "tools-service",
  "service_path": "/workspace/tools-service",
  "inputs": {
    "commit_log": "/workspace/tools-service/.agentbus-plans/001-feature-COMMITS.md",
    "other_services": ["bot-service", "payments-service"]
  },
  "outputs": {
    "test_results": "/workspace/tools-service/.agentbus-plans/001-feature-TEST-RESULTS.md",
    "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/tools-service.json"
  }
}
```

### Tareas del Subagente

1. **Leer COMMIT-LOG.md** - Ver qué se implementó
2. **Ejecutar test suite completa**:
   - Unit tests
   - Integration tests
   - E2E tests (si aplican)
3. **Verificar cross-service** (si hay interacciones):
   - Leer COMMIT-LOG de servicios relacionados
   - Verificar compatibilidad de APIs
4. **Escribir TEST-RESULTS.md**
5. **Escribir summary JSON**

### TEST-RESULTS.md Template

```markdown
# Test Results: 001-feature

## Service: tools-service

### Resumen de Tests

| Tipo | Ejecutados | Pasados | Fallidos | Skipped |
|------|------------|---------|----------|---------|
| Unit | 45 | 45 | 0 | 0 |
| Integration | 8 | 8 | 0 | 0 |
| E2E | 3 | 3 | 0 | 0 |

### Cobertura
- Lines: 87%
- Functions: 92%
- Branches: 85%

### Cross-Service Tests
- ✅ bot-service puede consumir la API modificada
- ✅ Contrato API respetado

### Verificación Manual Sugerida
- [ ] Revisar logs en staging
- [ ] Verificar métricas de performance
- [ ] Validar con equipo de QA

### Estado Final
✅ **Listo para deploy a producción**
```

### Summary JSON Output
```json
{
  "wave": 4,
  "status": "verified|failed|needs_manual_check",
  "test_summary": {
    "unit": {"run": 45, "passed": 45},
    "integration": {"run": 8, "passed": 8},
    "e2e": {"run": 3, "passed": 3}
  },
  "coverage": {"lines": 87, "functions": 92},
  "cross_service_ok": true,
  "artifacts_written": [
    "/workspace/tools-service/.agentbus-plans/001-feature-TEST-RESULTS.md"
  ]
}
```

---

## Cambios en Orchestrator

El orchestrator ahora ejecuta 4 waves:

```python
# Wave 3: Implementation
Task(
    subagent_name="agentbus/service-agent",
    description=f"Wave 3: Implement changes for {service}",
    prompt=json.dumps({
        "wave": 3,
        "inputs": {"plan": "...", "agents_md": "..."},
        "outputs": {"commit_log": "...", "summary_json": "..."}
    })
)

# Wave 4: Verification
Task(
    subagent_name="agentbus/service-agent",
    description=f"Wave 4: Verify implementation for {service}",
    prompt=json.dumps({
        "wave": 4,
        "inputs": {"commit_log": "...", "other_services": [...]},
        "outputs": {"test_results": "...", "summary_json": "..."}
    })
)
```

---

## Artefactos por Wave

| Wave | Artefacto | Propósito |
|------|-----------|-----------|
| 1 | AGENTS.md | Documentación del servicio |
| 2 | PLAN.md | Plan de implementación |
| 3 | COMMIT-LOG.md | Registro de cambios realizados |
| 4 | TEST-RESULTS.md | Resultados de verificación |

---

## Consideraciones de Seguridad

### Wave 3 es destructiva
- Modifica código fuente
- Hace commits
- Ejecuta tests

**Sugerencias**:
1. **Confirmación explícita del usuario** antes de Wave 3
2. **Branch de feature** para aislar cambios
3. **Backup automático** o instrucciones de rollback claras
4. **Modo dry-run** opcional: "Estos son los cambios que haría, ¿procedo?"

---

## Implementación Sugerida (MVP)

Para la primera versión lightweight:

1. **Wave 3** hace los cambios y commits básicos
2. **Wave 4** corre tests y reporta (sin verificación cross-service compleja)
3. **Sin rollback automático** - solo documentar cómo revertir
4. **Tests unitarios básicos** - integration tests si son rápidos

En el futuro:
- Integración con CI/CD
- Rollback automático si fallan tests
- Verificación cross-service más sofisticada
- Integración con GSD para fases complejas
