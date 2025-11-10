# StudyBuddy API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api/v1`
**Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## Table of Contents

- [Authentication](#authentication)
- [Health & Monitoring](#health--monitoring)
- [Auth Endpoints](#auth-endpoints)
- [User Endpoints](#user-endpoints)
- [Verification Endpoints](#verification-endpoints)
- [Community Endpoints](#community-endpoints)
- [Error Responses](#error-responses)

---

## Authentication

Most endpoints require authentication using JWT Bearer tokens.

### Getting a Token

```bash
POST /api/v1/auth/google
```

Include the token in subsequent requests:

```bash
Authorization: Bearer <your_access_token>
```

### Token Expiration

- **Access Token:** 15 minutes
- **Refresh Token:** 30 days

---

## Health & Monitoring

### Check API Health

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Check Readiness (DB & Redis)

```http
GET /api/v1/health/ready
```

**Response:**

```json
{
  "status": "ready",
  "checks": {
    "database": "connected",
    "redis": "connected"
  }
}
```

### Prometheus Metrics

```http
GET /api/v1/health/metrics
```

---

## Auth Endpoints

### 1. Google OAuth Login

Initiate Google OAuth flow.

```http
POST /api/v1/auth/google
Content-Type: application/json

{
  "redirect_uri": "http://localhost:3000/auth/callback"
}
```

**Response:**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

### 2. Google OAuth Callback

Handle OAuth callback and create/login user.

```http
POST /api/v1/auth/google/callback
Content-Type: application/json

{
  "code": "4/0AY0e-g7...",
  "state": "random_state_string"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@stanford.edu",
    "name": "Jane Doe",
    "avatar_url": "https://...",
    "role": "student"
  }
}
```

### 3. Refresh Access Token

Get a new access token using refresh token.

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 4. Logout

Invalidate refresh token.

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `204 No Content`

---

## User Endpoints

### 1. Get Current User Profile

Retrieve authenticated user's complete profile.

```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "student@stanford.edu",
  "name": "Jane Doe",
  "bio": "Computer Science student at Stanford",
  "avatar_url": "https://example.com/avatars/jane.jpg",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "verified_universities": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Stanford University",
      "domain": "stanford.edu",
      "logo_url": "https://...",
      "verified_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

### 2. Update Current User Profile

Update profile information (bio, avatar).

```http
PATCH /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Jane Smith",
  "bio": "CS PhD student researching AI",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "student@stanford.edu",
  "name": "Jane Smith",
  "bio": "CS PhD student researching AI",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

### 3. Delete Account (GDPR)

Soft delete user account.

```http
DELETE /api/v1/users/me
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

### 4. Get User by ID

Get public profile of any user.

```http
GET /api/v1/users/{user_id}
```

**Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Jane Doe",
  "bio": "Computer Science student",
  "avatar_url": "https://example.com/avatars/jane.jpg",
  "role": "student",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Verification Endpoints

### 1. Request Student Verification

Request verification for a university email.

```http
POST /api/v1/verifications
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "university_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@stanford.edu"
}
```

**Response:**

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "university": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Stanford University",
    "domain": "stanford.edu"
  },
  "email": "student@stanford.edu",
  "status": "pending",
  "created_at": "2024-01-15T12:00:00Z",
  "expires_at": "2024-01-16T12:00:00Z"
}
```

### 2. Confirm Verification

Confirm verification using token from email.

```http
POST /api/v1/verifications/confirm/{token}
```

**Response:**

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "university": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Stanford University",
    "domain": "stanford.edu"
  },
  "email": "student@stanford.edu",
  "status": "verified",
  "verified_at": "2024-01-15T12:30:00Z",
  "created_at": "2024-01-15T12:00:00Z"
}
```

### 3. Get My Verifications

List all verifications for current user.

```http
GET /api/v1/verifications/me
Authorization: Bearer <access_token>
```

**Response:**

```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440001",
    "university": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Stanford University",
      "domain": "stanford.edu",
      "logo_url": "https://..."
    },
    "email": "student@stanford.edu",
    "status": "verified",
    "verified_at": "2024-01-15T12:30:00Z",
    "created_at": "2024-01-15T12:00:00Z"
  }
]
```

### 4. Resend Verification Email

Resend verification email if not received.

```http
POST /api/v1/verifications/{verification_id}/resend
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

---

## Community Endpoints

### 1. List Communities

Get paginated list of communities with optional filters.

```http
GET /api/v1/communities?type=university&visibility=public&page=1&page_size=20
Authorization: Bearer <access_token> (optional for public communities)
```

**Query Parameters:**

- `type` (optional): Filter by type (`university`, `business`, `student_council`, `hobby`)
- `visibility` (optional): Filter by visibility (`public`, `private`, `closed`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response:**

```json
{
  "data": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "name": "Stanford CS Students",
      "description": "Community for Stanford Computer Science students",
      "type": "university",
      "visibility": "public",
      "requires_verification": true,
      "avatar_url": "https://...",
      "cover_url": "https://...",
      "member_count": 1250,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### 2. Create Community

Create a new community (creator becomes admin).

```http
POST /api/v1/communities
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Stanford AI Club",
  "description": "For students interested in artificial intelligence",
  "type": "hobby",
  "visibility": "public",
  "requires_verification": false,
  "parent_id": null,
  "avatar_url": "https://...",
  "cover_url": "https://..."
}
```

**Response:**

```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "name": "Stanford AI Club",
  "description": "For students interested in artificial intelligence",
  "type": "hobby",
  "visibility": "public",
  "requires_verification": false,
  "parent_id": null,
  "avatar_url": "https://...",
  "cover_url": "https://...",
  "member_count": 1,
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z",
  "parent": null,
  "my_role": "admin"
}
```

### 3. Get Community Details

Get detailed information about a community.

```http
GET /api/v1/communities/{community_id}
Authorization: Bearer <access_token> (optional for public communities)
```

**Response:**

```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "name": "Stanford CS Students",
  "description": "Community for Stanford Computer Science students",
  "type": "university",
  "visibility": "public",
  "requires_verification": true,
  "parent_id": null,
  "avatar_url": "https://...",
  "cover_url": "https://...",
  "member_count": 1250,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T00:00:00Z",
  "parent": null,
  "my_role": "member"
}
```

### 4. Update Community

Update community settings (admin/moderator only).

```http
PATCH /api/v1/communities/{community_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Stanford Computer Science Students",
  "description": "Updated description",
  "visibility": "private",
  "requires_verification": true,
  "avatar_url": "https://...",
  "cover_url": "https://..."
}
```

**Permissions:**

- **Admin:** Can update all fields
- **Moderator:** Can only update `description`

**Response:**

```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "name": "Stanford Computer Science Students",
  "description": "Updated description",
  "type": "university",
  "visibility": "private",
  "requires_verification": true,
  "parent_id": null,
  "avatar_url": "https://...",
  "cover_url": "https://...",
  "member_count": 1250,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-16T11:00:00Z",
  "parent": null,
  "my_role": "admin"
}
```

### 5. Delete Community

Soft delete a community (admin only).

```http
DELETE /api/v1/communities/{community_id}
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

