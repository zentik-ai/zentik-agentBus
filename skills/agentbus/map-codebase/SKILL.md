---
name: agentbus map-codebase
description: Deep service mapper for AgentBus. Explores a service codebase and generates 5 specialized documents (STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, CONCERNS) in .agentbus/AGENTS/. Used by the orchestrator during Wave 1.
version: 1.0.0
triggers: [agentbus mapping, service analysis, codebase exploration]
tools: [Read, Write, Bash, Glob, Grep]
tags: [agentbus, mapping, service-analysis, documentation]
---

# AgentBus Map Codebase

Deep service mapper that explores a codebase and generates structured documentation in `.agentbus/AGENTS/`. This is a subskill invoked by the orchestrator during Wave 1 (Service Mapping).

**Skill Padre**: `agentbus` — Este es un subskill especializado invocado vía Task tool por `agentbus orchestrator`.

## Purpose

Replace the monolithic `AGENTS.md` approach with 5 specialized documents that provide structured, searchable context for agent decision-making.

## Output Structure

```
{service}/
└── .agentbus/
    └── AGENTS/                    # 5 specialized documents
        ├── STACK.md              # Technology stack and dependencies
        ├── ARCHITECTURE.md       # Patterns, layers, data flow
        ├── STRUCTURE.md          # Directory layout, file placement
        ├── CONVENTIONS.md        # Implementation patterns available
        └── CONCERNS.md           # Tech debt and known issues
```

## When to Use

You are invoked by the AgentBus Orchestrator during Wave 1. You receive:

```json
{
  "service_name": "service-name",
  "service_path": "/absolute/path/to/service",
  "outputs": {
    "agents_dir": "/absolute/path/to/service/.agentbus/AGENTS",
    "summary_json": "/absolute/path/to/orchestrator/service-outputs/service.json"
  }
}
```

## Mapping Protocol

### Phase 1: Discovery

Explore the codebase to understand:

1. **Technology Stack** (for STACK.md)
   - Language and version
   - Framework
   - Database
   - Key dependencies
   - External services

2. **Architecture** (for ARCHITECTURE.md)
   - Architectural pattern (MVC, hexagonal, layered, etc.)
   - Layer boundaries
   - Data flow patterns
   - Key abstractions

3. **Structure** (for STRUCTURE.md)
   - Directory layout
   - Naming conventions
   - Where different types of code live
   - File organization patterns

4. **Conventions** (for CONVENTIONS.md) — MOST IMPORTANT
   - Implementation patterns available
   - When to use each pattern
   - Decision criteria for choosing approaches
   - Examples from codebase

5. **Concerns** (for CONCERNS.md)
   - Technical debt
   - Known bugs/limitations
   - Performance bottlenecks
   - Security concerns

### Phase 2: Pattern Detection (for CONVENTIONS.md)

Actively look for:

**Data Modification Patterns:**
- How is data created/updated?
- SQL migrations vs API endpoints vs config files?
- When is each used?

**API Design Patterns:**
- REST vs GraphQL vs RPC?
- Versioning strategy?
- Error response format?

**Error Handling:**
- How are errors propagated?
- Logging patterns?
- User-facing error messages?

**Testing Patterns:**
- Unit vs integration test structure?
- Mocking strategies?
- Test data setup?

### Phase 3: Document Generation

Write the 5 documents following the templates below.

---

## Document Templates

### STACK.md

```markdown
# Technology Stack

**Service:** [service-name]  
**Analysis Date:** [YYYY-MM-DD]

---

## Core Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Language | [e.g., Node.js] | [e.g., 20.11] | [LTS, ESM, etc.] |
| Framework | [e.g., Express] | [e.g., 4.18] | [notes] |
| Database | [e.g., PostgreSQL] | [e.g., 15] | [notes] |
| ORM/Client | [e.g., Prisma] | [e.g., 5.7] | [notes] |
| Cache | [e.g., Redis] | [e.g., 7] | [optional] |

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [package-name] | [version] | [what it does] |

## External Services

| Service | Purpose | Integration Type | Location in Code |
|---------|---------|------------------|------------------|
| [service-name] | [what it does] | [HTTP/API/Queue] | `[path to client]` |

## Build & Run

```bash
# Install dependencies
[command]

