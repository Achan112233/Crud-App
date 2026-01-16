# TaskFlow - Task Manager

A full-stack task management application built with Flask, SQLAlchemy, and Azure AD authentication. Features secure OAuth 2.0 login, JWT-protected REST API, and an interactive web dashboard.

## Features

✅ **Azure AD OAuth 2.0** - Login with Microsoft accounts  
✅ **JWT Token Authentication** - Secure API access  
✅ **Multi-user Task Management** - Isolated per-user data  
✅ **RESTful API** - Full CRUD operations  
✅ **Interactive Dashboard** - Real-time task management UI  
✅ **SQLite/Azure SQL** - Local development or cloud persistence  

## Tech Stack

- **Backend:** Python 3.11, Flask
- **Database:** SQLite (local) or Azure SQL Database
- **ORM:** SQLAlchemy
- **Authentication:** Azure AD OAuth 2.0 + JWT
- **Frontend:** Jinja2 templates, Vanilla JavaScript

## Project Structure

```
Crud-App/
├── app.py                   ← Flask main application with all routes
├── auth.py                  ← Azure AD OAuth 2.0 & JWT token management
├── database.py              ← SQLAlchemy models (User, Task)
├── requirements.txt         ← Python dependencies
├── .env.example             ← Environment configuration template
├── .gitignore               ← Git ignore rules
├── Dockerfile               ← Container deployment
├── templates/               ← HTML templates
│   ├── index.html          ← Landing page
│   ├── dashboard.html      ← Task management UI
│   ├── 404.html            ← Error page
│   └── 500.html            ← Server error page
├── static/                 ← CSS/JS assets
│   └── styles.css
├── AZURE_AD_AUTH.md        ← Authentication setup guide
└── README.md               ← This file
```

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Locally

```bash
python app.py
# Web UI available at: http://localhost:5000
# API available at: http://localhost:5000/api/
```

## API Endpoints

All endpoints: `http://localhost:5000/api/` (local) or `https://<your-app>/api/` (deployed)

### Authentication
```
GET  /login           - Azure AD login redirect
GET  /callback        - OAuth callback handler
POST /refresh         - Refresh access token
```

### Tasks (requires JWT token)
```
GET    /tasks                 - List all tasks
POST   /tasks                 - Create task
GET    /tasks/{id}            - Get specific task
PUT    /tasks/{id}            - Update task
DELETE /tasks/{id}            - Delete task
PATCH  /tasks/{id}/status     - Update task status
```

### User (requires JWT token)
```
GET /user/profile   - Get user profile
GET /stats          - Get task statistics
GET /health         - Health check
```

## Example API Usage

### 1. Get Access Token (via Dashboard)
Login at `http://localhost:5000` with Microsoft account, token stored automatically.

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
curl http://localhost:5000/api/tasks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Update Task Status
```bash
curl -X PATCH http://localhost:5000/api/tasks/{task_id}/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Database Schema

### User Table
- `id` (UUID) - Primary key
- `azure_id` (String) - Azure AD unique identifier
- `email` (String) - User email
- `name` (String) - User name
- `created_at` (DateTime) - Account creation timestamp
- `last_login` (DateTime) - Last login timestamp

### Task Table
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to User
- `title` (String) - Task title (required)
- `description` (Text) - Task description
- `status` (String) - pending | in_progress | completed
- `priority` (String) - low | medium | high
- `due_date` (DateTime) - Task due date
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `completed_at` (DateTime) - Completion timestamp

## Environment Variables

See `.env.example` for all required variables:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key

# Azure Database
USE_AZURE=False
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=user
AZURE_SQL_PASSWORD=pass

# Azure AD OAuth
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback

# JWT
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24
```

## Setup Azure AD

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Set **Redirect URI** to: `http://localhost:5000/auth/callback`
4. Copy **Application (Client) ID** and **Directory (Tenant) ID**
5. Create a **Client Secret** under **Certificates & secrets**
6. Add values to `.env` file

See [AZURE_AD_AUTH.md](AZURE_AD_AUTH.md) for detailed setup.

## Troubleshooting

### App won't start
```bash
python app.py --verbose
```

### Token validation fails
- Ensure `JWT_SECRET` is set in `.env`
- Verify token format: `Authorization: Bearer <token>`

### Database connection error
- Check SQLite path or Azure SQL credentials
- Verify database file exists

### Azure AD login fails
- Ensure `AZURE_REDIRECT_URI` in `.env` matches app config
- Use `http://localhost:5000/auth/callback` for local dev

See [AZURE_AD_AUTH.md](AZURE_AD_AUTH.md) for more troubleshooting.

## Security

✅ JWT token validation on all API requests  
✅ User data isolation (can only access own tasks)  
✅ Azure AD handles password security  
✅ Sensitive credentials in environment variables  
✅ HTTPS enforced in production  

## Next Steps

1. ✅ Flask backend with Azure AD authentication
2. ✅ REST API with JWT protection
3. ✅ Interactive dashboard UI
4. **TODO:** Deploy to Azure Container Instances
5. **TODO:** Email notifications
6. **TODO:** Task sharing between users
7. **TODO:** Activity logging

## Support & Documentation

- [Azure Functions Docs](https://learn.microsoft.com/en-us/azure/azure-functions/)
- [Azure AD Documentation](https://learn.microsoft.com/en-us/azure/active-directory/)
- [JWT Authentication](https://jwt.io/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

## License

MIT

---
