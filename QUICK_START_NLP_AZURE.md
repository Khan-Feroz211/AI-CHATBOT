# 🚀 Implementation Complete: NLP, WhatsApp Testing & Azure Deployment

This guide covers the three new features just implemented for your AI Chatbot.

---

## 📊 What Was Added

### 1. **NLP Processing (CPU-Friendly)** ✨
No GPU required! Lightweight models that run on CPU.

**Features:**
- ✅ **Sentiment Analysis** - Detect positive/negative/neutral sentiments
- ✅ **Intent Classification** - Classify user intentions (greeting, help, command, etc.)
- ✅ **Named Entity Recognition (NER)** - Extract people, places, emails, phone numbers
- ✅ **Text Summarization** - Condense long text to key points
- ✅ **Keyword Extraction** - Find important keywords in text

**Models Used:**
- `distilbert-base-uncased-finetuned-sst-2-english` - Sentiment (lightweight, 67MB)
- `facebook/bart-large-mnli` - Intent Classification
- Auto-fallback to keyword/pattern matching if models unavailable

---

## 🧪 Quick Start

### Step 1: Update Dependencies

```bash
# Install all dependencies (including NLP packages)
pip install -r requirements.txt

# Takes ~5-10 minutes on first run, mostly downloading models
```

### Step 2: Verify Setup

```bash
# Run comprehensive verification
python setup_verification.py

# This will:
# ✓ Check Python version
# ✓ Install dependencies
# ✓ Test NLP processor
# ✓ Verify WhatsApp config
# ✓ Test imports
```

### Step 3: Start API Server

```bash
# Run the FastAPI server
python -m uvicorn src.api.main:app --reload --port 8000

# Visit http://localhost:8000/docs to see all endpoints
```

---

## 🧠 Using NLP Features

### Via FastAPI (Recommended for production)

The API now includes 6 NLP endpoints:

#### 1. **Sentiment Analysis**
```bash]
curl -X POST "http://localhost:8000/api/v1/nlp/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product! Its amazing!"}'

# Response:
{
  "label": "positive",
  "score": 0.9987,
  "status": "success"
}
```

#### 2. **Intent Classification**
```bash
curl -X POST "http://localhost:8000/api/v1/nlp/intent" \
  -H "Content-Type: application/json" \
  -d '{"text": "Can you help me with my order?"}'

# Response:
{
  "intent": "help",
  "confidence": 0.85,
  "sub_intents": ["question", "command"],
  "status": "success"
}
```

#### 3. **Entity Extraction**
```bash
curl -X POST "http://localhost:8000/api/v1/nlp/entities" \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact John Smith at john@example.com or 555-1234"}'

# Response:
{
  "entities": [
    {
      "entity": "john@example.com",
      "label": "EMAIL",
      "position": {"start": 23, "end": 40},
      "confidence": 0.95
    },
    {
      "entity": "555-1234",
      "label": "PHONE",
      "position": {"start": 44, "end": 52},
      "confidence": 0.90
    }
  ],
  "entity_count": 2,
  "status": "success"
}
```

#### 4. **Text Summarization**
```bash
curl -X POST "http://localhost:8000/api/v1/nlp/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[Long article text...]",
    "max_length": 150,
    "min_length": 50
  }'

# Response:
{
  "original_length": 2500,
  "summary": "Key points from the article...",
  "summary_length": 85,
  "compression_ratio": 29.41,
  "status": "success"
}
```

#### 5. **Keyword Extraction**
```bash
curl -X POST "http://localhost:8000/api/v1/nlp/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python is great for machine learning...",
    "num_keywords": 5
  }'

# Response:
{
  "keywords": [
    {"text": "python", "score": 1.0},
    {"text": "machine", "score": 0.67},
    {"text": "learning", "score": 0.67}
  ],
  "status": "success"
}
```

#### 6. **Comprehensive Analysis** (All-in-One)
```bash
curl -X POST "http://localhost:8000/api/v1/nlp/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I love the service! Please help with my order.",
    "include_sentiment": true,
    "include_intent": true,
    "include_entities": true,
    "include_keywords": true
  }'

# Response includes: sentiment, intent, entities, keywords
```

### Via Python Code

