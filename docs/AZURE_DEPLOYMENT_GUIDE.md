# Azure Deployment Guide - Docker to Azure

## Overview
This guide covers deploying your AI Chatbot from Docker to Azure using multiple options.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option 1: Azure Container Instances (Serverless)](#option-1-azure-container-instances-serverless)
4. [Option 2: Azure App Service with Containers](#option-2-azure-app-service-with-containers)
5. [Option 3: Azure Kubernetes Service (AKS)](#option-3-azure-kubernetes-service-aks)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
```bash
# Install Azure CLI
# Windows: https://aka.ms/installazurecliwindows
# Or via PowerShell:
winget install Microsoft.AzureCLI

# Verify installation
az --version

# Install Docker Desktop
# https://www.docker.com/products/docker-desktop

# Install Docker buildx for multi-arch builds (optional)
docker buildx version
```

### Azure Setup
```bash
# Login to Azure
az login

# Check your subscriptions
az account list -o table

# Set your subscription (if you have multiple)
az account set --subscription "<subscription-id-or-name>"

# Check current context
az account show
```

---

## Deployment Options

### Quick Comparison

| Option | Cost | Scalability | Complexity | Best For |
|--------|------|-------------|-----------|----------|
| **Container Instances** | $0-50/month | Manual scaling | Simple | Dev/Test, low traffic |
| **App Service** | $50-200+/month | Auto-scaling | Medium | Production, consistent traffic |
| **AKS** | $200+/month + nodes | Excellent | High | Large scale, multi-container |

### Recommended: App Service (for most users)
- Full-managed service
- Auto-scaling available
- Good for your Docker setup
- Cost-effective for production

---

## Option 1: Azure Container Instances (Serverless)

**Best for**: Testing, dev environment, on-demand workloads

### Step 1: Create Registry

```bash
# Create Azure Container Registry
az acr create \
  --resource-group <your-resource-group> \
  --name <your-registry-name> \
  --sku Basic

# Get login credentials
az acr credential show \
  --name <your-registry-name> \
  --resource-group <your-resource-group>
```

### Step 2: Build and Push Image

```bash
# Build image locally
docker build -t chatbot:latest .

# Tag for Azure Registry
docker tag chatbot:latest <your-registry-name>.azurecr.io/chatbot:latest

# Login to registry
az acr login --name <your-registry-name>

# Push to Azure
docker push <your-registry-name>.azurecr.io/chatbot:latest

# Verify
az acr repository list --name <your-registry-name>
```

### Step 3: Deploy Container Instance

```bash
# Get registry credentials (needed for ACI)
az acr credential show \
  --name <your-registry-name> \
  --query "passwords[0].value" \
  --output tsv

# Deploy container
az container create \
  --resource-group <your-resource-group> \
  --name chatbot-container \
  --image <your-registry-name>.azurecr.io/chatbot:latest \
  --cpu 1 \
  --memory 1.5 \
  --registry-login-server <your-registry-name>.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --ip-address Public \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    WHATSAPP_SANDBOX_MODE=false
```

### Step 4: Monitor Container

```bash
# Get container status
az container show \
  --resource-group <your-resource-group> \
  --name chatbot-container \
  --query "containers[0].instanceView.currentState"

# View logs
az container logs \
  --resource-group <your-resource-group> \
  --name chatbot-container

# Test API
curl http://<public-ip>:8000/health
```

---

## Option 2: Azure App Service with Containers ⭐ RECOMMENDED

**Best for**: Production, consistent traffic, auto-scaling needed

### Step 1: Setup Resources

```bash
# Create resource group
az group create \
  --name chatbot-rg \
  --location eastus

# Create App Service Plan (Linux)
az appservice plan create \
  --name chatbot-plan \
  --resource-group chatbot-rg \
  --sku B2 \
  --is-linux

# Create Azure Container Registry
az acr create \
  --resource-group chatbot-rg \
  --name chatbotregistry \
  --sku Basic
```

### Step 2: Build and Push Image

```bash
# Build image
docker build -t chatbot:latest .

# Tag image
docker tag chatbot:latest chatbotregistry.azurecr.io/chatbot:latest

# Login to registry
az acr login --name chatbotregistry

# Push image
docker push chatbotregistry.azurecr.io/chatbot:latest
```

### Step 3: Create Web App

```bash
# Create Web App with Docker image
az webapp create \
  --resource-group chatbot-rg \
  --plan chatbot-plan \
  --name chatbot-app \
  --deployment-container-image-name chatbotregistry.azurecr.io/chatbot:latest

# Configure container registry
az webapp config container set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --docker-custom-image-name chatbotregistry.azurecr.io/chatbot:latest \
  --docker-registry-server-url https://chatbotregistry.azurecr.io \
  --docker-registry-server-user <username> \
  --docker-registry-server-password <password>
```

### Step 4: Configure Environment Variables

```bash
# Set environment variables
az webapp config appsettings set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --settings \
    ENVIRONMENT=production \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
    WHATSAPP_ENABLED=true \
    WHATSAPP_SANDBOX_MODE=false \
    WEBSITES_PORT=8000
```

### Step 5: Enable Continuous Deployment (Optional)

```bash
# Enable auto-deployment from registry
az webapp deployment container config \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --enable-continuous-deployment

# Get webhook URL
az webapp deployment container show \
  --name chatbot-app \
  --resource-group chatbot-rg
```

### Step 6: Views and Logs

```bash
# Get app URL
az webapp show \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --query defaultHostName

# View logs (real-time)
az webapp log tail \
  --name chatbot-app \
  --resource-group chatbot-rg

# Stream logs
az webapp up --logs
```

---

## Option 3: Azure Kubernetes Service (AKS)

**Best for**: High-scale, complex deployments, microservices

### Step 1: Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group chatbot-rg \
  --name chatbot-aks \
  --node-count 2 \
  --vm-set-type VirtualMachineScaleSets \
  --load-balancer-sku standard \
  --enable-managed-identity \
  --network-plugin azure

# Get credentials
az aks get-credentials \
  --resource-group chatbot-rg \
  --name chatbot-aks
```

### Step 2: Push Image to ACR

```bash
# Attach ACR to AKS
az aks update \
  --name chatbot-aks \
  --resource-group chatbot-rg \
  --attach-acr chatbotregistry
```

### Step 3: Deploy with Helm or kubectl

See [k8s-deployment.yaml](#kubernetes-deployment-config) below.

---

## Environment Configuration

### Create `.env.production` file

```bash
# Security
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>

# WhatsApp Configuration
WHATSAPP_ENABLED=true
WHATSAPP_SANDBOX_MODE=false
WHATSAPP_VERIFY_TOKEN=<your-verify-token>
WHATSAPP_APP_SECRET=<your-app-secret>
WHATSAPP_ACCESS_TOKEN=<your-access-token>
WHATSAPP_PHONE_NUMBER_ID=<your-phone-number-id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<your-business-account-id>

# Payment Configuration
PAYMENT_SANDBOX_MODE=false
JAZZCASH_MERCHANT_ID=<your-merchant-id>
JAZZCASH_PASSWORD=<your-password>

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Add Environment Variables to Azure

```bash
# Option 1: Using Azure CLI
az webapp config appsettings set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --settings \
    WHATSAPP_SANDBOX_MODE=false \
    PAYMENT_SANDBOX_MODE=false

# Option 2: Using Azure Portal
# 1. Navigate to your App Service
# 2. Click "Configuration" in left sidebar
# 3. Click "+ New application setting"
# 4. Add each variable
```

---

## Monitoring & Logs

### Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app chatbot-insights \
  --location eastus \
  --resource-group chatbot-rg \
  --application-type web

# Get instrumentation key
az monitor app-insights component show \
  --app chatbot-insights \
  --resource-group chatbot-rg \
  --query instrumentationKey
```

### View Logs

```bash
# Stream logs (real-time)
az webapp log tail \
  --name chatbot-app \
  --resource-group chatbot-rg

# Download logs
az webapp log download \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --log-file logs.zip
```

### Setup Alerts

```bash
# Create alert for failed requests
az monitor metrics alert create \
  --name chatbot-failed-requests \
  --resource-group chatbot-rg \
  --scopes "/subscriptions/<sub-id>/resourceGroups/chatbot-rg/providers/Microsoft.Web/sites/chatbot-app" \
  --condition "avg Total >= 10" \
  --description "Alert when failed requests exceed 10"
```

---

## Troubleshooting

### Container won't start

```bash
# Check container logs
az container logs \
  --resource-group chatbot-rg \
  --name chatbot-container

# Check for image pull errors
az container show \
  --resource-group chatbot-rg \
  --name chatbot-container \
  --query "containers[0].instanceView.events"
```

### HTTP 503 Service Unavailable

- Check if all environment variables are set
- Verify WhatsApp credentials are correct
- Check application logs for startup errors

### High Memory/CPU Usage

```bash
# Scale up App Service Plan
az appservice plan update \
  --name chatbot-plan \
  --sku P1V2
```

### Database Connection Issues

```bash
# Test database connection
# Add to your startup script:
python -c "import psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])"
```

---

## Cleanup

```bash
# Delete all resources
az group delete \
  --name chatbot-rg \
  --yes --no-wait
```

---

## Next Steps

1. ✅ Deploy to Azure
2. ✅ Setup WhatsApp webhook integration
3. ✅ Configure payment providers
4. ✅ Setup monitoring and alerts
5. ✅ Enable auto-scaling
6. ✅ Setup CI/CD pipeline

For questions or issues, check the [Troubleshooting](#troubleshooting) section.
