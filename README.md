# AgentBus Skills

Cross-service planning skills for LLM coding agents.

This project removes the "developer as messenger" problem when understanding and planning features that touch multiple repos. Uses an **evidence-based workflow**: files are the source of truth.

## Core Principle: Evidence Over Communication

Instead of accumulating state in memory, AgentBus writes artifacts at each stage:

```
Wave 1:   Service Mapping          →  .planning/codebase/ (5 docs per service)
Wave 1.5: Design Alignment         →  Validated approach decisions
Wave 2:   Plan Refinement          →  PLAN.md (plan the change)
Wave 2.5: Plan QA & Concerns       →  QA-REPORT.md (surface gaps for user input)
Wave 2.6: Plan Alignment           →  Cross-service consistency check
Wave 3:   Implementation           →  Code modified (no commits yet)
Wave 3.5: Contract Validation      →  Deep implementation check (optional)
Wave 4:   Verification             →  TEST-RESULTS.md (verify it works)
Wave 4b:  Adjustments (opt)        →  Minor fixes + clarifications
Wave 5:   Wrap-up (opt)            →  Git commits + deployment prep
```

Benefits:
- **Context efficiency**: Orchestrator reads only what it needs
- **Auditability**: Complete history in version-controlled files
- **Resumability**: Failed waves can be retried independently
- **Reusability**: `.planning/codebase/` serves as ongoing service documentation

## Repository Layout

```text
agentbus-skills/
├── skills/
│   ├── agentbus/                 # Skill family
│   │   ├── SKILL.md              # Entry point / base skill
│   │   ├── orchestrator/         # Cross-service coordinator
│   │   │   └── SKILL.md
│   │   ├── service-agent/        # Per-service specialist
│   │   │   └── SKILL.md
│   │   ├── review/               # Consistency checker
│   │   │   └── SKILL.md
│   │   └── map-codebase/         # Deep codebase mapper
│   │       └── SKILL.md
│   └── SKILL.md                  # Root skill manifest
```

### Skill Hierarchy

| Skill | Role | Invocation |
|-------|------|------------|
| `agentbus` | Entry point / docs | `/agentbus` (information only) |
| `agentbus orchestrator` | Wave coordinator | `/agentbus orchestrator ...` |
| `agentbus service agent` | Service specialist | Via Task tool (internal) |
| `agentbus review` | Consistency checker | `/agentbus review ...` |

**Note**: Skill names use hyphens (not slashes) for compatibility with Cursor's skill system.

### Wave Summary

| Wave | Purpose | Key Output |
|------|---------|------------|
| 1 | Map services | `.planning/codebase/` (5 docs) |
| 1.5 | Validate approaches | Design decisions |
| 2 | Create plans | `PLAN.md` |
| 2.5 | Surface concerns | `QA-REPORT.md` + user input |
| 2.6 | Check consistency | Alignment report |
| 3 | Implement changes | Modified code + `CHANGES.md` |
| 4 | Verify with tests | `TEST-RESULTS.md` |
| 4b | Adjust/fix minor issues | Updated code |
| 5 | Create commits | Git commits + `COMMITS.md` |

## Workspace Layout

Your workspace (parent of all service repos):

```
workspace/
├── agentbus-orchestrator/        # Orchestrator workspace (not a git repo)
│   └── 001-feature-slug/
│       ├── status.json           # Wave tracking
│       ├── SEED-PLAN.md          # Initial vision
│       ├── PLAN.md               # Consolidated view
│       ├── TEST-PLAN.md          # Cross-service tests
│       ├── DEPLOY-ORDER.md       # Rollout sequence
│       └── service-outputs/      # Subagent summaries
│           └── {service}.json
│
├── payments-service/             # Service repo
│   └── .planning/
│       └── codebase/             # ← Wave 1: 5 service documents
│           ├── STACK.md
│           ├── ARCHITECTURE.md
│           ├── STRUCTURE.md
│           ├── CONVENTIONS.md
│           └── CONCERNS.md
│   └── .agentbus-plans/
│       └── 001-feature-slug/     # Plan folder
│           ├── PLAN.md           # Written by Wave 2
│           ├── QA-REPORT.md      # Written by Wave 2.5
│           ├── CHANGES.md        # Written by Wave 3
│           ├── TEST-RESULTS.md   # Written by Wave 4
│           └── COMMITS.md        # Written by Wave 5 (optional)
│
└── notifications-service/
    └── ... (same structure)
```

## Prerequisites

### 1. Load the AgentBus Skill (Required First Step)

Before using any AgentBus commands, **you must initialize the skill** so the LLM understands the system:

```
/agentbus
```

This loads the base skill which provides context about:
- The wave execution model
- How to route to subskills (`agentbus orchestrator`, `agentbus review`)
- When to use AgentBus vs other skills

**Without this step, the LLM won't know how to use the orchestrator properly.**

### 2. Local Service Repositories (Required)

**All services you want to modify must be:**
- ✅ Cloned locally on your machine
- ✅ Inside your current working directory (workspace)
- ✅ Listed in `~/.agentbus/services.json` with correct paths

**Example:**
```
workspace/
├── exitus-agent-tools/     ← Local clone
├── exitus-bot-wa/          ← Local clone
└── agentbus-orchestrator/  ← Created by the tool
```

**The orchestrator cannot work with remote repositories** — it needs local access to read and modify files.

### 3. Service Registry Setup

## Service Registry

Global registry file: `~/.agentbus/services.json`

```json
{
  "payments-service": "/home/jero/repos/payments-service",
  "notifications-service": "/home/jero/repos/notifications-service"
}
```

**To register a service**: Read `~/.agentbus/services.json`, add entry, write back.

**To list services**: Read `~/.agentbus/services.json` and parse.

