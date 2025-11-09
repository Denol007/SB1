# Test Factories

This directory contains Factory Boy factories for generating test data with realistic fake values.

## Overview

Test factories provide a convenient way to create model instances for testing without manually specifying every field. They use [Factory Boy](https://factoryboy.readthedocs.io/) and [Faker](https://faker.readthedocs.io/) to generate realistic test data.

## Available Factories

### UserFactory

Base factory for creating User instances.

```python
from tests.factories import UserFactory

# Build a user (returns dict, will return model instance once User model exists)
user = UserFactory.build()

# Customize attributes
user = UserFactory.build(
    email="custom@example.com",
    name="Custom Name",
    role="admin"
)

# Build multiple users
users = UserFactory.build_batch(5)
```

### AdminUserFactory

Convenience factory for admin users (role='admin').

```python
from tests.factories import AdminUserFactory

admin = AdminUserFactory.build()
assert admin["role"] == "admin"
```

### ProspectiveStudentFactory

Factory for unverified students (role='prospective_student').

```python
from tests.factories import ProspectiveStudentFactory

prospect = ProspectiveStudentFactory.build()
assert prospect["role"] == "prospective_student"
```

### VerifiedStudentFactory

Factory for verified students with university email addresses.

```python
from tests.factories import VerifiedStudentFactory

student = VerifiedStudentFactory.build()
assert student["email"].endswith(".edu")
assert student["role"] == "student"
```

### DeletedUserFactory

Factory for soft-deleted users (deleted_at is set).

```python
from tests.factories import DeletedUserFactory

deleted = DeletedUserFactory.build()
assert deleted["deleted_at"] is not None
```

## Best Practices

### 1. Use Factories in Tests

Factories make tests more readable and maintainable:

```python
# ❌ BAD - Manual object creation
def test_user_creation():
    user = {
        "id": uuid4(),
        "email": "test@example.com",
        "name": "Test User",
        "google_id": "google_123456",
        "role": "student",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        # ... many more fields
    }

# ✅ GOOD - Use factory
def test_user_creation():
    user = UserFactory.build(email="test@example.com")
```

### 2. Override Only What Matters

Only specify fields relevant to your test:

```python
def test_admin_permissions():
    admin = UserFactory.build(role="admin")  # Only role matters for this test
    # ... test admin functionality
```

### 3. Build vs Create

- **`build()`**: Creates an in-memory instance (not persisted to database)
- **`create()`**: Creates and persists to database (once integrated with SQLAlchemy)

For now, all factories use `build()` since database models don't exist yet.

### 4. Batch Operations

Generate multiple instances efficiently:

```python
# Build 10 users
users = UserFactory.build_batch(10)

# Build 5 admins
admins = AdminUserFactory.build_batch(5)

# Build users with a common attribute
users = UserFactory.build_batch(3, role="student")
```

## Migration Path

Once the User SQLAlchemy model is created (Task T073), update factories:

```python
# Current (temporary)
class UserFactory(factory.Factory):
    class Meta:
        model = dict

# Future (after T073)
from app.infrastructure.database.models.user import User

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None  # Will be set by fixture
        sqlalchemy_session_persistence = "commit"
```

Then use `create()` to persist:

```python
# In tests with database session
@pytest.fixture
def user_factory(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    return UserFactory

def test_with_db(user_factory):
    user = user_factory.create()  # Persisted to database
```

## Adding New Factories

When creating new factories:

1. Create factory file: `tests/factories/<model>_factory.py`
2. Import Faker: `from faker import Faker`
3. Create factory class inheriting from `factory.Factory`
4. Use `factory.LazyAttribute` for dynamic values
5. Export in `tests/factories/__init__.py`
6. Write tests in `tests/unit/factories/test_<model>_factory.py`

Example structure:

```python
from datetime import UTC, datetime
from uuid import uuid4
import factory
from faker import Faker

fake = Faker()

class MyModelFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid4)
    name = factory.LazyAttribute(lambda _: fake.name())
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
```

## References

- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Faker Documentation](https://faker.readthedocs.io/)
- [Testing Best Practices](../../CONTRIBUTING.md#testing-requirements)
