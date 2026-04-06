# Refactor Plan: AgentBus Markdown-First Orchestrator

## 1. Goal

Refactor AgentBus to a markdown-first system where:

- Skills are the source of truth for behavior.
- Orchestration is driven by instructions and subagents, not local helper scripts.
- Cross-service planning stays coherent across microservices.
- Verification happens at the end in two layers:
  - service-level verification (owned by service subagents)
  - global verification (owned by orchestrator)

## 2. Core principles

- Markdown first: all behavior contracts live in `SKILL.md` files.
- No additional scripts: no new Python or shell helper scripts for orchestration logic.
- Orchestrator as control-plane: it owns global context, dispatch, sequencing, and final decision.
- Subagents as specialists: each service subagent receives enough context to do meaningful work.
- Verification as a final gate: no implementation start until service-level and global checks pass.

## 3. Scope

### In scope

- Redesign skill protocols (`agentbus-orchestrator`, `agentbus-expert`, `agentbus-review`).
- Add explicit subagent lifecycle in orchestrator instructions.
- Define context package contract passed to each subagent.
- Define final verification protocol split by service and global layers.
- Update docs (`README.md`, `agentBus_PRD`, `agentBus_details.md`) to match behavior.

### Out of scope

- New scripts/tools for orchestration.
- Automatic code implementation by default.
- Full autonomous conflict resolution without user confirmation.

## 4. Target architecture

### 4.1 Orchestrator responsibilities (global)

- Parse user goal and constraints.
- Build global context bundle.
- Detect likely impacted services (docs-first, then lightweight code signals if needed).
- Confirm impacted services with user when confidence is low.
- Launch service subagents with contextual payloads.
- Collect and consolidate outputs.
- Run final global verification and report readiness.

### 4.2 Service subagent responsibilities (local)

- Map service codebase and docs (`map-codebase` behavior).
- Refine service plan from orchestrator seed plan.
- Produce service verification summary (coverage, risks, unresolved questions).
- Return structured output for orchestrator consolidation.

### 4.3 Review responsibilities

- Service-level checks are executed by service subagents.
- Global cross-service checks are executed by orchestrator at the end.
- Orchestrator is the single owner of final go/no-go status.

## 5. Context contract for subagents

Each service subagent must receive a context package with:

- `feature_goal`: what change is requested.
- `business_intent`: why this change exists.
- `service_name`: canonical repo service name.
- `service_role`: role of this service in the feature.
- `other_services`: participants and expected interactions.
- `seed_plan`: initial service plan from orchestrator.
- `cross_service_decisions`: known decisions affecting this service.
- `known_constraints`: technical or org constraints.
- `open_questions`: questions pending resolution.
- `done_criteria`: what must be true for this service to be considered ready.

If any required field is missing, subagent must stop and request missing context.

## 6. End-to-end workflow (markdown-first)

1. Intake
   - User asks to understand or plan a multi-service feature.
2. Discovery
   - Orchestrator loads key docs across candidate services.
   - Optional Q/A mode for understanding (`--ask` style behavior).
3. Service impact proposal
   - Orchestrator proposes affected services and confidence.
   - User confirms or adjusts list.
4. Seed planning
   - Orchestrator creates initial plan per service.
5. Subagent wave 1: service mapping
   - Service subagents map codebase and produce service AGENTS context.
6. Subagent wave 2: plan refinement
   - Service subagents refine seed plan using local context.
7. Final verification gate
   - Service-level verification first.
   - Global verification second.
8. Final orchestrator report
   - Readiness status, key decisions, risks, unresolved items, recommended next step.

## 7. Verification model (final gate)

### 7.1 Service-level verification (subagent-owned)

Every service subagent must return:

- implementation readiness for that service (`ready` / `needs-work`)
- impacted modules/components
- required tests by layer (unit/integration/e2e as applicable)
- interface/API/event changes
- unresolved questions
- local risk assessment

Service-level pass criteria:

- clear implementation steps exist
- required tests are identified
- no blocking unknowns for local scope

### 7.2 Global verification (orchestrator-owned)

Orchestrator verifies cross-service consistency:

- all affected services have refined plans
- dependencies are mirrored correctly across plans
- decisions are consistent across service boundaries
- unresolved questions have clear owner and next action
- sequencing and rollout assumptions are coherent

Global pass criteria:

- no critical cross-service contradictions
- all critical dependencies acknowledged by both sides
- implementation can start without hidden coordination gaps

## 8. File-by-file refactor tasks

## 8.1 `skills/agentbus-orchestrator/SKILL.md`

- Redefine protocol around subagent waves.
- Add explicit context contract for subagent handoff.
- Add service detection strategy (docs-first, lightweight code signals).
- Add final verification section (service-level then global).
- Keep ask/discovery behavior but clarify it does not write plans.

## 8.2 `skills/agentbus-expert/SKILL.md`

- Reposition as service specialist subagent contract.
- Define required input context and expected output schema (markdown structure).
- Add service-level verification checklist at the end.
- Ensure it never assumes global ownership.

## 8.3 `skills/agentbus-review/SKILL.md`

- Convert to markdown-first review protocol (no script dependency).
- Define review playbook for manual/agentic consistency checks.
- Keep outputs structured so orchestrator can aggregate.

## 8.4 `README.md`

- Update architecture section: orchestrator + subagent waves.
- Add "How verification works" section.
- Add "No helper scripts required for orchestration logic" note.
- Keep installation and usage examples aligned with actual skills.

## 8.5 `agentBus_PRD`

- Update design section to markdown-first orchestration model.
- Add explicit verification model and ownership split.
- Add acceptance criteria for service/global verification flow.
- Remove script-first assumptions from core orchestration behavior.

## 8.6 `agentBus_details.md`

- Update implementation details to match subagent lifecycle.
- Add context package template and verification template examples.
- Remove contradictions with PRD and README.

## 9. Migration strategy

### Phase 1: Protocol-first refactor

- Update all skill markdown files.
- Keep existing scripts in repo temporarily but treat them as non-core.
- Confirm docs are internally consistent.

### Phase 2: Orchestrator dry-runs

- Run orchestrator in discovery and planning modes on 1-2 known features.
- Validate subagent handoff quality and context sufficiency.

### Phase 3: Verification hardening

- Enforce final gate output format.
- Ensure orchestrator blocks implementation recommendation when gate fails.

### Phase 4: Cleanup

- Remove script dependencies from skill instructions.
- Optionally archive/deprecate scripts not needed in markdown-first operation.

## 10. Risks and mitigations

- Risk: subagents receive incomplete context.
  - Mitigation: required context contract with hard-stop behavior.
- Risk: orchestrator over/under-selects services.
  - Mitigation: confidence + user confirmation loop.
- Risk: inconsistent plan formats across services.
  - Mitigation: strict output template in service subagent instructions.
- Risk: false confidence before implementation.
  - Mitigation: final verification gate with explicit pass/fail criteria.

## 11. Definition of done

Refactor is complete when:

- orchestrator runs subagent-driven flow end-to-end
- service-level verification outputs exist for every affected service
- orchestrator emits global verification result and readiness status
- docs (`README.md`, `agentBus_PRD`, `agentBus_details.md`) match actual behavior
- no core orchestration step requires helper scripts

## 12. Suggested execution order (practical)

1. Refactor `agentbus-orchestrator` protocol.
2. Refactor `agentbus-expert` as service subagent contract.
3. Refactor `agentbus-review` to markdown-first review protocol.
4. Sync PRD/details/README.
5. Run 2 full dry-run sessions on real features.
6. Adjust templates and checks from observed gaps.