```python
from src.ml.nlp.processor import CPUFriendlyNLPProcessor

# Initialize
processor = CPUFriendlyNLPProcessor()

# Sentiment
sentiment = processor.analyze_sentiment("I love this!")
print(f"Sentiment: {sentiment.label} ({sentiment.score})")

# Intent
intent = processor.classify_intent("Can you help me?")
print(f"Intent: {intent.intent} ({intent.confidence})")

# Entities
entities = processor.extract_entities("Contact john@example.com")
for entity in entities:
    print(f"Found {entity.label}: {entity.entity}")

# Summary
summary = processor.summarize_text(long_text)
print(f"Summary: {summary.summary}")

# Keywords
keywords = processor.extract_keywords(text)
for word, score in keywords:
    print(f"{word}: {score}")
```

---

## 📱 WhatsApp Integration Testing

### Run Complete Test Suite

```bash
# Run all WhatsApp tests
python tests/test_whatsapp_integration.py

# Output shows:
# ✓ Configuration Check
# ✓ Webhook Verification
# ✓ Sandbox Mode Testing
# ✓ Message Formatting
# ✓ Phone Number Validation
# ✓ Rate Limiting
```

### What Gets Tested

1. **Configuration** - Verifies all WhatsApp credentials are set
2. **Webhook Challenge** - Tests webhook verification token
3. **Signature Verification** - Validates webhook signatures (production)
4. **Sandbox Mode** - Sends test messages in sandbox
5. **Message Formatting** - Tests emoji, special chars, long messages
6. **Phone Validation** - Validates phone number formats
7. **Rate Limiting** - Checks retry mechanisms

### Test Output Example

```
✓ Configuration Check
✓ Webhook Verification
✓ Sandbox Mode Test - Status: sandbox_queued
✓ Message Formatting Test - 500 char message passed
✓ Phone Number Validation - Pakistani numbers valid
✓ Rate Limiting Configured - Max retries: 3

Total: 7 tests
Passed: 7, Failed: 0, Errors: 0
```

### Manual WhatsApp Testing

1. **Setup WhatsApp Business Account**
   - Go to developer.facebook.com
   - Create app with WhatsApp product
   - Get Phone Number ID and Access Token

2. **Configure in .env**
```bash
WHATSAPP_ENABLED=true
WHATSAPP_SANDBOX_MODE=false
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-account-id
```

3. **Send Test Message**
```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to_phone": "923001234567",
    "message": "Hello from AI Chatbot!"
  }'
```

4. **Setup Webhook**
   - Set callback URL in Facebook Developer Console
   - Endpoint: `https://yourdomain.com/api/v1/whatsapp/webhook`
   - Verify Token: (set in .env as WHATSAPP_VERIFY_TOKEN)

---

## 🌐 Deploying to Azure

### Quick Overview

You have **3 deployment options**:

| Option | Best For | Cost | Setup Time |
|--------|----------|------|-----------|
| **Container Instances** | Testing/Dev | $0-50/mo | 10 min |
| **App Service** ⭐ | Production | $50-200+/mo | 20 min |
| **Kubernetes (AKS)** | Enterprise | $200+/mo | 60 min |

### Recommended: Azure App Service

#### Step 1: Login to Azure

```bash
az login
az account show
```

#### Step 2: Create Resources

```bash
# Create resource group
az group create --name chatbot-rg --location eastus

# Create container registry
az acr create --resource-group chatbot-rg \
  --name chatbotregistry --sku Basic

# Create App Service Plan
az appservice plan create --name chatbot-plan \
  --resource-group chatbot-rg --sku B2 --is-linux
```

#### Step 3: Build & Push Docker Image

```bash
# Build
docker build -t chatbot:latest .

# Tag
docker tag chatbot:latest chatbotregistry.azurecr.io/chatbot:latest

# Login to registry
az acr login --name chatbotregistry

# Push
docker push chatbotregistry.azurecr.io/chatbot:latest
```

#### Step 4: Create Web App

```bash
# Create web app
az webapp create --resource-group chatbot-rg \
  --plan chatbot-plan --name chatbot-app \
  --deployment-container-image-name chatbotregistry.azurecr.io/chatbot:latest

# Configure registry
az webapp config container set --name chatbot-app \
  --resource-group chatbot-rg \
  --docker-custom-image-name chatbotregistry.azurecr.io/chatbot:latest \
  --docker-registry-server-url https://chatbotregistry.azurecr.io \
  --docker-registry-server-user <username> \
  --docker-registry-server-password <password>
```

#### Step 5: Set Environment Variables

