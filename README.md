# AgentBus Skills

Cross-service planning skills for LLM coding agents.

This project removes the "developer as messenger" problem when understanding
and planning features that touch multiple repos. The orchestrator can answer
cross-service questions from docs first, then write a draft plan into each
service repo when you are ready.

## Current design decisions

- State is file-based (`.agentbus-plans/` in each service repo)
- No MCP server, no Redis, no background bus
- Python scripts run with `uv`
- Canonical service names are repo names (for example `payments-service`)
- Simplified aliases are accepted (`payments`) and normalized to canonical names

## Repository layout

```text
agentbus-skills/
├── scripts/
│   ├── register_service.py
│   ├── list_services.py
│   ├── next_plan_number.py
│   ├── write_plan.py
│   └── read_plan.py
└── skills/
    ├── agentbus-orchestrator/
    ├── agentbus-expert/
    └── map-codebase/
```

## Prerequisites

- `uv`

Install:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Service registry

Global registry file:

`~/.agentbus/services.json`

Example:

```json
{
  "payments-service": "/home/jero/repos/payments-service",
  "notifications-service": "/home/jero/repos/notifications-service",
  "crm-service": "/home/jero/repos/crm-service"
}
```

Register services:

```bash
uv run scripts/register_service.py payments-service /path/to/payments-service
uv run scripts/register_service.py notifications-service /path/to/notifications-service
uv run scripts/register_service.py crm-service /path/to/crm-service
```

## Typical flow

1. Discover first (optional, no file writes):

```bash
/agentbus-orchestrator --ask "how does onboarding move across services today?" payments notifications crm
```

2. Run orchestrator in plan mode (can use aliases in invocation):

```bash
/agentbus-orchestrator "migrate sync calls to Kafka events" payments notifications crm
```

3. Open each service repo and run:

```bash
/agentbus-expert
```

4. Plans are stored in each repo under:

`<service-repo>/.agentbus-plans/<NNN>-<feature-slug>.md`

## Notes

- Current version favors simplicity over strong concurrency controls.
- Plans are kept in repo for visibility/auditability (not gitignored by default).
