---
description: "Task list for StudyBuddy platform implementation"
---

# Tasks: StudyBuddy Social Platform Backend

**Input**: 
- Specification: `.specify/specs/001-studybuddy-platform.md`
- Implementation Plan: `.specify/plans/001-studybuddy-platform-implementation.md`
- Constitution: `.specify/memory/constitution.md`

**Prerequisites**: All planning and design documents complete

**Tests**: Tests are MANDATORY per constitution (80% coverage minimum). All tests written FIRST before implementation (TDD).

**Organization**: Tasks grouped by user story to enable independent implementation and MVP delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US10)
- All file paths use hexagonal architecture structure from implementation plan

---

## Phase 0: Project Setup & Foundation

**Purpose**: Initialize project structure and core infrastructure

**Duration**: 1-2 days

### Environment Setup

- [x] T001 [P] Install Python 3.11+ and verify (`python --version`) ✅ Python 3.12.1
- [x] T002 [P] Install uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`) ✅ uv 0.9.8
- [x] T003 [P] Install Docker and Docker Compose ✅ Docker 28.3.1, Compose v2.38.2
- [x] T004 [P] Install pre-commit (`pip install pre-commit`) ✅ pre-commit 4.4.0

### Project Initialization

- [x] T005 Initialize Python project with uv (`uv init --name studybuddy --python 3.11`) ✅ Python 3.12
- [x] T006 Create `pyproject.toml` with all dependencies (FastAPI, SQLAlchemy, Redis, Celery, etc.) ✅ 117 packages
- [x] T007 Install dependencies (`uv sync && uv sync --extra dev`) ✅ 110 packages installed
- [x] T008 Create `.env.example` with all environment variables ✅ 80+ variables documented
- [x] T009 Create `.gitignore` for Python, virtual environments, IDEs ✅ Comprehensive gitignore

### Directory Structure

- [x] T010 Create core directory structure: ✅ Created
  - `app/{core,domain,application,infrastructure,api,tasks}/__init__.py`
  - `tests/{unit,integration,e2e,factories}/__init__.py`
  - `scripts/`, `docker/`, `kubernetes/`, `alembic/versions/`

- [ ] T011 [P] Create domain subdirectories:
  - `app/domain/{entities,value_objects,enums}/__init__.py`

- [ ] T012 [P] Create application subdirectories:
  - `app/application/{services,schemas,interfaces}/__init__.py`

- [ ] T013 [P] Create infrastructure subdirectories:
  - `app/infrastructure/{database/models,repositories,cache,storage,email,external}/__init__.py`

- [ ] T014 [P] Create API subdirectories:
  - `app/api/{v1/endpoints,v1/middleware,v1/dependencies,websocket}/__init__.py`

### Docker Configuration

- [ ] T015 [P] Create `docker/Dockerfile.dev` with hot-reload
- [ ] T016 [P] Create `docker/Dockerfile` (multi-stage production build)
- [ ] T017 Create `docker/docker-compose.yml` (PostgreSQL, Redis, API, Celery)
- [ ] T018 Create `scripts/dev.sh` startup script with executable permissions

### Code Quality Setup

- [ ] T019 [P] Create `.pre-commit-config.yaml` (Black, Ruff, MyPy)
- [ ] T020 [P] Install pre-commit hooks (`pre-commit install`)
- [ ] T021 [P] Run pre-commit on all files (`pre-commit run --all-files`)

### CI/CD Configuration

- [ ] T022 [P] Create `.github/workflows/ci.yml` (lint, test, build)
- [ ] T023 [P] Create `.github/workflows/cd-staging.yml` (auto-deploy to staging)
- [ ] T024 [P] Create `.github/workflows/cd-production.yml` (manual deploy to production)

### Kubernetes Manifests

- [ ] T025 [P] Create `kubernetes/namespace.yaml`
- [ ] T026 [P] Create `kubernetes/configmap.yaml`
- [ ] T027 [P] Create `kubernetes/secrets.yaml.template`
- [ ] T028 [P] Create `kubernetes/api-deployment.yaml`
- [ ] T029 [P] Create `kubernetes/celery-deployment.yaml`
- [ ] T030 [P] Create `kubernetes/ingress.yaml`
- [ ] T031 [P] Create `kubernetes/hpa.yaml` (Horizontal Pod Autoscaler)

### Documentation

- [ ] T032 [P] Create comprehensive `README.md`
- [ ] T033 [P] Create `QUICKSTART.md` guide
- [ ] T034 [P] Create `CONTRIBUTING.md` guidelines

**Checkpoint**: Project structure ready, Docker starts successfully, CI/CD configured

---

## Phase 1: Core Infrastructure (Blocking Prerequisites)

**Purpose**: Foundational infrastructure that ALL user stories depend on

**Duration**: Week 1-2

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Core Configuration

- [ ] T035 Create `app/core/config.py` - Settings class using Pydantic BaseSettings
  - Database URL, Redis URL
  - JWT secret, OAuth credentials
  - Email settings, file storage config
  - Environment-specific settings

- [ ] T036 Create `app/core/exceptions.py` - Custom exception classes
  - `BadRequestException`, `UnauthorizedException`
  - `NotFoundException`, `ForbiddenException`
  - `ConflictException`, `ValidationException`

- [ ] T037 Create `app/core/logging.py` - Structlog configuration
  - JSON logging for production
  - Request ID tracking
  - PII redaction (passwords, tokens)

### Database Setup

- [ ] T038 Create `app/infrastructure/database/base.py` - SQLAlchemy base class
  - Async engine configuration
  - Declarative base with UUID primary keys
  - Timestamp mixin (created_at, updated_at)

- [ ] T039 Create `app/infrastructure/database/session.py` - Database session management
  - Async session factory
  - Connection pooling (min: 5, max: 20)
  - Dependency for FastAPI

- [ ] T040 Initialize Alembic (`alembic init alembic`)
- [ ] T041 Configure `alembic.ini` for async SQLAlchemy
- [ ] T042 Update `alembic/env.py` for async migrations

### Security & Authentication

- [ ] T043 Create `app/core/security.py` - Security utilities
  - `create_access_token()` - JWT with 15min expiry
  - `create_refresh_token()` - JWT with 30 days expiry
  - `verify_token()` - JWT validation
  - `hash_password()` - Bcrypt hashing
  - `verify_password()` - Password verification

- [ ] T044 Create `app/infrastructure/external/google_oauth.py` - Google OAuth client
  - `get_authorization_url()`
  - `exchange_code_for_token()`
  - `get_user_info()`

### Cache & Redis

- [ ] T045 Create `app/infrastructure/cache/redis_client.py` - Redis connection
  - Async Redis client
  - Connection pool configuration

- [ ] T046 Create `app/infrastructure/cache/cache_service.py` - Caching utilities
  - `get()`, `set()`, `delete()` with TTL
  - Namespace-based keys (user:123, community:456)

### Background Tasks

- [ ] T047 Create `app/tasks/celery_app.py` - Celery configuration
  - Redis broker setup
  - Task routing
  - Retry configuration with exponential backoff

### File Storage

- [ ] T048 Create `app/infrastructure/storage/base.py` - Abstract storage interface
  - `upload()`, `delete()`, `get_url()` methods

- [ ] T049 [P] Create `app/infrastructure/storage/local_storage.py` - Local file system (dev)
- [ ] T050 [P] Create `app/infrastructure/storage/s3_storage.py` - S3-compatible storage (prod)

### Email Service

- [ ] T051 Create `app/infrastructure/email/base.py` - Abstract email interface
- [ ] T052 Create `app/infrastructure/email/smtp_email.py` - SMTP implementation
  - `send_verification_email()`
  - `send_event_reminder()`
  - Template rendering

### API Foundation

- [ ] T053 Create `app/main.py` - FastAPI application setup
  - App initialization
  - CORS middleware configuration
  - Global exception handler
  - Startup/shutdown events
  - Include routers

- [ ] T054 Create `app/api/v1/router.py` - Main API router aggregator

- [ ] T055 Create `app/api/v1/middleware/rate_limit.py` - Rate limiting middleware
  - 100 req/min per authenticated user
  - 20 req/min per IP for unauthenticated
  - 5 req/min for auth endpoints

- [ ] T056 Create `app/api/v1/middleware/logging.py` - Request/response logging
  - Log request ID, method, path, user ID
  - Log response status, duration

- [ ] T057 Create `app/api/v1/dependencies/auth.py` - Authentication dependencies
  - `get_current_user()` - Validates JWT and returns user
  - `get_current_active_user()` - Ensures user not deleted
  - `require_verified_student()` - Checks verification status

### Health Checks & Monitoring

- [ ] T058 Create `app/api/v1/endpoints/health.py` - Health check endpoints
  - `GET /health` - Liveness check (returns 200)
  - `GET /health/ready` - Readiness check (DB, Redis connectivity)
  - `GET /health/metrics` - Prometheus metrics

- [ ] T059 Configure `prometheus-fastapi-instrumentator` in `app/main.py`

- [ ] T060 Create `app/infrastructure/external/sentry_client.py` - Sentry integration

### Common Schemas

- [ ] T061 Create `app/application/schemas/common.py` - Shared Pydantic models
  - `PaginationParams` - page, page_size
  - `PaginatedResponse` - data, pagination metadata
  - `ErrorResponse` - error code, message, details
  - `SuccessResponse` - data, message

**Checkpoint**: Core infrastructure complete, database connected, health checks passing

---

## Phase 2: User Story 1 - Registration & Verification (Priority: P1) 🎯 MVP

**Goal**: Users can register via Google OAuth and verify student status via university email

**Independent Test**: Create account → Request verification → Confirm via email → Access verified content

**Duration**: Week 3-4

### Tests for User Story 1 (Write FIRST, ensure they FAIL)

- [ ] T062 [P] [US1] Create test factories in `tests/factories/user_factory.py`
  - `UserFactory` using Factory Boy + Faker

- [ ] T063 [P] [US1] Create test factories in `tests/factories/verification_factory.py`
  - `VerificationFactory`, `UniversityFactory`

- [ ] T064 [P] [US1] Unit test: `tests/unit/services/test_auth_service.py`
  - Test `create_user_from_google()`
  - Test `generate_tokens()`
  - Test `refresh_access_token()`

- [ ] T065 [P] [US1] Unit test: `tests/unit/services/test_verification_service.py`
  - Test `request_verification()`
  - Test `confirm_verification()`
  - Test `is_verified_for_university()`

- [ ] T066 [P] [US1] Integration test: `tests/integration/api/test_auth_endpoints.py`
  - Test `POST /api/v1/auth/google` OAuth flow
  - Test `POST /api/v1/auth/refresh` token refresh
  - Test `POST /api/v1/auth/logout`

- [ ] T067 [P] [US1] Integration test: `tests/integration/api/test_verification_endpoints.py`
  - Test `POST /api/v1/verifications` request
  - Test `POST /api/v1/verifications/confirm/{token}`
  - Test `GET /api/v1/verifications/me`

- [ ] T068 [US1] E2E test: `tests/e2e/test_registration_flow.py`
  - Complete flow: OAuth → Register → Request verification → Confirm → Access verified community

### Domain Models for User Story 1

- [ ] T069 [P] [US1] Create `app/domain/enums/user_role.py`
  - Enum: `student`, `prospective_student`, `admin`

- [ ] T070 [P] [US1] Create `app/domain/enums/verification_status.py`
  - Enum: `pending`, `verified`, `expired`

- [ ] T071 [P] [US1] Create `app/domain/value_objects/email.py`
  - Email value object with validation

- [ ] T072 [P] [US1] Create `app/domain/value_objects/verification_token.py`
  - Token generation and validation logic

### Database Models for User Story 1

- [ ] T073 [P] [US1] Create `app/infrastructure/database/models/user.py`
  - Fields: id (UUID), google_id, email, name, bio, avatar_url, role
  - Timestamps: created_at, updated_at, deleted_at

- [ ] T074 [P] [US1] Create `app/infrastructure/database/models/university.py`
  - Fields: id (UUID), name, domain, logo_url, country

- [ ] T075 [P] [US1] Create `app/infrastructure/database/models/verification.py`
  - Fields: id (UUID), user_id (FK), university_id (FK), email, token_hash, status
  - Timestamps: verified_at, expires_at

- [ ] T076 [US1] Create Alembic migration: `alembic revision --autogenerate -m "Add users, universities, verifications tables"`

- [ ] T077 [US1] Review and test migration: `alembic upgrade head`

### Repository Interfaces for User Story 1

- [ ] T078 [P] [US1] Create `app/application/interfaces/user_repository.py`
  - Abstract methods: `create()`, `get_by_id()`, `get_by_email()`, `get_by_google_id()`, `update()`, `delete()`

- [ ] T079 [P] [US1] Create `app/application/interfaces/verification_repository.py`
  - Abstract methods: `create()`, `get_by_token()`, `get_by_user_and_university()`, `update()`

- [ ] T080 [P] [US1] Create `app/application/interfaces/university_repository.py`
  - Abstract methods: `get_by_domain()`, `list_all()`

### Repository Implementations for User Story 1

- [ ] T081 [US1] Create `app/infrastructure/repositories/user_repository.py`
  - Implement all interface methods with SQLAlchemy async queries

- [ ] T082 [US1] Create `app/infrastructure/repositories/verification_repository.py`
  - Implement all interface methods

- [ ] T083 [US1] Create `app/infrastructure/repositories/university_repository.py`
  - Implement all interface methods

### Schemas (DTOs) for User Story 1

- [ ] T084 [P] [US1] Create `app/application/schemas/auth.py`
  - `GoogleAuthRequest`, `GoogleAuthResponse`
  - `TokenResponse` (access_token, refresh_token, token_type)
  - `RefreshTokenRequest`

- [ ] T085 [P] [US1] Create `app/application/schemas/user.py`
  - `UserCreate`, `UserUpdate`, `UserResponse`
  - `UserProfileResponse` (detailed user info)

- [ ] T086 [P] [US1] Create `app/application/schemas/verification.py`
  - `VerificationRequest` (university_id, email)
  - `VerificationConfirmRequest` (token)
  - `VerificationResponse` (status, university, verified_at)

### Services for User Story 1

- [ ] T087 [US1] Create `app/application/services/auth_service.py`
  - `create_user_from_google(google_user_info)` → User
  - `generate_tokens(user_id)` → access_token, refresh_token
  - `refresh_access_token(refresh_token)` → new access_token
  - `logout(refresh_token)` → invalidate token

- [ ] T088 [US1] Create `app/application/services/user_service.py`
  - `get_user_profile(user_id)` → User
  - `update_user_profile(user_id, data)` → User
  - `delete_user(user_id)` → soft delete

- [ ] T089 [US1] Create `app/application/services/verification_service.py`
  - `request_verification(user_id, university_id, email)` → Verification
  - `confirm_verification(token)` → Verification
  - `is_verified_for_university(user_id, university_id)` → bool
  - `get_user_verifications(user_id)` → List[Verification]

### Background Tasks for User Story 1

- [ ] T090 [US1] Create `app/tasks/email_tasks.py`
  - `send_verification_email(verification_id)` - Celery task
  - Email template with verification link (24h expiry)

### API Endpoints for User Story 1

- [ ] T091 [US1] Create `app/api/v1/endpoints/auth.py`
  - `POST /api/v1/auth/google` - Initiate OAuth, handle callback
  - `POST /api/v1/auth/refresh` - Refresh access token
  - `POST /api/v1/auth/logout` - Invalidate refresh token

- [ ] T092 [US1] Create `app/api/v1/endpoints/users.py`
  - `GET /api/v1/users/me` - Get current user profile
  - `PATCH /api/v1/users/me` - Update profile (bio, avatar)
  - `DELETE /api/v1/users/me` - Delete account (GDPR)
  - `GET /api/v1/users/{user_id}` - Get user by ID

- [ ] T093 [US1] Create `app/api/v1/endpoints/verifications.py`
  - `POST /api/v1/verifications` - Request student verification
  - `POST /api/v1/verifications/confirm/{token}` - Confirm verification
  - `GET /api/v1/verifications/me` - List my verifications
  - `POST /api/v1/verifications/{verification_id}/resend` - Resend email

- [ ] T094 [US1] Update `app/api/v1/router.py` to include auth, users, verifications routers

### Seed Data for User Story 1

- [ ] T095 [US1] Create `scripts/seed_data.py`
  - Seed universities (Stanford, MIT, Harvard, etc.)
  - Create test users (verified, unverified, admin)

**Checkpoint**: US1 complete - Users can register, verify, and access platform ✅ MVP DELIVERED

---

## Phase 3: User Story 2 - Community Management (Priority: P1) 🎯 MVP

**Goal**: Create/manage communities with hierarchical structure and role-based access

**Independent Test**: Create university community → Configure settings → Invite members → Assign roles

**Duration**: Week 5-6

### Tests for User Story 2 (Write FIRST, ensure they FAIL)

- [ ] T096 [P] [US2] Create test factories in `tests/factories/community_factory.py`
  - `CommunityFactory`, `MembershipFactory`

- [ ] T097 [P] [US2] Unit test: `tests/unit/services/test_community_service.py`
  - Test `create_community()`
  - Test `update_community_settings()`
  - Test `add_member()`, `remove_member()`, `update_member_role()`
  - Test hierarchical permissions

- [ ] T098 [P] [US2] Integration test: `tests/integration/api/test_community_endpoints.py`
  - Test all CRUD operations
  - Test membership management
  - Test permission enforcement

- [ ] T099 [US2] E2E test: `tests/e2e/test_community_creation_flow.py`
  - Create community → Configure → Add members → Sub-community

### Domain Models for User Story 2

- [ ] T100 [P] [US2] Create `app/domain/enums/community_type.py`
  - Enum: `university`, `business`, `student_council`, `hobby`

- [ ] T101 [P] [US2] Create `app/domain/enums/community_visibility.py`
  - Enum: `public`, `private`, `closed`

- [ ] T102 [P] [US2] Create `app/domain/enums/membership_role.py`
  - Enum: `admin`, `moderator`, `member`

### Database Models for User Story 2

- [ ] T103 [P] [US2] Create `app/infrastructure/database/models/community.py`
  - Fields: id, name, description, type, visibility, parent_id (self-referential FK)
  - Fields: requires_verification, avatar_url, cover_url, member_count
  - Timestamps: created_at, updated_at, deleted_at

- [ ] T104 [P] [US2] Create `app/infrastructure/database/models/membership.py`
  - Fields: id, user_id (FK), community_id (FK), role
  - Timestamp: joined_at
  - Unique constraint: (user_id, community_id)

- [ ] T105 [US2] Create Alembic migration: `alembic revision --autogenerate -m "Add communities and memberships tables"`

### Repository Layer for User Story 2

- [ ] T106 [P] [US2] Create `app/application/interfaces/community_repository.py`
- [ ] T107 [US2] Create `app/infrastructure/repositories/community_repository.py`
  - `create()`, `get_by_id()`, `list_by_type()`, `update()`, `delete()`
  - `get_children()` - Get sub-communities
  - `get_members()` - Get community members with roles

- [ ] T108 [P] [US2] Create `app/application/interfaces/membership_repository.py`
- [ ] T109 [US2] Create `app/infrastructure/repositories/membership_repository.py`
  - `add_member()`, `remove_member()`, `update_role()`, `get_user_memberships()`

### Schemas for User Story 2

- [ ] T110 [P] [US2] Create `app/application/schemas/community.py`
  - `CommunityCreate`, `CommunityUpdate`, `CommunityResponse`
  - `CommunityDetailResponse` (with member_count, parent info)

- [ ] T111 [P] [US2] Create `app/application/schemas/membership.py`
  - `MembershipCreate`, `MembershipUpdate`, `MembershipResponse`

### Services for User Story 2

- [ ] T112 [US2] Create `app/application/services/community_service.py`
  - `create_community(user_id, data)` → Community
  - `update_community(community_id, user_id, data)` → Community
  - `delete_community(community_id, user_id)` → void
  - `join_community(user_id, community_id)` → Membership
  - `leave_community(user_id, community_id)` → void
  - `add_member(community_id, user_id, target_user_id, role)` → Membership
  - `update_member_role(community_id, user_id, target_user_id, new_role)` → Membership
  - `check_permission(user_id, community_id, required_role)` → bool

### API Endpoints for User Story 2

- [ ] T113 [US2] Create `app/api/v1/endpoints/communities.py`
  - `GET /api/v1/communities` - List communities (filters: type, visibility)
  - `POST /api/v1/communities` - Create community
  - `GET /api/v1/communities/{community_id}` - Get details
  - `PATCH /api/v1/communities/{community_id}` - Update
  - `DELETE /api/v1/communities/{community_id}` - Delete
  - `POST /api/v1/communities/{community_id}/join` - Join
  - `POST /api/v1/communities/{community_id}/leave` - Leave
  - `GET /api/v1/communities/{community_id}/members` - List members
  - `PATCH /api/v1/communities/{community_id}/members/{user_id}` - Update role

- [ ] T114 [US2] Create `app/api/v1/dependencies/permissions.py`
  - `require_community_admin(community_id)` dependency
  - `require_community_moderator(community_id)` dependency

- [ ] T115 [US2] Update `app/api/v1/router.py` to include communities router

**Checkpoint**: US2 complete - Communities functional with role-based access ✅

---

## Phase 4: User Story 3 - Social Feed (Priority: P2)

**Goal**: Users can create posts, react, comment in communities

**Independent Test**: Create post → Add reactions → Comment → Edit → Delete

**Duration**: Week 7-8

### Tests for User Story 3 (Write FIRST)

- [ ] T116 [P] [US3] Create factories: `tests/factories/post_factory.py`
  - `PostFactory`, `ReactionFactory`, `CommentFactory`

- [ ] T117 [P] [US3] Unit test: `tests/unit/services/test_post_service.py`
- [ ] T118 [P] [US3] Integration test: `tests/integration/api/test_post_endpoints.py`
- [ ] T119 [P] [US3] Integration test: `tests/integration/api/test_comment_endpoints.py`
- [ ] T120 [US3] E2E test: `tests/e2e/test_post_creation_flow.py`

### Domain Models for User Story 3

- [ ] T121 [P] [US3] Create `app/domain/enums/reaction_type.py`
  - Enum: `like`, `love`, `celebrate`, `support`

### Database Models for User Story 3

- [ ] T122 [P] [US3] Create `app/infrastructure/database/models/post.py`
  - Fields: id, author_id (FK), community_id (FK), content, attachments (JSONB)
  - Fields: is_pinned (bool), edited_at
  - Timestamps: created_at, deleted_at

- [ ] T123 [P] [US3] Create `app/infrastructure/database/models/reaction.py`
  - Fields: id, user_id (FK), post_id (FK), reaction_type
  - Timestamp: created_at
  - Unique constraint: (user_id, post_id)

- [ ] T124 [P] [US3] Create `app/infrastructure/database/models/comment.py`
  - Fields: id, author_id (FK), post_id (FK), parent_comment_id (nullable FK), content
  - Timestamps: created_at, deleted_at

- [ ] T125 [US3] Create migration: `alembic revision --autogenerate -m "Add posts, reactions, comments"`

### Repository Layer for User Story 3

- [ ] T126 [P] [US3] Interface + Implementation: `post_repository.py`
- [ ] T127 [P] [US3] Interface + Implementation: `reaction_repository.py`
- [ ] T128 [P] [US3] Interface + Implementation: `comment_repository.py`

### Schemas for User Story 3

- [ ] T129 [P] [US3] Create `app/application/schemas/post.py`
  - `PostCreate`, `PostUpdate`, `PostResponse`
  - `PostDetailResponse` (with reaction counts, comment count)

- [ ] T130 [P] [US3] Create `app/application/schemas/reaction.py`
  - `ReactionCreate`, `ReactionResponse`

- [ ] T131 [P] [US3] Create `app/application/schemas/comment.py`
  - `CommentCreate`, `CommentUpdate`, `CommentResponse`

### Services for User Story 3

- [ ] T132 [US3] Create `app/application/services/post_service.py`
  - `create_post()`, `update_post()`, `delete_post()`
  - `get_community_feed()` with pagination and sorting
  - `pin_post()`, `unpin_post()`
  - `add_reaction()`, `remove_reaction()`
  - `get_post_reactions()` grouped by type

### API Endpoints for User Story 3

- [ ] T133 [US3] Create `app/api/v1/endpoints/posts.py`
  - `GET /api/v1/communities/{community_id}/posts` - Feed with pagination
  - `POST /api/v1/communities/{community_id}/posts` - Create
  - `GET /api/v1/posts/{post_id}` - Get details
  - `PATCH /api/v1/posts/{post_id}` - Update
  - `DELETE /api/v1/posts/{post_id}` - Delete
  - `POST /api/v1/posts/{post_id}/pin` - Pin (moderator)
  - `POST /api/v1/posts/{post_id}/reactions` - Add reaction
  - `DELETE /api/v1/posts/{post_id}/reactions` - Remove reaction

- [ ] T134 [US3] Create `app/api/v1/endpoints/comments.py`
  - `GET /api/v1/posts/{post_id}/comments` - List
  - `POST /api/v1/posts/{post_id}/comments` - Create
  - `PATCH /api/v1/comments/{comment_id}` - Update
  - `DELETE /api/v1/comments/{comment_id}` - Delete

- [ ] T135 [US3] Update router to include posts and comments

**Checkpoint**: US3 complete - Social feed functional ✅

---

## Phase 5: User Story 4 - Event Management (Priority: P2)

**Goal**: Create events, manage registrations, track attendance

**Independent Test**: Create event → Register → Capacity limits → Waitlist → Reminders

**Duration**: Week 9-10

### Tests for User Story 4

- [ ] T136 [P] [US4] Factories: `event_factory.py`, `event_registration_factory.py`
- [ ] T137 [P] [US4] Unit tests: `test_event_service.py`
- [ ] T138 [P] [US4] Integration tests: `test_event_endpoints.py`
- [ ] T139 [US4] E2E test: `test_event_registration_flow.py`

### Domain Models for User Story 4

- [ ] T140 [P] [US4] Create `app/domain/enums/event_type.py` - online, offline, hybrid
- [ ] T141 [P] [US4] Create `app/domain/enums/event_status.py` - draft, published, completed, cancelled
- [ ] T142 [P] [US4] Create `app/domain/enums/registration_status.py` - registered, waitlisted, attended, no_show

### Database Models for User Story 4

- [ ] T143 [P] [US4] Create `app/infrastructure/database/models/event.py`
  - Fields: id, community_id, creator_id, title, description, type, location
  - Fields: start_time, end_time, participant_limit, status
  - Timestamps: created_at, updated_at

- [ ] T144 [P] [US4] Create `app/infrastructure/database/models/event_registration.py`
  - Fields: id, event_id (FK), user_id (FK), status
  - Timestamp: registered_at
  - Unique constraint: (event_id, user_id)

- [ ] T145 [US4] Create migration: `alembic revision --autogenerate -m "Add events and registrations"`

### Repository & Service Layer for User Story 4

- [ ] T146 [US4] Repository interfaces and implementations for events and registrations
- [ ] T147 [US4] Create `app/application/services/event_service.py`
  - `create_event()`, `update_event()`, `delete_event()`
  - `register_for_event()` - Handle capacity and waitlist
  - `unregister_from_event()` - Auto-promote from waitlist
  - `get_event_participants()`
  - `change_event_status()`

### Background Tasks for User Story 4

- [ ] T148 [US4] Add to `app/tasks/event_tasks.py`
  - `send_event_reminders()` - Celery beat task (24h before)
  - `send_event_cancellation_notice()`

### API Endpoints for User Story 4

- [ ] T149 [US4] Create `app/api/v1/endpoints/events.py`
  - `GET /api/v1/communities/{community_id}/events` - List
  - `POST /api/v1/communities/{community_id}/events` - Create
  - `GET /api/v1/events/{event_id}` - Get details
  - `PATCH /api/v1/events/{event_id}` - Update
  - `DELETE /api/v1/events/{event_id}` - Delete
  - `POST /api/v1/events/{event_id}/register` - Register
  - `DELETE /api/v1/events/{event_id}/register` - Unregister
  - `GET /api/v1/events/{event_id}/participants` - List participants

- [ ] T150 [US4] Update router

**Checkpoint**: US4 complete - Event system functional ✅

---

## Phase 6: User Story 5 - Real-Time Chat (Priority: P2)

**Goal**: WebSocket-based chat for direct messages, groups, communities

**Independent Test**: Send direct message → Create group chat → Real-time delivery → Typing indicators

**Duration**: Week 11-13

### Tests for User Story 5

- [ ] T151 [P] [US5] Factories: `chat_factory.py`, `message_factory.py`
- [ ] T152 [P] [US5] Unit tests: `test_chat_service.py`
- [ ] T153 [P] [US5] Integration tests: `test_chat_endpoints.py`
- [ ] T154 [P] [US5] WebSocket tests: `test_chat_websocket.py`
- [ ] T155 [US5] E2E test: `test_messaging_flow.py`

### Domain Models for User Story 5

- [ ] T156 [P] [US5] Create `app/domain/enums/chat_type.py` - direct, group, community

### Database Models for User Story 5

- [ ] T157 [P] [US5] Create `app/infrastructure/database/models/chat.py`
  - Fields: id, type, name, community_id (nullable), created_at

- [ ] T158 [P] [US5] Create `app/infrastructure/database/models/chat_participant.py`
  - Fields: id, chat_id (FK), user_id (FK), joined_at, last_read_at

- [ ] T159 [P] [US5] Create `app/infrastructure/database/models/message.py`
  - Fields: id, chat_id (FK), sender_id (FK), content, attachments (JSONB)
  - Timestamps: created_at, deleted_at

- [ ] T160 [P] [US5] Create `app/infrastructure/database/models/message_read_receipt.py`
  - Fields: id, message_id (FK), user_id (FK), read_at

- [ ] T161 [US5] Create migration: `alembic revision --autogenerate -m "Add chat tables"`

### WebSocket Infrastructure

- [ ] T162 [US5] Create `app/api/websocket/manager.py` - WebSocket connection manager
  - Track active connections per user
  - `connect()`, `disconnect()`, `send_personal_message()`
  - `broadcast_to_chat()`

- [ ] T163 [US5] Configure Redis Pub/Sub in `app/api/websocket/manager.py`
  - Multi-instance message broadcasting
  - Subscribe to chat channels

- [ ] T164 [US5] Create `app/api/websocket/models.py` - WebSocket message models
  - `WebSocketMessage`, `TypingIndicator`, `ReadReceipt`

- [ ] T165 [US5] Create `app/api/websocket/handlers.py` - Message handlers
  - Handle incoming WebSocket messages
  - Route to appropriate service methods
  - Send typing indicators

### Repository & Service Layer for User Story 5

- [ ] T166 [US5] Repository interfaces and implementations for chats, messages
- [ ] T167 [US5] Create `app/application/services/chat_service.py`
  - `create_chat()`, `get_user_chats()`, `add_participant()`
  - `send_message()`, `edit_message()`, `delete_message()`
  - `get_message_history()` with pagination
  - `mark_messages_as_read()`
  - `search_messages()`

### Schemas for User Story 5

- [ ] T168 [P] [US5] Create `app/application/schemas/chat.py`
  - `ChatCreate`, `ChatResponse`, `ChatDetailResponse`

- [ ] T169 [P] [US5] Create `app/application/schemas/message.py`
  - `MessageCreate`, `MessageUpdate`, `MessageResponse`

### API Endpoints for User Story 5

- [ ] T170 [US5] Create `app/api/v1/endpoints/chats.py`
  - `GET /api/v1/chats` - List my chats
  - `POST /api/v1/chats` - Create chat
  - `GET /api/v1/chats/{chat_id}` - Get details
  - `GET /api/v1/chats/{chat_id}/messages` - Message history
  - `POST /api/v1/chats/{chat_id}/messages` - Send message
  - `PATCH /api/v1/messages/{message_id}` - Edit
  - `DELETE /api/v1/messages/{message_id}` - Delete
  - `POST /api/v1/chats/{chat_id}/read` - Mark as read
  - `GET /api/v1/chats/{chat_id}/search` - Search messages

- [ ] T171 [US5] Create WebSocket endpoint: `WS /api/v1/ws?token={jwt}`
  - Authenticate via JWT in query param
  - Handle connect, disconnect, message events
  - Send typing indicators, read receipts

- [ ] T172 [US5] Update router

**Checkpoint**: US5 complete - Real-time chat functional ✅

---

## Phase 7: User Story 6 - Moderation (Priority: P2)

**Goal**: Report content, moderation queue, admin actions

**Independent Test**: Report post → Review in queue → Take action → Log decision

**Duration**: Week 14-15

### Tests for User Story 6

- [ ] T173 [P] [US6] Factories: `report_factory.py`, `moderation_action_factory.py`
- [ ] T174 [P] [US6] Unit tests: `test_moderation_service.py`
- [ ] T175 [P] [US6] Integration tests: `test_moderation_endpoints.py`
- [ ] T176 [US6] E2E test: `test_moderation_flow.py`

### Domain Models for User Story 6

- [ ] T177 [P] [US6] Create `app/domain/enums/report_reason.py`
  - Enum: spam, harassment, inappropriate_content, misinformation, other

- [ ] T178 [P] [US6] Create `app/domain/enums/report_status.py`
  - Enum: pending, resolved, dismissed

- [ ] T179 [P] [US6] Create `app/domain/enums/moderation_action_type.py`
  - Enum: remove, warn, ban_temporary, ban_permanent

### Database Models for User Story 6

- [ ] T180 [P] [US6] Create `app/infrastructure/database/models/report.py`
  - Fields: id, reporter_id (FK), reported_user_id (nullable), reported_content_id, reported_content_type
  - Fields: reason, details, status
  - Timestamps: created_at, resolved_at

- [ ] T181 [P] [US6] Create `app/infrastructure/database/models/moderation_action.py`
  - Fields: id, moderator_id (FK), report_id (FK), action_type, reason, target_id, target_type
  - Timestamp: created_at

- [ ] T182 [US6] Create migration: `alembic revision --autogenerate -m "Add moderation tables"`

### Repository & Service Layer for User Story 6

- [ ] T183 [US6] Repository interfaces and implementations for reports and actions
- [ ] T184 [US6] Create `app/application/services/moderation_service.py`
  - `submit_report()`, `get_moderation_queue()`, `update_report_status()`
  - `take_action()` - remove, warn, ban
  - `get_moderation_logs()`
  - `block_user()`, `unblock_user()`

### Schemas for User Story 6

- [ ] T185 [P] [US6] Create `app/application/schemas/report.py`
  - `ReportCreate`, `ReportUpdate`, `ReportResponse`

- [ ] T186 [P] [US6] Create `app/application/schemas/moderation.py`
  - `ModerationActionCreate`, `ModerationActionResponse`

### API Endpoints for User Story 6

- [ ] T187 [US6] Create `app/api/v1/endpoints/moderation.py`
  - `POST /api/v1/reports` - Submit report
  - `GET /api/v1/reports` - Moderation queue (moderator)
  - `PATCH /api/v1/reports/{report_id}` - Update status
  - `POST /api/v1/moderation/actions` - Take action
  - `GET /api/v1/moderation/logs` - View logs (admin)

- [ ] T188 [US6] Update router

**Checkpoint**: US6 complete - Moderation system functional ✅

---

## Phase 8: User Story 7 - Search (Priority: P3)

**Goal**: Global search across communities, users, posts, events

**Independent Test**: Search query → Filter results → Sort → Autocomplete

**Duration**: Week 16-17

### Tests for User Story 7

- [ ] T189 [P] [US7] Unit tests: `test_search_service.py`
- [ ] T190 [P] [US7] Integration tests: `test_search_endpoints.py`

### Service Layer for User Story 7

- [ ] T191 [US7] Create `app/application/services/search_service.py`
  - `global_search()` - Search across all entities
  - `search_communities()`, `search_users()`, `search_posts()`, `search_events()`
  - `autocomplete()` - Top 5 suggestions
  - Use PostgreSQL full-text search (pg_trgm extension)

### Schemas for User Story 7

- [ ] T192 [US7] Create `app/application/schemas/search.py`
  - `SearchQuery`, `SearchResults`, `AutocompleteResponse`

### API Endpoints for User Story 7

- [ ] T193 [US7] Create `app/api/v1/endpoints/search.py`
  - `GET /api/v1/search?q={query}&type={type}&filters={filters}` - Global search
  - `GET /api/v1/search/autocomplete?q={query}` - Autocomplete

- [ ] T194 [US7] Update router

**Checkpoint**: US7 complete - Search functional ✅

---

## Phase 9: User Story 8 - Analytics (Priority: P3)

**Goal**: Premium analytics dashboard for institutions

**Independent Test**: View DAU/WAU/MAU → Conversion funnel → Export CSV

**Duration**: Week 18-19

### Tests for User Story 8

- [ ] T195 [P] [US8] Unit tests: `test_analytics_service.py`
- [ ] T196 [P] [US8] Integration tests: `test_analytics_endpoints.py`

### Database Models for User Story 8

- [ ] T197 [US8] Create `app/infrastructure/database/models/analytics_metric.py`
  - Fields: id, community_id (FK), metric_type, metric_value, period_start, period_end
  - Timestamp: created_at

- [ ] T198 [US8] Create migration: `alembic revision --autogenerate -m "Add analytics table"`

### Background Tasks for User Story 8

- [ ] T199 [US8] Create `app/tasks/analytics_tasks.py`
  - `aggregate_daily_metrics()` - Celery beat task (daily)
  - Calculate DAU, WAU, MAU
  - Aggregate post/reaction/comment counts
  - Calculate conversion rates

### Service Layer for User Story 8

- [ ] T200 [US8] Create `app/application/services/analytics_service.py`
  - `get_user_metrics()`, `get_content_metrics()`, `get_event_metrics()`
  - `get_chat_metrics()`, `get_conversion_funnel()`
  - `export_analytics()` - Generate CSV/PDF

### Schemas for User Story 8

- [ ] T201 [US8] Create `app/application/schemas/analytics.py`
  - `AnalyticsQuery`, `UserMetrics`, `ContentMetrics`, `ConversionFunnel`

### API Endpoints for User Story 8

- [ ] T202 [US8] Create `app/api/v1/endpoints/analytics.py`
  - `GET /api/v1/analytics/users?period={period}` - User metrics (premium)
  - `GET /api/v1/analytics/content?period={period}` - Content metrics
  - `GET /api/v1/analytics/events?period={period}` - Event metrics
  - `GET /api/v1/analytics/conversion?period={period}` - Conversion funnel
  - `POST /api/v1/analytics/export?format={csv|pdf}` - Export

- [ ] T203 [US8] Add premium tier check middleware

- [ ] T204 [US8] Update router

**Checkpoint**: US8 complete - Analytics functional ✅

---

## Phase 10: User Story 9 - Notifications (Priority: P3)

**Goal**: Real-time and email notifications with preferences

**Independent Test**: Trigger notification → Receive via WebSocket → Configure preferences

**Duration**: Week 20-21

### Tests for User Story 9

- [ ] T205 [P] [US9] Unit tests: `test_notification_service.py`
- [ ] T206 [P] [US9] Integration tests: `test_notification_endpoints.py`

### Domain Models for User Story 9

- [ ] T207 [US9] Create `app/domain/enums/notification_type.py`
  - Enum: mention, reaction, comment, message, event_reminder, event_update

### Database Models for User Story 9

- [ ] T208 [US9] Create `app/infrastructure/database/models/notification.py`
  - Fields: id, user_id (FK), type, title, content, link, is_read
  - Timestamp: created_at

- [ ] T209 [US9] Create `app/infrastructure/database/models/notification_preference.py`
  - Fields: id, user_id (FK), notification_type, email_enabled, push_enabled

- [ ] T210 [US9] Create migration: `alembic revision --autogenerate -m "Add notification tables"`

### Service Layer for User Story 9

- [ ] T211 [US9] Create `app/application/services/notification_service.py`
  - `create_notification()`, `send_notification()` (WebSocket + email)
  - `get_user_notifications()`, `mark_as_read()`, `mark_all_as_read()`
  - `get_preferences()`, `update_preferences()`

### Schemas for User Story 9

- [ ] T212 [US9] Create `app/application/schemas/notification.py`
  - `NotificationResponse`, `NotificationPreferences`

### API Endpoints for User Story 9

- [ ] T213 [US9] Create `app/api/v1/endpoints/notifications.py`
  - `GET /api/v1/notifications` - List notifications
  - `PATCH /api/v1/notifications/{notification_id}/read` - Mark as read
  - `PATCH /api/v1/notifications/read-all` - Mark all as read
  - `GET /api/v1/notifications/preferences` - Get preferences
  - `PATCH /api/v1/notifications/preferences` - Update preferences

- [ ] T214 [US9] Update router

- [ ] T215 [US9] Integrate notification triggers across services
  - Post reactions → notify author
  - Comments → notify post author
  - Mentions → notify mentioned user
  - Messages → notify recipient

**Checkpoint**: US9 complete - Notification system functional ✅

---

## Phase 11: User Story 10 - Multi-University Affiliation (Priority: P3)

**Goal**: Users can verify and access multiple universities

**Independent Test**: Verify second university → Access both communities → View combined feed

**Duration**: Week 22

### Tests for User Story 10

- [ ] T216 [P] [US10] Unit tests: `test_multi_affiliation.py`
- [ ] T217 [US10] E2E test: `test_multi_university_flow.py`

### Service Updates for User Story 10

- [ ] T218 [US10] Update `verification_service.py` - Support multiple verifications per user
- [ ] T219 [US10] Update `user_service.py` - Display all verified universities on profile
- [ ] T220 [US10] Update `post_service.py` - Combined feed from all affiliated communities

### API Updates for User Story 10

- [ ] T221 [US10] Update user profile endpoints to show all verifications
- [ ] T222 [US10] Add feed filter: `GET /api/v1/posts?scope=all_communities`

**Checkpoint**: US10 complete - Multi-affiliation functional ✅

---

## Phase 12: Polish & Production Readiness

**Purpose**: Final touches before production deployment

**Duration**: Week 23-24

### Security Hardening

- [ ] T223 [P] Run security audit with Bandit (`bandit -r app/`)
- [ ] T224 [P] Dependency vulnerability check (`safety check`)
- [ ] T225 [P] Implement CSP headers in `app/main.py`
- [ ] T226 [P] Add request rate limiting headers
- [ ] T227 [P] Implement API key authentication for premium features

### Performance Optimization

- [ ] T228 [P] Add database indexes based on query analysis (`EXPLAIN ANALYZE`)
- [ ] T229 [P] Implement Redis caching for frequently accessed data
- [ ] T230 [P] Optimize N+1 queries with eager loading (SQLAlchemy `selectinload`)
- [ ] T231 [P] Add pagination to all list endpoints (verify max 100 items)
- [ ] T232 [P] Configure database connection pooling parameters

### Documentation

- [ ] T233 [P] Review and enhance OpenAPI documentation (add examples)
- [ ] T234 [P] Create API usage guide with cURL examples
- [ ] T235 [P] Document environment variables in `.env.example`
- [ ] T236 [P] Create deployment guide for Kubernetes
- [ ] T237 [P] Document backup and recovery procedures

### Testing & Coverage

- [ ] T238 Verify test coverage is >80% (`pytest --cov=app --cov-report=term`)
- [ ] T239 [P] Add missing unit tests for edge cases
- [ ] T240 [P] Add load tests for critical endpoints (Locust or JMeter)
- [ ] T241 Run full E2E test suite and fix any failures

### Monitoring & Observability

- [ ] T242 [P] Verify Prometheus metrics are exposed at `/health/metrics`
- [ ] T243 [P] Test Sentry error tracking in staging
- [ ] T244 [P] Verify structured logging includes all required fields
- [ ] T245 [P] Create Grafana dashboards for key metrics
- [ ] T246 [P] Set up alerts for error rate, response time, resource usage

### Deployment Verification

- [ ] T247 Test Docker build: `docker build -f docker/Dockerfile .`
- [ ] T248 Test Docker Compose startup: `./scripts/dev.sh`
- [ ] T249 Test database migrations on clean database
- [ ] T250 Deploy to staging and run smoke tests
- [ ] T251 Perform load testing on staging (1000 concurrent users)
- [ ] T252 Security penetration testing on staging
- [ ] T253 GDPR compliance verification (data export, deletion)

### Final Checks

- [ ] T254 Run `quickstart.md` guide from scratch to verify setup works
- [ ] T255 Review all API endpoints against specification
- [ ] T256 Verify all constitution requirements are met
- [ ] T257 Code review for DRY violations and complexity
- [ ] T258 Final pre-commit check on entire codebase

**Checkpoint**: Production ready! ✅ Ready for deployment

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Phase 0 (Setup)**: No dependencies - Start immediately
2. **Phase 1 (Core Infrastructure)**: Depends on Phase 0 - BLOCKS all user stories
3. **Phase 2-11 (User Stories)**: All depend on Phase 1 completion
   - User stories can proceed in parallel (if team capacity allows)
   - Or sequentially by priority: US1 → US2 → US3 → ...
4. **Phase 12 (Polish)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (Auth)**: Foundation - No dependencies on other stories
- **US2 (Communities)**: Can start after Phase 1 - Independent
- **US3 (Posts)**: Needs US2 (communities) for context, but independently testable
- **US4 (Events)**: Needs US2 (communities), but independently testable
- **US5 (Chat)**: Independent of other stories
- **US6 (Moderation)**: Works with US3/US5 content, but independently testable
- **US7 (Search)**: Needs US1-4 data to search, but independently testable
- **US8 (Analytics)**: Aggregates data from all stories, but independently testable
- **US9 (Notifications)**: Integrates with all stories, build after core features
- **US10 (Multi-affiliation)**: Enhances US1, can be last

### Parallel Opportunities

**Phase 0**: All T001-T034 can run in parallel (different files)

**Phase 1**: Tasks marked [P] can run in parallel:
- T035-T037 (Core config)
- T043-T044 (Security)
- T045-T046 (Cache)
- T049-T050 (Storage)
- T058-T060 (Monitoring)

**User Stories**: Once Phase 1 completes, all user stories can start in parallel if team has capacity

**Within Each Story**: Tasks marked [P] (tests, factories, models) can run in parallel

### Recommended Execution Strategy

#### Solo Developer (Sequential)
```
Week 1-2:   Phase 0 + Phase 1 (Foundation)
Week 3-4:   US1 (Auth & Verification) ✅ MVP MILESTONE
Week 5-6:   US2 (Communities)
Week 7-8:   US3 (Social Feed)
Week 9-10:  US4 (Events)
Week 11-13: US5 (Chat)
Week 14-15: US6 (Moderation)
Week 16-17: US7 (Search)
Week 18-19: US8 (Analytics)
Week 20-21: US9 (Notifications)
Week 22:    US10 (Multi-affiliation)
Week 23-24: Phase 12 (Polish & Deploy)
```

#### Team of 3 Developers (Parallel)
```
Week 1-2:   Everyone: Phase 0 + Phase 1
Week 3-4:   Dev A: US1, Dev B: US2, Dev C: US5
Week 5-6:   Dev A: US3, Dev B: US4, Dev C: US6
Week 7-8:   Dev A: US7, Dev B: US8, Dev C: US9
Week 9:     Dev A: US10, Dev B+C: Integration testing
Week 10-11: Everyone: Phase 12 (Polish & Deploy)
```

### MVP Milestone (Minimum Viable Product)

**Complete Phase 1 + US1 + US2 = Functional MVP**
- Users can register and verify
- Communities can be created and managed
- Basic social platform operational
- **Duration**: ~6 weeks solo, ~4 weeks with team

---

## Testing Strategy (TDD - Required by Constitution)

### Test-Driven Development Workflow

For EVERY task that involves implementation:

1. **Write tests FIRST** (ensure they FAIL)
   - Unit tests for services
   - Integration tests for API endpoints
   - E2E tests for user journeys

2. **Implement the feature** (make tests PASS)
   - Follow the implementation plan
   - Use type hints, docstrings
   - Keep complexity ≤ 10

3. **Refactor** (keep tests PASSING)
   - Remove duplication
   - Improve readability
   - Optimize performance

4. **Verify coverage** (must be ≥ 80%)
   ```bash
   pytest --cov=app --cov-report=term
   ```

### Test Execution Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/services/test_auth_service.py

# Run tests for specific user story (use markers)
pytest -m us1

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration

# Run only E2E tests
pytest tests/e2e
```

