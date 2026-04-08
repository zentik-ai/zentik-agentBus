# AgentBus Skills — Agent Guide

Generated: 2026-04-06

## Project Overview

AgentBus Skills is a **cross-service planning system for LLM coding agents**. It eliminates the "developer as messenger" problem when planning features that span multiple microservices.

**Core Principle**: Evidence over communication. Files are the source of truth.

The system uses an **evidence-based workflow** where artifacts are written at each stage instead of accumulating state in memory:

```
Wave 1:  Service Mapping      →  AGENTS.md per service
Wave 2a: Plan Refinement      →  PLAN.md per service
Wave 2b: Context Queries      →  Answers from adjacent services
Wave 3:  Implementation       →  Modified code + CHANGES.md
Wave 4:  Verification         →  TEST-RESULTS.md per service
Wave 4b: Adjustments (opt)   →  Minor fixes + clarifications
Wave 5:  Wrap-up (opt)       →  Git commits + deployment prep
```

**Benefits**:
- **Context efficiency**: Orchestrator reads only what it needs
- **Auditability**: Complete history in version-controlled files
- **Resumability**: Failed waves can be retried independently
- **Reusability**: AGENTS.md serves as living service documentation

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Markdown (SKILL.md files with YAML frontmatter) |
| **Orchestration** | Skill-based via `Task` tool |
| **State Management** | File-based (JSON + Markdown) |
| **Subagents** | Spawned via `Task` tool for parallel execution |
| **Dependencies** | None for core orchestration |

---

## Architecture

### Seven-Wave Execution Model

| Wave | Name | Input | Output | Purpose |
|------|------|-------|--------|---------|
| 1 | Service Mapping | Service codebase | AGENTS.md | Understand the service |
| 2a | Plan Refinement | AGENTS.md + requirement | PLAN.md | Plan the change |
| 2b | Context Queries | PLAN provisional | Answers from other services | Get info without mapping |
| 3 | Implementation | PLAN.md | Modified code + CHANGES.md | Execute (no commits) |
| 4 | Verification | Modified code + tests | TEST-RESULTS.md | Verify it works |
| 4b | Adjustments (opt) | TEST-RESULTS.md | Minor fixes | Quick fixes, no replan |
| 5 | Wrap-up (opt) | Verified changes | COMMITS.md | Create commits |

**Important**: Commits only happen in Wave 5, after successful verification and user confirmation.

**Key Features**:
- **Context Queries (2b)**: Query adjacent services without adding them to the plan
- **Adjustments (4b)**: Minor fixes after tests without full replanning

### Skill Hierarchy

```
agentbus (base skill - entry point/router)
├── agentbus/orchestrator (wave coordinator)
│   └── spawns agentbus/service-agent via Task tool
└── agentbus/review (consistency checker - called by user)
```

| Skill | Purpose | Location | Invocation |
|-------|---------|----------|------------|
| **agentbus** | Entry point / router | `skills/agentbus/SKILL.md` | Implicit via subskill |
| **agentbus-orchestrator** | Coordinates waves, spawns subagents | `skills/agentbus/orchestrator/SKILL.md` | `/agentbus-orchestrator ...` |
| **agentbus-service-agent** | Per-service specialist | `skills/agentbus/service-agent/SKILL.md` | Via Task tool only |
| **agentbus-review** | Verifies cross-service consistency | `skills/agentbus/review/SKILL.md` | `/agentbus-review ...` |
| **map-codebase** | Codebase explorer | `skills/map-codebase/SKILL.md` | Auto-invoked |

---

## Directory Structure

```
agentbus-skills/
├── README.md                          # Human-facing documentation
├── AGENTS.md                          # This file - agent guide

├── .gitignore                         # Git ignore rules
├── skills/
│   ├── SKILL.md                       # Skill registry / base skill index
│   ├── agentbus/                      # AgentBus skill family
│   │   ├── SKILL.md                   # Base skill (entry point)
│   │   ├── orchestrator/              # Wave coordinator subskill
│   │   │   └── SKILL.md
│   │   ├── service-agent/             # Per-service specialist subskill
│   │   │   └── SKILL.md
│   │   └── review/                    # Consistency checker subskill
│   │       └── SKILL.md
│   └── map-codebase/                  # Independent codebase explorer
│       └── SKILL.md
```