# Run locally
[command]

# Run tests
[command]

# Build for production
[command]
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `[VAR_NAME]` | [yes/no] | [description] |
```

### ARCHITECTURE.md

```markdown
# Architecture

**Service:** [service-name]  
**Analysis Date:** [YYYY-MM-DD]

---

## Pattern Overview

**Primary Pattern:** [e.g., Layered Architecture, Hexagonal, MVC]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]

## Layers

### [Layer Name]

**Purpose:** [What this layer does]

**Location:** `[path]`

**Contains:**
- [Type of code, e.g., HTTP controllers]
- [Type of code, e.g., Request validation]

**Dependencies:** [What this layer depends on]

**Used By:** [What depends on this layer]

**Key Files:**
| File | Purpose |
|------|---------|
| `[path]` | [what it does] |

## Data Flow

### [Flow Name, e.g., "API Request"]

1. **[Step 1]:** [Description]
   - Files: `[path]`
2. **[Step 2]:** [Description]
   - Files: `[path]`
3. **[Step 3]:** [Description]
   - Files: `[path]`

## Key Abstractions

| Concept | Implementation | Location |
|---------|---------------|----------|
| [e.g., "User"] | [e.g., "Class/Interface"] | `[path]` |

## API Surface

| Endpoint | Method | Purpose | Handler Location |
|----------|--------|---------|------------------|
| `/path` | GET | [description] | `[path]` |
```

### STRUCTURE.md

```markdown
# Codebase Structure

**Service:** [service-name]  
**Analysis Date:** [YYYY-MM-DD]

---

## Directory Layout

```
[project-root]/
├── [directory]/          # [purpose]
│   ├── [subdir]/         # [purpose]
│   └── [file.ext]        # [purpose]
├── [directory]/          # [purpose]
└── [config-file]         # [purpose]
```

## Where to Add New Code

### New Feature

| Type | Location | Notes |
|------|----------|-------|
| Domain logic | `[path]` | [conventions] |
| API endpoint | `[path]` | [conventions] |
| Database model | `[path]` | [conventions] |
| Tests | `[path]` | [conventions] |

### New API Endpoint

1. Add handler in: `[path]`
2. Add business logic in: `[path]`
3. Add tests in: `[path]`
4. Update routes in: `[path]`

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | [e.g., kebab-case.ts] | `user-service.ts` |
| Classes | [e.g., PascalCase] | `UserService` |
| Functions | [e.g., camelCase] | `getUserById` |
| Constants | [e.g., UPPER_SNAKE] | `MAX_RETRIES` |
| Database tables | [e.g., snake_case] | `user_accounts` |

## File Organization Principles

- [Principle 1, e.g., "Co-locate tests with source"]
- [Principle 2, e.g., "Feature folders over type folders"]
```

### CONVENTIONS.md

```markdown
# Coding Conventions & Patterns

**Service:** [service-name]  
**Analysis Date:** [YYYY-MM-DD]

---

## Data Modification Patterns

### Pattern: [Name, e.g., "Database Migration for Schema Changes"]

**When to use:**
- [Criterion 1, e.g., "ALTER TABLE operations"]
- [Criterion 2, e.g., "Creating new tables"]

**When NOT to use:**
- [Case 1, e.g., "Dynamic/runtime data creation"]

**Implementation:**
- Location: `[path pattern]`
- Naming: `[convention, e.g., YYYYMMDD_description.sql]`
- Process: [steps]

**Examples in codebase:**
- `[file path]` - [brief description of what it does]

**Pros:**
- [Advantage 1]
- [Advantage 2]

**Cons:**
- [Disadvantage 1]

---

### Pattern: [Name, e.g., "API Endpoint for Dynamic Data"]

**When to use:**
- [Criterion 1, e.g., "Data varies by environment"]
- [Criterion 2, e.g., "Needs runtime CRUD operations"]

**When NOT to use:**
- [Case 1, e.g., "Static reference data"]

**Implementation:**
- Location: `[path pattern]`
- Structure: [pattern, e.g., "Controller → Service → Repository"]

**Examples in codebase:**
- `[file path]` - [brief description]

**Pros:**
- [Advantage 1]

**Cons:**
- [Disadvantage 1]