## Typical Flow

The flow is split into two stages: **Setup** (one-time per feature) and **Waves** (the iterative execution loop). Each wave produces a file artifact and you review before continuing.

### Setup

#### Discovery (optional)

Ask questions without writing files:

```bash
/agentbus orchestrator --ask "how does onboarding work across services?" payments notifications
```

#### Initialize Plan

Create the seed plan with natural language (services detected automatically):

```bash
/agentbus orchestrator "remove deprecated field from Tool model in tools and bot"
```

The orchestrator:
1. Detects services mentioned in your prompt ("tools" → exitus-agent-tools, "bot" → exitus-bot-wa)
2. Asks for confirmation of detected services
3. Validates plan numbering (scans `.agentbus-plans/` in each service, finds next sequential number)
4. Creates:
   - `agentbus-orchestrator/004-remove-field/status.json`
   - `agentbus-orchestrator/004-remove-field/SEED-PLAN.md`

**Fuzzy matching examples**:
- "bot de WA" → exitus-bot-wa
- "tools" → exitus-agent-tools
- "api gateway" → exitus-api-gateway

### Waves

All wave commands use the same form: `/agentbus orchestrator --continue <plan-id>`. The orchestrator reads `status.json` and runs the next pending wave.

#### Wave 1 — Service Mapping

```bash
/agentbus orchestrator --continue 004-remove-field
```

Each subagent writes:
- `{service}/.planning/codebase/*.md` (5 documents, creates or updates)
- Summary JSON to orchestrator workspace

#### Wave 2 — Plan Refinement

```bash
/agentbus orchestrator --continue 004-remove-field
```

Each subagent:
- Reads `.planning/codebase/` documents from its service (especially `CONVENTIONS.md`)
- Reads `SEED-PLAN.md`
- Writes refined `PLAN.md` to its service repo

#### Wave 2.5 — Plan QA & Concerns

```bash
/agentbus orchestrator --continue 004-remove-field
```

Each subagent:
- Reads `PLAN.md` and `.planning/codebase/` docs
- Identifies concerns, gaps, and doubts
- Writes `QA-REPORT.md`

The orchestrator:
- Consolidates all QA reports
- Presents questions and concerns to you
- Refines plans based on your input

#### Wave 3 — Implementation

⚠️ **Destructive** — Modifies source code (does not commit yet)

```bash
/agentbus orchestrator --continue 004-remove-field
```

Each subagent:
- Reads `PLAN.md` from its service
- Implements changes to source code
- Writes `CHANGES.md` with modified files

The orchestrator will ask for confirmation before proceeding.

#### Wave 4 — Verification

```bash
/agentbus orchestrator --continue 004-remove-field
```

Each subagent:
- Reads `CHANGES.md` from its service
- Runs tests
- Writes `TEST-RESULTS.md` with results

### Review

```bash
/agentbus review --feature-slug "004-remove-field"
```

Reads all `PLAN.md`, `QA-REPORT.md`, and `TEST-RESULTS.md` files and checks:
- All services pass tests
- Cross-service dependencies are mirrored
- API contracts are consistent
- Deploy order is coherent
- High-severity QA concerns are addressed in the final plan

## How Verification Works

Verification is split across multiple stages and artifacts. There is no single `REPORT.md` — each wave produces a focused document.

### Per-Service Artifacts

Each service writes the following inside `{service}/.agentbus-plans/{plan-id}/`:

| Artifact | Wave | Contents |
|----------|------|----------|
| `PLAN.md` | 2 | Files to modify, approach, dependencies, rollback plan |
| `QA-REPORT.md` | 2.5 | Concerns (severity), gaps, questions for the user, recommendations |
| `CHANGES.md` | 3 | Log of files modified during implementation |
| `TEST-RESULTS.md` | 4 | Test summary, coverage, cross-service compatibility checks |
| `COMMITS.md` | 5 (opt) | Commit log written after wrap-up |

### Cross-Service Verification

Two layers of cross-service verification run during the flow:

1. **Wave 2.6 — Plan Alignment** (orchestrator): reads every `PLAN.md` and detects design-level mismatches (endpoint paths, field names, HTTP methods, schema differences). Cheap to fix because it happens before implementation.
2. **Wave 3.5 — Contract Validation** (optional, specialist agents): after implementation, validates that the actual code matches the planned contracts. Detects implementation drift, type mismatches, and silent regressions.

### Final Review (`/agentbus review`)

Run after Wave 4. Reads `PLAN.md`, `QA-REPORT.md`, and `TEST-RESULTS.md` from every service and verifies:
- Plan completeness (no missing artifacts)
- Dependency mirroring (A depends on B → B acknowledges A)
- API contract consistency between producer and consumer
- Sequencing coherence (no circular deploy order)
- Question ownership (every open question has an owner and blocking status)
- High-severity QA concerns are resolved in the final plan

## Adding Services Mid-Flight

1. Update `status.json` to add service
2. Re-run orchestrator for current wave
3. Only new service gets processed

## Retry Strategy

If a subagent fails:
1. Check `status.json` for error details
2. Fix underlying issue
3. Re-run orchestrator for that wave
4. Subagent overwrites its artifacts

## Notes

- **No helper scripts required** for core orchestration logic
- Skills use `Task` tool to spawn parallel subagents
- `.planning/codebase/` persists as living service documentation (5 specialized documents)
- Plans are kept in repos for visibility/auditability
- Current version favors simplicity over strong concurrency controls
- The orchestrator acts as a solution architect: it understands cross-service implications but **never reads source code directly** — it always delegates to specialist agents. It does read planning artifacts (`PLAN.md`, `QA-REPORT.md`, `CHANGES.md`, etc.) since those are documents, not code.