---

## Key Conventions

### SKILL.md Format

All skills use YAML frontmatter with standard metadata:

```yaml
---
name: skill-name
description: What this skill does
version: 1.0.0
triggers: [keyword1, keyword2]
tools: [Read, Write, Bash, Task]
tags: [tag1, tag2]
---
```

### Workspace Layout (Runtime)

```
workspace/                          # Parent folder of all repos
├── agentbus-orchestrator/          # Orchestrator state (NOT a git repo)
│   └── 001-feature-slug/
│       ├── status.json             # Wave tracking, resume/retry
│       ├── SEED-PLAN.md            # Initial vision
│       ├── PLAN.md                 # Consolidated view (final)
│       ├── TEST-PLAN.md            # Cross-service tests
│       ├── DEPLOY-ORDER.md         # Rollout sequence
│       ├── REVIEW.md               # Consistency review report
│       └── service-outputs/        # Subagent summaries
│           └── {service}.json
│
├── payments-service/               # Service repo
│   ├── AGENTS.md                   # ← Wave 1: service documentation
│   └── .agentbus-plans/
│       └── 001-feature/            # ← Wave 2-5: plan folder
│           ├── PLAN.md             # ← Wave 2: refined plan
│           ├── CHANGES.md          # ← Wave 3: implementation log
│           ├── TEST-RESULTS.md     # ← Wave 4: test results
│           └── COMMITS.md          # ← Wave 5: commit log (optional)
│
└── notifications-service/
    └── ... (same structure)
```

### Artifact Chain

1. **AGENTS.md** — Living service documentation (stack, arch, APIs, conventions)
2. **PLAN.md** — Refined implementation plan per feature
3. **CHANGES.md** — List of files modified in Wave 3 (ready for commit)
4. **TEST-RESULTS.md** — Verification report with test results
5. **COMMITS.md** — Git commit log (created in Wave 5, optional)

### Status Tracking

`status.json` tracks progress without storing content:
- Current wave
- Service statuses (pending/ready/completed/failed)
- Artifact paths (not content)
- Retry counts

Example status.json:
```json
{
  "plan_id": "001-feature",
  "feature_slug": "feature",
  "services": ["svc1", "svc2"],
  "status": "in_progress",
  "current_wave": 2,
  "waves": {
    "wave_1_mapping": {"status": "completed"},
    "wave_2_refinement": {"status": "in_progress"},
    "wave_3_implementation": {"status": "pending"},
    "wave_4_verification": {"status": "pending"},
    "wave_5_wrapup": {"status": "pending", "optional": true}
  }
}
```

---

## Development Workflow

### Typical Usage Flow

1. **Discovery** (optional):
   ```
   /agentbus-orchestrator --ask "how does X work across services?" svc1 svc2
   ```

2. **Initialize Plan**:
   ```
   /agentbus-orchestrator "feature description" svc1 svc2
   ```
   Creates: `agentbus-orchestrator/001-feature/status.json` + `SEED-PLAN.md`

3. **Wave 1 - Service Mapping**:
   ```
   /agentbus-orchestrator --continue 001-feature
   ```
   Creates/updates: `{service}/AGENTS.md`

4. **Wave 2 - Plan Refinement**:
   ```
   /agentbus-orchestrator --continue 001-feature
   ```
   Creates: `{service}/.agentbus-plans/001-feature/PLAN.md`

5. **Wave 3 - Implementation**:
   ```
   /agentbus-orchestrator --continue 001-feature
   ```
   Modifies code, creates: `{service}/.agentbus-plans/001-feature/CHANGES.md`

6. **Wave 4 - Verification**:
   ```
   /agentbus-orchestrator --continue 001-feature
   ```
   Creates: `{service}/.agentbus-plans/001-feature/TEST-RESULTS.md`

