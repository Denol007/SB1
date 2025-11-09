# StudyBuddy Backend - Quick Start Guide

## 🚀 Getting Started

This guide will help you set up the StudyBuddy backend development environment in minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## Quick Setup (5 minutes)

### 1. Install uv (Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

### 2. Clone and setup

```bash
cd studybuddy-backend
cp .env.example .env  # Edit with your configuration
```

### 3. Start development environment

```bash
./scripts/dev.sh
```

This will:

- Start PostgreSQL on port 5432
- Start Redis on port 6379
- Start API on port 8000 with hot-reload
- Start Celery worker and beat
- Run database migrations

### 4. Access the application

- **API Documentation (Swagger)**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **Health Check**: <http://localhost:8000/health>

## Development Workflow

### Install dependencies

```bash
uv sync              # Install production dependencies
uv sync --extra dev  # Install dev dependencies too
```

### Run tests

```bash
# All tests with coverage
uv run pytest

# Specific test file
uv run pytest tests/unit/services/test_auth_service.py

# With coverage report
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Code quality checks

```bash
# Format code
uv run black app tests

# Lint
uv run ruff check app tests

# Type check
uv run mypy app

# Run all checks (what CI runs)
uv run pre-commit run --all-files
```

### Database migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Add users table"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Run locally without Docker

```bash
# Make sure PostgreSQL and Redis are running
uv run uvicorn app.main:app --reload

# In another terminal, start Celery worker
uv run celery -A app.tasks.celery_app worker --loglevel=info

# In another terminal, start Celery beat
uv run celery -A app.tasks.celery_app beat --loglevel=info
```

## Deployment

### Deploy to Staging (Automatic)

```bash
git checkout develop
git commit -m "Your changes"
git push origin develop
# GitHub Actions automatically deploys to staging
```

### Deploy to Production (Manual approval)

```bash
# Merge to main after PR approval
git checkout main
git merge develop
git push origin main
# GitHub Actions deploys to production (requires manual approval)
```

### Manual Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml  # Create from template first!
kubectl apply -f kubernetes/api-deployment.yaml
kubectl apply -f kubernetes/celery-deployment.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml

# Check status
kubectl get pods -n studybuddy-production
kubectl logs -f deployment/studybuddy-api -n studybuddy-production
```

## Useful Commands

### Docker Compose

```bash
# Start all services
cd docker && docker compose up -d

# View logs
docker compose logs -f api

# Restart API only
docker compose restart api

# Stop all services
docker compose down

# Rebuild and start
docker compose up -d --build
```

### Database

```bash
# Connect to PostgreSQL
docker exec -it studybuddy-postgres psql -U studybuddy -d studybuddy

# Backup database
docker exec studybuddy-postgres pg_dump -U studybuddy studybuddy > backup.sql

# Restore database
docker exec -i studybuddy-postgres psql -U studybuddy studybuddy < backup.sql
```

### Redis

```bash
# Connect to Redis CLI
docker exec -it studybuddy-redis redis-cli

# Monitor Redis commands
docker exec -it studybuddy-redis redis-cli monitor

# Clear Redis cache
docker exec -it studybuddy-redis redis-cli FLUSHDB
```

## Project Structure Overview

```
studybuddy-backend/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── application/      # Business logic services
│   ├── core/             # Configuration, security
│   ├── domain/           # Domain models and entities
│   ├── infrastructure/   # Database, cache, external services
│   └── tasks/            # Celery background tasks
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # API integration tests
│   └── e2e/              # End-to-end tests
├── docker/               # Docker configurations
├── kubernetes/           # Kubernetes manifests
└── alembic/              # Database migrations
```

## Environment Variables

Key variables to configure in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://studybuddy:studybuddy@localhost:5432/studybuddy

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Troubleshooting

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Database connection error

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Redis connection error

```bash
# Check if Redis is running
docker compose ps redis

# Restart Redis
docker compose restart redis
```

### Migrations out of sync

```bash
# Reset database (CAUTION: deletes all data)
docker compose down -v
docker compose up -d
uv run alembic upgrade head
```

## Resources

- **Specification**: `.specify/specs/001-studybuddy-platform.md`
- **Constitution**: `.specify/memory/constitution.md`
- **Implementation Plan**: `.specify/plans/001-studybuddy-platform-implementation.md`
- **FastAPI Docs**: <https://fastapi.tiangolo.com>
- **SQLAlchemy Docs**: <https://docs.sqlalchemy.org>
- **Celery Docs**: <https://docs.celeryproject.org>

## Need Help?

1. Check the specification document for requirements
2. Review the constitution for coding standards
3. Check existing code for patterns and examples
4. Run tests to ensure nothing breaks
5. Use pre-commit hooks to catch issues early

Happy coding! 🎉
