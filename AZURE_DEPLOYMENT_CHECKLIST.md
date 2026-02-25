# ☁️ Azure Deployment Checklist

Complete this checklist before deploying your AI Chatbot to Azure.

## 📋 Pre-Deployment Checklist

### 1. Azure Account & CLI
- [ ] Azure subscription active
- [ ] Azure CLI installed (`az --version` works)
- [ ] Logged in to Azure (`az login` successful)
- [ ] Correct subscription selected (`az account show`)

### 2. Local Testing
- [ ] Run `python setup_verification.py` - all checks pass
- [ ] Start API locally: `python -m uvicorn src.api.main:app --reload`
- [ ] Test NLP endpoints: http://localhost:8000/docs
- [ ] Run WhatsApp tests: `python tests/test_whatsapp_integration.py`
- [ ] API health check: `curl http://localhost:8000/health`

### 3. Docker Setup
- [ ] Docker Desktop installed
- [ ] Docker running (`docker ps` works)
- [ ] Build image: `docker build -t chatbot:latest .`
- [ ] Run locally: `docker run -p 8000:8000 chatbot:latest`
- [ ] Test: `curl http://localhost:8000/health`

### 4. Environment Configuration
- [ ] `.env` file created with all required variables
- [ ] `WHATSAPP_VERIFY_TOKEN` generated (random string)
- [ ] `WHATSAPP_APP_SECRET` obtained from Facebook
- [ ] `SECRET_KEY` generated (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `PAYMENT_SANDBOX_MODE=false` for production
- [ ] Database URL configured (if using external DB)

### 5. Azure Resource Group
- [ ] Resource group created: `az group create --name chatbot-rg --location eastus`
- [ ] Verified in Portal: https://portal.azure.com

---

## 🏗️ Deployment Steps

### Step 1: Create Azure Container Registry (2 min)

```bash
# Create registry
az acr create \
  --resource-group chatbot-rg \
  --name chatbotregistry \
  --sku Basic

# Enable admin for push
az acr update -n chatbotregistry --admin-enabled true

# Get credentials
az acr credential show --name chatbotregistry

# Save username and password
```

**CheckPoint:**
- [ ] Registry created
- [ ] Admin credentials obtained

---

### Step 2: Build & Push Docker Image (5-10 min)

```bash
# Build image
docker build -t chatbot:latest .

# Tag for Azure registry
docker tag chatbot:latest chatbotregistry.azurecr.io/chatbot:latest

# Login to Azure registry
az acr login --name chatbotregistry

# Push to Azure
docker push chatbotregistry.azurecr.io/chatbot:latest

# Verify push
az acr repository list --name chatbotregistry
```

**CheckPoint:**
- [ ] Docker image building completes
- [ ] Image pushed to registry
- [ ] Repository list shows `chatbot`

---

### Step 3: Create App Service Plan (2 min)

```bash
# Create plan (B2 = ~$50/month, auto-scales)
az appservice plan create \
  --name chatbot-plan \
  --resource-group chatbot-rg \
  --sku B2 \
  --number-of-workers 1 \
  --is-linux

# Verify
az appservice plan show -n chatbot-plan -g chatbot-rg
```

**CheckPoint:**
- [ ] Plan created with B2 SKU
- [ ] Provisioning state is "Succeeded"

---

### Step 4: Create Web App (3 min)

```bash
# Create web app
az webapp create \
  --resource-group chatbot-rg \
  --plan chatbot-plan \
  --name chatbot-app \
  --deployment-container-image-name chatbotregistry.azurecr.io/chatbot:latest

# Verify
az webapp show -n chatbot-app -g chatbot-rg --query state
```

**CheckPoint:**
- [ ] Web app created
- [ ] State is "Running"

---

### Step 5: Configure Container Registry (2 min)

```bash
# Get registry credentials
REGISTRY_USERNAME=$(az acr credential show --name chatbotregistry --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name chatbotregistry --query passwords[0].value -o tsv)

# Configure app to use registry
az webapp config container set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --docker-custom-image-name chatbotregistry.azurecr.io/chatbot:latest \
  --docker-registry-server-url https://chatbotregistry.azurecr.io \
  --docker-registry-server-user "$REGISTRY_USERNAME" \
  --docker-registry-server-password "$REGISTRY_PASSWORD"
```

**CheckPoint:**
- [ ] Registry credentials configured
- [ ] No errors in output

---

### Step 6: Set Environment Variables (5 min)

```bash
# Set critical environment variables
az webapp config appsettings set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --settings \
    ENVIRONMENT=production \
    DEBUG=false \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
    WEBSITES_PORT=8000 \
    WHATSAPP_ENABLED=true \
    WHATSAPP_SANDBOX_MODE=false \
    WHATSAPP_VERIFY_TOKEN="your-verify-token" \
    WHATSAPP_APP_SECRET="your-app-secret" \
    WHATSAPP_ACCESS_TOKEN="your-access-token" \
    WHATSAPP_PHONE_NUMBER_ID="your-phone-id" \
    PAYMENT_SANDBOX_MODE=false

# Verify settings
az webapp config appsettings list -n chatbot-app -g chatbot-rg
```

**CheckPoint:**
- [ ] All variables listed in output
- [ ] No "InvalidParameterSyntax" errors

---

### Step 7: Wait for Deployment (5-10 min)

```bash
# Check deployment status
az webapp show -n chatbot-app -g chatbot-rg --query "state, availabilityState"

# Wait until state is "Running"
```

**CheckPoint:**
- [ ] State: "Running"
- [ ] Availability: "Normal"

---

### Step 8: Get Your App URL

```bash
# Get the URL
CHATBOT_URL=$(az webapp show \
  -n chatbot-app \
  -g chatbot-rg \
  --query defaultHostName -o tsv)

echo "Your chatbot is at: https://$CHATBOT_URL"

# Test it
curl https://$CHATBOT_URL/health

# Open in browser
# https://$CHATBOT_URL/docs
```

**CheckPoint:**
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Swagger docs load at `/docs`

---

## ✅ Post-Deployment Verification

### 1. Test Health Endpoint
```bash
curl https://chatbot-app.azurewebsites.net/health
# Should return: {"status": "healthy", "service": "api"}
```
- [ ] Health check passes

### 2. Test NLP Endpoints
```bash
# Sentiment analysis
curl -X POST "https://chatbot-app.azurewebsites.net/api/v1/nlp/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this!"}'

# Should return sentiment analysis
```
- [ ] Sentiment endpoint works
- [ ] Intent endpoint works
- [ ] Other NLP endpoints work

### 3. Check Logs
```bash
# Stream logs
az webapp log tail -n chatbot-app -g chatbot-rg

# Should show successful startup logs
```
- [ ] No error messages in logs
- [ ] Logs show server started

### 4. Test WhatsApp Integration
```bash
# Send test message (if configured)
curl -X POST "https://chatbot-app.azurewebsites.net/api/v1/whatsapp/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to_phone": "923001234567",
    "message": "Test from Azure!"
  }'
```
- [ ] Message sends successfully
- [ ] Webhook configured in Facebook Developer Console

### 5. Setup Monitoring (Optional)
```bash
# Create Application Insights
az monitor app-insights component create \
  --app chatbot-insights \
  --location eastus \
  --resource-group chatbot-rg

# Link to web app
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app chatbot-insights \
  --resource-group chatbot-rg \
  --query instrumentationKey -o tsv)

az webapp config appsettings set \
  --name chatbot-app \
  --resource-group chatbot-rg \
  --settings APPINSIGHTS_INSTRUMENTATION_KEY=$INSTRUMENTATION_KEY
```
- [ ] Application Insights created
- [ ] Linked to web app

---

## 🔧 Troubleshooting

### Issue: Container won't start

```bash
# Check logs
az webapp log tail -n chatbot-app -g chatbot-rg

# Common causes:
# 1. Missing environment variables - add them
# 2. Port not 8000 - ensure WEBSITES_PORT=8000 is set
# 3. Missing dependencies - rebuild Docker image
```

### Issue: 503 Service Unavailable

```bash
# Check app status
az webapp show -n chatbot-app -g chatbot-rg --query "state, availabilityState"

# Check if app crashed
az webapp log tail -n chatbot-app -g chatbot-rg | tail -20

# Restart app
az webapp restart -n chatbot-app -g chatbot-rg
```

### Issue: NLP endpoints fail

```bash
# Check if dependencies installed
# Rebuild and push new image
docker build -t chatbot:latest .
docker push chatbotregistry.azurecr.io/chatbot:latest

# Restart web app to pull new image
az webapp restart -n chatbot-app -g chatbot-rg
```

### Issue: WhatsApp not working

```bash
# Verify environment variables
az webapp config appsettings list -n chatbot-app -g chatbot-rg | grep WHATSAPP

# Test locally with production credentials
# Then deploy again
```

---

## 💰 Cost Optimization

### Current Setup Costs
- **App Service Plan (B2)**: ~$50/month
- **Container Registry**: ~$5/month
- **Data Transfer**: Variable (usually $0-20/month)
- **Total**: ~$55-75/month

### To Reduce Costs
```bash
# Use B1 plan instead of B2 (~$25/month)
az appservice plan update \
  --name chatbot-plan \
  --resource-group chatbot-rg \
  --sku B1

# Or use Container Instances for dev/test
az container create \
  --resource-group chatbot-rg \
  --name chatbot-dev \
  --image chatbotregistry.azurecr.io/chatbot:latest \
  --cpu 1 --memory 1.5
```

---

## 🔐 Security Checklist

### Before Going Live
- [ ] `DEBUG=false` in production
- [ ] `SECRET_KEY` is strong (32+ characters)
- [ ] No credentials in `.env` file (use Azure Key Vault)
- [ ] HTTPS only (automatic with azurewebsites.net)
- [ ] CORS configured properly
- [ ] WhatsApp webhook signature verification enabled
- [ ] Rate limiting enabled for API endpoints
- [ ] Database has regular backups

### Add Azure Key Vault (Recommended)

```bash
# Create key vault
az keyvault create \
  --resource-group chatbot-rg \
  --name chatbot-vault

# Add secret
az keyvault secret set \
  --vault-name chatbot-vault \
  --name whatsapp-access-token \
  --value "your-token"

# Reference in app (handled by Azure automatically)
```

---

## 📈 Scaling

### Enable Auto-Scaling

```bash
# Create auto-scale rule
az monitor autoscale create \
  --name chatbot-autoscale \
  --resource-group chatbot-rg \
  --resource chatbot-plan \
  --resource-type "Microsoft.Web/serverfarms" \
  --min-count 1 \
  --max-count 5 \
  --count 2
```

### Monitor CPU & Memory

```bash
# View metrics
az monitor metrics list \
  --resource chatbot-app \
  --resource-group chatbot-rg \
  --metric "CpuPercentage"
```

---

## 🧹 Cleanup

### Remove All Resources (Delete Everything)

```bash
# Delete entire resource group
az group delete \
  --name chatbot-rg \
  --yes \
  --no-wait

# This deletes:
# ✓ Web app
# ✓ App Service plan
# ✓ Container registry
# ✓ All associated resources
```

**WARNING**: This is irreversible!

---

## 📞 Support Resources

- **Azure Documentation**: https://docs.microsoft.com/azure/app-service/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **WhatsApp API**: https://developers.facebook.com/docs/whatsapp
- **Our GitHub**: [Your Repo URL]

---

## ✨ Congratulations!

Your AI Chatbot with NLP is now running on Azure! 🎉

Next steps:
1. ✅ Share the URL: https://chatbot-app.azurewebsites.net
2. ✅ Integrate with WhatsApp: Set webhook in Facebook Developer Console
3. ✅ Monitor with Application Insights
4. ✅ Setup CI/CD pipeline for automatic deployments
5. ✅ Configure custom domain (optional)

Happy chatting! 🚀