---

### Decision Matrix: Data Modification

| Scenario | Preferred Approach | Reason |
|----------|-------------------|--------|
| Schema change (ALTER, CREATE TABLE) | Migration | Version controlled, reproducible |
| Dynamic permission/config | API Endpoint | Runtime variability |
| Environment-specific config | API/Config | Per-environment values |
| Static reference data | Migration/Seed | Immutable, version controlled |
| Temporary feature flag | API/Config | Frequent changes |

---

## API Design Patterns

[Document patterns for API design]

---

## Error Handling Patterns

[Document how errors are handled]

---

## Validation Patterns

[Document input validation approaches]

---

## Testing Patterns

### Unit Tests
- Location: `[path pattern]`
- Framework: [e.g., Jest, pytest]
- Mocking: [strategy]

### Integration Tests
- Location: `[path pattern]`
- Database: [approach, e.g., "Test containers"]

---

## Common Anti-Patterns to Avoid

| Anti-Pattern | Why Avoid | Prefer Instead |
|--------------|-----------|----------------|
| [Pattern] | [Reason] | [Alternative] |
```

### CONCERNS.md

```markdown
# Codebase Concerns & Technical Debt

**Service:** [service-name]  
**Analysis Date:** [YYYY-MM-DD]

---

## Critical Issues

### CONCERN-001: [Title]

**Files:** `[paths]`

**Issue:** [Description of the problem]

**Impact:** [What breaks or degrades]

**Root Cause:** [Why it exists]

**Workaround:** [Current mitigation, if any]

**Recommended Fix:** [How to properly fix it]

**Priority:** [Critical/High/Medium/Low]

---

## Known Limitations

### LIMIT-001: [Title]

**Current:** [How it works now]

**Limitation:** [What you can't do]

**Workaround:** [How to work around it]

**Planned Resolution:** [If known]

---

## Performance Bottlenecks

| Location | Issue | Impact | Mitigation |
|----------|-------|--------|------------|
| `[path]` | [description] | [severity] | [current approach] |

---

## Security Considerations

| Location | Concern | Risk Level | Mitigation |
|----------|---------|------------|------------|
| `[path]` | [description] | [High/Med/Low] | [current approach] |

---

## Migration Notes

[Notes for future migrations or major changes]

---

## Deprecated Code

| Location | What | Replacement | Removal Target |
|----------|------|-------------|----------------|
| `[path]` | [description] | [use this instead] | [version/date] |
```

---

## Output Requirements

Always write:

1. **Five markdown documents** in `.agentbus/AGENTS/`
2. **Summary JSON** for the orchestrator

### Summary JSON Format

```json
{
  "wave": 1,
  "status": "completed",
  "service": "service-name",
  "artifacts_written": [
    "/path/to/service/.agentbus/AGENTS/STACK.md",
    "/path/to/service/.agentbus/AGENTS/ARCHITECTURE.md",
    "/path/to/service/.agentbus/AGENTS/STRUCTURE.md",
    "/path/to/service/.agentbus/AGENTS/CONVENTIONS.md",
    "/path/to/service/.agentbus/AGENTS/CONCERNS.md"
  ],
  "key_findings": [
    "Uses layered architecture with clear separation",
    "Has both migrations and API endpoints for data changes",
    "PostgreSQL with Prisma ORM"
  ],
  "patterns_detected": [
    {
      "pattern": "Database Migration",
      "use_case": "Schema changes",
      "example": "prisma/migrations/20240115_add_users"
    },
    {
      "pattern": "API Endpoint",
      "use_case": "Dynamic permissions",
      "example": "src/routes/permissions.ts"
    }
  ],
  "blockers": [],
  "unresolved_questions": []
}
```

---

## Anti-Patterns

❌ **Don't**: Write a single AGENTS.md file (deprecated approach)
❌ **Don't**: Skip CONVENTIONS.md (it's critical for decision-making)
❌ **Don't**: Return analysis in response instead of writing files
❌ **Don't**: Leave sections empty with just headers
✅ **Do**: Write complete, useful documentation
✅ **Do**: Detect actual patterns from code, not generic advice
✅ **Do**: Provide specific file paths and examples
✅ **Do**: Document decision criteria in CONVENTIONS.md
