# AgentBus Skills

Cross-service planning skills for LLM coding agents.

This project removes the "developer as messenger" problem when understanding and planning features that touch multiple repos. Uses an **evidence-based workflow**: files are the source of truth.

## Core Principle: Evidence Over Communication

Instead of accumulating state in memory, AgentBus writes artifacts at each stage:

```
Wave 1: Service Mapping    →  AGENTS.md in each service
Wave 2: Plan Refinement    →  PLAN.md in each service  
Wave 3: Verification       →  REPORT.md in each service
Final:   Orchestrator reads REPORTs → Global view
```

Benefits:
- **Context efficiency**: Orchestrator reads only what it needs
- **Auditability**: Complete history in version-controlled files
- **Resumability**: Failed waves can be retried independently
- **Reusability**: AGENTS.md serves as ongoing service documentation

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
│   │   └── review/               # Consistency checker
│   │       └── SKILL.md
│   └── map-codebase/             # Codebase exploration
│       └── SKILL.md
```

### Skill Hierarchy

| Skill | Role | Invocation |
|-------|------|------------|
| `agentbus` | Entry point / router | `/agentbus-orchestrator ...` |
| `agentbus/orchestrator` | Wave coordinator | Via `agentbus` |
| `agentbus/service-agent` | Service specialist | Via Task tool |
| `agentbus/review` | Consistency checker | `/agentbus-review ...` |

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
│   ├── AGENTS.md                 # Written by Wave 1
│   └── .agentbus-plans/
│       ├── 001-feature-slug.md         # Written by Wave 2
│       └── 001-feature-slug-REPORT.md  # Written by Wave 3
│
└── notifications-service/
    └── ... (same structure)
```

## Prerequisites

None for core orchestration. Skills use `Task` tool for subagent spawning.

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

### Phase 1: Discovery (Optional)

Ask questions without writing files:

```bash
/agentbus-orchestrator --ask "how does onboarding work across services?" payments notifications
```

### Phase 2: Initialize Plan

Create seed plan for confirmed services:

```bash
/agentbus-orchestrator "remove deprecated field from Tool model" tools-service bot-service
```

This creates:
- `agentbus-orchestrator/001-remove-field/status.json`
- `agentbus-orchestrator/001-remove-field/SEED-PLAN.md`

### Phase 3: Wave 1 — Service Mapping

Run orchestrator again to start mapping:

```bash
# Reads status.json, launches parallel subagents
/agentbus-orchestrator --continue 001-remove-field
```

Each subagent writes:
- `{service}/AGENTS.md` (creates or updates)
- Summary JSON to orchestrator workspace

### Phase 4: Wave 2 — Plan Refinement

```bash
/agentbus-orchestrator --continue 001-remove-field
```

Each subagent:
- Reads `AGENTS.md` from its service
- Reads `SEED-PLAN.md`
- Writes refined `PLAN.md` to service repo

### Phase 5: Wave 3 — Verification

```bash
/agentbus-orchestrator --continue 001-remove-field
```

Each subagent:
- Reads `PLAN.md` from its service
- Reads `PLAN.md` from dependent services
- Writes `REPORT.md` with verification status

### Phase 6: Review

```bash
/agentbus-review --feature-slug "001-remove-field"
```

Reads all `REPORT.md` files and checks:
- All services report "ready" status
- Dependencies are mirrored
- API contracts are consistent
- Deploy order is coherent

## How Verification Works

### Service-Level Verification (Wave 3 Subagent)

Each service subagent writes `REPORT.md` with:
- Verification status: ready / needs_work / blocked
- Implementation checklist
- Files to modify
- Local risks with mitigations
- Cross-service dependencies
- Open questions with owners

### Global Verification (Orchestrator + Review)

Orchestrator reads all `REPORT.md` and verifies:
- Plan completeness
- Dependency mirroring (A depends on B → B acknowledges A)
- Contract consistency
- Sequencing coherence
- Question ownership

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
- AGENTS.md persists as living service documentation
- Plans are kept in repos for visibility/auditability
- Current version favors simplicity over strong concurrency controls
