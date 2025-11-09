# StudyBuddy Backend Constitution

A social platform backend focused on collaborative learning, built with FastAPI, PostgreSQL, and modern Python practices.

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)

**Standards:**

- **PEP 8 Compliance**: All code must follow PEP 8 style guidelines
- **Type Hints**: Required for all function signatures, method parameters, and return values
- **Documentation**: Google-style docstrings for all modules, classes, functions, and methods
- **DRY Principle**: No code duplication; extract common logic into reusable functions/classes
- **Complexity Limits**: Maximum cyclomatic complexity ≤ 10 per function

**Enforcement:**

- Pre-commit hooks: black, isort, flake8, mypy
- CI/CD pipeline must pass all linters before merge
- Code review checklist includes quality verification

### II. Testing Standards (NON-NEGOTIABLE)

**Coverage Requirements:**

- Minimum 80% code coverage across the entire codebase
- 100% coverage for critical business logic (authentication, payments, user data)
- No PRs merged with decreased coverage

**Testing Strategy:**

- **Unit Tests**: All business logic, utilities, models, and services
- **Integration Tests**: All API endpoints with database interactions
- **Test Framework**: pytest with pytest-asyncio for async code
- **Mocking**: External dependencies (email, payment gateways, third-party APIs) must be mocked
- **Test Data**: Use Faker for generating realistic test data; implement factory patterns

**Test Structure:**

```
tests/
├── unit/          # Pure logic tests
├── integration/   # API + DB tests
├── fixtures/      # Shared test fixtures
└── factories/     # Test data factories
```

### III. API Design

**RESTful Principles:**

- Clear resource naming (plural nouns: `/users`, `/study-groups`)
- Proper HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE (remove)
- Consistent status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Server Error)

**Versioning:**

- URL-based versioning: `/api/v1/`, `/api/v2/`
- Maintain backward compatibility for at least one major version
- Deprecation warnings 6 months before removal

**Validation & Documentation:**

- Pydantic models for all request/response validation
- Comprehensive OpenAPI (Swagger) documentation auto-generated
- Include examples in schema definitions
- Rate limiting: 100 requests/minute per authenticated user, 20 requests/minute for unauthenticated

**Response Structure:**

```python
# Success
{"data": {...}, "message": "Success"}

# Error
{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {...}}}
```

### IV. Database Management

**ORM & Migrations:**

- SQLAlchemy ORM exclusively (no raw SQL except for complex analytics)
- Alembic for all schema migrations
- Migration naming: `{timestamp}_{action}_{table}.py`
- Never modify existing migrations; create new ones

**Query Optimization:**

- Proper indexes on all foreign keys and frequently queried columns
- Never use `SELECT *` in production code; specify columns explicitly
- Use `EXPLAIN ANALYZE` for queries returning >1000 rows
- Eager loading for relationships to prevent N+1 queries

**Data Integrity:**

- Database transactions for multi-step operations
- Soft deletes for user-generated content (set `deleted_at` timestamp)
- Hard deletes only for GDPR compliance requests
- Foreign key constraints enforced at database level

### V. Security (NON-NEGOTIABLE)

**Authentication & Authorization:**

- JWT tokens with 15-minute access token expiry
- Refresh tokens with 7-day expiry, stored in HTTP-only cookies
- Password hashing with bcrypt (cost factor: 12)
- Multi-factor authentication support for sensitive operations

**Input Validation:**

- Sanitize all user input before storage
- Pydantic validators for email, URLs, phone numbers
- Escape HTML/JavaScript in user-generated content
- File upload validation (type, size, malware scanning)

**Attack Prevention:**

- SQL Injection: Use ORM exclusively, parameterized queries only
- XSS: Content Security Policy headers, sanitize responses
- CSRF: Token validation for state-changing operations
- CORS: Whitelist known origins only (no wildcards in production)

**Rate Limiting:**

- Authentication endpoints: 5 attempts/minute per IP
- API endpoints: 100 requests/minute per authenticated user
- WebSocket connections: 3 concurrent per user

### VI. Performance Standards

**Response Times:**

- 95th percentile < 200ms for read operations
- 95th percentile < 500ms for write operations
- WebSocket message latency < 100ms

**Caching Strategy:**

- Redis for session data, frequently accessed profiles
- Cache invalidation on data updates
- Cache TTL: 5 minutes for user data, 1 hour for static content

**Async Operations:**

- Use `async/await` for all I/O operations (database, external APIs, file system)
- Background tasks with Celery for emails, notifications, data processing
- WebSocket connection pooling with max 10,000 concurrent connections

**Pagination:**

- All list endpoints must support pagination
- Default page size: 20 items, max: 100 items
- Include total count and pagination metadata in responses

