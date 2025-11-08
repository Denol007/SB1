# Implementation Plan: StudyBuddy Social Platform Backend

**Branch**: `001-studybuddy-platform` | **Date**: 2025-11-08 | **Spec**: [001-studybuddy-platform.md](../specs/001-studybuddy-platform.md)

**Input**: Feature specification from `/specs/001-studybuddy-platform.md`

## Summary

StudyBuddy is a social networking platform for university students and prospective students featuring verified communities, real-time chat, event management, and moderation capabilities. The backend implements a scalable, production-ready REST API with WebSocket support, built on FastAPI, PostgreSQL, Redis, and Celery for background processing.

**Primary Requirements:**
- User authentication via Google OAuth 2.0 with JWT tokens
- Student verification system via university email domains
- Hierarchical community structure with role-based access
- Social feed with posts, reactions, and nested comments
- Real-time chat (direct, group, community) via WebSocket
- Event creation and registration management
- Content moderation system with reporting and admin actions
- Premium analytics dashboard for institutions
- Global search across communities, users, posts, and events

**Technical Approach:**
- **Hexagonal Architecture** with clear separation of concerns (Domain, Application, Infrastructure)
- **Repository Pattern** for data access abstraction
- **Service Layer** for business logic encapsulation
- **Dependency Injection** via FastAPI's DI system
- **Async-first** design for I/O operations
- **Event-driven** background processing for scalability
- **Horizontal scaling** ready (stateless API instances)

## Technical Context

**Language/Version**: Python 3.11+ (async/await, type hints, performance improvements)  
**Primary Dependencies**: 
- FastAPI 0.104+ (web framework)
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)
- Redis 7+ (cache, sessions, WebSocket pub/sub)
- Celery 5+ (background tasks)
- Pydantic V2 (validation, serialization)

**Storage**: 
- PostgreSQL 15+ (primary database with JSONB, full-text search)
- Redis 7+ (caching, sessions, rate limiting, WebSocket state)
- S3-compatible storage (file uploads: MinIO for dev, AWS S3 for prod)

**Testing**: 
- pytest + pytest-asyncio (async test support)
- pytest-cov (coverage reporting, target: 80%+)
- httpx (async HTTP client for API testing)
- Factory Boy (test data factories)
- Faker (realistic test data generation)

**Target Platform**: Linux server (Docker containers on Kubernetes/Docker Swarm)

**Project Type**: Web API (backend-only, consumed by separate frontend)

**Performance Goals**: 
- 95th percentile response time: <200ms (reads), <500ms (writes)
- Support 10,000 concurrent WebSocket connections per instance
- Handle 100,000+ daily active users
- Process 1,000+ background jobs per minute

**Constraints**: 
- GDPR compliance (data export, deletion, anonymization)
- 99.9% uptime SLA
- Maximum cyclomatic complexity: 10 per function
- 80%+ test coverage (mandatory)
- All API endpoints must have OpenAPI documentation

**Scale/Scope**: 
- Support 100+ universities with 1,000+ communities
- 500,000+ registered users
- 1M+ posts, 10M+ messages
- 50+ API endpoints across 11 resource categories
- 20+ database tables with complex relationships

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **CODE QUALITY**
- Black + Ruff for formatting and linting (enforced via pre-commit)
- MyPy for type checking with strict mode
- Type hints on all functions and methods
- Google-style docstrings (enforced via pre-commit)
- Maximum cyclomatic complexity ≤ 10 (monitored via Ruff)

✅ **TESTING STANDARDS**
- pytest + pytest-asyncio framework
- Target: 80%+ code coverage (enforced in CI/CD)
- Unit tests for all business logic (services, utilities)
- Integration tests for all API endpoints
- Factory Boy for test data factories
- Faker for realistic test data

✅ **API DESIGN**
- RESTful resource-based URLs: `/api/v1/communities/{id}/posts`
- Versioning: `/api/v1/`, `/api/v2/`
- Pydantic models for request/response validation
- OpenAPI documentation auto-generated
- Rate limiting: 100 req/min per authenticated user

