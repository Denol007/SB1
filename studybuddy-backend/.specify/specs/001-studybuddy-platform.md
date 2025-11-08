# Feature Specification: StudyBuddy Social Platform Backend

**Feature Branch**: `001-studybuddy-platform`  
**Created**: 2025-11-08  
**Status**: Draft  
**Input**: User description: "Build a social networking platform backend (StudyBuddy) for university students and prospective students"

## Executive Summary

StudyBuddy is a social networking platform designed to connect university students, prospective students, and educational communities. The platform facilitates knowledge sharing, event organization, and peer-to-peer communication within a verified, university-focused ecosystem.

**Core Value Propositions:**
- Verified student communities with institutional trust
- Prospective student guidance through direct connection with current students
- Event-driven engagement for campus activities
- Real-time communication with moderation safeguards
- Analytics-driven insights for educational institutions

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Student Registration & Verification (Priority: P1)

A prospective student visits StudyBuddy to explore university communities, creates an account via Google OAuth, and verifies their student status using their university email to access exclusive content.

**Why this priority**: Foundation for the entire platform. Without user registration and verification, no other features can function. This is the entry point for all users.

**Independent Test**: Can be fully tested by creating an account via Google OAuth, receiving a verification email, clicking the confirmation link, and gaining access to a university community. Delivers immediate value by establishing trusted identity.

**Acceptance Scenarios**:

1. **Given** a new visitor on StudyBuddy, **When** they click "Sign in with Google", **Then** they are redirected to Google OAuth consent screen
2. **Given** successful Google authentication, **When** they complete the OAuth flow, **Then** a user account is created with their Google profile data (name, email, avatar)
3. **Given** a registered user with a university email (e.g., john@stanford.edu), **When** they request verification for Stanford University community, **Then** a verification email with a unique token is sent to their university email
4. **Given** a verification email sent, **When** the user clicks the verification link within 24 hours, **Then** their account is marked as verified for that university
5. **Given** an expired verification token (>24h), **When** user clicks the link, **Then** they receive an error message and option to request a new verification email
6. **Given** a verified student, **When** they view university communities, **Then** they can access private university content

---

### User Story 2 - Community Creation & Management (Priority: P1)

A university administrator creates a new community for their institution, configures visibility settings, and manages member roles to build a structured campus presence.

**Why this priority**: Communities are the organizing structure for all content. Without communities, there's no context for posts, events, or conversations.

**Independent Test**: Can be tested by creating a community with various settings (public/private, verification requirements), inviting members, and assigning roles. Delivers value as a functional community hub.

**Acceptance Scenarios**:

1. **Given** a verified student or admin, **When** they create a new community with type "university", **Then** the community is created with them as the admin
2. **Given** a community admin, **When** they configure visibility as "private" and enable "student verification required", **Then** only verified students can view and join the community
3. **Given** a community admin, **When** they invite a user and assign them the "moderator" role, **Then** the user gains moderation permissions (pin posts, manage reports)
4. **Given** a university community, **When** an admin creates a sub-community for "Computer Science Department", **Then** the sub-community inherits parent settings and displays hierarchical relationship
5. **Given** a public community, **When** any user searches for it, **Then** the community appears in search results with preview information
6. **Given** a closed community, **When** a non-member attempts to view it, **Then** they see a join request button but cannot view content

---

### User Story 3 - Social Feed & Engagement (Priority: P2)

A student posts an update about a study session in their community, receives reactions and comments from peers, and moderators pin important announcements.

**Why this priority**: Core social functionality that drives daily engagement. Builds on communities (P1) to enable content sharing.

**Independent Test**: Post content to a community, receive reactions/comments, edit/delete posts, and view a paginated feed. Delivers value as a functional social feed.

**Acceptance Scenarios**:

1. **Given** a community member, **When** they create a post with rich text and image attachments, **Then** the post appears in the community feed
2. **Given** a published post, **When** other members react with "like", "love", "celebrate", or "support", **Then** reaction counts update in real-time
3. **Given** a post with reactions, **When** a user clicks on reaction counts, **Then** they see a list of users who reacted with each emotion
4. **Given** a community member, **When** they comment on a post, **Then** the comment appears in nested thread format
5. **Given** a post author, **When** they edit their post within 24 hours, **Then** the post shows an "edited" indicator
6. **Given** a moderator, **When** they pin a post, **Then** the post remains at the top of the feed with a pin indicator
7. **Given** a community feed, **When** a user scrolls down, **Then** posts load in pages of 20 with infinite scroll

---

### User Story 4 - Event Management & Registration (Priority: P2)

A student council member creates an event for a campus workshop, sets participant limits, and tracks registrations as students sign up.

**Why this priority**: Events are a key differentiator for educational communities. Enables offline/online engagement beyond pure social interaction.

**Independent Test**: Create an event, set registration limits, allow users to register/unregister, and view participant lists. Delivers value as a functional event system.

**Acceptance Scenarios**:

1. **Given** a community moderator, **When** they create an event with type "hybrid", date, location, and participant limit of 50, **Then** the event is published with registration enabled
2. **Given** a published event, **When** a community member clicks "Register", **Then** their registration is confirmed and count updates
3. **Given** an event at capacity (50/50), **When** a new user tries to register, **Then** they are added to a waitlist
4. **Given** a registered attendee, **When** they unregister, **Then** the next waitlisted user is automatically promoted
5. **Given** an event owner, **When** they change status from "published" to "cancelled", **Then** all registered attendees receive cancellation notifications
6. **Given** an upcoming event (within 24h), **When** the reminder job runs, **Then** all registered attendees receive reminder notifications

