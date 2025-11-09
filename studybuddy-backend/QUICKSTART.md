# 🚀 StudyBuddy Backend - Quick Start Guide

This guide will help you set up the StudyBuddy backend for local development in under 10 minutes.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

| Software | Minimum Version | Installation Link |
|----------|----------------|------------------|
| **Python** | 3.12+ (3.11+ supported) | [python.org](https://www.python.org/downloads/) |
| **Docker** | 28.3+ | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | v2.38+ | Included with Docker Desktop |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com/downloads/) |

### Verify Installations

Run these commands to verify your installations:

```bash
python --version   # Should show 3.12.x or 3.11.x
docker --version   # Should show 28.3.x or higher
docker compose version  # Should show v2.38.x or higher
git --version      # Should show 2.40.x or higher
```

## 📦 Step 1: Install uv Package Manager

StudyBuddy uses [uv](https://github.com/astral-sh/uv) - an ultra-fast Python package manager written in Rust.

### Install uv

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation

```bash
uv --version  # Should show 0.9.8 or higher
```

## 🔄 Step 2: Clone and Configure

### Clone the Repository

```bash
git clone https://github.com/denol007/sb1.git
cd sb1/studybuddy-backend
```

### Create Environment File

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

**Important Configuration Variables:**

Open `.env` in your editor and review/update these key settings:

```bash
# Application Settings
APP_NAME="StudyBuddy API"
APP_ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1

# Database (Docker Compose will use these)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=studybuddy_dev
DATABASE_USER=studybuddy
DATABASE_PASSWORD=studybuddy_dev_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# CORS (Add your frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

> 💡 **Tip:** For local development, the default values work fine. Change security keys for staging/production.

## 🐳 Step 3: Start Development Environment

### Using the Dev Script (Recommended)

The project includes a convenient development script that manages all Docker services:

```bash
./scripts/dev.sh start
```

This single command will:

- ✅ Start all required services (PostgreSQL, Redis, API, Celery, Flower)
- ✅ Create the database and run migrations
- ✅ Display service URLs and health status
- ✅ Show logs in real-time

### Services Overview

After starting, you'll have access to:

| Service | URL | Description |
|---------|-----|-------------|
| 🚀 **FastAPI API** | <http://localhost:8000> | Main API server |
| 📚 **API Docs (Swagger)** | <http://localhost:8000/docs> | Interactive API documentation |
| 📖 **API Docs (ReDoc)** | <http://localhost:8000/redoc> | Alternative API docs |
| 🏥 **Health Check** | <http://localhost:8000/health> | Service health status |
| 🐘 **PostgreSQL** | localhost:5432 | Database server |
| 🔴 **Redis** | localhost:6379 | Cache & message broker |
| 🌸 **Flower** | <http://localhost:5555> | Celery task monitor |

### Verify Services are Running

```bash
./scripts/dev.sh ps
```

You should see all services in "Up" state:

```
NAME                    STATUS          PORTS
studybuddy-api          Up 2 minutes    0.0.0.0:8000->8000/tcp
studybuddy-postgres     Up 2 minutes    0.0.0.0:5432->5432/tcp
studybuddy-redis        Up 2 minutes    0.0.0.0:6379->6379/tcp
studybuddy-celery-worker Up 2 minutes
studybuddy-celery-beat  Up 2 minutes
studybuddy-flower       Up 2 minutes    0.0.0.0:5555->5555/tcp
```

## 🧪 Step 4: Run Tests

### Install Development Dependencies

First, ensure all dependencies are installed:

```bash
uv sync --all-extras
```

### Run the Test Suite

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test files
uv run pytest tests/unit/
uv run pytest tests/integration/

# Run tests for specific user stories
uv run pytest -m US1  # User Registration & Authentication
uv run pytest -m US2  # Community Management
```

### View Coverage Report

After running tests with coverage, open the HTML report:

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

> 📊 **Coverage Requirement:** The project enforces a minimum of 80% test coverage in CI.

## 🛠️ Step 5: Development Workflow

### Code Quality Tools

The project uses several code quality tools. Run them before committing:

```bash
# Format code with Black
uv run black app/ tests/

# Lint with Ruff
uv run ruff check app/ tests/

# Type check with MyPy
uv run mypy app/

# Or run all checks at once with pre-commit
pre-commit run --all-files
```

### Database Migrations

When you modify database models, create and apply migrations:

```bash
# Create a new migration
docker compose exec api alembic revision --autogenerate -m "description of changes"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback one migration
docker compose exec api alembic downgrade -1

# View migration history
docker compose exec api alembic history
```

### Background Tasks

Monitor Celery background tasks using Flower:

1. Open <http://localhost:5555> in your browser
2. View active tasks, workers, and task history
3. Monitor task execution times and success/failure rates

### Viewing Logs

```bash
# View logs for all services
./scripts/dev.sh logs

# View logs for specific service
./scripts/dev.sh logs api
./scripts/dev.sh logs postgres
./scripts/dev.sh logs redis
./scripts/dev.sh logs celery-worker

# Follow logs in real-time
docker compose logs -f api
```

## 📝 Step 6: Make Your First API Request

### Using the Interactive Docs

1. Open <http://localhost:8000/docs> in your browser
2. Explore available endpoints
3. Click "Try it out" on any endpoint
4. Fill in parameters and click "Execute"

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/api/v1/
```

### Using HTTPie (Alternative)

```bash
# Install HTTPie
pip install httpie

# Make requests
http GET http://localhost:8000/health
```

## 🔧 Common Commands Reference

### Dev Script Commands

```bash
./scripts/dev.sh start    # Start all services
./scripts/dev.sh stop     # Stop all services
./scripts/dev.sh restart  # Restart all services
./scripts/dev.sh logs     # View logs
./scripts/dev.sh ps       # Show service status
./scripts/dev.sh down     # Stop and remove containers
./scripts/dev.sh clean    # Clean everything (includes volumes)
./scripts/dev.sh build    # Rebuild Docker images
```

### Direct Docker Compose Commands

```bash
# Start services in background
docker compose up -d

# View running containers
docker compose ps

# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Rebuild and start
docker compose up -d --build

# Execute commands in containers
docker compose exec api python -m app.main
docker compose exec postgres psql -U studybuddy -d studybuddy_dev
docker compose exec redis redis-cli
```

## 🐛 Troubleshooting

### Port Already in Use

If you see errors about ports already in use:

```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop the process or change ports in .env
```

### Database Connection Errors

```bash
# Ensure PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Reset database (WARNING: deletes all data)
./scripts/dev.sh down
./scripts/dev.sh clean
./scripts/dev.sh start
```

### Docker Issues

```bash
# Restart Docker daemon
# macOS: Restart Docker Desktop
# Linux: sudo systemctl restart docker

# Clean Docker cache
docker system prune -a --volumes

# Rebuild from scratch
./scripts/dev.sh clean
./scripts/dev.sh build
./scripts/dev.sh start
```

### Pre-commit Hook Failures

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Skip hooks for emergency commits (use sparingly!)
git commit --no-verify -m "message"
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --all-extras

# Verify uv environment
uv pip list
```

## 🎯 Next Steps

Now that you have the development environment running:

1. **📖 Read the Documentation**
   - [Architecture Guide](docs/architecture.md) - Understand hexagonal architecture
   - [API Documentation](http://localhost:8000/docs) - Explore available endpoints
   - [Contributing Guide](CONTRIBUTING.md) - Learn development guidelines

2. **🏗️ Explore the Codebase**
   - `app/domain/` - Business logic and entities
   - `app/application/` - Use cases and services
   - `app/api/v1/endpoints/` - HTTP endpoints
   - `app/infrastructure/` - External integrations

3. **✍️ Start Contributing**
   - Check [open issues](https://github.com/denol007/sb1/issues)
   - Read [CONTRIBUTING.md](CONTRIBUTING.md)
   - Join our [Discord community](#)

4. **🧪 Write Tests**
   - Follow TDD (Test-Driven Development)
   - Maintain 80%+ coverage
   - Use factories in `tests/factories/`

## 📚 Additional Resources

- **Main README:** [README.md](README.md)
- **Contributing Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Project Specification:** [.specify/specification.md](.specify/specification.md)
- **Development Constitution:** [.specify/constitution.md](.specify/constitution.md)
- **GitHub Actions Workflows:** [.github/workflows/](.github/workflows/)
- **Kubernetes Manifests:** [kubernetes/](kubernetes/)

## 💬 Getting Help

- **Issues:** [GitHub Issues](https://github.com/denol007/sb1/issues)
- **Discussions:** [GitHub Discussions](https://github.com/denol007/sb1/discussions)
- **Discord:** [Join our community](#)
- **Email:** <support@studybuddy.example.com>

---

**Happy Coding! 🎉**

If you found this guide helpful, please ⭐ star the repository!