✅ **DATABASE**
- SQLAlchemy ORM (no raw SQL except analytics)
- Alembic migrations (never modify existing migrations)
- Indexes on all foreign keys and frequently queried columns
- Soft deletes for user data (deleted_at timestamp)

✅ **SECURITY**
- JWT with access (15min) + refresh tokens (30 days)
- Bcrypt password hashing (if email/password added)
- Input sanitization via Pydantic validators
- SQL injection prevention (ORM only)
- CORS whitelisting (no wildcards in production)
- Rate limiting enforced

✅ **PERFORMANCE**
- Redis caching (5-15min TTL)
- Async/await for all I/O operations
- Pagination: default 20, max 100 items
- WebSocket connection pooling

✅ **SCALABILITY**
- Stateless API design (no local state)
- Horizontal scaling ready
- Celery for background tasks
- Database connection pooling (5-20 per instance)

✅ **MONITORING & OBSERVABILITY**
- Structlog for structured JSON logging
- Prometheus metrics via prometheus-fastapi-instrumentator
- Sentry error tracking
- Health check endpoints: `/health`, `/health/ready`, `/health/metrics`

✅ **DOCUMENTATION**
- README.md with setup instructions
- OpenAPI docs at `/docs` and `/redoc`
- Database ER diagrams
- Deployment guides

**Constitution Compliance**: ✅ PASS - All requirements met

## Project Structure

### Documentation (this feature)

```text
.specify/
├── memory/
│   └── constitution.md          # Development principles and standards
├── specs/
│   └── 001-studybuddy-platform.md  # Feature specification
├── plans/
│   └── 001-studybuddy-platform-implementation.md  # This file
└── templates/                   # Speckit templates
```

### Source Code (repository root)

