# AgentBus Skills — Agent Guide

Generated: 2026-04-06

## Project Overview

Cross-service planning system for LLM coding agents. Eliminates the "developer as messenger" problem when planning features that span multiple microservices.

**Core Principle**: Evidence over communication. Files are the source of truth.

## Technology Stack

- **Language**: Markdown (SKILL.md files)
- **Orchestration**: Skill-based via `Task` tool
- **State Management**: File-based (JSON + Markdown)
- **Subagents**: Spawned via `Task` tool for parallel execution

## Architecture

### Three-Wave Execution Model

```
Wave 1: Service Mapping     →  AGENTS.md per service
Wave 2: Plan Refinement     →  PLAN.md per service
Wave 3: Verification        →  REPORT.md per service
Final:  Global synthesis    →  Consolidated views
```

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Orchestrator | Coordinates waves, reads artifacts | `skills/agentbus-orchestrator/` |
| Service Agent | Maps, refines, verifies per service | `skills/agentbus-service-agent/` |
| Review | Checks cross-service consistency | `skills/agentbus-review/` |

### File Structure

```
agentbus-skills/
├── README.md
├── AGENTS.md                    # This file
├── agentBus_PRD                 # Product requirements
├── agentBus_details.md          # Implementation details (Spanish)
├── refactor_agentbus.md         # Refactor plan
└── skills/
    ├── agentbus-orchestrator/   # Global coordinator
    ├── agentbus-service-agent/  # Per-service specialist
    ├── agentbus-review/         # Consistency checker
    └── map-codebase/            # Codebase exploration
```

## Key Conventions

### Workspace Layout (Runtime)

```
workspace/
├── agentbus-orchestrator/       # Orchestrator state (not a git repo)
│   └── 001-feature/
│       ├── status.json          # Wave tracking
│       ├── SEED-PLAN.md         # Initial vision
│       ├── PLAN.md              # Consolidated view
│       └── service-outputs/     # Subagent summaries
│
├── service-a/                   # Service repo
│   ├── AGENTS.md               # Written by Wave 1
│   └── .agentbus-plans/
│       ├── 001-feature.md      # Written by Wave 2
│       └── 001-feature-REPORT.md # Written by Wave 3
│
└── service-b/
    └── ... (same structure)
```

### Artifact Chain

1. **AGENTS.md** — Service documentation (stack, arch, APIs, conventions)
2. **PLAN.md** — Refined implementation plan per feature
3. **REPORT.md** — Verification report with readiness status

### Status Tracking

`status.json` tracks progress without storing content:
- Current wave
- Service statuses
- Artifact paths (not content)
- Retry counts

## Testing

### Dry-Run Strategy

1. **Phase 1**: Single service, Wave 1 only
2. **Phase 2**: Single service, all 3 waves
3. **Phase 3**: Two services, all 3 waves
4. **Phase 4**: Retry and mid-flight service addition

### Success Criteria

- [ ] Wave 1 creates AGENTS.md with complete structure
- [ ] Wave 2 reads AGENTS.md, writes PLAN.md
- [ ] Wave 3 reads PLAN.md, writes REPORT.md
- [ ] Orchestrator reads REPORTs for global verification
- [ ] Retry mechanism works (overwrite artifacts)
- [ ] Resume from status.json works

## External Dependencies

- None for core orchestration
- `Task` tool (provided by Kimi Code CLI) for subagent spawning

## Notes

- Orchestrator lives at workspace level, not in a service repo
- Subagents write to their own service repos only
- No helper scripts required for core flow
- AGENTS.md persists as living documentation
