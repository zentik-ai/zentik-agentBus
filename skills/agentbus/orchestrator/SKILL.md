---
name: agentbus-orchestrator
description: Cross-service planning orchestrator for AgentBus. Coordinates multi-wave planning across microservices using evidence-based workflow.
version: 1.0.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado para coordinar waves.

## Skill Base vs Orchestrator

| | Skill Base (`agentbus/SKILL.md`) | Orchestrator (`agentbus-orchestrator/SKILL.md`) |
|---|---|---|
| **Propósito** | Router/documentador. Decide si tu caso aplica para AgentBus. | Protocolo completo de ejecución. |
| **Contenido** | Qué es, cuándo usar, comandos clave. | Waves, spawn de subagentes, manejo de errores. |
| **Cuándo leer** | Primera vez usando AgentBus. | Cuando necesites detalles de implementación. |

## Core Principle: Evidence Over Communication

**Files are the source of truth.** You don't accumulate state—you read artifacts when you need to know the status.

```
Wave 1: Service Mapping    →  AGENTS.md (understand service)
Wave 2: Plan Refinement    →  PLAN.md (plan the change)
Wave 3: Implementation     →  Code modified (no commits yet)
Wave 4: Verification       →  TEST-RESULTS.md (verify it works)
Wave 5: Wrap-up (optional) →  Git commits + final deployment prep
```

## When to Use

User invokes with descripción natural:

```
/agentbus-orchestrator "necesito modificar el endpoint de credits en el bot de WA y tools"
```

El orchestrator detecta automáticamente los servicios mencionados (ver "Service Detection" abajo).

O para continuar:

```
/agentbus-orchestrator --continue 001-feature
```

## Service Detection & Fuzzy Matching

### Algoritmo de Detección

1. **Extrae candidatos** del prompt del usuario:
   - Busca nombres de servicios, variaciones, o abreviaturas
   - Ejemplos: "bot de WA" → "exitus-bot-wa", "tools" → "exitus-agent-tools"

2. **Lee registry**: `~/.agentbus/services.json`

3. **Fuzzy matching**:
   - Match exacto: "exitus-bot-wa" → exitus-bot-wa
   - Match parcial: "bot" → exitus-bot-wa (si es único)
   - Match semántico: "bot de WA" → exitus-bot-wa
   - Abreviaturas: "tools" → exitus-agent-tools

4. **Resolución de conflictos**:
   - Si hay múltiples matches, muestra opciones numeradas
   - Si no hay matches claros, muestra todos los servicios disponibles

### Interacción con Usuario

**Caso A: Matches claros encontrados**

```
Usuario: /agentbus-orchestrator "modificar endpoint en bot de WA y tools"

Orchestrator: Detecté posibles servicios:
• "bot de WA" → exitus-bot-wa ✓
• "tools" → exitus-agent-tools ✓

¿Confirmas estos servicios? (yes/no/edit): _
```

**Caso B: Matches ambiguos**

```
Usuario: /agentbus-orchestrator "cambiar el api"

Orchestrator: "api" podría ser:
1. exitus-api-gateway
2. exitus-agent-tools (tiene APIs)

¿Cuál servicio(s)? (número(s) o nombre(s)): _
```

**Caso C: Sin matches**

```
Usuario: /agentbus-orchestrator "hacer algo"

Orchestrator: No detecté servicios en tu mensaje.

Servicios disponibles en registry:
1. exitus-agent-tools  (/workspace/exitus-agent-tools)
2. exitus-bot-wa       (/workspace/exitus-bot-wa)
3. exitus-api-gateway  (/workspace/exitus-api-gateway)

¿Cuáles usar? (números o nombres, separados por comas o espacios): _
```

### Implementación del Matching