```text
studybuddy-backend/
├── alembic/                     # Database migrations
│   ├── versions/                # Migration files
│   └── env.py                   # Alembic configuration
│
├── app/                         # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── core/                    # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py            # Settings via Pydantic BaseSettings
│   │   ├── security.py          # JWT, password hashing, OAuth helpers
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── logging.py           # Structlog configuration
│   │   └── dependencies.py      # FastAPI dependency injection
│   │
│   ├── domain/                  # Domain models (business logic)
│   │   ├── __init__.py
│   │   ├── entities/            # Pure domain entities
│   │   │   ├── user.py
│   │   │   ├── community.py
│   │   │   ├── post.py
│   │   │   ├── event.py
│   │   │   ├── chat.py
│   │   │   └── ...
│   │   ├── value_objects/       # Value objects (immutable)
│   │   │   ├── email.py
│   │   │   ├── verification_token.py
│   │   │   └── ...
│   │   └── enums/               # Domain enums
│   │       ├── user_role.py
│   │       ├── community_type.py
│   │       ├── event_status.py
│   │       └── ...
│   │
│   ├── application/             # Application layer (use cases, services)
│   │   ├── __init__.py
│   │   ├── services/            # Business logic services
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── verification_service.py
│   │   │   ├── community_service.py
│   │   │   ├── post_service.py
│   │   │   ├── event_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── moderation_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── search_service.py
│   │   │   └── notification_service.py
│   │   ├── schemas/             # Pydantic models (DTOs)
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── community.py
│   │   │   ├── post.py
│   │   │   ├── event.py
│   │   │   ├── chat.py
│   │   │   ├── common.py        # Shared schemas (pagination, etc.)
│   │   │   └── ...
│   │   └── interfaces/          # Repository interfaces (abstract)
│   │       ├── user_repository.py
│   │       ├── community_repository.py
│   │       ├── post_repository.py
│   │       └── ...
│   │
│   ├── infrastructure/          # Infrastructure layer (implementations)
│   │   ├── __init__.py
│   │   ├── database/            # Database setup and models
│   │   │   ├── base.py          # SQLAlchemy base class
│   │   │   ├── session.py       # Database session management
│   │   │   └── models/          # SQLAlchemy models
│   │   │       ├── user.py
│   │   │       ├── verification.py
│   │   │       ├── community.py
│   │   │       ├── membership.py
│   │   │       ├── post.py
│   │   │       ├── reaction.py
│   │   │       ├── comment.py
│   │   │       ├── event.py
│   │   │       ├── chat.py
│   │   │       ├── message.py
│   │   │       ├── report.py
│   │   │       └── ...
│   │   ├── repositories/        # Repository implementations
│   │   │   ├── user_repository.py
│   │   │   ├── community_repository.py
│   │   │   ├── post_repository.py
│   │   │   ├── event_repository.py
│   │   │   └── ...
│   │   ├── cache/               # Caching implementations
│   │   │   ├── redis_client.py
│   │   │   └── cache_service.py
│   │   ├── storage/             # File storage implementations
│   │   │   ├── base.py          # Abstract storage interface
│   │   │   ├── local_storage.py # Development
│   │   │   └── s3_storage.py    # Production
│   │   ├── email/               # Email service implementations
│   │   │   ├── base.py
│   │   │   └── smtp_email.py
│   │   └── external/            # External API integrations
│   │       ├── google_oauth.py
│   │       └── sentry_client.py
│   │
│   ├── api/                     # API layer (routes, controllers)
│   │   ├── __init__.py
│   │   ├── v1/                  # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Main router aggregator
│   │   │   ├── endpoints/       # Endpoint implementations
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── verifications.py
│   │   │   │   ├── communities.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── comments.py
│   │   │   │   ├── events.py
│   │   │   │   ├── chats.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── moderation.py
│   │   │   │   ├── search.py
│   │   │   │   ├── notifications.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── health.py
│   │   │   ├── middleware/      # API middleware
│   │   │   │   ├── rate_limit.py
│   │   │   │   ├── auth.py
│   │   │   │   └── logging.py
│   │   │   └── dependencies/    # Route-specific dependencies
│   │   │       ├── auth.py      # get_current_user, etc.
│   │   │       ├── permissions.py
│   │   │       └── pagination.py
│   │   └── websocket/           # WebSocket handlers
│   │       ├── __init__.py
│   │       ├── manager.py       # Connection manager
│   │       ├── handlers.py      # WebSocket message handlers
│   │       └── models.py        # WebSocket message models
│   │
│   └── tasks/                   # Celery background tasks
│       ├── __init__.py
│       ├── celery_app.py        # Celery configuration
│       ├── email_tasks.py       # Email sending tasks
│       ├── analytics_tasks.py   # Analytics aggregation
│       ├── event_tasks.py       # Event reminders
│       └── cleanup_tasks.py     # Cleanup jobs
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── factories/               # Factory Boy factories
│   │   ├── user_factory.py
│   │   ├── community_factory.py
│   │   ├── post_factory.py
│   │   └── ...
│   ├── unit/                    # Unit tests
│   │   ├── services/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_user_service.py
│   │   │   ├── test_community_service.py
│   │   │   └── ...
│   │   ├── repositories/
│   │   └── utilities/
│   ├── integration/             # Integration tests
│   │   ├── api/
│   │   │   ├── test_auth_endpoints.py
│   │   │   ├── test_user_endpoints.py
│   │   │   ├── test_community_endpoints.py
│   │   │   ├── test_post_endpoints.py
│   │   │   ├── test_event_endpoints.py
│   │   │   ├── test_chat_endpoints.py
│   │   │   └── ...
│   │   ├── websocket/
│   │   │   └── test_chat_websocket.py
│   │   └── tasks/
│   │       └── test_email_tasks.py
│   └── e2e/                     # End-to-end tests
│       ├── test_registration_flow.py
│       ├── test_verification_flow.py
│       ├── test_post_creation_flow.py
│       └── test_event_registration_flow.py
│
├── scripts/                     # Utility scripts
│   ├── seed_data.py             # Database seeding for development
│   ├── create_admin.py          # Create admin user
│   └── migrate_data.py          # Data migration utilities
│
├── docker/                      # Docker configurations
│   ├── Dockerfile               # Multi-stage production build
│   ├── Dockerfile.dev           # Development with hot-reload
│   └── docker-compose.yml       # Local development stack
│
├── kubernetes/                  # Kubernetes manifests (production)
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml             # Template (actual secrets from vault)
│   ├── api-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   ├── ingress.yaml
│   └── hpa.yaml                 # Horizontal Pod Autoscaler
│
├── .github/                     # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml               # Lint, test, build
│       ├── cd-staging.yml       # Deploy to staging
│       └── cd-production.yml    # Deploy to production
│
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Project metadata and dependencies (uv)
├── uv.lock                      # Dependency lock file
├── .env.example                 # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── README.md                    # Project documentation
├── CONTRIBUTING.md              # Contribution guidelines
└── LICENSE
```

