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
