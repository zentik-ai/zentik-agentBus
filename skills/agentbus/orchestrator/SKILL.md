---
name: agentbus orchestrator
description: Cross-service planning orchestrator for AgentBus. Coordinates multi-wave planning across microservices using evidence-based workflow. Updated for Deep Mapping (5-document AGENTS/ folder).
version: 2.1.0
triggers: [agentbus plan, cross-service feature, multi-service orchestration]
tools: [Read, Write, Bash, Glob, Grep, Task]
tags: [agentbus, orchestrator, wave-based, coordination, microservices]
---

# AgentBus Orchestrator

Coordinates cross-service planning across microservices. Lives at the workspace level (parent folder of service repos), not inside any service.

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado para coordinar waves.

## Core Principle: Explicit Instructions

**Subagents CANNOT see your context.** You must explicitly tell them:
1. **What files to read** (absolute paths)
2. **What to do with them** (analyze, extract, compare)
3. **What files to write** (absolute paths)

---

## Wave Flow (Updated for Deep Mapping)

```
Wave 1: Service Mapping    →  AGENTS/ (5 docs via map-codebase)
Wave 1.5: Design Alignment →  Validated approach decisions
Wave 2: Plan Refinement    →  PLAN.md
Wave 2.5: Contract Check   →  Consistency validation (optional)
Wave 3: Implementation     →  Code modified (no commits yet)
Wave 4: Verification       →  TEST-RESULTS.md
Wave 5: Wrap-up (optional) →  Git commits + final deployment prep
```

---

## Subagent Communication Protocol

**CRITICAL**: Subagents receive NO context from you. The `prompt` parameter is their ONLY source of information.

### Required Prompt Structure

```python
Task(
    subagent_name="agentbus [subskill]",
    description="Wave X: [description]",
    prompt=json.dumps({
        # 1. MISSION - What to do
        "mission": "Create detailed implementation plan",
        "wave": 2,
        "mode": "plan_refinement",  # If applicable
        
        # 2. CONTEXT - What to read (ABSOLUTE PATHS)
        "read_files": {
            "agents_dir": "/workspace/service/.agentbus/AGENTS",
            "required_documents": [
                "STACK.md",
                "ARCHITECTURE.md", 
                "STRUCTURE.md",
                "CONVENTIONS.md",  # MOST IMPORTANT
                "CONCERNS.md"
            ],
            "seed_plan": "/workspace/agentbus-orchestrator/001-feature/SEED-PLAN.md",
            "design_decisions": "/workspace/agentbus-orchestrator/001-feature/service-outputs/service-dac.json"
        },
        "read_instructions": {
            "order": ["CONVENTIONS.md", "ARCHITECTURE.md", "STRUCTURE.md", "STACK.md", "CONCERNS.md"],
            "focus": "CONVENTIONS.md contains decision patterns - read this first",
            "fallback": "If any file missing, proceed with available info and note in report"
        },
        
        # 3. OUTPUT - What to write (ABSOLUTE PATHS)
        "output_files": {
            "refined_plan": "/workspace/service/.agentbus-plans/001-feature/PLAN.md",
            "summary_json": "/workspace/agentbus-orchestrator/001-feature/service-outputs/service.json"
        },
        "output_requirements": {
            "plan_must_include": ["approach_selected", "files_to_modify", "testing_strategy"],
            "summary_must_include": ["status", "artifacts_written", "blockers"]
        },
        
        # 4. SERVICE CONTEXT
        "service": {
            "name": "service-name",
            "path": "/workspace/service"
        }
    }),
    readonly=False
)
```

---

## Wave-by-Wave Subagent Instructions

### Wave 1: Service Mapping

**Subagent**: `agentbus map-codebase`