```python
def detect_services(user_prompt, registry_services):
    """
    registry_services: dict from ~/.agentbus/services.json
    Returns: list of matched service names
    """
    candidates = []
    
    # 1. Extraer tokens potenciales del prompt
    #    (nombres propios, términos técnicos, etc.)
    
    # 2. Para cada servicio en registry, calcular score de match
    for service_name in registry_services:
        score = calculate_match_score(user_prompt, service_name)
        if score > THRESHOLD:
            candidates.append((service_name, score))
    
    # 3. Ordenar por score y retornar
    return sorted(candidates, key=lambda x: x[1], reverse=True)

def calculate_match_score(prompt, service_name):
    """
    Estrategias de matching:
    - Exact match: 100 puntos
    - Contiene substring: 80 puntos
    - Palabra similar (Levenshtein): 60 puntos
    - Abreviatura match: 70 puntos
    """
    prompt_lower = prompt.lower()
    service_lower = service_name.lower()
    
    # Exact match
    if service_name in prompt or service_lower in prompt_lower:
        return 100
    
    # Substring match (ej: "bot" en "exitus-bot-wa")
    parts = service_name.replace('-', ' ').replace('_', ' ').split()
    for part in parts:
        if part in prompt_lower and len(part) > 2:
            return 80
    
    # Abreviaturas comunes
    abbreviations = {
        'tools': ['exitus-agent-tools', 'agent-tools'],
        'bot': ['exitus-bot-wa', 'exitus-bot'],
        'wa': ['exitus-bot-wa'],
        'api': ['exitus-api-gateway'],
        'gateway': ['exitus-api-gateway'],
    }
    
    for abbr, services in abbreviations.items():
        if abbr in prompt_lower and service_name in services:
            return 70
    
    return 0
```

## Limitaciones

- **Solo coordina, no implementa detalles de servicio**: La implementación específica va en `agentbus/service-agent`.
- **No acumula estado en contexto**: Debe leer artefactos, no mantener estado en memoria.
- **Requiere `agentbus/service-agent` disponible**: El subskill debe estar accesible para invocación vía Task tool.
- **Wave 3 modifica código pero NO commitea**: Los commits son en Wave 5 (opcional) tras verificación exitosa.
- **No toma decisiones de arquitectura**: Presenta opciones, el usuario decide.

## Subagent Runtime (Cursor / Task Tool)

**⚠️ Importante**: Para que los subagentes puedan escribir archivos, debes configurar correctamente el Task tool.

### Configuración requerida

```python
Task(
    subagent_name="agentbus/service-agent",  # o "coder" según tu entorno
    description="Wave X: Task description",
    prompt=json.dumps({
        "wave": 1,
        "service_name": "service-name",
        "service_path": "/absolute/path/to/service",
        "outputs": {
            "agents_md": "/absolute/path/to/service/AGENTS.md",
            "summary_json": "/absolute/path/to/orchestrator/service-outputs/service.json"
        }
    }),
    # Flags IMPORTANTES para Cursor:
    readonly=False,  # Permite escritura de archivos
    # subagent_type="generalPurpose"  # Si tu entorno lo requiere
)
```

### Fallback si subagentes no pueden escribir

Si los subagentes reportan "Read-only mode":

1. **Modo Manual**: Guía al usuario paso a paso:
   ```
   "El subagente no puede escribir en este modo. 
    Por favor, ejecuta manualmente:
    1. Crea archivo en {path}
    2. Contenido: {...}"
   ```

2. **Modo Directo**: El orchestrator ejecuta las tareas directamente sin subagentes (más lento pero funciona).

## Execution Model: Sequential Waves, Parallel Services

```
Wave 1 (Mapping)
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 2 (Refinement)
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 3 (Implementation)
  └─► Spawn N subagents in parallel ──► Wait ──► Read summaries ──► Update status
Wave 4 (Verification)
  └─► Spawn N subagents in parallel ──► Wait ──► Read reports ──► Global verify
Wave 5 (Wrap-up - optional)
  └─► Git commits, tags, deployment prep
```

Each wave is a separate invocation. You run Wave 1, wait for user to continue, then run Wave 2, etc.

## End-to-End Workflow

### Phase 1: Intake & Discovery

1. **Parse request**
   - Feature description completa del prompt del usuario
   - Extrae candidatos de servicios usando "Service Detection & Fuzzy Matching" (ver sección arriba)
   - Si no hay matches claros, muestra lista de servicios disponibles
   - **NO asumas servicios** sin confirmación del usuario

2. **Confirmar servicios con usuario**
   - Muestra matches propuestos con explicación (ej: "bot de WA" → exitus-bot-wa)
   - Espera confirmación: yes / no / edit
   - Si editar: pide lista de servicios correctos
   - Si no hay registry: guía al usuario a crear `~/.agentbus/services.json` primero

3. **Detect service impact** (docs-first, post-confirmación)
   - Read existing AGENTS.md from confirmed services (if exists)
   - Read README.md, API.md, CLAUDE.md
   - Search for code-signals: endpoints, event names, imports between services
   - Propose list of affected services

4. **User confirmation final**
   - Write proposed services to temp file: `/tmp/agentbus-XXX-proposed-services.txt`
   - Ask user to confirm/adjust
   - Finalize service list

### Phase 2: Plan ID Generation & Validation

Before creating the plan, validate numbering consistency across all services.

