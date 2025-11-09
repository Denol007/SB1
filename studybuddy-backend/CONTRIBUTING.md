# Contributing to StudyBuddy Backend

Thank you for your interest in contributing to StudyBuddy! 🎉

This document provides guidelines and best practices for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Architecture](#project-architecture)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background or identity.

### Our Standards

**Positive behaviors:**

- Using welcoming and inclusive language
- Respecting differing viewpoints and experiences
- Accepting constructive criticism gracefully
- Focusing on what's best for the community
- Showing empathy towards other community members

**Unacceptable behaviors:**

- Harassment, trolling, or derogatory comments
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## 🚀 Getting Started

### Prerequisites

1. **Read the documentation:**
   - [README.md](README.md) - Project overview
   - [QUICKSTART.md](QUICKSTART.md) - Setup instructions
   - [.specify/specification.md](.specify/specification.md) - Detailed requirements
   - [.specify/constitution.md](.specify/constitution.md) - Development principles

2. **Set up your development environment:**

   ```bash
   # Follow the QUICKSTART.md guide
   git clone https://github.com/denol007/sb1.git
   cd sb1/studybuddy-backend
   cp .env.example .env
   ./scripts/dev.sh start
   ```

3. **Verify your setup:**

   ```bash
   # Run tests to ensure everything works
   uv run pytest

   # Run code quality checks
   pre-commit run --all-files
   ```

## 🔄 Development Process

### 1. Choose an Issue

- Browse [open issues](https://github.com/denol007/sb1/issues)
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Comment on the issue to express your interest
- Wait for assignment to avoid duplicate work

### 2. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/sb1.git
cd sb1/studybuddy-backend

# Add upstream remote
git remote add upstream https://github.com/denol007/sb1.git
```

### 3. Create a Branch

Use descriptive branch names following this convention:

```bash
# Feature branches
git checkout -b feature/user-story-1-authentication
git checkout -b feature/US2-community-management

# Bug fix branches
git checkout -b fix/login-validation-error
git checkout -b fix/issue-123-redis-connection

# Documentation branches
git checkout -b docs/update-api-examples
git checkout -b docs/architecture-guide
```

### 4. Make Changes

Follow the code standards and architecture guidelines below.

### 5. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run with coverage (minimum 80% required)
uv run pytest --cov=app --cov-report=html

# Run specific tests
uv run pytest tests/unit/services/test_auth_service.py
```

### 6. Commit Your Changes

Follow the [commit guidelines](#commit-guidelines) below.

### 7. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-branch-name

# Create a Pull Request on GitHub
```

## 📏 Code Standards

### Python Style Guide

We follow PEP 8 with some modifications enforced by our tools:

**Formatting (Black):**

- Line length: 100 characters
- String quotes: Double quotes preferred
- Trailing commas: Yes for multi-line structures

**Linting (Ruff):**

- Rules: E, W, F, I, C, B, UP (see pyproject.toml)
- Complexity: Maximum 10 per function
- Imports: Sorted and organized

**Type Hints (MyPy):**

- **MANDATORY** on all function signatures
- Strict mode enabled
- No `Any` types unless absolutely necessary

### Code Quality Tools

Run these before committing:

```bash
# Format code
uv run black app/ tests/

# Lint and fix auto-fixable issues
uv run ruff check --fix app/ tests/

# Type check
uv run mypy app/

# Security check
uv run bandit -r app/

# Run all checks at once
pre-commit run --all-files
```

### Architecture Principles

StudyBuddy follows **Hexagonal Architecture (Ports and Adapters)**:

```
app/
├── domain/           # Business logic (entities, value objects, enums)
├── application/      # Use cases (services, schemas, interfaces)
├── infrastructure/   # External adapters (database, cache, email, etc.)
└── api/              # HTTP/WebSocket adapters
```

**Key principles:**

1. **Domain Layer** (Pure Python, no dependencies):
   - Business entities and value objects
   - Domain events and exceptions
   - No framework dependencies

2. **Application Layer** (Business logic):
   - Service classes implementing use cases
   - DTOs (Pydantic schemas) for data transfer
   - Port interfaces defining contracts

3. **Infrastructure Layer** (Technical implementation):
   - Repository implementations
   - External service integrations
   - Database models (SQLAlchemy)

4. **API Layer** (Delivery mechanism):
   - HTTP endpoints (FastAPI)
   - WebSocket handlers
   - Request/response transformation

**Dependencies flow inward:**

```
API → Application → Domain ← Infrastructure
```

### Naming Conventions

**Files and directories:**

```python
# Use snake_case for modules
user_service.py
auth_repository.py

# Use kebab-case for directories with multiple words
domain/value-objects/
api/v1/endpoints/
```

**Classes:**

```python
# Use PascalCase
class UserService:
    pass

class AuthRepository:
    pass

class EmailValueObject:
    pass
```

**Functions and variables:**

```python
# Use snake_case
def create_user(user_data: UserCreate) -> User:
    pass

async def send_verification_email(email: str) -> None:
    pass

user_repository = UserRepository()
```

**Constants:**

```python
# Use UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5
DEFAULT_PAGE_SIZE = 20
JWT_ALGORITHM = "HS256"
```

### Docstrings

Use **Google-style docstrings** for all public APIs:

```python
def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    """Create a new user in the system.

    Args:
        user_data: User creation data including email and password.
        db: Database session for persistence.

    Returns:
        The newly created user instance.

    Raises:
        UserAlreadyExistsError: If email is already registered.
        ValidationError: If user data is invalid.

    Example:
        >>> user_data = UserCreate(email="test@example.com", password="secure123")
        >>> user = await create_user(user_data, db)
        >>> print(user.email)
        "test@example.com"
    """
    pass
```

### Error Handling

**Use custom exceptions:**

```python
# domain/exceptions.py
class DomainException(Exception):
    """Base exception for domain errors."""

class UserAlreadyExistsError(DomainException):
    """Raised when attempting to create a user with existing email."""

# In your code
if await user_repository.exists(email=user_data.email):
    raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")
```

**Never catch generic exceptions in business logic:**

```python
# ❌ BAD
try:
    result = await some_operation()
except Exception:
    pass

# ✅ GOOD
try:
    result = await some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

## 🧪 Testing Requirements

### Coverage Requirements

- **Minimum coverage:** 80% (enforced in CI)
- **Target coverage:** 90%+
- **Critical paths:** 100% coverage required

### Test Structure

```python
# tests/unit/services/test_user_service.py
import pytest
from app.application.services.user_service import UserService
from tests.factories.user_factory import UserFactory

@pytest.mark.US1  # Link to user story
@pytest.mark.asyncio
async def test_create_user_success(db_session, user_repository):
    """Test successful user creation."""
    # Arrange
    user_data = UserFactory.build()
    service = UserService(user_repository)

    # Act
    user = await service.create_user(user_data, db_session)

    # Assert
    assert user.email == user_data.email
    assert user.is_active is True

@pytest.mark.US1
@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session, user_repository):
    """Test user creation fails with duplicate email."""
    # Arrange
    existing_user = await UserFactory.create(db_session)
    user_data = UserFactory.build(email=existing_user.email)
    service = UserService(user_repository)

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError):
        await service.create_user(user_data, db_session)
```

### Test Categories

**Unit Tests** (`tests/unit/`):

- Test individual functions/methods in isolation
- Mock external dependencies
- Fast execution (< 1ms per test)

**Integration Tests** (`tests/integration/`):

- Test multiple components together
- Use real database (test container)
- Test API endpoints

**E2E Tests** (`tests/e2e/`):

- Test complete user workflows
- Simulate real user scenarios
- Cover critical paths only

### Test Data Factories

Use Factory Boy for test data:

```python
# tests/factories/user_factory.py
import factory
from app.domain.entities.user import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Faker('user_name')
    full_name = factory.Faker('name')
    is_active = True
    is_verified = False
```

## 📝 Commit Guidelines

We use **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add Google OAuth login` |
| `fix` | Bug fix | `fix(api): correct email validation regex` |
| `docs` | Documentation | `docs(readme): update setup instructions` |
| `style` | Code style changes | `style(user): format with Black` |
| `refactor` | Code refactoring | `refactor(auth): extract validation logic` |
| `test` | Add/update tests | `test(user): add registration tests` |
| `chore` | Maintenance tasks | `chore(deps): update FastAPI to 0.121.0` |
| `perf` | Performance improvements | `perf(db): add index on user email` |
| `ci` | CI/CD changes | `ci(github): add coverage reporting` |

### Commit Examples

```bash
# Good commits
git commit -m "feat(US1): implement user registration endpoint"
git commit -m "fix(auth): resolve JWT token expiration issue"
git commit -m "test(community): add community creation tests"
git commit -m "docs(api): add authentication examples"

# Detailed commit
git commit -m "feat(US2): implement community creation

- Add CommunityService with create_community method
- Add validation for community name uniqueness
- Add integration tests for community endpoints
- Update API documentation

Closes #42"
```

### Pre-commit Hooks

Hooks will automatically run on `git commit`:

- Trailing whitespace removal
- File formatting (Black)
- Linting (Ruff)
- Type checking (MyPy)
- Security scanning (Bandit)
- Commit message validation

**If hooks fail:**

```bash
# Fix the issues and commit again
# Or bypass hooks (use sparingly!)
git commit --no-verify -m "message"
```

## 🔀 Pull Request Process

### Before Creating a PR

1. **Update from upstream:**

   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. **Run all checks:**

   ```bash
   uv run pytest --cov=app
   pre-commit run --all-files
   ```

3. **Update documentation** if needed

### PR Title Format

Use the same format as commits:

```
feat(US1): implement user registration endpoint
fix(auth): resolve token validation issue
docs(api): add WebSocket examples
```

### PR Description Template

```markdown
## Description
Brief description of changes.

## Related Issues
Closes #123
Relates to #456

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Coverage meets 80% minimum

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Pre-commit hooks pass

## Screenshots (if applicable)
Add screenshots for UI changes.

## Additional Notes
Any additional information for reviewers.
```

### Review Process

1. **Automated checks** must pass (CI, tests, coverage)
2. **Code review** by at least one maintainer
3. **Address feedback** and push updates
4. **Approval** from maintainer
5. **Merge** (squash and merge preferred)

## 🏗️ Project Architecture

### Directory Structure

```
studybuddy-backend/
├── app/
│   ├── core/                    # Core configuration
│   │   ├── config.py            # Settings management
│   │   ├── security.py          # Auth utilities
│   │   └── dependencies.py      # FastAPI dependencies
│   │
│   ├── domain/                  # Domain layer (pure business logic)
│   │   ├── entities/            # Business entities
│   │   ├── value_objects/       # Value objects
│   │   └── enums/               # Enumerations
│   │
│   ├── application/             # Application layer
│   │   ├── services/            # Business services
│   │   ├── schemas/             # DTOs (Pydantic models)
│   │   └── interfaces/          # Port definitions
│   │
│   ├── infrastructure/          # Infrastructure layer
│   │   ├── database/
│   │   │   └── models/          # SQLAlchemy models
│   │   ├── repositories/        # Repository implementations
│   │   ├── cache/               # Redis cache
│   │   ├── storage/             # File storage (S3)
│   │   ├── email/               # Email service
│   │   └── external/            # External APIs
│   │
│   ├── api/                     # API layer
│   │   ├── v1/
│   │   │   ├── endpoints/       # HTTP endpoints
│   │   │   ├── middleware/      # Middleware
│   │   │   └── dependencies/    # Route dependencies
│   │   └── websocket/           # WebSocket handlers
│   │
│   └── tasks/                   # Celery tasks
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end tests
│   ├── factories/               # Test factories
│   └── conftest.py              # Pytest configuration
│
├── alembic/                     # Database migrations
├── docker/                      # Docker configurations
├── kubernetes/                  # K8s manifests
└── scripts/                     # Utility scripts
```

### Adding New Features

When implementing a new feature (e.g., User Story 3: Content Creation):

1. **Domain layer:**

   ```python
   # app/domain/entities/post.py
   @dataclass
   class Post:
       id: UUID
       title: str
       content: str
       author_id: UUID
       created_at: datetime
   ```

2. **Application layer:**

   ```python
   # app/application/schemas/post.py
   class PostCreate(BaseModel):
       title: str = Field(..., min_length=1, max_length=200)
       content: str = Field(..., min_length=1)

   # app/application/services/post_service.py
   class PostService:
       async def create_post(self, data: PostCreate) -> Post:
           pass
   ```

3. **Infrastructure layer:**

   ```python
   # app/infrastructure/database/models/post.py
   class PostModel(Base):
       __tablename__ = "posts"
       id = Column(UUID, primary_key=True)
       title = Column(String(200), nullable=False)

   # app/infrastructure/repositories/post_repository.py
   class PostRepository:
       async def create(self, post: Post) -> Post:
           pass
   ```

4. **API layer:**

   ```python
   # app/api/v1/endpoints/posts.py
   @router.post("/", response_model=PostResponse)
   async def create_post(
       data: PostCreate,
       service: PostService = Depends(get_post_service)
   ):
       return await service.create_post(data)
   ```

5. **Tests:**

   ```python
   # tests/unit/services/test_post_service.py
   # tests/integration/api/test_posts_endpoints.py
   ```

## 🐛 Issue Reporting

### Bug Reports

Include the following information:

```markdown
**Description:**
Clear description of the bug.

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen.

**Actual Behavior:**
What actually happens.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12.1]
- Docker: [e.g., 28.3.1]

**Logs:**
```

Paste relevant logs here

```

**Screenshots:**
If applicable.
```

### Feature Requests

```markdown
**Problem Statement:**
What problem does this feature solve?

**Proposed Solution:**
How should it work?

**Alternatives Considered:**
Other approaches you've thought about.

**Additional Context:**
Any other relevant information.
```

## 📚 Additional Resources

- **FastAPI Documentation:** <https://fastapi.tiangolo.com>
- **SQLAlchemy Documentation:** <https://docs.sqlalchemy.org>
- **Pydantic Documentation:** <https://docs.pydantic.dev>
- **pytest Documentation:** <https://docs.pytest.org>
- **Hexagonal Architecture:** <https://alistair.cockburn.us/hexagonal-architecture/>

## 🙏 Thank You

Your contributions make StudyBuddy better for everyone. We appreciate your time and effort! ❤️

---

**Questions?** Open a [discussion](https://github.com/denol007/sb1/discussions) or reach out to the maintainers.

**Happy Contributing! 🚀**