```python
Task(
    subagent_name="agentbus map-codebase",
    description=f"Wave 1: Deep map {service}",
    prompt=json.dumps({
        "mission": "Explore codebase and generate 5 AGENTS/ documents",
        "wave": 1,
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "discovery_focus": {
            "stack": ["language", "framework", "database", "dependencies"],
            "architecture": ["pattern", "layers", "data_flow"],
            "structure": ["directory_layout", "naming_conventions"],
            "conventions": ["patterns_available", "when_to_use_each", "decision_matrix"],
            "concerns": ["tech_debt", "known_issues", "limitations"]
        },
        "output_files": {
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "documents_to_create": [
                "STACK.md",
                "ARCHITECTURE.md",
                "STRUCTURE.md",
                "CONVENTIONS.md",
                "CONCERNS.md"
            ],
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

**Post-Spawn**: Wait for completion, read summary JSON, update status.json

---

### Wave 1.5: Design Alignment Checkpoint

**No subagent** — Orchestrator does this directly:

```python
# 1. Read SEED-PLAN.md
seed_plan = read_file(f"{orchestrator_path}/SEED-PLAN.md")

# 2. Read CONVENTIONS.md from each service
for service in services:
    conventions = read_file(f"/workspace/{service}/.agentbus/AGENTS/CONVENTIONS.md")
    # Apply heuristics
    # Detect conflicts
    # Present to user
```

---

### Wave 2: Plan Refinement

**Subagent**: `agentbus service agent`

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 2: Refine plan for {service}",
    prompt=json.dumps({
        "mission": "Create detailed implementation plan based on AGENTS/ and SEED-PLAN",
        "wave": 2,
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "read_files": {
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "required_documents": {
                "CONVENTIONS.md": "MOST IMPORTANT - contains decision patterns",
                "ARCHITECTURE.md": "Understand patterns and data flow",
                "STRUCTURE.md": "Know where to place files",
                "STACK.md": "Technology constraints",
                "CONCERNS.md": "Things to avoid"
            },
            "seed_plan": f"/workspace/agentbus-orchestrator/{plan_id}/SEED-PLAN.md",
            "design_decisions": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}-dac.json"
        },
        "read_instructions": {
            "step_1": "Read CONVENTIONS.md first - identify available patterns",
            "step_2": "Read ARCHITECTURE.md - understand how components interact",
            "step_3": "Read SEED-PLAN.md - understand what needs to be built",
            "step_4": "Cross-reference: Does SEED-PLAN approach match CONVENTIONS patterns?",
            "step_5": "Read STRUCTURE.md - determine exact file locations"
        },
        "analysis_requirements": {
            "must_check_conventions": True,
            "must_check_architecture": True,
            "must_provide_file_paths": True,
            "must_select_approach_from_conventions": True
        },
        "output_files": {
            "refined_plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        },
        "output_requirements": {
            "plan_must_include": [
                "Approach selected (from CONVENTIONS.md)",
                "Files to modify/create with absolute paths",
                "Database changes (if any)",
                "API changes (if any)",
                "Testing strategy",
                "Dependencies on other services"
            ],
            "if_needs_context": {
                "set_status": "needs_context",
                "provide_queries": "List of specific questions for other services"
            }
        }
    }),
    readonly=False
)
```

---

### Wave 3: Implementation