**Structure Decision**: 

We've chosen a **Hexagonal Architecture (Ports and Adapters)** with the following layers:

1. **Domain Layer** (`app/domain/`): Pure business logic, entities, value objects
2. **Application Layer** (`app/application/`): Use cases, services, DTOs (schemas), repository interfaces
3. **Infrastructure Layer** (`app/infrastructure/`): Concrete implementations (database, cache, external APIs)
4. **API Layer** (`app/api/`): HTTP endpoints, WebSocket handlers, middleware

**Benefits for Scalability:**
- ✅ **Loose Coupling**: Business logic independent of frameworks and databases
- ✅ **Testability**: Easy to mock dependencies and test in isolation
- ✅ **Replaceability**: Can swap implementations (e.g., PostgreSQL → MongoDB) without changing business logic
- ✅ **Maintainability**: Clear separation of concerns makes codebase easier to navigate
- ✅ **Team Scalability**: Multiple developers can work on different layers simultaneously

## Complexity Tracking

> **No violations - Constitution Check passed**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Phase 0: Research & Foundation Setup

### 0.1 Development Environment Setup

**Objective**: Set up a reproducible development environment that matches production as closely as possible.

**Tasks:**
1. Install Python 3.11+ via pyenv or system package manager
2. Install uv package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Install Docker and Docker Compose
4. Install pre-commit: `pip install pre-commit`
5. Set up IDE (VS Code recommended) with extensions:
   - Python
   - Pylance
   - Ruff
   - GitLens
   - Docker
   - Thunder Client (API testing)

**Deliverables:**
- [ ] Python 3.11+ installed and verified (`python --version`)
- [ ] uv installed and verified (`uv --version`)
- [ ] Docker installed and verified (`docker --version`)
- [ ] Docker Compose installed and verified (`docker compose version`)
- [ ] IDE configured with extensions

### 0.2 Project Initialization

**Objective**: Initialize the project structure and dependency management.

**Tasks:**

1. **Initialize Python project with uv:**
```bash
cd studybuddy-backend
uv init --name studybuddy --python 3.11
```

2. **Create `pyproject.toml` with dependencies:**
```toml
[project]
name = "studybuddy"
version = "0.1.0"
description = "Social networking platform for university students"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi[all]>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.23",
    "alembic>=1.12.1",
    "asyncpg>=0.29.0",  # PostgreSQL async driver
    "redis>=5.0.1",
    "celery[redis]>=5.3.4",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",  # Form data
    "httpx>=0.25.2",  # OAuth + testing
    "structlog>=23.2.0",
    "prometheus-fastapi-instrumentator>=6.1.0",
    "sentry-sdk[fastapi]>=1.39.1",
    "boto3>=1.34.0",  # AWS S3
    "pillow>=10.1.0",  # Image processing
    "python-magic>=0.4.27",  # File type detection
    "email-validator>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "factory-boy>=3.3.0",
    "faker>=21.0.0",
    "black>=23.12.0",
    "ruff>=0.1.8",
    "mypy>=1.7.1",
    "pre-commit>=3.6.0",
    "httpx>=0.25.2",  # Async HTTP testing
]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # complexity (handled separately)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=app --cov-report=term-missing --cov-report=html"

[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

3. **Install dependencies:**
```bash
uv sync
uv sync --extra dev
```

4. **Create `.env.example`:**
```env
# Application
APP_NAME=StudyBuddy
APP_VERSION=0.1.0
DEBUG=true
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Database
DATABASE_URL=postgresql+asyncpg://studybuddy:studybuddy@localhost:5432/studybuddy
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth (Google)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@studybuddy.com