---

### User Story 5 - Real-Time Chat & Direct Messaging (Priority: P2)

A prospective student initiates a direct message with a verified university student to ask questions about campus life, receives real-time responses via WebSocket, and sees typing indicators.

**Why this priority**: Differentiating feature connecting prospective and current students. Real-time communication increases engagement and value.

**Independent Test**: Send direct messages, create group chats, observe real-time delivery and typing indicators. Delivers value as a functional messaging system.

**Acceptance Scenarios**:

1. **Given** a prospective student, **When** they click "Message" on a verified student's profile, **Then** a direct chat is created with special "prospective ↔ verified" badge
2. **Given** an active WebSocket connection, **When** user A sends a message, **Then** user B receives it in real-time without refresh
3. **Given** user A typing a message, **When** they type in the chat input, **Then** user B sees "[User A] is typing..." indicator
4. **Given** a delivered message, **When** the recipient views it, **Then** a read receipt is sent and displayed to the sender
5. **Given** a community admin, **When** they create a community chat, **Then** all community members can participate in the chat
6. **Given** a group chat with 10 members, **When** one member sends a message with an image attachment, **Then** all members receive the message with the image
7. **Given** a user searching their message history, **When** they enter "assignment deadline", **Then** all messages containing that phrase are displayed

---

### User Story 6 - Content Moderation & Reporting (Priority: P2)

A community moderator receives a report about inappropriate content, reviews it in the moderation queue, takes action (remove post, warn user), and logs the decision.

**Why this priority**: Essential for platform safety and trust. Moderators need tools to maintain community standards.

**Independent Test**: Report content, view moderation queue, take moderation actions, and verify logging. Delivers value as a functional moderation system.

**Acceptance Scenarios**:

1. **Given** a community member viewing inappropriate content, **When** they click "Report" and select reason "spam", **Then** a report is created in the moderation queue
2. **Given** a moderator viewing the queue, **When** they review a report, **Then** they see the reported content, reporter info (anonymized), and action options
3. **Given** a moderator reviewing a valid report, **When** they select "Remove post", **Then** the post is deleted and reporter is notified
4. **Given** a repeat offender, **When** a moderator bans them from the community, **Then** the user loses access and all their content is hidden
5. **Given** a user who was reported, **When** the report is marked "not a violation", **Then** no action is taken and the report is closed
6. **Given** all moderation actions, **When** an action is taken, **Then** it is logged with timestamp, moderator ID, reason, and action type

---

### User Story 7 - Search & Discovery (Priority: P3)

A student searches for "machine learning" and discovers relevant communities, posts, events, and users, using filters to refine results.

**Why this priority**: Enhances discoverability but not critical for MVP. Users can manually browse communities initially.

**Independent Test**: Perform searches with various queries, apply filters, verify autocomplete suggestions. Delivers value as enhanced navigation.

**Acceptance Scenarios**:

1. **Given** a user on the search page, **When** they type "machine learning", **Then** they see results grouped by: Communities, Posts, Events, Users
2. **Given** search results, **When** they apply filter "Communities only" and sort by "Most members", **Then** only communities are shown, sorted by member count
3. **Given** typing in search box, **When** they enter 3+ characters, **Then** autocomplete suggestions appear with top 5 results
4. **Given** a search for "Stanford", **When** results load, **Then** verified communities rank higher than unverified ones

---

### User Story 8 - Analytics Dashboard (Premium) (Priority: P3)

A university administrator with a premium subscription views the analytics dashboard, tracks daily active users, post engagement, and conversion rates from prospective to verified students.

**Why this priority**: Revenue-generating feature but not essential for core functionality. Free tier provides basic value.

**Independent Test**: Access premium analytics, view metrics charts, export data to CSV. Delivers value for paying customers.

**Acceptance Scenarios**:

1. **Given** a premium community admin, **When** they access analytics dashboard, **Then** they see DAU, WAU, MAU metrics for the last 30 days
2. **Given** the analytics dashboard, **When** viewing "Conversion Tracking", **Then** they see a funnel: Prospective Students → Verified Students → Active Members
3. **Given** a free tier community, **When** an admin tries to access advanced analytics, **Then** they see a paywall with upgrade prompt
4. **Given** a premium admin, **When** they click "Export to CSV", **Then** a CSV file with all metrics is downloaded
5. **Given** event metrics, **When** viewing attendance rates, **Then** they see: Total registrations, actual attendance, no-show rate

---

### User Story 9 - Notification System (Priority: P3)

A user receives real-time notifications when someone reacts to their post, mentions them in a comment, or sends them a direct message, with the ability to configure notification preferences.

**Why this priority**: Increases engagement but platform functions without it initially. Users can check manually.

**Independent Test**: Trigger notifications via various actions, receive them via WebSocket and email, configure preferences. Delivers value as enhanced UX.

**Acceptance Scenarios**:

1. **Given** user B reacting to user A's post, **When** the reaction occurs, **Then** user A receives a real-time notification "User B reacted ❤️ to your post"
2. **Given** a user mentioned in a comment (@username), **When** the comment is posted, **Then** the mentioned user receives a notification
3. **Given** a user's notification preferences, **When** they disable "Email notifications", **Then** they only receive in-app WebSocket notifications
4. **Given** a user offline, **When** they receive 5 notifications, **Then** those notifications are queued and delivered when they reconnect
5. **Given** an event registration, **When** a user registers for an event, **Then** they receive a confirmation notification with event details