**5. Scan existing plans in each service:**
   ```python
   def get_next_plan_id(services, registry):
       """
       Finds the highest plan number across all services.
       Returns next plan ID (e.g., '004-feature-name').
       """
       max_number = 0
       all_plans = []
       
       for service in services:
           service_path = registry[service]
           plans_dir = f"{service_path}/.agentbus-plans"
           
           # List all plan directories (format: XXX-name)
           if os.path.exists(plans_dir):
               for entry in os.listdir(plans_dir):
                   if os.path.isdir(f"{plans_dir}/{entry}"):
                       # Extract number from start of name
                       match = re.match(r'^(\d+)-', entry)
                       if match:
                           num = int(match.group(1))
                           max_number = max(max_number, num)
                           all_plans.append({
                               'service': service,
                               'plan': entry,
                               'number': num
                           })
       
       next_number = max_number + 1
       return f"{next_number:03d}"
   ```

**6. Validate numbering consistency:**
   - Check that there are no gaps in numbering (001, 002, 004 ← gap at 003)
   - If gaps found: **warn user** but allow to continue
   - If duplicate numbers found: **error** — require manual fix

**7. Generate plan ID:**
   - Use next sequential number: `004-feature-slug`
   - **Confirm with user** before proceeding
   
   Example interaction:
   ```
   Plan ID propuesto: 004-modify-credits-endpoint
   
   Planes existentes encontrados:
   - tools-service: 001-init, 002-auth-refactor, 003-api-changes
   - bot-service: 001-init, 002-webhook-update
   
   ¿Confirmas crear el plan 004? (yes/no): _
   ```

### Phase 3: Initialize Plan Workspace

8. **Create orchestrator workspace**:
   ```
   agentbus-orchestrator/001-feature-slug/
   ├── status.json
   ├── SEED-PLAN.md
   └── service-outputs/
   ```

9. **Write SEED-PLAN.md** with:
   - Feature description
   - One section per service with initial understanding
   - Cross-service interactions (guessed)

10. **Initialize status.json**:
   ```json
   {
     "plan_id": "001-remove-field",
     "feature_slug": "remove-field",
     "services": ["tools-service", "bot-service"],
     "status": "initialized",
     "current_wave": null,
     "waves": {
       "wave_1_mapping": {"status": "ready"},
       "wave_2_refinement": {"status": "pending"},
       "wave_3_implementation": {"status": "pending"},
       "wave_4_verification": {"status": "pending"},
       "wave_5_wrapup": {"status": "pending", "optional": true}
     }
   }
   ```

11. **Report to user**: "Wave 1 ready. Run orchestrator again to start mapping."

### Phase 4: Wave 1 — Service Mapping

12. **Check status.json**: Verify wave 1 is "ready"

13. **Launch parallel subagents**:
   ```python
   for service in services:
       Task(
           subagent_name="agentbus/service-agent",
           description=f"Wave 1: Map {service}",
           prompt=json.dumps({
               "wave": 1,
               "service_name": service,
               "service_path": f"/workspace/{service}",
               "outputs": {
                   "agents_md": f"/workspace/{service}/AGENTS.md",
                   "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
               }
           }),
           readonly=False  # IMPORTANTE: Permitir escritura
       )
   ```

14. **Wait** for all subagents to complete

15. **Read** summary JSON files from `service-outputs/`

16. **Update status.json**:
    - Mark wave 1 as "completed"
    - Record artifact paths
    - Mark wave 2 as "ready"

17. **Report**: Summary of AGENTS.md created/updated

### Phase 5: Wave 2 — Plan Refinement

18. **Check status.json**: Verify wave 1 is "completed"

19. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 2: Refine plan for {service}",
        prompt=json.dumps({
            "wave": 2,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "agents_md": f"/workspace/{service}/AGENTS.md",
                "seed_plan": f"/workspace/agentbus-orchestrator/{plan_id}/SEED-PLAN.md"
            },
            "outputs": {
                "refined_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        }),
        readonly=False
    )
    ```

16. **Wait**, **read** summaries, **update** status.json

17. **Report**: Summary of plans refined

### Phase 5: Wave 3 — Implementation

18. **Confirm with user**:
    - "Wave 3 will modify source code files but NOT commit them."
    - "Ensure you're on a feature branch."
    - "¿Proceder? (yes/no)"

19. **Check status.json**: Verify wave 2 is "completed"

20. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 3: Implement changes for {service}",
        prompt=json.dumps({
            "wave": 3,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
                "agents_md": f"/workspace/{service}/AGENTS.md"
            },
            "outputs": {
                "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        }),
        readonly=False
    )
    ```

21. **Wait**, **read** summaries, **update** status.json

22. **Report**: Summary of changes made (files modified, NO commits yet)

### Phase 6: Wave 4 — Verification

23. **Check status.json**: Verify wave 3 is "completed"

24. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 4: Verify implementation for {service}",
        prompt=json.dumps({
            "wave": 4,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
                "other_services": [s for s in services if s != service]
            },
            "outputs": {
                "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        }),
        readonly=False
    )
    ```

25. **Wait**, **read** summaries

26. **Read** all TEST-RESULTS.md files for global verification

27. **Run Global Verification**:
    - All services pass tests
    - Cross-service dependencies work
    - API contracts are respected

28. **Update status.json**: Mark wave 4 as "completed"

29. **Report**: Test results summary, readiness status

### Phase 7: Wave 5 — Wrap-up (Optional)

**Only run after user confirmation that everything looks good.**

30. **Confirm with user**:
    - "Wave 5 will create git commits for all changes."
    - "This is the point of no return."
    - "¿Proceder con commits? (yes/no)"

31. **Launch parallel subagents**:
    ```python
    Task(
        subagent_name="agentbus/service-agent",
        description=f"Wave 5: Create commits for {service}",
        prompt=json.dumps({
            "wave": 5,
            "service_name": service,
            "service_path": f"/workspace/{service}",
            "inputs": {
                "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
                "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md"
            },
            "outputs": {
                "commit_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/COMMITS.md",
                "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
            }
        }),
        readonly=False
    )
    ```

32. **Wait**, **read** summaries

33. **Write Final Artifacts**:
    - `DEPLOY-ORDER.md` — Rollout sequence with verified commits

34. **Update status.json**: Mark as "completed"

35. **Final Report**:
    - Implementation status per service
    - Commit hashes
    - Deploy readiness
    - Recommended next step: deploy to staging/production

## Error Handling & Retries

### If a subagent fails

1. Read its summary JSON for error details
2. Update status.json:
   ```json
   {
     "services": {
       "bot-service": {
         "status": "failed",
         "error": "...",
         "retries": 1
       }
     }
   }
   ```
3. Report failure to user
4. On retry: Re-run orchestrator for same wave (subagent will overwrite artifacts)

### If subagent reports "Read-only mode"

1. **Intentar modo fallback**:
   ```python
   # Reintentar con configuración diferente
   Task(
       subagent_name="coder",  # Probar con otro tipo
       description=f"Wave X: {service} (fallback mode)",
       prompt=...,
       readonly=False  # Asegurar que está en False
   )
   ```

2. **Si sigue fallando, modo manual**:
   - Reporta al usuario: "Los subagentes no pueden escribir en este modo."
   - Proporciona instrucciones manuales paso a paso.
   - O ejecuta las tareas directamente tú (orchestrator).

### If user wants to add service mid-flight

1. Update status.json to add service
2. Mark current wave as "needs_update" for that service
3. Re-run orchestrator for that wave
4. Only the new service gets processed

### If you need to resume

1. Read status.json
2. Determine current wave from status
3. Continue from there

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
    "wave_3_implementation": {
      "status": "pending"
    },
    "wave_4_verification": {
      "status": "pending"
    },
    "wave_5_wrapup": {
      "status": "pending",
      "optional": true
    }
  }
}
```

## Global Verification Checklist

After Wave 4, read all TEST-RESULTS.md and verify:

- [ ] All services pass their tests
- [ ] Dependencies: If Service A lists dependency on B, Service B acknowledges
- [ ] API contracts: Breaking changes documented by producer AND consumer
- [ ] Deploy order: No circular dependencies
- [ ] Open questions: All have owners assigned

If any check fails, report which services need re-processing.

## Output Artifacts

You produce:
1. **status.json** — Tracking for resume/retry
2. **SEED-PLAN.md** — Initial vision
3. **DEPLOY-ORDER.md** — Rollout sequence (final)

## Anti-Patterns

❌ **Don't**: Accumulate detailed knowledge in your context
❌ **Don't**: Ask subagents to return data in response text
❌ **Don't**: Write implementation details in status.json
❌ **Don't**: Assume services without AGENTS.md are unimportant
❌ **Don't**: Spawn subagents without `readonly=False` if they need to write
✅ **Do**: Read artifacts when you need to know something
✅ **Do**: Write clear, actionable final reports
✅ **Do**: Let subagents own service-level details
✅ **Do**: Confirm with user before destructive operations (Wave 3, Wave 5)