# File Storage
STORAGE_TYPE=local  # local or s3
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes

# AWS S3 (if STORAGE_TYPE=s3)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=studybuddy-uploads

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Monitoring
SENTRY_DSN=
ENABLE_METRICS=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_AUTH_PER_MINUTE=5

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

5. **Create basic directory structure:**
```bash
mkdir -p app/{core,domain/{entities,value_objects,enums},application/{services,schemas,interfaces},infrastructure/{database/models,repositories,cache,storage,email,external},api/{v1/endpoints,v1/middleware,v1/dependencies,websocket},tasks}
mkdir -p tests/{unit/{services,repositories},integration/{api,websocket,tasks},e2e,factories}
mkdir -p scripts docker kubernetes .github/workflows alembic/versions
touch app/__init__.py
touch app/{core,domain,application,infrastructure,api,tasks}/__init__.py
```

**Deliverables:**
- [ ] `pyproject.toml` created with all dependencies
- [ ] Dependencies installed via uv
- [ ] `.env.example` created
- [ ] Directory structure created
- [ ] Git repository initialized with initial commit

### 0.3 Docker Setup for Local Development

**Objective**: Create Docker Compose setup for local development with PostgreSQL, Redis, and API.

**Tasks:**

1. **Create `docker/Dockerfile.dev`:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --extra dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with hot-reload
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

2. **Create `docker/Dockerfile` (production):**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Create `docker/docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: studybuddy-postgres
    environment:
      POSTGRES_USER: studybuddy
      POSTGRES_PASSWORD: studybuddy
      POSTGRES_DB: studybuddy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U studybuddy"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: studybuddy-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    container_name: studybuddy-api
    env_file:
      - ../.env
    ports:
      - "8000:8000"
    volumes:
      - ../app:/app/app
      - ../tests:/app/tests
      - ../alembic:/app/alembic
      - upload_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "

  celery_worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    container_name: studybuddy-celery
    env_file:
      - ../.env
    volumes:
      - ../app:/app/app
    depends_on:
      - redis
      - postgres
    command: celery -A app.tasks.celery_app worker --loglevel=info

  celery_beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    container_name: studybuddy-celery-beat
    env_file:
      - ../.env
    volumes:
      - ../app:/app/app
    depends_on:
      - redis
      - postgres
    command: celery -A app.tasks.celery_app beat --loglevel=info

volumes:
  postgres_data:
  redis_data:
  upload_data:
```

4. **Create startup script `scripts/dev.sh`:**
```bash
#!/bin/bash
set -e

echo "🚀 Starting StudyBuddy Development Environment..."

# Copy .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
    exit 1
fi

# Start Docker Compose
echo "🐳 Starting Docker containers..."
cd docker && docker compose up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo "🏥 Checking service health..."
docker compose ps

echo "✅ Development environment ready!"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📊 ReDoc: http://localhost:8000/redoc"
echo "🔍 Health Check: http://localhost:8000/health"
```

```bash
chmod +x scripts/dev.sh
```

**Deliverables:**
- [ ] `docker/Dockerfile.dev` created
- [ ] `docker/Dockerfile` created (production)
- [ ] `docker/docker-compose.yml` created
- [ ] `scripts/dev.sh` startup script created
- [ ] Docker containers start successfully
- [ ] PostgreSQL accessible on port 5432
- [ ] Redis accessible on port 6379

### 0.4 Pre-commit Hooks Setup

**Objective**: Enforce code quality standards automatically before commits.

**Tasks:**

1. **Create `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.5.0, sqlalchemy>=2.0.23]
        args: [--strict, --ignore-missing-imports]
```

2. **Install pre-commit hooks:**
```bash
uv run pre-commit install
uv run pre-commit run --all-files  # Test on existing files
```

**Deliverables:**
- [ ] `.pre-commit-config.yaml` created
- [ ] Pre-commit hooks installed
- [ ] All hooks pass on initial run

