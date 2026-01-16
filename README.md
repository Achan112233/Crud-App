# Serverless Task Manager

A full-stack task management application built with Azure Functions (serverless), Azure AD authentication, and JWT tokens. No VMs required.

## Features

✅ **Azure AD OAuth 2.0** - Login with Microsoft accounts  
✅ **JWT Token Authentication** - Secure API access  
✅ **Multi-user Task Management** - Isolated per-user data  
✅ **RESTful API** - Full CRUD operations  
✅ **Serverless** - Auto-scaling, pay per request  
✅ **Azure SQL Database** - Cloud-based persistence  

## Tech Stack

- **Backend:** Python 3.11, Azure Functions
- **Database:** Azure SQL Database (or SQLite)
- **Authentication:** Azure AD + JWT
- **Infrastructure:** Azure Functions (Consumption Plan)

## Project Structure

```
Crud-App/
├── function_app.py          ← Azure Functions entry point (all API routes)
├── function_app.json        ← Function configuration
├── auth.py                  ← Azure AD OAuth 2.0 & JWT token management
├── database.py              ← SQLAlchemy models (User, Task)
├── requirements.txt         ← Python dependencies
├── .env.example            ← Environment configuration template
├── .gitignore              ← Git ignore rules
├── SERVERLESS_DEPLOYMENT.md ← Deployment guide
└── AZURE_AD_AUTH.md        ← Authentication setup guide
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

### 3. Local Development

```bash
func start
# API available at: http://localhost:7071/api/
```

### 4. Deploy to Azure

```bash
# Prerequisites: Azure CLI, Azure Functions Core Tools, Azure account

az functionapp create \
  --resource-group crud-app-rg \
  --consumption-plan-name crud-app-func-plan \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name my-task-app-functions \
  --storage-account cruddappstg \
  --os-type Linux

func azure functionapp publish my-task-app-functions --build remote
```

See [SERVERLESS_DEPLOYMENT.md](SERVERLESS_DEPLOYMENT.md) for detailed instructions.

## API Endpoints

All endpoints: `https://<your-function-app>.azurewebsites.net/api/`

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

### 1. Login (Get Access Token)
```bash
curl https://<your-app>.azurewebsites.net/api/login
# Redirects to Azure AD login
```

### 2. Create Task
```bash
curl -X POST https://<your-app>.azurewebsites.net/api/tasks \
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
curl https://<your-app>.azurewebsites.net/api/tasks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Update Task Status
```bash
curl -X PATCH https://<your-app>.azurewebsites.net/api/tasks/{task_id}/status \
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
AZURE_REDIRECT_URI=https://my-task-app.azurewebsites.net/api/callback

# JWT
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24
```

## Setup Azure AD

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Set **Redirect URI** to: `https://<your-function-app>.azurewebsites.net/api/callback`
4. Copy **Application (Client) ID** and **Directory (Tenant) ID**
5. Create a **Client Secret** under **Certificates & secrets**

See [AZURE_AD_AUTH.md](AZURE_AD_AUTH.md) for detailed setup.

## Monitoring & Debugging

```powershell
# View logs
az functionapp log tail --resource-group crud-app-rg --name my-task-app-functions

# Check function status
az functionapp show --resource-group crud-app-rg --name my-task-app-functions

# List deployed functions
func azure functionapp logstream my-task-app-functions
```

## Cost Estimate

- **Execution:** First 1 million executions free/month
- **Storage:** ~$0.50/month
- **After free tier:** $0.20 per million requests

**Typical usage:** $1-5/month

## Deployment Options

- **Azure Functions** (Current) - Serverless, pay-per-request ✅
- See [SERVERLESS_DEPLOYMENT.md](SERVERLESS_DEPLOYMENT.md) for details

## Troubleshooting

### Function won't start
```powershell
func start --verbose
```

### Token validation fails
- Ensure `JWT_SECRET` is set in `.env`
- Verify token format: `Authorization: Bearer <token>`

### Database connection error
- Check `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, credentials
- Verify firewall rules allow your IP

### Azure AD callback error
- Ensure `AZURE_REDIRECT_URI` matches app configuration
- Use `https://` in production

See [AZURE_AD_AUTH.md](AZURE_AD_AUTH.md) for more troubleshooting.

## Security

✅ JWT token validation on all API requests  
✅ User data isolation (can only access own tasks)  
✅ Azure AD handles password security  
✅ Sensitive credentials in environment variables  
✅ HTTPS enforced in production  

## Next Steps

1. ✅ Serverless backend deployed
2. ✅ Azure AD authentication working
3. ✅ REST API fully functional
4. **TODO:** Frontend dashboard (React/Vue)
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

**Built with Azure Functions - Serverless. Scalable. Secure.** 🚀