---

### User Story 10 - Multi-University Affiliation (Priority: P3)

A transfer student or dual-enrollment student verifies their email for multiple universities and accesses content from both communities simultaneously.

**Why this priority**: Nice-to-have for edge cases. Most users affiliate with one university initially.

**Independent Test**: Verify multiple university emails, view content from multiple communities, switch between affiliations. Delivers value for multi-affiliated users.

**Acceptance Scenarios**:

1. **Given** a user verified at Stanford, **When** they verify their MIT email, **Then** they gain access to both Stanford and MIT communities
2. **Given** a multi-affiliated user, **When** they view their profile, **Then** all verified universities are displayed as badges
3. **Given** viewing the feed, **When** a multi-affiliated user selects "All communities", **Then** posts from all their universities appear in one feed

---

### Edge Cases

- **What happens when a user's verification expires?** University emails may be deactivated after graduation. System should handle re-verification or graceful degradation of access.
- **How does the system handle duplicate Google accounts?** Prevent multiple accounts with the same Google ID; handle email changes in Google profiles.
- **What if a university domain changes?** Admin override mechanism to migrate verifications to new domain.
- **How are sub-community permissions inherited?** Child communities inherit parent visibility settings but can be more restrictive, not less.
- **What happens to posts when a community is deleted?** Soft delete community and cascade to all content; allow admin to export data first.
- **How does the system prevent spam in direct messages?** Rate limit new conversations (5 per hour for new accounts); message request system for non-connections.
- **What happens when an event reaches capacity mid-registration?** Atomic transactions ensure only X registrations succeed; implement optimistic locking.
- **How are WebSocket reconnections handled?** Exponential backoff retry strategy; message queue persistence during disconnection.
- **What if a reported user is also a moderator?** Escalate to community admin; moderators cannot moderate reports about themselves.
- **How does search handle special characters or SQL injection attempts?** Input sanitization; use full-text search with parameterized queries.
- **What happens to analytics when a user deletes their account?** Anonymize historical metrics; don't retroactively adjust counts.
- **How are notification preferences handled for new notification types?** Default to enabled; allow granular control per type.

## Requirements *(mandatory)*

### Functional Requirements

#### Authentication & Authorization
- **FR-001**: System MUST support Google OAuth 2.0 for user authentication
- **FR-002**: System MUST generate JWT access tokens (15-minute expiry) and refresh tokens (7-day expiry)
- **FR-003**: System MUST store refresh tokens in HTTP-only cookies for security
- **FR-004**: System MUST support role-based access control with roles: student, prospective_student, admin, moderator
- **FR-005**: System MUST validate JWT tokens on all protected endpoints

#### User Management
- **FR-006**: System MUST create user profiles with fields: name, email, bio (max 500 chars), avatar URL, created_at, updated_at
- **FR-007**: System MUST support avatar image upload (max 5MB, formats: JPG, PNG, WebP)
- **FR-008**: System MUST validate university email domains against a whitelist of recognized institutions
- **FR-009**: System MUST allow users to have multiple university affiliations
- **FR-010**: System MUST provide user search by name with autocomplete (min 3 characters)

#### Student Verification
- **FR-011**: System MUST send verification emails with unique tokens to university email addresses
- **FR-012**: System MUST expire verification tokens after 24 hours
- **FR-013**: System MUST track verification status per university per user (verified, pending, expired)
- **FR-014**: System MUST provide admin override to manually verify students
- **FR-015**: System MUST log all verification attempts with timestamp, IP address, and result

#### Communities
- **FR-016**: System MUST support community types: university, business, student_council, hobby
- **FR-017**: System MUST support visibility settings: public (anyone can view/join), private (invite-only, searchable), closed (invite-only, not searchable)
- **FR-018**: System MUST support hierarchical communities with parent-child relationships (max depth: 3 levels)
- **FR-019**: System MUST enforce student verification requirement if enabled for university communities
- **FR-020**: System MUST support community roles: admin (full control), moderator (content management), member (basic participation)
- **FR-021**: System MUST allow communities to have avatars and cover images
- **FR-022**: System MUST support community metadata: name, description (max 2000 chars), created_at, member_count

#### Social Feed
- **FR-023**: System MUST allow community members to create posts with rich text content (max 10,000 chars)
- **FR-024**: System MUST support media attachments on posts (max 10 files, 20MB total, formats: images, PDFs)
- **FR-025**: System MUST support reaction types: like, love, celebrate, support
- **FR-026**: System MUST allow one reaction per user per post (can change reaction type)
- **FR-027**: System MUST support nested comments on posts (max depth: 3 levels)
- **FR-028**: System MUST allow post authors to edit posts within 24 hours (with "edited" indicator)
- **FR-029**: System MUST allow post authors and moderators to delete posts
- **FR-030**: System MUST allow moderators/admins to pin posts to the top of the feed
- **FR-031**: System MUST paginate feeds with default 20 posts per page, max 100
- **FR-032**: System MUST sort feed by: most recent, most reactions, most comments

