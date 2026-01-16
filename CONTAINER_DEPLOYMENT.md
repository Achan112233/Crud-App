# Deploy Flask App to Azure Container Instances (No VMs)

Your Flask app can run serverless on **Azure Container Instances** - auto-scaling containers with no VMs.

## Why Container Instances?

✅ **Serverless** - No VMs to manage  
✅ **Auto-scaling** - Scales to 0 when idle  
✅ **Docker-based** - Consistent environments  
✅ **Cheap** - ~$0.02/hour per container  
✅ **Fast** - Deploy in 2 minutes  

---

## Quick Deploy (5 minutes)

### Prerequisites

```powershell
# Install Docker Desktop
choco install docker-desktop

# Install Azure CLI
choco install azure-cli

# Login to Azure
az login
```

### Step 1: Build Docker Image

```powershell
cd C:\Users\antho\OneDrive\Documents\GitHub\Crud-App

# Build image
docker build -t crud-app:latest .

# Test locally
docker run -p 5000:5000 `
  -e USE_AZURE=False `
  -e FLASK_SECRET_KEY="test-secret" `
  -e AZURE_TENANT_ID="your-id" `
  -e AZURE_CLIENT_ID="your-id" `
  -e AZURE_CLIENT_SECRET="your-secret" `
  -e JWT_SECRET="your-secret" `
  crud-app:latest

# Visit: http://localhost:5000
```

### Step 2: Push to Docker Hub

```powershell
# Create Docker Hub account at hub.docker.com

# Tag image
docker tag crud-app:latest your-username/crud-app:latest

# Login to Docker Hub
docker login

# Push image
docker push your-username/crud-app:latest
```

### Step 3: Deploy to Azure Container Instances

```powershell
$resourceGroup = "crud-app-rg"
$containerName = "crud-app-container"
$image = "your-username/crud-app:latest"

# Create container
az container create `
  --resource-group $resourceGroup `
  --name $containerName `
  --image $image `
  --cpu 1 `
  --memory 1 `
  --ports 5000 `
  --protocol TCP `
  --environment-variables `
    USE_AZURE="True" `
    AZURE_SQL_SERVER="your-server.database.windows.net" `
    AZURE_SQL_DATABASE="your-database" `
    AZURE_SQL_USERNAME="user" `
    AZURE_SQL_PASSWORD="pass" `
    AZURE_TENANT_ID="your-tenant-id" `
    AZURE_CLIENT_ID="your-client-id" `
    AZURE_CLIENT_SECRET="your-client-secret" `
    AZURE_REDIRECT_URI="http://YOUR_PUBLIC_IP:5000/auth/callback" `
    JWT_SECRET="your-jwt-secret" `
    FLASK_SECRET_KEY="your-flask-secret"

# Get public IP
$publicIp = az container show --resource-group $resourceGroup --name $containerName --query ipAddress.ip --output tsv
echo "App running at: http://$publicIp:5000"
```

---

## Update AZURE_REDIRECT_URI

After getting the public IP, update your Azure AD app:

1. Go to [Azure Portal](https://portal.azure.com)
2. **Azure Active Directory** → **App registrations** → Your app
3. **Authentication** → Update Redirect URI to: `http://<public-ip>:5000/auth/callback`

---

## View Logs

```powershell
# View container logs
az container logs --resource-group $resourceGroup --name $containerName

# View real-time logs
az container attach --resource-group $resourceGroup --name $containerName
```

---

## Cost

- **First 5 minutes:** Free
- **Typical usage:** ~$15/month for 1 container running 24/7
- **On-demand:** Pay only when running (~$0.02/hour)

---

## Stop/Start Container

```powershell
# Stop container (free)
az container stop --resource-group $resourceGroup --name $containerName

# Start container
az container start --resource-group $resourceGroup --name $containerName

# Delete container (save cost)
az container delete --resource-group $resourceGroup --name $containerName --yes
```

---

## Upgrade to Multiple Replicas (Load Balancing)

For high traffic, scale to multiple containers:

```powershell
# Delete old container
az container delete --resource-group $resourceGroup --name $containerName --yes

# Create container group with 3 replicas
az container create `
  --resource-group $resourceGroup `
  --name $containerName `
  --image $image `
  --cpu 2 `
  --memory 2 `
  --ports 5000 `
  --protocol TCP `
  --environment-variables ... `
  --no-wait
```

---

## Alternative: Use Azure Container Registry

For production, store images in Azure Container Registry:

```powershell
# Create container registry
az acr create --resource-group $resourceGroup --name crudappregistry --sku Basic

# Login to ACR
az acr login --name crudappregistry

# Tag and push image
docker tag crud-app:latest crudappregistry.azurecr.io/crud-app:latest
docker push crudappregistry.azurecr.io/crud-app:latest

# Deploy from ACR
az container create `
  --resource-group $resourceGroup `
  --name $containerName `
  --image crudappregistry.azurecr.io/crud-app:latest `
  --registry-login-server crudappregistry.azurecr.io `
  --registry-username <username> `
  --registry-password <password> `
  ...
```

---

## Troubleshooting

### Container won't start
```powershell
az container logs --resource-group $resourceGroup --name $containerName
```

### Connection refused
- Check port is 5000 (not 80)
- Verify environment variables are set
- Check firewall allows traffic

### Database connection fails
- Verify Azure SQL firewall allows container IP
- Check connection string is correct
- Test credentials locally first

### ODBC driver not found
Already included in Dockerfile. If error persists:
```dockerfile
RUN apt-get install -y unixodbc-dev
```

---

## Cleanup

```powershell
# Delete everything
az group delete --name crud-app-rg --yes
```

---

## Your Setup

```
Local Development
    ↓ (Docker)
Build Docker Image
    ↓
Docker Hub / Azure Container Registry
    ↓
Azure Container Instances (Serverless)
    ↓
Flask App Running
```

No VMs, no management, true serverless! 🚀