**Subagent**: `agentbus service agent`

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 3: Implement changes for {service}",
    prompt=json.dumps({
        "mission": "Execute PLAN.md - modify code, run tests, NO commits",
        "wave": 3,
        "pre_flight_checks": [
            "Verify on feature branch (git branch)",
            "Verify working directory clean"
        ],
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "read_files": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS",
            "key_documents": ["CONVENTIONS.md", "STRUCTURE.md"]
        },
        "read_instructions": {
            "step_1": "Read PLAN.md completely - understand all changes",
            "step_2": "Read CONVENTIONS.md - verify approach is still appropriate",
            "step_3": "Read STRUCTURE.md - confirm file locations",
            "step_4": "For each change in PLAN: implement, test, proceed"
        },
        "execution_rules": {
            "no_commits": True,
            "test_after_each_change": True,
            "stop_on_test_failure": True,
            "preserve_existing_code": True
        },
        "output_files": {
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        },
        "output_requirements": {
            "changes_log_must_include": [
                "List of all files modified",
                "What changed in each file",
                "Test results for each change",
                "Rollback commands",
                "Suggested commit messages (for Wave 5)"
            ]
        }
    }),
    readonly=False
)
```

---

### Wave 4: Verification

**Subagent**: `agentbus service agent`

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 4: Verify implementation for {service}",
    prompt=json.dumps({
        "mission": "Run full test suite and verify production readiness",
        "wave": 4,
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "read_files": {
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md"
        },
        "read_instructions": {
            "step_1": "Read CHANGES.md - understand what was implemented",
            "step_2": "Read PLAN.md - verify all items completed",
            "step_3": "Run full test suite",
            "step_4": "Check cross-service compatibility"
        },
        "verification_checklist": [
            "All unit tests pass",
            "All integration tests pass",
            "Code follows project conventions",
            "No breaking changes without migration path",
            "Documentation updated (if needed)"
        ],
        "output_files": {
            "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

---

### Wave 4b: Adjustments

**Subagent**: `agentbus service agent` (mode: explain or quick_fix)

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 4b: Quick fix for {service}",
    prompt=json.dumps({
        "mission": "Apply quick fix to address test failure",
        "wave": "4b",
        "mode": "quick_fix",
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "read_files": {
            "plan": f"/workspace/{service}/.agentbus-plans/{plan_id}/PLAN.md",
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md",
            "agents_dir": f"/workspace/{service}/.agentbus/AGENTS"
        },
        "fix_request": "[User's specific fix request]",
        "constraints": {
            "no_architectural_changes": True,
            "no_new_endpoints": True,
            "test_after_fix": True
        },
        "output_files": {
            "changes_log_append": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}-4b.json"
        }
    }),
    readonly=False
)
```

---

### Wave 5: Wrap-up

**Subagent**: `agentbus service agent`

```python
Task(
    subagent_name="agentbus service agent",
    description=f"Wave 5: Create commits for {service}",
    prompt=json.dumps({
        "mission": "Create git commits for all verified changes",
        "wave": 5,
        "pre_flight_requirements": [
            "User explicitly confirmed commits",
            "On feature branch (not main/master)",
            "All tests pass",
            "Working directory has Wave 3 changes"
        ],
        "service": {
            "name": service,
            "path": f"/workspace/{service}"
        },
        "read_files": {
            "changes_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/CHANGES.md",
            "test_results": f"/workspace/{service}/.agentbus-plans/{plan_id}/TEST-RESULTS.md"
        },
        "commit_rules": {
            "atomic_commits": True,
            "conventional_commits": True,
            "reference_plan_id": True
        },
        "output_files": {
            "commit_log": f"/workspace/{service}/.agentbus-plans/{plan_id}/COMMITS.md",
            "summary_json": f"/workspace/agentbus-orchestrator/{plan_id}/service-outputs/{service}.json"
        }
    }),
    readonly=False
)
```

---

## Status.json Schema (Updated)

```json
{
  "plan_id": "001-feature",
  "services": ["svc1", "svc2"],
  "current_wave": 2,
  "waves": {
    "wave_1_mapping": {
      "status": "completed",
      "artifacts": {
        "svc1": {
          "agents_dir": "/workspace/svc1/.agentbus/AGENTS",
          "documents": ["STACK.md", "ARCHITECTURE.md", "STRUCTURE.md", "CONVENTIONS.md", "CONCERNS.md"]
        }
      }
    },
    "wave_2_refinement": {"status": "in_progress"},
    "wave_3_implementation": {"status": "pending"},
    "wave_4_verification": {"status": "pending"},
    "wave_5_wrapup": {"status": "pending", "optional": true}
  }
}
```

---

## Anti-Patterns

❌ **Don't**: Assume subagents know what to read
❌ **Don't**: Pass only directory paths without file lists
❌ **Don't**: Omit `read_instructions` section
❌ **Don't**: Use relative paths in prompts (always absolute)

✅ **Do**: Explicitly list every file subagent must read
✅ **Do**: Provide step-by-step reading order
✅ **Do**: Explain WHY each file matters
✅ **Do**: Include fallback instructions
✅ **Do**: Verify subagent received all paths before spawning