#### Events
- **FR-033**: System MUST support event types: online, offline, hybrid
- **FR-034**: System MUST require event fields: title, description, type, start_time, end_time, location (for offline/hybrid)
- **FR-035**: System MUST support participant limits (optional)
- **FR-036**: System MUST implement waitlist when events reach capacity
- **FR-037**: System MUST support event statuses: draft, published, completed, cancelled
- **FR-038**: System MUST allow event creators to update event details before start time
- **FR-039**: System MUST send reminders 24 hours before event start time to registered attendees
- **FR-040**: System MUST track registration timestamp and attendance status

#### Real-Time Chat
- **FR-041**: System MUST support chat types: direct (1-on-1), group, community
- **FR-042**: System MUST use WebSocket protocol for real-time message delivery
- **FR-043**: System MUST support special "prospective ↔ verified student" chat type with visual indicator
- **FR-044**: System MUST implement typing indicators with 3-second timeout
- **FR-045**: System MUST implement read receipts showing when messages are viewed
- **FR-046**: System MUST support media attachments in messages (images, files, max 10MB)
- **FR-047**: System MUST provide message history search by content
- **FR-048**: System MUST paginate message history (50 messages per page)
- **FR-049**: System MUST persist messages to database for offline access
- **FR-050**: System MUST implement message queue for offline users

#### Moderation
- **FR-051**: System MUST allow reporting of posts, comments, messages, and users
- **FR-052**: System MUST support report reasons: spam, harassment, inappropriate_content, misinformation, other
- **FR-053**: System MUST create moderation queue entries for all reports
- **FR-054**: System MUST allow moderators to: remove content, warn users, ban users
- **FR-055**: System MUST prevent moderators from moderating reports about themselves (escalate to admin)
- **FR-056**: System MUST log all moderation actions with: timestamp, moderator_id, action_type, reason, target_id
- **FR-057**: System MUST allow users to block other users (hide content, prevent messaging)
- **FR-058**: System MUST support ban durations: temporary (specify days), permanent

#### Analytics (Premium Feature)
- **FR-059**: System MUST track user metrics: DAU (Daily Active Users), WAU, MAU
- **FR-060**: System MUST track content metrics: post count, reaction count, comment count per period
- **FR-061**: System MUST track event metrics: registration count, attendance rate, no-show rate
- **FR-062**: System MUST track chat metrics: message count, response time averages
- **FR-063**: System MUST track conversion: prospective students → verified students → active members
- **FR-064**: System MUST provide export functionality (CSV, PDF) for all metrics
- **FR-065**: System MUST restrict advanced analytics to premium tier communities
- **FR-066**: System MUST retain historical data: 30 days (free), 1 year (premium)

#### Search
- **FR-067**: System MUST support global search across: communities, users, posts, events
- **FR-068**: System MUST provide autocomplete suggestions (min 3 characters, top 5 results)
- **FR-069**: System MUST support filters: entity type, date range, community scope
- **FR-070**: System MUST support sorting: relevance (default), most recent, most popular
- **FR-071**: System MUST implement full-text search with relevance ranking
- **FR-072**: System MUST sanitize search inputs to prevent SQL injection

#### Notifications
- **FR-073**: System MUST support notification types: mention, reaction, comment, message, event_reminder, event_update
- **FR-074**: System MUST deliver notifications via: WebSocket (real-time), email (configurable)
- **FR-075**: System MUST allow users to configure notification preferences per type and per channel
- **FR-076**: System MUST queue notifications for offline users (deliver on reconnect)
- **FR-077**: System MUST mark notifications as read/unread
- **FR-078**: System MUST paginate notification history (20 per page)

### Non-Functional Requirements

#### Performance
- **NFR-001**: System MUST respond to 95% of API requests within 200ms (read operations)
- **NFR-002**: System MUST respond to 95% of API requests within 500ms (write operations)
- **NFR-003**: System MUST deliver WebSocket messages with <100ms latency
- **NFR-004**: System MUST support 10,000 concurrent WebSocket connections
- **NFR-005**: System MUST cache frequently accessed data (user profiles, community metadata) in Redis with 5-minute TTL

#### Scalability
- **NFR-006**: System MUST be stateless to enable horizontal scaling
- **NFR-007**: System MUST use connection pooling for database (min: 5, max: 20 per instance)
- **NFR-008**: System MUST process background jobs (emails, notifications) via Celery task queue
- **NFR-009**: System MUST support database read replicas for analytics queries

#### Security
- **NFR-010**: System MUST hash passwords with bcrypt (cost factor: 12) if supporting email/password auth
- **NFR-011**: System MUST sanitize all user input to prevent XSS attacks
- **NFR-012**: System MUST use parameterized queries or ORM to prevent SQL injection
- **NFR-013**: System MUST implement CORS with whitelisted origins (no wildcards in production)
- **NFR-014**: System MUST implement rate limiting: 100 req/min per authenticated user, 20 req/min per IP for unauthenticated
- **NFR-015**: System MUST implement stricter rate limits for auth endpoints: 5 attempts/minute per IP
- **NFR-016**: System MUST encrypt sensitive data at rest (passwords, tokens)
- **NFR-017**: System MUST use HTTPS for all communications
- **NFR-018**: System MUST validate file uploads for type, size, and malware

#### Reliability
- **NFR-019**: System MUST achieve 99.9% uptime (excluding planned maintenance)
- **NFR-020**: System MUST implement health check endpoints: `/health` (liveness), `/health/ready` (readiness)
- **NFR-021**: System MUST implement graceful degradation: if Redis fails, serve uncached data
- **NFR-022**: System MUST use database transactions for all multi-step operations
- **NFR-023**: System MUST implement retry logic with exponential backoff for external API calls