### 0.5 CI/CD Pipeline Setup (GitHub Actions)

**Objective**: Automate testing, linting, and deployment.

**Tasks:**

1. **Create `.github/workflows/ci.yml`:**
```yaml
name: CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: |
          uv sync --extra dev
      
      - name: Run Ruff
        run: uv run ruff check app tests
      
      - name: Run Black
        run: uv run black --check app tests
      
      - name: Run MyPy
        run: uv run mypy app

  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: studybuddy
          POSTGRES_PASSWORD: studybuddy
          POSTGRES_DB: studybuddy_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: uv sync --extra dev
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://studybuddy:studybuddy@localhost:5432/studybuddy_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: |
          uv run pytest --cov=app --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          push: false
          tags: studybuddy:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

2. **Create `.github/workflows/cd-staging.yml`:**
```yaml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          push: true
          tags: ${{ secrets.REGISTRY_URL }}/studybuddy:staging-${{ github.sha }}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/studybuddy-api \
            api=${{ secrets.REGISTRY_URL }}/studybuddy:staging-${{ github.sha }} \
            -n studybuddy-staging
          kubectl rollout status deployment/studybuddy-api -n studybuddy-staging
```

3. **Create `.github/workflows/cd-production.yml`:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          push: true
          tags: |
            ${{ secrets.REGISTRY_URL }}/studybuddy:production-${{ github.sha }}
            ${{ secrets.REGISTRY_URL }}/studybuddy:latest
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/studybuddy-api \
            api=${{ secrets.REGISTRY_URL }}/studybuddy:production-${{ github.sha }} \
            -n studybuddy-production
          kubectl rollout status deployment/studybuddy-api -n studybuddy-production
      
      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          body: |
            Production deployment of commit ${{ github.sha }}
          draft: false
          prerelease: false
```

**Deliverables:**
- [ ] CI workflow created (lint, test, build)
- [ ] CD staging workflow created
- [ ] CD production workflow created
- [ ] GitHub secrets configured (when deploying)

### 0.6 Kubernetes Manifests for Production

**Objective**: Create Kubernetes configurations for easy production deployment.

**Tasks:**

1. **Create `kubernetes/namespace.yaml`:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: studybuddy-production
---
apiVersion: v1
kind: Namespace
metadata:
  name: studybuddy-staging
```

2. **Create `kubernetes/configmap.yaml`:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: studybuddy-config
  namespace: studybuddy-production
data:
  APP_NAME: "StudyBuddy"
  APP_VERSION: "0.1.0"
  ENVIRONMENT: "production"
  DEBUG: "false"
  HOST: "0.0.0.0"
  PORT: "8000"
  RELOAD: "false"
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "10"
  ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "15"
  REFRESH_TOKEN_EXPIRE_DAYS: "30"
  STORAGE_TYPE: "s3"
  MAX_UPLOAD_SIZE: "10485760"
  ENABLE_METRICS: "true"
  RATE_LIMIT_PER_MINUTE: "100"
  RATE_LIMIT_AUTH_PER_MINUTE: "5"
```

3. **Create `kubernetes/secrets.yaml.template`:**
```yaml
# DO NOT COMMIT THIS FILE WITH REAL VALUES
# Use Kubernetes secrets management or external vault
apiVersion: v1
kind: Secret
metadata:
  name: studybuddy-secrets
  namespace: studybuddy-production
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:password@postgres:5432/studybuddy"
  REDIS_URL: "redis://redis:6379/0"
  SECRET_KEY: "your-super-secret-key-here"
  GOOGLE_CLIENT_ID: "your-google-client-id"
  GOOGLE_CLIENT_SECRET: "your-google-client-secret"
  SMTP_USER: "your-email@gmail.com"
  SMTP_PASSWORD: "your-app-password"
  AWS_ACCESS_KEY_ID: "your-aws-key"
  AWS_SECRET_ACCESS_KEY: "your-aws-secret"
  SENTRY_DSN: "your-sentry-dsn"
```

