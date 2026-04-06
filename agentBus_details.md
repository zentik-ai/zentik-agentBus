# AgentBus Skills — Implementation Plan

**Para usar junto con el PRD**
**Fecha:** Marzo 2026

---

## Estructura final del repo

```
agentbus-skills/
├── README.md
├── scripts/
│   ├── register_service.py
│   ├── list_services.py
│   ├── next_plan_number.py
│   ├── write_plan.py
│   └── read_plan.py
└── skills/
    ├── agentbus-orchestrator/
    │   └── SKILL.md
    ├── agentbus-expert/
    │   └── SKILL.md
    └── map-codebase/
        └── SKILL.md
```

---

## Scripts Python

Todos los scripts usan `uv` con inline script metadata (PEP 723).
Se corren con: `uv run <script>.py [args]`
El registry global vive en: `~/.agentbus/services.json`

Convenciones acordadas:
- Las keys del registry son nombres canónicos del repo (`payments-service`, `notifications-service`, `crm-service`).
- Se aceptan aliases simplificados (`payments`, `notifications`, `crm`) y se normalizan a canónico antes de planear.

---

### `register_service.py`

**Propósito:** Registrar o actualizar un servicio en el registry global.

**Uso:**
```bash
uv run register_service.py <name> <absolute-path>
```

**Ejemplos:**
```bash
uv run register_service.py payments-service /home/jero/repos/payments-service
uv run register_service.py crm-service /home/jero/repos/crm-service
```

**Lógica:**
1. Validar que se reciben exactamente 2 argumentos
2. Validar que el path existe en el filesystem (`Path.exists()`)
3. Crear `~/.agentbus/` si no existe
4. Leer `services.json` si existe, si no inicializar `{}`
5. Agregar o sobreescribir la entrada `{name: path}`
6. Escribir el JSON con `indent=2`
7. Imprimir confirmación: `Registered 'payments-service' → /home/jero/repos/payments-service`

**Errores:**
- Path no existe → `Error: path '/x/y' does not exist`
- Argumentos incorrectos → usage message

**Dependencies:** ninguna (stdlib only — `json`, `sys`, `pathlib`)

---

### `list_services.py`

**Propósito:** Listar todos los servicios registrados.

**Uso:**
```bash
uv run list_services.py
uv run list_services.py --json    # output machine-readable
```

**Output default (human-readable):**
```
Registered services:
  payments-service      → /home/jero/repos/payments-service
  crm-service           → /home/jero/repos/crm-service
  notifications-service → /home/jero/repos/notifications-service
```

**Output `--json`:**
```json
{
  "payments-service": "/home/jero/repos/payments-service",
  "crm-service": "/home/jero/repos/crm-service"
}
```

**Lógica:**
1. Leer `~/.agentbus/services.json`
2. Si no existe → `No services registered yet. Use register_service.py to add one.`
3. Si `--json` → dump JSON a stdout
4. Si no → imprimir tabla formateada

**Dependencies:** ninguna (stdlib only)

---

### `next_plan_number.py`

**Propósito:** Retornar el siguiente número disponible para un plan en un repo dado.

**Uso:**
```bash
uv run next_plan_number.py <service-path>
```

**Output:**
```
003
```

**Lógica:**
1. Recibir path del repo como argumento
2. Buscar `.agentbus-plans/` dentro del repo
3. Si no existe la carpeta → retornar `001`
4. Listar archivos `.md` en la carpeta
5. Extraer el prefijo numérico de cada nombre (`001-kafka.md` → `1`)
6. Tomar el máximo + 1, formatear como 3 dígitos con zero-padding
7. Imprimir el número

**Edge cases:**
- Carpeta vacía → `001`
- Archivos sin prefijo numérico → ignorarlos, solo contar los que sigan el patrón
- Gap en números (001, 003) → next es `004` (máximo + 1, no gap-fill)

**Dependencies:** ninguna (stdlib only)

---

### `write_plan.py`

**Propósito:** Escribir un archivo de plan en el repo de un servicio.

**Uso:**
```bash
uv run write_plan.py <service-path> <feature-slug> <plan-content-file>
```

**Ejemplo:**
```bash
uv run write_plan.py /home/jero/repos/payments kafka-migration /tmp/plan_payments.md
```

**Lógica:**
1. Validar que `service-path` existe
2. Validar que `plan-content-file` existe y es legible
3. Crear `.agentbus-plans/` si no existe
4. Calcular siguiente número disponible
5. Construir el nombre: `{NNN}-{feature-slug}.md`
6. Escribir el plan en destino final
7. Imprimir: `Written: /home/jero/repos/payments-service/.agentbus-plans/003-kafka-migration.md`