#### Monitoring & Observability
- **NFR-024**: System MUST use structured JSON logging in production
- **NFR-025**: System MUST include request_id in all logs for request tracing
- **NFR-026**: System MUST redact PII from logs (passwords, tokens, credit cards)
- **NFR-027**: System MUST expose Prometheus metrics at `/health/metrics`
- **NFR-028**: System MUST integrate with Sentry for error tracking
- **NFR-029**: System MUST log all moderation actions, verification attempts, and security events

#### Compliance & Privacy
- **NFR-030**: System MUST support GDPR compliance: data export, right to deletion
- **NFR-031**: System MUST implement soft deletes for user data (allow recovery within 30 days)
- **NFR-032**: System MUST anonymize user data in analytics after account deletion
- **NFR-033**: System MUST provide clear privacy policy and terms of service acceptance tracking

#### Documentation
- **NFR-034**: System MUST provide OpenAPI 3.0 documentation at `/docs` (Swagger UI)
- **NFR-035**: System MUST provide ReDoc documentation at `/redoc`
- **NFR-036**: System MUST include example requests/responses in API documentation
- **NFR-037**: System MUST maintain database schema diagrams (ER diagrams)
- **NFR-038**: System MUST document all background jobs and their schedules

### Key Entities

#### User
- **Purpose**: Represents a platform user (student, prospective student, admin)
- **Key Attributes**: id (UUID), google_id (unique), email, name, bio, avatar_url, role, created_at, updated_at, deleted_at
- **Relationships**: Has many verifications, memberships, posts, messages, reactions, reports

#### Verification
- **Purpose**: Tracks student verification status for universities
- **Key Attributes**: id (UUID), user_id, university_id, email, token (hashed), status (pending/verified/expired), verified_at, expires_at
- **Relationships**: Belongs to user, belongs to university

#### University
- **Purpose**: Represents educational institutions with verified domains
- **Key Attributes**: id (UUID), name, domain, logo_url, country, created_at
- **Relationships**: Has many verifications, has many communities

#### Community
- **Purpose**: Organizational unit for content (university, club, department)
- **Key Attributes**: id (UUID), name, description, type, visibility, parent_id, requires_verification, avatar_url, cover_url, member_count, created_at
- **Relationships**: Belongs to parent community, has many child communities, has many memberships, posts, events

#### Membership
- **Purpose**: Tracks user membership in communities with roles
- **Key Attributes**: id (UUID), user_id, community_id, role (admin/moderator/member), joined_at
- **Relationships**: Belongs to user, belongs to community

#### Post
- **Purpose**: User-generated content within communities
- **Key Attributes**: id (UUID), author_id, community_id, content (rich text), attachments (JSON array), is_pinned, edited_at, created_at, deleted_at
- **Relationships**: Belongs to author (user), belongs to community, has many reactions, comments

#### Reaction
- **Purpose**: User reactions to posts (like, love, etc.)
- **Key Attributes**: id (UUID), user_id, post_id, reaction_type (enum), created_at
- **Relationships**: Belongs to user, belongs to post
- **Constraints**: Unique constraint on (user_id, post_id)

#### Comment
- **Purpose**: Nested comments on posts
- **Key Attributes**: id (UUID), author_id, post_id, parent_comment_id, content, created_at, deleted_at
- **Relationships**: Belongs to author (user), belongs to post, belongs to parent comment (self-referential)

#### Event
- **Purpose**: Community events with registration tracking
- **Key Attributes**: id (UUID), community_id, creator_id, title, description, type (online/offline/hybrid), location, start_time, end_time, participant_limit, status, created_at
- **Relationships**: Belongs to community, belongs to creator (user), has many registrations

#### EventRegistration
- **Purpose**: Tracks user registration for events
- **Key Attributes**: id (UUID), event_id, user_id, status (registered/waitlisted/attended/no_show), registered_at
- **Relationships**: Belongs to event, belongs to user

#### Chat
- **Purpose**: Container for messages (direct, group, community)
- **Key Attributes**: id (UUID), type (direct/group/community), name, community_id (nullable), created_at
- **Relationships**: Has many participants, has many messages

#### ChatParticipant
- **Purpose**: Tracks users in chats
- **Key Attributes**: id (UUID), chat_id, user_id, joined_at, last_read_at
- **Relationships**: Belongs to chat, belongs to user

#### Message
- **Purpose**: Individual messages within chats
- **Key Attributes**: id (UUID), chat_id, sender_id, content, attachments (JSON array), created_at, deleted_at
- **Relationships**: Belongs to chat, belongs to sender (user), has many read receipts

#### MessageReadReceipt
- **Purpose**: Tracks when messages are read
- **Key Attributes**: id (UUID), message_id, user_id, read_at
- **Relationships**: Belongs to message, belongs to user

#### Report
- **Purpose**: User reports of content/users
- **Key Attributes**: id (UUID), reporter_id, reported_user_id (nullable), reported_content_id (nullable), reported_content_type (enum), reason, details, status (pending/resolved/dismissed), created_at
- **Relationships**: Belongs to reporter (user), polymorphic to reported content (post/comment/message/user)