### VII. Scalability & Architecture

**Stateless Design:**

- No local state stored in application servers
- Session data in Redis, not in-memory
- Horizontal scaling ready (load balancer compatible)

**Background Processing:**

- Celery for async tasks (email, notifications, report generation)
- Task retries with exponential backoff
- Dead letter queue for failed tasks

**Database:**

- Connection pooling (min: 5, max: 20 per instance)
- Read replicas for analytics queries
- Prepared for database sharding (user-based partitioning)

## Quality Gates

### Pre-Commit

- Code formatting (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Security scanning (bandit)

### CI/CD Pipeline

1. **Linting & Formatting**: Must pass without warnings
2. **Type Checking**: mypy strict mode must pass
3. **Unit Tests**: 80%+ coverage required
4. **Integration Tests**: All endpoints must pass
5. **Security Scan**: No high/critical vulnerabilities
6. **Performance Tests**: Response time benchmarks met

### Code Review

- At least one approval required
- Checklist verification:
  - [ ] Type hints present
  - [ ] Docstrings complete
  - [ ] Tests added/updated
  - [ ] Security considerations addressed
  - [ ] Performance implications considered
  - [ ] Database migrations tested

## Monitoring & Observability

### Logging

- Structured JSON logging (production)
- Log levels: DEBUG (dev), INFO (staging), WARNING (production)
- Request ID tracking across all logs
- PII redaction in logs (passwords, tokens, credit cards)

**Required Log Fields:**

```python
{
    "timestamp": "ISO-8601",
    "level": "INFO|WARNING|ERROR",
    "request_id": "uuid",
    "user_id": "uuid",
    "endpoint": "path",
    "method": "GET|POST|...",
    "duration_ms": 123,
    "status_code": 200
}
```

### Metrics

- Prometheus format for all metrics
- Track: request count, response time, error rate, database query time
- Custom business metrics: daily active users, study group creation rate

### Error Tracking

- Sentry integration for exception tracking
- Automatic issue creation for new error types
- Context capture: user ID, request parameters, stack trace

### Health Checks

- `/health`: Basic liveness check
- `/health/ready`: Readiness check (database, Redis, external services)
- `/health/metrics`: Prometheus metrics endpoint

## User Experience (API)

### Error Messages

- Clear, actionable error messages
- Include field-specific validation errors
- Suggest corrective actions
- Example: `{"error": {"field": "email", "message": "Email format invalid", "suggestion": "Use format: user@example.com"}}`

### Response Consistency

```python
# List response
{
    "data": [...],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 150,
        "total_pages": 8
    }
}
```

### Filtering & Sorting

- Support query parameters: `?filter[status]=active&sort=-created_at`
- Date range filtering: `?created_after=2025-01-01&created_before=2025-12-31`
- Search: `?search=study group name`

### Webhooks

- Event-driven notifications for: new messages, study group invites, assignments
- Retry failed webhooks with exponential backoff (max 3 attempts)
- Webhook signature verification (HMAC-SHA256)

## Documentation Requirements

### Repository Documentation

- **README.md**: Project overview, setup instructions, tech stack
- **CONTRIBUTING.md**: Contribution guidelines, code standards, PR process
- **docs/architecture/**: System architecture, data flow diagrams
- **docs/adr/**: Architecture Decision Records for significant decisions

### API Documentation

- Auto-generated OpenAPI documentation at `/docs` (Swagger UI)
- ReDoc alternative at `/redoc`
- Postman collection for manual testing
- Example requests/responses for each endpoint

### Database Documentation

- ER diagrams for database schema
- Migration history and rationale
- Index strategy documentation

### Deployment

- Infrastructure as Code (Terraform/CloudFormation)
- Environment-specific configuration guides
- Rollback procedures
- Disaster recovery plan

## Governance

### Constitution Authority

- This constitution supersedes all other development practices
- Amendments require: documentation, team approval, migration plan
- All PRs must demonstrate constitution compliance

### Exceptions

- Security vulnerabilities: hotfix process bypasses standard review (post-review required)
- Performance emergencies: optimizations may temporarily reduce coverage (recovery plan required)
- All exceptions logged in `docs/adr/exceptions.md`

### Continuous Improvement

- Quarterly constitution review
- Metrics-driven refinement (track: deployment frequency, change failure rate, recovery time)
- Team retrospectives inform amendments

### Enforcement

- Automated checks in CI/CD
- Code review checklist includes constitution compliance
- Monthly compliance audit
- Constitution violations trigger team discussion (blameless postmortem)

**Version**: 1.0.0 | **Ratified**: 2025-11-08 | **Last Amended**: 2025-11-08
