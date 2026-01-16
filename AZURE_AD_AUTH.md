# Azure AD Authentication & JWT Implementation Guide

## Overview

This task manager now includes:
- ✅ **Azure AD OAuth 2.0** - Secure login via Microsoft accounts
- ✅ **JWT Tokens** - Access and refresh token system
- ✅ **Protected REST API** - All endpoints require valid JWT
- ✅ **Enhanced Data Models** - User association and task status tracking
- ✅ **Multi-user Support** - Tasks isolated per user

---

## Setup Instructions

### 1. Register Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in:
   - **Name:** `Task Manager App`
   - **Supported account types:** `Accounts in any organizational directory (Any Azure AD directory - Multitenant)`
   - **Redirect URI:** `Web` - `http://localhost:5000/auth/callback`

4. After registration, copy:
   - **Application (Client) ID** → `AZURE_CLIENT_ID`
   - **Directory (Tenant) ID** → `AZURE_TENANT_ID`

5. Go to **Certificates & secrets** → **New client secret**
   - Copy the secret value → `AZURE_CLIENT_SECRET`

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Azure SQL (if using)
USE_AZURE=False
AZURE_SQL_SERVER=...
AZURE_SQL_DATABASE=...
AZURE_SQL_USERNAME=...
AZURE_SQL_PASSWORD=...

# Azure AD
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback

# JWT
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Application

```bash
python app.py
```

Visit: `http://localhost:5000`

---

## Authentication Flow

### Web UI Flow (Browser)

```
1. User clicks "Login with Microsoft"
   ↓
2. Redirects to Azure AD login page
   ↓
3. User enters credentials
   ↓
4. Azure AD redirects to /auth/callback with authorization code
   ↓
5. App exchanges code for access token
   ↓
6. App fetches user info from Microsoft Graph
   ↓
7. App creates JWT tokens and stores in session
   ↓
8. User redirected to dashboard
```

### REST API Flow (Token-based)

```
1. Client calls POST /auth/login or /auth/callback
   ↓
2. Receives JWT access token + refresh token
   ↓
3. Client stores tokens
   ↓
4. For API requests, send: Authorization: Bearer <access_token>
   ↓
5. Server validates JWT token
   ↓
6. If valid, request proceeds
   ↓
7. If expired, use refresh token to get new access token
```

---

## API Reference

### Authentication Endpoints

#### Login (Redirect to Azure AD)
```
GET /auth/login
```

#### Callback (Handle Azure AD response)
```
GET /auth/callback?code=...
```

#### Logout
```
GET /auth/logout
```

#### Refresh Token
```
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}

Response:
{
  "access_token": "new-access-token"
}
```

---

### Task Endpoints

All require: `Authorization: Bearer <access_token>`

#### Get All Tasks
```
GET /api/tasks?status=pending&priority=high

Response:
[
  {
    "id": "uuid",
    "title": "Task title",
    "description": "...",
    "status": "pending|in_progress|completed",
    "priority": "low|medium|high",
    "due_date": "2026-01-20T10:00:00",
    "created_at": "2026-01-16T10:00:00",
    "updated_at": "2026-01-16T10:00:00",
    "completed_at": null
  }
]
```

#### Get Single Task
```
GET /api/tasks/{task_id}

Response: {task object}
```

#### Create Task
```
POST /api/tasks
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "New task",
  "description": "Optional description",
  "priority": "medium",
  "due_date": "2026-01-20T10:00:00"
}

Response: {task object} (201)
```

#### Update Task
```
PUT /api/tasks/{task_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Updated title",
  "description": "...",
  "status": "in_progress",
  "priority": "high",
  "due_date": "2026-01-25T10:00:00"
}

Response: {updated task object}
```

#### Update Task Status
```
PATCH /api/tasks/{task_id}/status
Content-Type: application/json
Authorization: Bearer <token>

{
  "status": "completed"
}

Response: {updated task object}
```

#### Delete Task
```
DELETE /api/tasks/{task_id}
Authorization: Bearer <token>

Response: 204 No Content
```