#### ModerationAction
- **Purpose**: Log of moderation actions taken
- **Key Attributes**: id (UUID), moderator_id, report_id, action_type (remove/warn/ban), reason, target_id, target_type, created_at
- **Relationships**: Belongs to moderator (user), belongs to report

#### Notification
- **Purpose**: User notifications for various events
- **Key Attributes**: id (UUID), user_id, type (mention/reaction/comment/message/event), title, content, link, is_read, created_at
- **Relationships**: Belongs to user

#### AnalyticsMetric
- **Purpose**: Stores analytics data points
- **Key Attributes**: id (UUID), community_id, metric_type, metric_value, period_start, period_end, created_at
- **Relationships**: Belongs to community

## Technical Architecture

### Technology Stack
- **Backend Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with TimescaleDB extension (for time-series analytics)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Cache**: Redis 7+ (session data, frequently accessed content)
- **Task Queue**: Celery with Redis broker
- **WebSocket**: FastAPI WebSocket with Redis pub/sub for multi-instance support
- **Authentication**: OAuth2 (Google), JWT
- **File Storage**: S3-compatible object storage (AWS S3, MinIO)
- **Search**: PostgreSQL full-text search (pg_trgm extension) or Elasticsearch (future)
- **Monitoring**: Prometheus + Grafana, Sentry for error tracking
- **API Documentation**: OpenAPI 3.0 (auto-generated via FastAPI)

### API Versioning
- URL-based versioning: `/api/v1/`, `/api/v2/`
- Maintain backward compatibility for one major version
- Deprecation warnings via response headers: `Deprecated: true`, `Sunset: 2026-01-01`

### Database Design Principles
- Use UUIDs for all primary keys (prevents enumeration attacks)
- Implement soft deletes with `deleted_at` timestamp
- Add indexes on all foreign keys and frequently queried fields
- Use database-level constraints (foreign keys, unique, not null)
- Implement optimistic locking for concurrent updates (version column)
- Use database migrations exclusively (never manual schema changes)

### WebSocket Architecture
- Connection authentication via JWT in query parameter or header
- Redis pub/sub for multi-instance message distribution
- Heartbeat/ping mechanism (30-second interval) to detect dead connections
- Graceful reconnection with message replay for missed messages
- Connection pooling: max 10,000 concurrent connections per instance

### Background Jobs
- **Email Delivery**: Verification emails, event reminders, notifications
- **Event Reminders**: Scheduled 24 hours before event start
- **Analytics Aggregation**: Daily rollup of metrics (DAU, WAU, MAU)
- **Cleanup Jobs**: Delete expired verification tokens, purge old soft-deleted records
- **Notification Dispatch**: Batch email notifications (digest emails)

### File Upload Handling
- Direct upload to S3 with pre-signed URLs (reduce backend load)
- File validation: type whitelist (MIME type), size limits, virus scanning (ClamAV)
- Image processing: thumbnail generation, format conversion (WebP)
- CDN integration for serving uploaded files (CloudFront)

### Rate Limiting Strategy
- **Global**: 100 req/min per authenticated user, 20 req/min per IP (unauthenticated)
- **Authentication**: 5 req/min per IP (prevent brute force)
- **Message Sending**: 10 messages/min per user (prevent spam)
- **Post Creation**: 5 posts/hour per user (prevent spam)
- **Report Submission**: 10 reports/hour per user (prevent abuse)
- Implementation: Redis-based token bucket algorithm