**Validaciones de slug:**
- Lowercase
- Solo letras, números y guiones
- Si el input tiene espacios o mayúsculas → auto-normalizar (`"Kafka Migration"` → `"kafka-migration"`)

**Dependencies:** ninguna (stdlib only)

---

### `read_plan.py`

**Propósito:** Leer e imprimir el contenido de un plan del repo actual.

**Uso:**
```bash
# Desde dentro del repo del servicio:
uv run read_plan.py                  # lee el plan más reciente
uv run read_plan.py --plan 002       # lee el plan con número específico
uv run read_plan.py --list           # lista todos los planes disponibles
uv run read_plan.py --path           # imprime solo el path del plan seleccionado
```

**Output `--list`:**
```
Plans in .agentbus-plans/:
  001-kafka-migration.md       (draft — pending expert review)
  002-webhook-redesign.md      (refined — pending developer review)
```

El status se extrae leyendo la línea que contiene `**Status:**` en el archivo.

**Lógica:**
1. Detectar `.agentbus-plans/` en el directorio actual
2. Si no existe → `No plans found in this repo.`
3. Si `--list` → listar archivos con su status extraído
4. Si `--plan NNN` → buscar archivo que empiece con `NNN-`, leer e imprimir
5. Si ningún flag → leer el archivo con el número más alto, imprimir a stdout

**Nota de implementación:**
- `--path` permite que `agentbus-expert` actualice el plan in-place sin crear
  archivos nuevos ni depender de heurísticas de path.

**Dependencies:** ninguna (stdlib only)

---

## Skills