---

## Notes & Best Practices

### Task Execution
- ✅ Commit after each task or logical group
- ✅ Run tests after each implementation
- ✅ Update documentation as you go
- ✅ Use pre-commit hooks (auto-runs on commit)

### Code Quality
- ✅ Type hints on all functions
- ✅ Google-style docstrings
- ✅ Maximum function complexity: 10
- ✅ No code duplication (DRY)
- ✅ Format with Black before committing

### Testing
- ✅ Write tests BEFORE implementation (TDD)
- ✅ Use factories for test data (Factory Boy + Faker)
- ✅ Mock external dependencies
- ✅ Test edge cases and error scenarios
- ✅ Aim for >80% coverage

### Git Workflow
- ✅ Create feature branch: `git checkout -b feature/us1-authentication`
- ✅ Commit frequently with descriptive messages
- ✅ Push to remote and create PR when story complete
- ✅ Merge to `develop` → auto-deploy to staging
- ✅ Merge to `main` → manual approval → deploy to production

### Constitution Compliance Checklist
Every PR must verify:
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] Tests added/updated (>80% coverage)
- [ ] No linting errors (Ruff passes)
- [ ] No type errors (MyPy passes)
- [ ] Formatted with Black
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Database migrations tested

---

## Success Criteria

### Phase 0 Complete ✅
- Docker containers start successfully
- CI/CD pipelines configured
- Pre-commit hooks working

### Phase 1 Complete ✅
- Health checks return 200
- Database connected
- Redis connected
- JWT authentication working

### Each User Story Complete ✅
- All tests passing (unit + integration + E2E)
- Test coverage >80% for new code
- Feature independently testable
- API documentation updated
- No linting/type errors

### Phase 12 Complete ✅
- All user stories implemented
- Test coverage >80% overall
- Security audit passed
- Load testing passed
- Documentation complete
- Staging deployment successful

### Production Deployment ✅
- All acceptance criteria met
- Performance benchmarks achieved
- Monitoring and alerting active
- Backup and recovery tested
- GDPR compliance verified

---

**Total Tasks**: 258 tasks across 12 phases

**Estimated Duration**: 
- Solo: 22-24 weeks
- Team of 3: 10-11 weeks

**MVP Timeline**: 
- Solo: 6 weeks (Phase 0 + Phase 1 + US1 + US2)
- Team: 4 weeks

**Constitution Compliance**: All tasks designed to meet StudyBuddy development principles ✅