#### Get User Profile
```
GET /api/user/profile
Authorization: Bearer <token>

Response: {user object}
```

#### Get Task Statistics
```
GET /api/stats
Authorization: Bearer <token>

Response:
{
  "total_tasks": 10,
  "completed_tasks": 5,
  "pending_tasks": 3,
  "in_progress_tasks": 2,
  "high_priority_tasks": 1
}
```

---

## Database Schema

### User Table
```sql
CREATE TABLE user (
  id VARCHAR(36) PRIMARY KEY,
  azure_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Task Table
```sql
CREATE TABLE task (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) FOREIGN KEY REFERENCES user(id),
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  priority VARCHAR(20) DEFAULT 'medium',
  due_date DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME
);
```

---

## JWT Token Structure

### Access Token
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "iat": 1705417200,
  "exp": 1705503600
}
```

### Refresh Token
```json
{
  "user_id": "uuid",
  "type": "refresh",
  "iat": 1705417200,
  "exp": 1708095600
}
```

---

## Testing with cURL

### 1. Get Access Token
```bash
# Login (browser redirect needed for Azure AD)
curl http://localhost:5000/auth/login

# Copy token from response
```

### 2. Create Task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "priority": "high",
    "due_date": "2026-01-20T18:00:00"
  }'
```

### 3. Get Tasks
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:5000/api/tasks
```

### 4. Update Task Status
```bash
curl -X PATCH http://localhost:5000/api/tasks/{task_id}/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### 5. Get Stats
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:5000/api/stats
```

---

## Security Features

### 1. Token Validation
- All API endpoints validate JWT tokens
- Expired tokens are rejected
- Invalid tokens return 401 Unauthorized

### 2. User Isolation
- Users can only access their own tasks
- Queries filtered by `user_id`
- No cross-user data access

### 3. Password Security
- Passwords never stored locally
- Azure AD handles authentication
- No plaintext credentials in database

### 4. HTTPS (Production)
- Always use HTTPS in production
- Set `AZURE_REDIRECT_URI` to HTTPS URL
- Update JWT_SECRET to strong random value

### 5. Environment Variables
- Sensitive data stored in `.env`
- `.env` added to `.gitignore`
- Never commit secrets to git

---

## Troubleshooting

### "Invalid authorization header"
```
Error: Missing or malformed Authorization header
Solution: Use format: Authorization: Bearer <token>
```

### "Invalid or expired token"
```
Error: JWT token expired or invalid
Solution: 
1. Use /auth/refresh to get new access token
2. Re-authenticate if refresh token expired
```

### Azure AD Callback Error
```
Error: "Invalid redirect URI"
Solution:
1. Check AZURE_REDIRECT_URI matches Azure AD app config
2. Ensure scheme (http/https) matches
3. Port number must match
```

### "User not found"
```
Error: User in JWT doesn't exist in database
Solution: User was deleted; re-authenticate to recreate
```

### MSAL Error: "Not configured"
```
Error: Azure AD credentials not set
Solution:
1. Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
2. Restart Flask app
3. Check .env file is loaded
```

---

## Deployment to Azure App Service

See [DEPLOYMENT_AZURE.md](DEPLOYMENT_AZURE.md) for full instructions.

**Key steps:**
1. Set environment variables in Azure Portal
2. Update `AZURE_REDIRECT_URI` to production URL
3. Update app permissions in Azure AD (add production redirect URI)
4. Deploy using Git, Docker, or VS Code

---

## Next Steps

1. ✅ Implement Azure AD authentication
2. ✅ Create REST API endpoints
3. ✅ Add JWT token system
4. **TODO:** Frontend dashboard UI
5. **TODO:** Email notifications
6. **TODO:** Task sharing between users
7. **TODO:** Activity logging

---

## Support

For issues or questions:
1. Check Azure AD app configuration
2. Verify environment variables
3. Review Flask debug logs
4. Check Azure Portal for Azure AD audit logs