Formato: [Agent Skills spec](https://agentskills.io)
Cada skill es un `SKILL.md` con frontmatter YAML + instrucciones en markdown.

---

### `skills/agentbus-orchestrator/SKILL.md`

```markdown
---
name: agentbus-orchestrator
description: >
  Orchestrates a cross-service planning session. Reads documentation from
  multiple service repos and writes a tailored, numbered plan into each one.
  Use when planning a feature that spans more than one service.
compatibility: Requires uv and local filesystem write access to registered repos.
metadata:
  invocation: manual-only
---

# agentbus-orchestrator

You are coordinating a cross-service planning session. Your job is to read each
service's documentation and write a tailored plan into each repo so that every
coding agent can start its own planning session with full context.

This skill also supports a discovery mode for Q&A without file writes.

## Prerequisites

Before anything else, verify that `uv` is available:

```bash
uv --version
```

If not found, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then verify the requested services are registered:

```bash
uv run /absolute/path/to/agentbus-skills/scripts/list_services.py --json
```

If any requested service is not in the registry, stop and ask the developer to
register it first:

```bash
uv run /absolute/path/to/agentbus-skills/scripts/register_service.py <name> <absolute-path>
```

## Step 1 — Read service documentation

For each requested service, locate its repo path from the registry.
Then read files in this priority order:

1. `AGENTS.md`
2. `README.md`
3. `CLAUDE.md` or `claude.md`
4. `GEMINI.md` or `gemini.md`
5. Any other `.md` file at root level or one level deep

Rules:
- **Only `.md` files** — no source code, no config files
- Skip files over 300 lines (note the filename and skip reason)
- Read at most 5 files per service
- After reading each service, write a one-paragraph internal summary before
  moving to the next service — this prevents context exhaustion

**If no relevant `.md` files are found in a service repo:**
Invoke the `map-codebase` skill on that repo. Use the generated `AGENTS.md`
as your documentation input for that service.

## Step 2 — Generate plans

Branch by mode:

- Ask mode (`--ask "<question>"`): answer the question with evidence per service,
  list ambiguities, and do not write plan files.
- Plan mode (default): for each service, generate a plan document using this
  exact format:

```markdown
# Plan: <feature description>
**Service:** <service-name>
**Feature slug:** <feature-slug>
**Plan number:** <NNN>
**Date:** <ISO date>
**Status:** draft — pending expert review

---

## Context
<1-2 paragraphs: what this feature is and why it's being done>

## What is expected from this service
<clear description of the change this service needs to make>

## Decisions from other services
<one bullet per service — key constraint or decision relevant to this service>
- <service-A>: <decision>
- <service-B>: <decision>

## Open questions
<things this service's agent needs to resolve during its planning session>
- [ ] <question>
- [ ] <question>

## Other services involved
<one line per service — its role in this feature>
- <service-A>: <role>
- <service-B>: <role>

---
*Generated by agentbus-orchestrator. To be refined by agentbus-expert.*
```

Plans must be coherent with each other: if service A produces a Kafka event,
service B's plan must consume it with matching event names and payloads.

## Step 3 — Write plans

Plan mode only. For each service, save the generated plan to a temp file, then write it:

```bash
uv run /absolute/path/to/agentbus-skills/scripts/write_plan.py <service-path> <feature-slug> /tmp/plan_<service>.md
```

`write_plan.py` will auto-compute the next plan number for each repo.

## Step 4 — Report

Tell the developer:
- In ask mode: explicit statement that no plan files were written
- In plan mode: which services received a plan and the full file path of each
- Any services that were skipped and why
- Whether `map-codebase` was triggered for any service
- Suggested next step: open each service CLI and run `/agentbus-expert`
```

---

### `skills/agentbus-expert/SKILL.md`

```markdown
---
name: agentbus-expert
description: >
  Checks for pending AgentBus plans in this service repo. If a plan exists,
  reads it, analyzes the local codebase for impact, and produces a refined
  implementation plan. Run when starting work on a cross-service feature
  or when asked to check for AgentBus plans.
compatibility: Requires uv and local filesystem read/write access in current repo.
metadata:
  invocation: manual-or-contextual
---

# agentbus-expert

You are the domain expert for this service. Your job is to take a plan written
by the orchestrator and make it concrete: resolve open questions using knowledge
of the local codebase, surface constraints, and produce actionable implementation
steps.

## Step 0 — Check for plans

```bash
uv run scripts/read_plan.py --list
```

If no `.agentbus-plans/` folder exists or it is empty, report:
> No AgentBus plans found for this service. Proceeding normally.

Do not interfere with the agent's normal workflow.

## Step 1 — Read the plan

```bash
uv run scripts/read_plan.py           # latest plan
uv run scripts/read_plan.py --plan NNN  # specific plan if developer specified one
```

Acknowledge the feature context and what is expected from this service before
continuing.

## Step 2 — Analyze local impact

Explore the local repo to understand:
- Which modules, files, and classes are directly affected
- What API contracts, events, or data models might change
- What hard dependencies on other services exist (HTTP calls, shared schemas, etc.)
- Estimated effort and risk areas

Focus on what is relevant to the plan — do not do a full codebase audit.

## Step 3 — Resolve open questions

Go through each open question in the plan (`- [ ] ...`) and answer it using
your knowledge of the local codebase. If a question cannot be resolved without
input from another service or the developer, mark it explicitly with:
> ⚠ Needs input: <who> — <why>

## Step 4 — Refine and overwrite the plan

Update (not duplicate) the `## Expert Review` section and update the Status line.
Always overwrite the same plan file in place (resolved via `read_plan.py --path`).

The `## Expert Review` section format:

```markdown
## Expert Review
**Reviewed by:** <agent or CLI name>
**Date:** <ISO date>
**Status:** refined — pending developer review

### Local impact
<which files and modules are affected>

### Constraints
<what this service cannot or must do given its current architecture>

### Decisions
<what this service will do and how — concrete, not vague>

### Impact on other services
<contract changes, new events, or API changes others need to know about>

### Resolved questions
- [x] <question> → <answer>

### Still open
- [ ] <question that needs developer or peer input>

### Implementation steps
1. <concrete step>
2. <concrete step>
3. <...>
```

Also update the `**Status:**` line at the top of the file:
```
**Status:** refined — pending developer review
```

## Step 5 — Notify the developer

Summarize:
- Plan file path that was updated
- Key decisions made in this session
- Any questions still open and who needs to answer them
- Suggested next step (e.g., "Run `/agentbus-expert` in notifications-service")
```

---

### `skills/map-codebase/SKILL.md`

```markdown
---
name: map-codebase
description: >
  Explores the current project to understand its architecture, tech stack,
  and conventions. Writes findings to AGENTS.md. Use when a project has no
  documentation for AI agents, or to refresh existing docs. Also invoked
  automatically by agentbus-orchestrator when no relevant docs are found.
compatibility: Requires filesystem read/write access in target repository.
metadata:
  invocation: user-or-orchestrator
---

# map-codebase

You are a software engineering expert with many years of experience across
multiple languages and ecosystems.

Explore the current project directory to understand its architecture and main
details. Be thorough but precise — only document what you actually find.

## Task

1. Analyze the project structure and identify key configuration files:
   `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, etc.

2. Understand the technology stack, build process, and runtime architecture.

3. Identify how the code is organized and the main module divisions.

4. Discover project-specific development conventions, testing strategies,
   and deployment processes.

## Output

After exploration, write your findings into `AGENTS.md` at the project root.

- If `AGENTS.md` already exists, **merge** your findings with what is already
  there — preserve existing content, add or update sections as needed.
- If it does not exist, create it.

`AGENTS.md` is intended to be read by AI coding agents.
Write as if the reader knows nothing about this project.
Use the natural language found in the project's own comments and documentation.
Do not make assumptions or generalizations — only document what you find.

## Sections to include (as applicable)

- **Project overview** — what this service does, its role in the larger system
- **Build and test commands** — exact commands to build, run, and test
- **Architecture and module structure** — how the code is organized
- **Code style guidelines** — conventions found in the codebase
- **Testing instructions** — how to run tests, what coverage exists
- **Security considerations** — auth, secrets management, sensitive data handling
- **Key dependencies** — most important libraries and why they're used
- **Known constraints** — performance limits, external dependencies, tech debt

After writing `AGENTS.md`, report the file path and a brief summary of what
was documented.
```

---

## README.md del repo

```markdown
# agentbus-skills

Cross-service planning skills for LLM coding agents.

Eliminate the developer-as-messenger role when planning features that span
multiple services. The orchestrator reads each service's docs and writes a
tailored plan into each repo. Each service's agent refines the plan using
local knowledge.

## How it works

1. Register your services once:
   ```bash
   uv run scripts/register_service.py payments-service /path/to/payments-service
   uv run scripts/register_service.py notifications-service /path/to/notifications-service
   ```

2. Run the orchestrator from any CLI:
   ```bash
   /agentbus-orchestrator --ask "how does onboarding work across services?" payments notifications
   ```
   (discovery mode, no writes)

3. Run plan mode from any CLI:
   ```bash
   /agentbus-orchestrator "migrate to Kafka events" payments notifications
   ```
   (`payments` and `notifications` are aliases to canonical repo names)

4. Open each service's CLI and refine the plan:
   ```bash
   /agentbus-expert
   ```

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — Python package and script runner
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Any LLM coding agent supporting the [Agent Skills spec](https://agentskills.io)
  (Claude Code, Gemini CLI, Cursor, Codex, etc.)

## Installation

```bash
# Orchestrator — install globally (available in all projects)
npx skills add zentik/agentbus-skills --skill agentbus-orchestrator -g

# Expert — install per service repo
npx skills add zentik/agentbus-skills --skill agentbus-expert

# map-codebase — optional, install globally for manual use
npx skills add zentik/agentbus-skills --skill map-codebase -g
```

## Skills

| Skill | Scope | Invocation |
|---|---|---|
| `agentbus-orchestrator` | global | `/agentbus-orchestrator "<feature>" <svc1> <svc2>` |
| `agentbus-expert` | per project | `/agentbus-expert` |
| `map-codebase` | global or per project | `/map-codebase` |

## Scripts

All scripts require `uv` and use only Python stdlib — no extra dependencies.

| Script | Purpose |
|---|---|
| `register_service.py` | Add a service to the global registry |
| `list_services.py` | List all registered services |
| `next_plan_number.py` | Get next available plan number for a repo |
| `write_plan.py` | Write a plan file into a service repo |
| `read_plan.py` | Read a plan from the current repo |
```

---

## Checklist de implementación

### Scripts
- [ ] `register_service.py` — registry R/W, path validation
- [ ] `list_services.py` — human + JSON output
- [ ] `next_plan_number.py` — scan `.agentbus-plans/`, return `NNN`
- [ ] `write_plan.py` — slug normalization, crear carpeta, escribir archivo
- [ ] `read_plan.py` — leer latest, por número, o listar con status

### Skills
- [ ] `skills/agentbus-orchestrator/SKILL.md`
- [ ] `skills/agentbus-expert/SKILL.md`
- [ ] `skills/map-codebase/SKILL.md`

### Repo
- [ ] `README.md`
- [ ] Verificar que todos los scripts corren con `uv run` sin dependencias externas
- [ ] Smoke test: registrar 2 servicios, correr orchestrator, correr expert

### Validación final
- [ ] Escenario 1: orchestrator escribe planes en 3 repos
- [ ] Escenario 2: expert refina un plan
- [ ] Escenario 3: expert con repo sin planes — no interfiere
- [ ] Escenario 4: repo sin docs — map-codebase se activa automáticamente
- [ ] Escenario 5: numeración correcta con planes existentes