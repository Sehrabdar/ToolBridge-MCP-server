# ToolBridge — Secure MCP Server for Authenticated Tool Execution

> **Streamable HTTP is the production transport; stdio is used only for local development and rapid iteration.**

ToolBridge is a production-grade MCP (Model Context Protocol) server that exposes authenticated, authorized external tools to any MCP-compatible client. It enforces per-user authentication, per-user authorization, secure credential handling, tool-level permissions, audit logging, failure handling, and observability. MCP-compatible AI agents and clients connect to ToolBridge to access its tools — the agent/client itself is not part of this project.

---

## Architecture

```
MCP-compatible Client or AI Agent (external — not part of this project)
  ↓
MCP (Streamable HTTP — production | stdio — local dev)
  ↓
ToolBridge MCP Server
  ↓
Authentication
  ↓
Authorization / Policy
  ↓
Tool Executor
  ↓
External APIs (GitHub REST API)
```

The server combines two concerns, kept deliberately separate:

| Concern | Layer |
|---|---|
| MCP protocol, tool registration, tool routing | Official Python MCP SDK server |
| HTTP authentication, OAuth callback | Thin FastAPI auth layer |

---

## Phase Status

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Architecture & Requirements | ✅ COMPLETE |
| **Phase 1** | Project Foundation | ✅ COMPLETE |
| **Phase 2** | MCP Server Core | ✅ COMPLETE |
| Phase 3 | GitHub Tool Integrations | ⏳ NEXT |
| Phase 4 | MCP Transport & Protocol | ⏳ |
| Phase 5 | Authentication | ⏳ |
| Phase 6 | Authorization & Permissions | ⏳ |
| Phase 7 | Secure Credential Management | ⏳ |
| Phase 8 | Policy Engine | ⏳ |
| Phase 9 | Reliability & Error Handling | ⏳ |
| Phase 10 | Audit Logging & Observability | ⏳ |
| Phase 11 | Security Hardening | ⏳ |
| Phase 12 | MCP Server Evaluation | ⏳ |
| Phase 13 | Production Deployment | ⏳ |
| Phase 14 | Documentation & Demo | ⏳ |

---

## Technology Decisions

### Current Implementation (Phase 1 & Phase 2)

| Technology | Purpose | Status |
|---|---|---|
| **Python 3.12** | Primary language | ✅ Implemented |
| **uv** | Dependency management & virtual environments | ✅ Implemented |
| **FastAPI** | Web framework (`/health` endpoint; future auth layer) | ✅ Implemented |
| **pydantic-settings** | Typed configuration from environment variables | ✅ Implemented |
| **structlog** | Structured application logging | ✅ Implemented |
| **SQLAlchemy (async)** | Async ORM / database connectivity | ✅ Implemented |
| **asyncpg** | Async PostgreSQL driver | ✅ Implemented |
| **Alembic** | Database schema migrations | ✅ Implemented |
| **PostgreSQL 16** | Primary data store (via Docker) | ✅ Implemented |
| **Docker / Docker Compose** | Containerisation & local dev environment | ✅ Implemented |
| **pytest** | Test framework | ✅ Implemented |
| **Ruff** | Linting & formatting | ✅ Implemented |
| **mypy** | Static type checking | ✅ Implemented |
| **GitHub Actions** | CI pipeline | ✅ Implemented |
| **Official Python MCP SDK** (`mcp` 2.x) | MCP server primitives, tool registration, in-process client testing | ✅ Implemented (Phase 2) |

### Future Phases (not yet implemented)

| Technology | Purpose | Phase |
|---|---|---|
| **GitHub REST API** | External tool target (`search_repositories`, `list_issues`, `get_file_content`) | Phase 3 |
| **GitHub OAuth** | User identity via GitHub authorization | Phase 5 |
| **JWT** | Short-lived session tokens for MCP requests | Phase 5 |

---

## Phase 2 — MCP Server Core — ✅ COMPLETE

Implemented the core ToolBridge MCP server using the MCP 2.x `MCPServer` API
(`mcp.server.mcpserver.MCPServer`). The server exposes three discoverable MCP tools
with explicit Pydantic input/output schemas, backed by in-process tests that cover
both tool invocation and MCP tool discovery. Phase 2 maintains the quality bar
established in Phase 1: 4 passing tests, Ruff passing with 0 issues, and mypy
passing with 0 issues.

### What was delivered

| Item | Detail |
|---|---|
| MCP server instance | `mcp = MCPServer("toolbridge")` in `src/toolbridge/mcp/server.py` |
| Tool: `search_repositories` | Input: `query: str` → Output: `SearchRepositoriesResult` |
| Tool: `list_issues` | Input: `repo: str`, `state: str` → Output: `ListIssuesResponse` |
| Tool: `get_file_content` | Input: `repo: str`, `path: str` → Output: `FileContentsResponse` |
| Pydantic output schemas | `RepositoryResult`, `SearchRepositoriesResult`, `IssueResult`, `ListIssuesResponse`, `FileContentsResponse` |
| Test: tool invocation × 3 | `test_search_repositories_return_structured_response`, `test_list_issues_returns_structured_response`, `test_get_file_content_returns_structured_response` |
| Test: tool discovery | `test_tools_are_discoverable_with_schemas` — asserts all three tools are listed |
| Test suite | `tests/mcp/test_server.py` — 4 tests, 0 failures |
| Ruff | 0 issues |
| mypy | 0 issues |

All three tools currently return empty stub results (no GitHub REST API calls).
GitHub integration is Phase 3.