```bash
az webapp config appsettings set --name chatbot-app \
  --resource-group chatbot-rg --settings \
    ENVIRONMENT=production \
    WHATSAPP_SANDBOX_MODE=false \
    WEBSITES_PORT=8000 \
    WHATSAPP_ENABLED=true \
    WHATSAPP_ACCESS_TOKEN=your-token
```

#### Step 6: Get Your App URL

```bash
az webapp show --name chatbot-app --resource-group chatbot-rg \
  --query defaultHostName

# Output: chatbot-app.azurewebsites.net
# Access: https://chatbot-app.azurewebsites.net/docs
```

### View Logs

```bash
# Stream real-time logs
az webapp log tail --name chatbot-app --resource-group chatbot-rg

# Download logs
az webapp log download --name chatbot-app --resource-group chatbot-rg
```

---

## 🐳 Using Docker Compose for Local Testing

### Start All Services

```bash
# Development mode
docker-compose up

# Production mode
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chatbot-api
```

### Services Included

- **API** (Port 8000) - FastAPI server with NLP
- **Database** (PostgreSQL) - Data storage
- **Redis** (Port 6379) - Caching & sessions

---

## 📋 Files Added/Modified

### New Files
- ✅ `src/ml/nlp/processor.py` - NLP processor with all features
- ✅ `src/ml/nlp/__init__.py` - NLP module init
- ✅ `src/api/routes/nlp.py` - NLP API endpoints
- ✅ `tests/test_whatsapp_integration.py` - Complete WhatsApp test suite
- ✅ `setup_verification.py` - Setup & verification script
- ✅ `docs/AZURE_DEPLOYMENT_GUIDE.md` - Complete Azure guide
- ✅ `docker-compose.prod.yml` - Production Docker setup

### Modified Files
- ✅ `src/api/main.py` - Added NLP router
- ✅ `requirements.txt` - Added NLP dependencies

---

## 🔍 Troubleshooting

### NLP Models Download Slow?
Models (67-350MB each) download on first use. Options:
```bash
# Pre-download (optional)
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('distilbert-base-uncased')"
```

### WhatsApp Tests Failing?
```bash
# Check configuration
grep WHATSAPP .env

# Verify credentials in Facebook Developer Console
# Check webhook URL is correct
# Verify token matches
```

### Azure Deployment Issues?
```bash
# Check app logs
az webapp log tail --name chatbot-app --resource-group chatbot-rg

# Verify environment variables
az webapp config appsettings list --name chatbot-app --resource-group chatbot-rg

# Check container status
az container show --name chatbot-container --resource-group chatbot-rg
```

---

## 📈 Next Steps

1. ✅ Test NLP locally: `curl http://localhost:8000/docs`
2. ✅ Run WhatsApp tests: `python tests/test_whatsapp_integration.py`
3. ✅ Deploy to Azure: Follow Azure Deployment Guide
4. ✅ Setup webhooks: Configure WhatsApp webhooks in Facebook Developer Console
5. ✅ Monitor: Setup Azure Application Insights

---

## 📚 Resources

- **NLP Processor**: `src/ml/nlp/processor.py` (Full documentation)
- **WhatsApp Integration**: `src/services/whatsapp.py`
- **Azure Guide**: `docs/AZURE_DEPLOYMENT_GUIDE.md`
- **API Docs**: `http://localhost:8000/docs` (when running)

---

## ❓ Quick FAQ

**Q: Do I need a GPU for NLP?**
A: No! All models are CPU-optimized. Works great on CPU.

**Q: How long do models take to download?**
A: First run ~5-10 minutes. Then cached. Subsequent runs instant.

**Q: Can I use my own intent categories?**
A: Yes! Pass `custom_intents` parameter to `/api/v1/nlp/intent`.

**Q: How do I test WhatsApp without production credentials?**
A: Use `WHATSAPP_SANDBOX_MODE=true` in .env. No credentials needed!

**Q: Which Azure service should I use?**
A: App Service (B2 SKU) is best. ~$50/month, auto-scales, production-ready.

**Q: How do I monitor performance?**
A: Enable Application Insights. Setup alerts for CPU, memory, errors.

---

## 🎯 Summary

You now have:
✅ Production-ready NLP processing (CPU-friendly)
✅ Complete WhatsApp integration with tests
✅ Docker setup ready for Azure
✅ Comprehensive Azure deployment guide
✅ Setup verification script

Happy deploying! 🚀