### 6. Join Community

Join a public community as a member.

```http
POST /api/v1/communities/{community_id}/join
Authorization: Bearer <access_token>
```

**Notes:**

- Only works for **public** communities
- Private communities require admin invitation
- Returns 409 if already a member

**Response:**

```json
{
  "id": "950e8400-e29b-41d4-a716-446655440000",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Jane Doe",
    "avatar_url": "https://..."
  },
  "community": {
    "id": "750e8400-e29b-41d4-a716-446655440000",
    "name": "Stanford CS Students"
  },
  "role": "member",
  "joined_at": "2024-01-16T12:00:00Z"
}
```

### 7. Leave Community

Leave a community.

```http
POST /api/v1/communities/{community_id}/leave
Authorization: Bearer <access_token>
```

**Notes:**

- Cannot leave if you're the last admin
- Returns 403 if trying to leave as last admin

**Response:** `204 No Content`

### 8. List Community Members

Get paginated list of community members.

```http
GET /api/v1/communities/{community_id}/members?role=admin&page=1&page_size=20
Authorization: Bearer <access_token> (optional for public communities)
```

**Query Parameters:**

- `role` (optional): Filter by role (`admin`, `moderator`, `member`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response:**

```json
{
  "data": [
    {
      "id": "950e8400-e29b-41d4-a716-446655440000",
      "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Jane Doe",
        "avatar_url": "https://...",
        "bio": "CS student"
      },
      "community": {
        "id": "750e8400-e29b-41d4-a716-446655440000",
        "name": "Stanford CS Students"
      },
      "role": "admin",
      "joined_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 20,
  "total_pages": 63
}
```

### 9. Update Member Role

Update a member's role (admin only).

```http
PATCH /api/v1/communities/{community_id}/members/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "role": "moderator"
}
```

**Roles:**

- `admin`: Full control (manage settings, members, content)
- `moderator`: Manage content (pin posts, moderate), limited settings
- `member`: Basic participation (view, post, comment)

**Response:**

```json
{
  "id": "950e8400-e29b-41d4-a716-446655440000",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Jane Doe",
    "avatar_url": "https://..."
  },
  "community": {
    "id": "750e8400-e29b-41d4-a716-446655440000",
    "name": "Stanford CS Students"
  },
  "role": "moderator",
  "joined_at": "2024-01-01T00:00:00Z"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `204` | No Content | Request successful, no response body |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Resource conflict (e.g., already exists) |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

### Example Error Responses

**400 Bad Request:**

```json
{
  "detail": "Invalid email format"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**

```json
{
  "detail": "Admin role required for this action"
}
```

**404 Not Found:**

```json
{
  "detail": "Community not found"
}
```

**409 Conflict:**

```json
{
  "detail": "You are already a member of this community"
}
```

**422 Validation Error:**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authenticated users:** 100 requests/minute
- **Unauthenticated users:** 20 requests/minute
- **Auth endpoints:** 5 requests/minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

---

## Pagination

List endpoints support pagination with these parameters:

- `page`: Page number (starts at 1)
- `page_size`: Items per page (max: 100)

Paginated responses include:

```json
{
  "data": [...],
  "total": 1250,
  "page": 1,
  "page_size": 20,
  "total_pages": 63
}
```

---

## Best Practices

### 1. Always Use HTTPS in Production

```bash
https://api.studybuddy.com/api/v1/...
```

### 2. Store Tokens Securely

- Never store tokens in localStorage (vulnerable to XSS)
- Use httpOnly cookies or secure storage

### 3. Refresh Tokens Before Expiry

Check token expiration and refresh proactively:

```javascript
if (tokenExpiresIn < 5 * 60) { // Less than 5 minutes
  await refreshToken();
}
```

### 4. Handle Errors Gracefully

```javascript
try {
  const response = await fetch('/api/v1/users/me');
  if (!response.ok) {
    const error = await response.json();
    console.error(error.detail);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### 5. Respect Rate Limits

Implement exponential backoff when hitting rate limits:

```javascript
async function fetchWithRetry(url, options, retries = 3) {
  for (let i = 0; i < retries; i++) {
    const response = await fetch(url, options);
    if (response.status !== 429) return response;
    await new Promise(resolve => setTimeout(resolve, 2 ** i * 1000));
  }
  throw new Error('Rate limit exceeded');
}
```

---

## Next Steps

For more information:

- **Interactive API Docs:** Visit `/docs` for Swagger UI
- **OpenAPI Schema:** Available at `/openapi.json`
- **Support:** Contact the development team

---

**Last Updated:** January 16, 2024
**API Version:** 1.0.0