#### MCP SDK Version Drift & Migration

During Phase 2 a real MCP SDK version-drift issue was encountered and deliberately
resolved.

**Initial implementation** used the MCP 1.x API:

```python
from mcp.server.fastmcp import FastMCP
```

**The problem**: when the virtual environment was recreated and dependencies were
resolved, `uv` resolved MCP `2.1.1` (the latest available version satisfying the
broad `mcp>=1.9.0` constraint in `pyproject.toml`). The `mcp.server.fastmcp` module
does not exist in MCP 2.x, causing:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

**Deliberate resolution**: rather than silently adapting code until the error
disappeared, the project treated this as a real API compatibility issue and
deliberately migrated from the MCP 1.x `FastMCP` API to the MCP 2.x `MCPServer`
API:

```
MCP 1.x
FastMCP  (mcp.server.fastmcp)
    ↓
API / version drift discovered (mcp.server.fastmcp absent in MCP 2.x)
    ↓
MCP 2.x
MCPServer  (mcp.server.mcpserver)
```

The final import in the implementation is:

```python
from mcp.server.mcpserver import MCPServer
```

The `uv.lock` was updated as part of this resolution and now pins the resolved
version to MCP `2.1.1`. The `pyproject.toml` dependency constraint (`mcp>=1.9.0`)
remains broad enough to have admitted MCP 2.x; constraining it to `mcp>=2,<3`
would pin the project to MCP 2.x while preventing an uncontrolled future
major-version API change from silently breaking the server. That constraint update
is tracked as a follow-on hygiene item.

---

## MCP Tools

Three read-oriented tools are registered on the MCP server as of Phase 2:

```
search_repositories(query)              → SearchRepositoriesResult
list_issues(repo, state="open")         → ListIssuesResponse
get_file_content(repo, path)            → FileContentsResponse
```

These tools are **discoverable** (verified by `test_tools_are_discoverable_with_schemas`)
and return **schema-driven structured output** (verified by the three invocation
tests). They currently return empty stub results; real GitHub REST API integration
is Phase 3.

---

## Planned Database Schema

```sql
users (id, github_username, created_at)
user_tokens (id, user_id, provider, access_token, refresh_token NULL, expires_at NULL, scopes[])
tool_permissions (id, user_id, tool_name, allowed)
audit_log (id, user_id, tool_name, request_payload, response_status, latency_ms, created_at)
```

> **Note:** `refresh_token` and `expires_at` are intentionally nullable.
> The exact GitHub token lifecycle will be verified during Phase 5 before the schema is finalised.

---

## Getting Started (Phase 1 & Phase 2)

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd toolbridge

# Copy environment configuration
cp .env.example .env
# Edit .env if needed (defaults work with docker compose)

# Install dependencies
uv sync

# Start PostgreSQL
docker compose up -d

# Run the application
uv run uvicorn toolbridge.main:app --reload

# Verify health
curl http://localhost:8000/health
# {"status":"ok","db":"ok"}
```

### Running Tests

```bash
# Unit tests (no external services required)
uv run pytest tests/unit/

# Integration tests (requires PostgreSQL from docker compose up -d)
uv run pytest tests/integration/ -m integration

# All tests
uv run pytest
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Formatting check
uv run ruff format --check .

# Type checking
uv run mypy .
```

### Database Migrations

```bash
# Run pending migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "description"
```

---

## Project Structure

```
toolbridge/
│
├── src/
│   └── toolbridge/
│       ├── config/       # Typed settings (pydantic-settings)
│       ├── logging/      # Structured logging (structlog)
│       ├── db/           # Async SQLAlchemy engine + health check
│       ├── server/       # FastAPI application + /health endpoint
│       └── mcp/          # MCP server instance + tool definitions (Phase 2)
│
├── tests/
│   ├── unit/             # Tests with no external service dependencies
│   ├── integration/      # Tests requiring PostgreSQL
│   └── mcp/              # In-process MCP server tests (Phase 2)
│
├── migrations/           # Alembic migration scripts
├── docs/                 # Architecture documentation
├── scripts/              # Development utility scripts
├── .github/workflows/    # GitHub Actions CI
│
├── pyproject.toml        # Project metadata, dependencies, tool config
├── Dockerfile            # Multi-stage production image
├── docker-compose.yml    # Local development environment (PostgreSQL)
├── .env.example          # Environment variable reference (no secrets)
└── README.md
```

---

## Observability

Logs are emitted in JSON format in production and human-readable format in development.
Every log record includes: `timestamp`, `level`, `logger`, `message`.

Future phases will add: `request_id`, `user_id`, `tool_name`, `latency_ms`, `status`.

---

## Security Notes

- Secrets are **never** committed. The `.env` file is in `.gitignore`.
- See `.env.example` for all required environment variables.
- OAuth credentials, JWT secrets, and API keys are out of scope until Phase 5/7.

---

## Engineering Decisions & Implementation Notes

### MCP SDK Version Drift (Phase 2)

During Phase 2, MCP SDK version drift exposed an API incompatibility between the
original MCP 1.x `FastMCP` implementation and the MCP 2.x package resolved by `uv`
(`mcp==2.1.1`). The issue was resolved deliberately by migrating the server from
`FastMCP` to `MCPServer` and updating the code to the MCP 2.x API at
`mcp.server.mcpserver`.

This keeps the implementation aligned with the resolved MCP major version. Constraining
the `pyproject.toml` dependency to `mcp>=2,<3` is tracked as a follow-on step to
prevent an uncontrolled future major-version upgrade from introducing another
breaking API change.