### Error Handling
- Consistent error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email format is invalid",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "suggestion": "Use format: user@example.com"
    },
    "request_id": "uuid"
  }
}
```
- HTTP status codes: 400 (validation), 401 (auth), 403 (forbidden), 404 (not found), 409 (conflict), 429 (rate limit), 500 (server error)

### Security Measures
- **Input Validation**: Pydantic models for all requests
- **Output Encoding**: Escape HTML/JavaScript in responses
- **CSRF Protection**: Token validation for state-changing operations (non-GET)
- **SQL Injection**: ORM exclusively, no raw SQL in application code
- **XSS Prevention**: Content Security Policy headers, sanitize rich text
- **File Upload**: Type validation, size limits, virus scanning, secure filenames
- **Secrets Management**: Environment variables, never commit secrets to git
- **Audit Logging**: Log all authentication events, moderation actions, data access

## API Endpoints Overview

### Authentication
- `POST /api/v1/auth/google` - Initiate Google OAuth flow
- `POST /api/v1/auth/google/callback` - Handle OAuth callback, issue tokens
- `POST /api/v1/auth/refresh` - Refresh access token using refresh token
- `POST /api/v1/auth/logout` - Invalidate refresh token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update current user profile
- `DELETE /api/v1/users/me` - Delete account (GDPR)
- `GET /api/v1/users/{user_id}` - Get user profile by ID
- `GET /api/v1/users/search?q={query}` - Search users

### Verification
- `POST /api/v1/verifications` - Request student verification
- `POST /api/v1/verifications/confirm/{token}` - Confirm verification
- `GET /api/v1/verifications/me` - List my verifications
- `POST /api/v1/verifications/{verification_id}/resend` - Resend verification email

### Communities
- `GET /api/v1/communities` - List communities (with filters)
- `POST /api/v1/communities` - Create community
- `GET /api/v1/communities/{community_id}` - Get community details
- `PATCH /api/v1/communities/{community_id}` - Update community
- `DELETE /api/v1/communities/{community_id}` - Delete community (soft delete)
- `POST /api/v1/communities/{community_id}/join` - Join community
- `POST /api/v1/communities/{community_id}/leave` - Leave community
- `GET /api/v1/communities/{community_id}/members` - List members
- `PATCH /api/v1/communities/{community_id}/members/{user_id}` - Update member role

### Posts
- `GET /api/v1/communities/{community_id}/posts` - List posts in community
- `POST /api/v1/communities/{community_id}/posts` - Create post
- `GET /api/v1/posts/{post_id}` - Get post details
- `PATCH /api/v1/posts/{post_id}` - Update post
- `DELETE /api/v1/posts/{post_id}` - Delete post
- `POST /api/v1/posts/{post_id}/pin` - Pin post (moderator)
- `POST /api/v1/posts/{post_id}/reactions` - Add reaction
- `DELETE /api/v1/posts/{post_id}/reactions` - Remove reaction

### Comments
- `GET /api/v1/posts/{post_id}/comments` - List comments on post
- `POST /api/v1/posts/{post_id}/comments` - Create comment
- `PATCH /api/v1/comments/{comment_id}` - Update comment
- `DELETE /api/v1/comments/{comment_id}` - Delete comment

### Events
- `GET /api/v1/communities/{community_id}/events` - List events
- `POST /api/v1/communities/{community_id}/events` - Create event
- `GET /api/v1/events/{event_id}` - Get event details
- `PATCH /api/v1/events/{event_id}` - Update event
- `DELETE /api/v1/events/{event_id}` - Delete event
- `POST /api/v1/events/{event_id}/register` - Register for event
- `DELETE /api/v1/events/{event_id}/register` - Unregister from event
- `GET /api/v1/events/{event_id}/participants` - List participants

### Chats
- `GET /api/v1/chats` - List my chats
- `POST /api/v1/chats` - Create chat (direct or group)
- `GET /api/v1/chats/{chat_id}` - Get chat details
- `GET /api/v1/chats/{chat_id}/messages` - List messages
- `POST /api/v1/chats/{chat_id}/messages` - Send message
- `PATCH /api/v1/messages/{message_id}` - Edit message
- `DELETE /api/v1/messages/{message_id}` - Delete message
- `POST /api/v1/chats/{chat_id}/read` - Mark messages as read
- `GET /api/v1/chats/{chat_id}/search?q={query}` - Search messages

### WebSocket
- `WS /api/v1/ws?token={jwt_token}` - WebSocket connection for real-time updates

### Moderation
- `POST /api/v1/reports` - Submit report
- `GET /api/v1/reports` - List reports (moderator)
- `PATCH /api/v1/reports/{report_id}` - Update report status
- `POST /api/v1/moderation/actions` - Take moderation action
- `GET /api/v1/moderation/logs` - View moderation logs (admin)

### Search
- `GET /api/v1/search?q={query}&type={type}&filters={filters}` - Global search

### Notifications
- `GET /api/v1/notifications` - List notifications
- `PATCH /api/v1/notifications/{notification_id}/read` - Mark as read
- `PATCH /api/v1/notifications/read-all` - Mark all as read
- `GET /api/v1/notifications/preferences` - Get notification preferences
- `PATCH /api/v1/notifications/preferences` - Update preferences

### Analytics (Premium)
- `GET /api/v1/analytics/users?period={period}` - User metrics (DAU, WAU, MAU)
- `GET /api/v1/analytics/content?period={period}` - Content metrics
- `GET /api/v1/analytics/events?period={period}` - Event metrics
- `GET /api/v1/analytics/conversion?period={period}` - Conversion funnel
- `POST /api/v1/analytics/export?format={csv|pdf}` - Export analytics

### Health & Monitoring
- `GET /health` - Liveness check
- `GET /health/ready` - Readiness check (DB, Redis, external services)
- `GET /health/metrics` - Prometheus metrics

## Testing Strategy

### Unit Tests
- All service layer functions (business logic)
- All utility functions (validation, formatting, etc.)
- Pydantic model validation
- Target: 80%+ code coverage

### Integration Tests
- All API endpoints with database interactions
- Authentication flows (OAuth, JWT refresh)
- WebSocket connections and message delivery
- Background job execution
- Target: 100% endpoint coverage

### End-to-End Tests
- Critical user journeys:
  - Registration → Verification → Join community → Post content
  - Create event → Register → Receive reminder
  - Report content → Moderate → Ban user
- Target: Cover all P1 and P2 user stories

### Performance Tests
- Load testing: 1,000 concurrent users, 10,000 requests/min
- Stress testing: Find breaking point
- WebSocket scalability: 10,000 concurrent connections
- Database query performance: All queries <50ms

### Security Tests
- OWASP Top 10 vulnerability scanning
- SQL injection attempts
- XSS attempts
- CSRF token validation
- Rate limit enforcement
- Authentication/authorization bypass attempts

## Deployment Strategy

### Environments
- **Development**: Local Docker Compose setup
- **Staging**: Kubernetes cluster (mirrors production)
- **Production**: Kubernetes cluster with auto-scaling

### CI/CD Pipeline
1. **Linting**: black, isort, flake8, mypy
2. **Unit Tests**: pytest with coverage report
3. **Integration Tests**: pytest with test database
4. **Security Scan**: bandit, safety (dependency vulnerabilities)
5. **Build**: Docker image build
6. **Deploy to Staging**: Automated on merge to `develop`
7. **E2E Tests**: Run against staging
8. **Deploy to Production**: Manual approval required

### Infrastructure Components
- **Application**: 3+ replicas (auto-scale based on CPU)
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster (3 nodes)
- **Task Queue**: Celery workers (5+ instances)
- **Load Balancer**: NGINX or cloud LB
- **Object Storage**: S3 or compatible
- **CDN**: CloudFront or similar

### Monitoring & Alerting
- **Application Metrics**: Prometheus + Grafana dashboards
- **Error Tracking**: Sentry with Slack notifications
- **Logs**: Centralized logging (ELK stack or CloudWatch)
- **Uptime Monitoring**: Pingdom or UptimeRobot
- **Alerts**:
  - Error rate >1% (5-minute window)
  - Response time >500ms (95th percentile)
  - Database connections >80% of pool
  - Disk usage >80%
  - WebSocket connection failures >10/min

## Success Metrics

### Technical Metrics
- API response time: p95 <200ms (read), <500ms (write)
- Uptime: 99.9%
- Test coverage: >80%
- Zero high/critical security vulnerabilities
- WebSocket latency: <100ms

### Business Metrics
- User registration conversion: >60% (OAuth initiated → account created)
- Verification completion: >70% (email sent → verified)
- Daily active users (DAU): Track growth
- Community engagement: avg 5+ posts per community per day
- Event registration rate: >40% of community members for events
- Prospective → Verified conversion: >30% within 6 months

### User Experience Metrics
- Time to first post: <5 minutes after registration
- Search result relevance: >80% click-through on first page
- Notification delivery time: <500ms
- Chat message delivery: <100ms

## Open Questions & Clarifications Needed

1. **University Domain Whitelist**: How will the list of approved university domains be maintained? Manual admin curation or third-party service integration?
2. **Premium Tier Pricing**: What is the pricing model for premium communities? Per-seat, flat-rate, or usage-based?
3. **Media Storage Costs**: Should there be storage limits per user/community? How long to retain deleted content?
4. **Internationalization**: Should the platform support multiple languages initially, or start with English only?
5. **Mobile Apps**: Will there be native mobile apps, or web-only initially? Impacts push notification strategy.
6. **Email Provider**: Which email service? SendGrid, AWS SES, or custom SMTP?
7. **Moderation Automation**: Should we implement AI-based content moderation (e.g., OpenAI Moderation API) or manual-only initially?
8. **Data Retention for Deleted Accounts**: How long to retain soft-deleted user data before permanent deletion? 30 days?
9. **WebSocket Scaling**: Expected max concurrent WebSocket connections? Impacts infrastructure sizing.
10. **Community Transfer**: Can community ownership be transferred? What's the process?

## Dependencies & Integrations

### Required Third-Party Services
- **Google OAuth**: OAuth 2.0 client credentials
- **Email Service**: SendGrid/AWS SES/Mailgun for transactional emails
- **Object Storage**: AWS S3 or MinIO for file uploads
- **Monitoring**: Sentry account for error tracking

### Optional Integrations (Future)
- **Payment Gateway**: Stripe for premium subscriptions
- **Analytics**: Mixpanel or Amplitude for product analytics
- **Calendar**: Google Calendar/Outlook for event sync
- **Video Conferencing**: Zoom/Google Meet API for online events
- **Push Notifications**: Firebase Cloud Messaging for mobile apps

## Timeline Estimate

### Phase 1: MVP (8-10 weeks)
- **Week 1-2**: Project setup, database schema, core models
- **Week 3-4**: Authentication (Google OAuth, JWT), user management
- **Week 5-6**: Communities, memberships, student verification
- **Week 7-8**: Posts, reactions, comments (social feed)
- **Week 9-10**: Testing, bug fixes, documentation

### Phase 2: Events & Chat (6-8 weeks)
- **Week 11-12**: Event creation, registration, management
- **Week 13-15**: Real-time chat (WebSocket, direct messages, group chats)
- **Week 16-18**: Testing, performance optimization

### Phase 3: Moderation & Search (4-6 weeks)
- **Week 19-20**: Reporting system, moderation queue, actions
- **Week 21-22**: Global search, filtering, autocomplete
- **Week 23-24**: Testing, security audit

### Phase 4: Analytics & Polish (4-6 weeks)
- **Week 25-26**: Analytics dashboard, metrics tracking
- **Week 27-28**: Notifications system, preferences
- **Week 29-30**: Performance optimization, final testing, deployment

**Total Estimated Timeline: 22-30 weeks (5.5-7.5 months)**

## Conclusion

This specification defines a comprehensive social networking platform for university students with verified identity, real-time communication, event management, and moderation capabilities. The platform prioritizes security, scalability, and user experience while maintaining code quality and testing standards as defined in the StudyBuddy Constitution.

The phased development approach ensures incremental value delivery with each phase building on the previous foundation. The MVP (Phase 1) focuses on core social features, followed by real-time capabilities (Phase 2), safety features (Phase 3), and premium functionality (Phase 4).

All requirements align with the constitution's principles of code quality, testing standards, API design, security, and performance. The platform is designed for horizontal scalability, GDPR compliance, and operational excellence.

---

**Next Steps:**
1. Review and approve this specification
2. Create detailed task breakdown for Phase 1 (MVP)
3. Set up development environment and CI/CD pipeline
4. Begin implementation following TDD principles
5. Regular checkpoints at end of each phase for review and course correction
