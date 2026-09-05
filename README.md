# ToolBridge — Secure Multi-Tool MCP Server

> **Streamable HTTP is the production transport; stdio is used only for local development and rapid iteration.**

ToolBridge is a production-oriented MCP (Model Context Protocol) infrastructure project that exposes real external tools to an autonomous AI agent while enforcing per-user authentication, per-user authorization, secure credential handling, tool-level permissions, audit logging, failure handling, agent verification, and observability.

---

## Architecture

```
User
  ↓
LangGraph Agent
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
| Phase 2 | MCP Server (Streamable HTTP transport) | 🔜 Planned |
| Phase 3 | Tool Executor Framework | 🔜 Planned |
| Phase 4 | GitHub Tool Implementations | 🔜 Planned |
| Phase 5 | Audit Logging | 🔜 Planned |
| Phase 6 | GitHub OAuth & JWT Session Auth | 🔜 Planned |
| Phase 7 | Policy Engine & Per-Tool Authorization | 🔜 Planned |
| Phase 8 | LangGraph Agent | 🔜 Planned |
| Phase 9 | Failure Handling & Retry Engine | 🔜 Planned |
| Phase 10 | Agent Verification | 🔜 Planned |
| Phase 11 | Evaluation Framework | 🔜 Planned |

---

## Technology Decisions

### Current Implementation (Phase 1)

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

### Future Phases (not yet implemented)

| Technology | Purpose | Phase |
|---|---|---|
| **Official Python MCP SDK** (`mcp`) | MCP server primitives, tool registration, protocol handling | Phase 2 |
| **LangGraph** | Autonomous agent graph (Planner → Tool Executor → Verifier) | Phase 8 |
| **Anthropic Claude** | Primary LLM for the agent | Phase 8 |
| **GitHub REST API** | External tool target (`search_repositories`, `list_issues`, `get_file_contents`) | Phase 4 |
| **GitHub OAuth** | User identity via GitHub authorization | Phase 6 |
| **JWT** | Short-lived session tokens for MCP requests | Phase 6 |

---

## Planned Tools

Three initial read-oriented tools are planned for Phase 4:

```
search_repositories(query)
list_issues(repo, filters)
get_file_contents(repo, path)
```

These are **not implemented yet**.

---

## Planned Database Schema

```sql
users (id, github_username, created_at)
user_tokens (id, user_id, provider, access_token, refresh_token NULL, expires_at NULL, scopes[])
tool_permissions (id, user_id, tool_name, allowed)
audit_log (id, user_id, tool_name, request_payload, response_status, latency_ms, created_at)
```

> **Note:** `refresh_token` and `expires_at` are intentionally nullable.
> The exact GitHub token lifecycle will be verified during Phase 6 before the schema is finalised.

---

## Getting Started (Phase 1)

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
│       └── server/       # FastAPI application + /health endpoint
│
├── tests/
│   ├── unit/             # Tests with no external service dependencies
│   └── integration/      # Tests requiring PostgreSQL
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

Future phases will add: `request_id`, `user_id`, `agent_run_id`, `tool_name`, `latency_ms`, `status`.

---

## Security Notes

- Secrets are **never** committed. The `.env` file is in `.gitignore`.
- See `.env.example` for all required environment variables.
- OAuth credentials, JWT secrets, and API keys are out of scope until Phase 6/8.