4. **Create `kubernetes/api-deployment.yaml`:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: studybuddy-api
  namespace: studybuddy-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: studybuddy-api
  template:
    metadata:
      labels:
        app: studybuddy-api
    spec:
      containers:
      - name: api
        image: your-registry/studybuddy:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: studybuddy-config
        - secretRef:
            name: studybuddy-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: studybuddy-api
  namespace: studybuddy-production
spec:
  selector:
    app: studybuddy-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

5. **Create `kubernetes/celery-deployment.yaml`:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: studybuddy-celery-worker
  namespace: studybuddy-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: studybuddy-celery-worker
  template:
    metadata:
      labels:
        app: studybuddy-celery-worker
    spec:
      containers:
      - name: celery-worker
        image: your-registry/studybuddy:latest
        command: ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: studybuddy-config
        - secretRef:
            name: studybuddy-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: studybuddy-celery-beat
  namespace: studybuddy-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: studybuddy-celery-beat
  template:
    metadata:
      labels:
        app: studybuddy-celery-beat
    spec:
      containers:
      - name: celery-beat
        image: your-registry/studybuddy:latest
        command: ["celery", "-A", "app.tasks.celery_app", "beat", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: studybuddy-config
        - secretRef:
            name: studybuddy-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

6. **Create `kubernetes/ingress.yaml`:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: studybuddy-ingress
  namespace: studybuddy-production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.studybuddy.com
    secretName: studybuddy-tls
  rules:
  - host: api.studybuddy.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: studybuddy-api
            port:
              number: 80
```

7. **Create `kubernetes/hpa.yaml` (Horizontal Pod Autoscaler):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: studybuddy-api-hpa
  namespace: studybuddy-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: studybuddy-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deliverables:**
- [ ] Kubernetes namespace configuration created
- [ ] ConfigMap for application settings created
- [ ] Secrets template created (documented process for real secrets)
- [ ] API deployment manifest created
- [ ] Celery worker/beat deployments created
- [ ] Ingress configuration created
- [ ] HPA for auto-scaling created
- [ ] Deployment script documented in README

## Phase 0 Deliverables Summary

✅ **Development Environment**
- Python 3.11+, uv, Docker, Docker Compose installed
- IDE configured with extensions

✅ **Project Foundation**
- `pyproject.toml` with all dependencies
- Directory structure following hexagonal architecture
- `.env.example` with all configuration options

✅ **Local Development**
- Docker Compose with PostgreSQL, Redis, API, Celery
- Hot-reload enabled for development
- Startup script for easy local setup

✅ **Code Quality**
- Pre-commit hooks (Black, Ruff, MyPy)
- Enforced before every commit

✅ **CI/CD**
- GitHub Actions for testing and linting
- Automated deployment to staging
- Manual approval for production deployment

✅ **Production Infrastructure**
- Kubernetes manifests for all services
- Horizontal pod autoscaling
- Health checks and monitoring
- Easy path from local → staging → production

## Next Steps

After completing Phase 0, proceed with:

1. **Phase 1: Core Infrastructure** (Week 1-2)
   - Database models and migrations
   - Core configuration and settings
   - Error handling and logging
   - Health check endpoints

2. **Phase 2: Authentication** (Week 3-4)
   - Google OAuth integration
   - JWT token management
   - User registration and profile management
   - Student verification system

3. **Phase 3: Communities** (Week 5-6)
   - Community CRUD operations
   - Membership management
   - Role-based permissions
   - Hierarchical structure

4. **Phase 4: Social Feed** (Week 7-8)
   - Posts, reactions, comments
   - Feed generation and pagination
   - Media upload handling

... (Continue with remaining phases as per specification)

---

**Constitution Compliance**: This plan adheres to all principles defined in the StudyBuddy Constitution, ensuring code quality, testing standards, security, performance, and scalability from day one.

**Easy Local to Production Path:**
```bash
# Local development
./scripts/dev.sh

# Push to develop branch
git push origin develop
# → Automatically deploys to staging via GitHub Actions

# Merge to main (after PR approval)
git checkout main && git merge develop && git push
# → Automatically deploys to production via GitHub Actions
```
