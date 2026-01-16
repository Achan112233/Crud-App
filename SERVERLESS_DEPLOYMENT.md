# Deploy Serverless Task Manager to Azure Functions

## No VMs Required - True Serverless Architecture

Your app now runs on **Azure Functions** - pay per execution, auto-scales to 0.

---

## Quick Deploy (5 minutes)

### Prerequisites
```powershell
# Install Azure Functions Core Tools
choco install azure-functions-core-tools

# Or download: https://github.com/Azure/azure-functions-core-tools/releases
```

### Step 1: Create Storage Account
```powershell
$storageAccount = "cruddappstg"
$resourceGroup = "crud-app-rg"

az storage account create `
  --resource-group $resourceGroup `
  --name $storageAccount `
  --location eastus `
  --sku Standard_LRS
```

### Step 2: Deploy Function App
```powershell
cd C:\Users\antho\OneDrive\Documents\GitHub\Crud-App

# Login to Azure
az login

# Create function app
az functionapp create `
  --resource-group $resourceGroup `
  --consumption-plan-name crud-app-func-plan `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --name my-task-app-functions `
  --storage-account $storageAccount `
  --os-type Linux
```

### Step 3: Add Configuration
```powershell
az functionapp config appsettings set `
  --resource-group $resourceGroup `
  --name my-task-app-functions `
  --settings `
    USE_AZURE="True" `
    AZURE_SQL_SERVER="your-server.database.windows.net" `
    AZURE_SQL_DATABASE="your-db" `
    AZURE_SQL_USERNAME="user" `
    AZURE_SQL_PASSWORD="pass" `
    AZURE_TENANT_ID="your-tenant-id" `
    AZURE_CLIENT_ID="your-client-id" `
    AZURE_CLIENT_SECRET="your-client-secret" `
    AZURE_REDIRECT_URI="https://my-task-app-functions.azurewebsites.net/api/callback" `
    JWT_SECRET="your-secret-key" `
    FLASK_SECRET_KEY="your-secret-key"
```

### Step 4: Deploy Code
```powershell
# Deploy from local project
func azure functionapp publish my-task-app-functions --build remote

# Or publish via Git:
git init
git add .
git commit -m "Serverless task manager"
git remote add azure https://my-task-app-functions.scm.azurewebsites.net/my-task-app-functions.git
git push azure main
```

### Step 5: Test
```powershell
# Get function URL
$funcUrl = az functionapp show --resource-group $resourceGroup --name my-task-app-functions --query defaultHostName -o tsv

# Test health
Invoke-WebRequest "https://$funcUrl/api/health"

# Get login URL
Invoke-WebRequest "https://$funcUrl/api/login"
```

---

## API Endpoints

All endpoints available at: `https://<your-function-app>.azurewebsites.net/api/`

```
Authentication:
  GET  /login           → Azure AD login redirect
  GET  /callback        → OAuth callback handler
  POST /refresh         → Refresh access token

Tasks:
  GET    /tasks                    → List all tasks
  POST   /tasks                    → Create task
  GET    /tasks/{id}               → Get specific task
  PUT    /tasks/{id}               → Update task
  DELETE /tasks/{id}               → Delete task
  PATCH  /tasks/{id}/status        → Update status

User:
  GET  /user/profile   → Get user info
  GET  /stats          → Get task statistics
  GET  /health         → Health check
```

---

## Architecture

```
User Request
    ↓
Azure Functions (Serverless)
    ├─ Authentication Handler (JWT)
    ├─ Task API Handlers
    └─ User Handlers
    ↓
Azure SQL Database (or SQLite)
    ↓
Response (JSON)
```

---

## Cost Structure

- **Execution**: First 1 million executions free per month
- **Storage**: $0.50 per GB/month
- **After free tier**: $0.20 per million requests

**Total cost**: ~$2-5/month for typical usage

---

## Local Development

```powershell
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run locally
func start

# Test locally
Invoke-WebRequest http://localhost:7071/api/health
```

---

## Monitor & Debug

```powershell
# View logs
az functionapp log tail --resource-group $resourceGroup --name my-task-app-functions

# View real-time logs
func azure functionapp logstream my-task-app-functions --build remote

# Check function status
az functionapp show --resource-group $resourceGroup --name my-task-app-functions
```

---

## File Structure

```
Crud-App/
├── function_app.py          ← Main serverless entry point
├── function_app.json        ← Function configuration
├── database.py              ← SQLAlchemy models (shared)
├── auth.py                  ← Azure AD & JWT (shared)
├── requirements.txt         ← Python dependencies
└── .env.example            ← Configuration template
```

---

## Key Differences from Flask

| Flask App Server | Azure Functions |
|---|---|
| Always running (costs 24/7) | Pay per execution |
| VM required | Serverless |
| Cold starts: ~5s | Cold starts: ~2s |
| Scale manually | Auto-scale to 0 |
| $12-20/month minimum | $0.20 per million requests |

---

## Troubleshooting

### "Deployment failed"
```powershell
# Verify storage account
az storage account list --resource-group $resourceGroup

# Recreate function app
az functionapp delete --resource-group $resourceGroup --name my-task-app-functions --yes
```

### "Function timeout"
Functions have 5-minute limit. Increase in `function_app.json`:
```json
"functionTimeout": "00:10:00"
```

### "Database connection failed"
Check firewall rules on Azure SQL:
```powershell
az sql server firewall-rule list --resource-group $resourceGroup --server-name <server>
```

### "Token validation fails"
Ensure `JWT_SECRET` and `FLASK_SECRET_KEY` are set in app settings

---

## Clean Up

```powershell
# Delete everything
az group delete --name crud-app-rg --yes

# Or keep resources, just delete function app
az functionapp delete --resource-group crud-app-rg --name my-task-app-functions --yes
```

---

## Next Steps

1. ✅ Code converted to Azure Functions
2. ✅ Serverless deployment ready
3. **TODO:** Add Application Insights monitoring
4. **TODO:** Set up automated CI/CD pipeline
5. **TODO:** Add email notifications
6. **TODO:** Create web dashboard

---

**Your app is now truly serverless - no VMs, infinite scalability!** 🚀