7. **Review**:
   ```
   /agentbus-review --feature-slug "001-feature"
   ```
   Creates: `agentbus-orchestrator/001-feature/REVIEW.md`

8. **Wave 5 - Wrap-up** (optional, requires user confirmation):
   ```
   /agentbus-orchestrator --continue 001-feature
   ```
   Creates git commits + `{service}/.agentbus-plans/001-feature/COMMITS.md`

---

## Testing Strategy

### Dry-Run Phases

1. **Phase 1**: Single service, Wave 1 only
2. **Phase 2**: Single service, all waves
3. **Phase 3**: Two services, all waves
4. **Phase 4**: Retry and mid-flight service addition

### Success Criteria

- [ ] Wave 1 creates AGENTS.md with complete structure
- [ ] Wave 2 reads AGENTS.md, writes PLAN.md
- [ ] Wave 3 modifies code, writes CHANGES.md
- [ ] Wave 4 runs tests, writes TEST-RESULTS.md
- [ ] Orchestrator reads reports for global verification
- [ ] Retry mechanism works (overwrite artifacts)
- [ ] Resume from status.json works

---

## Error Handling & Recovery

### Subagent Fails

1. Check `status.json` for error details
2. Fix underlying issue
3. Re-run: `/agentbus-orchestrator --continue {plan-id}`
4. Failed subagent re-runs, others unchanged

### Add Service Mid-Flight

1. Update `status.json` to add service
2. Re-run current wave
3. Only new service gets processed

### Resume After Interruption

1. Read `status.json` to see current wave
2. Run: `/agentbus-orchestrator --continue {plan-id}`
3. Continues from where it left off

---

## Security Considerations

### Wave 3 is Destructive (but no commits)

- Modifies source code files
- Runs tests
- Does NOT commit changes

### Wave 5 is Commits (requires confirmation)

- Only runs after explicit user confirmation
- Creates git commits
- Should be on feature branch, not main/master

### Best Practices

1. **Confirm with user** before Wave 3 (code modification)
2. **Confirm with user** before Wave 5 (git commits)
3. Use **feature branches** to isolate changes
4. **Working directory** should be clean before starting

---

## Service Registry

Global registry file: `~/.agentbus/services.json`

```json
{
  "payments-service": "/home/user/repos/payments-service",
  "notifications-service": "/home/user/repos/notifications-service"
}
```

**To register a service**: Read `~/.agentbus/services.json`, add entry, write back.

**To list services**: Read `~/.agentbus/services.json` and parse.

---

## Language Notes

This project uses **mixed language documentation**:
- Main documentation (README.md, SKILL.md files): **English**
- Design documents (WAVE-3-4-DESIGN.md): **Spanish**
- Code comments: Varies by context

When modifying files, match the language of the existing content.

---

## External Dependencies

- **None** for core orchestration
- `Task` tool (provided by Kimi Code CLI) for subagent spawning

---

## Anti-Patterns to Avoid

❌ **Don't**: Run all waves in one session (context exhaustion)
✅ **Do**: Run one wave at a time, review, then continue

❌ **Don't**: Modify AGENTS.md manually during planning
✅ **Do**: Let Wave 1 subagent update it

❌ **Don't**: Skip Wave 4 (verification)
✅ **Do**: Always verify before committing

❌ **Don't**: Add too many services (>5) without user confirmation
✅ **Do**: Propose list, let user confirm/adjust

❌ **Don't**: Commit in Wave 3 (only Wave 5)
✅ **Do**: Leave files modified but uncommitted after Wave 3

---

## Related Files

- `README.md` — Human-facing project overview
- `WAVE-3-4-DESIGN.md` — Detailed design for implementation and verification waves (Spanish)
- `skills/agentbus/SKILL.md` — Base skill definition
- `skills/agentbus/orchestrator/SKILL.md` — Orchestrator protocol
- `skills/agentbus/service-agent/SKILL.md` — Service agent protocol
- `skills/agentbus/review/SKILL.md` — Review protocol
- `skills/map-codebase/SKILL.md` — Codebase exploration skill

---

## Version

AgentBus Skills v1.0.0 — Evidence-Based Wave Model
