# Transform to ML Architecture - Automation Script
# Run this from your project root: .\transform_to_ml_architecture.ps1

Write-Host "=" -ForegroundColor Cyan
Write-Host "🚀 AI Chatbot - ML Architecture Transformation" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

# Check if Git is available
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Confirm transformation
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Backup current state" -ForegroundColor Yellow
Write-Host "  2. Create new ML architecture structure" -ForegroundColor Yellow
Write-Host "  3. Move existing files" -ForegroundColor Yellow
Write-Host "  4. Create configuration files" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Do you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "❌ Transformation cancelled" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "📦 Phase 1: Backup and Prepare" -ForegroundColor Green
Write-Host "-" * 50

# Backup current state
Write-Host "Creating backup..." -ForegroundColor Cyan
git add .
git commit -m "Backup before ML architecture transformation" -ErrorAction SilentlyContinue
git push origin main -ErrorAction SilentlyContinue

# Create backup branch
Write-Host "Creating backup branch..." -ForegroundColor Cyan
git checkout -b backup-before-ml-transform -ErrorAction SilentlyContinue
git push origin backup-before-ml-transform -ErrorAction SilentlyContinue
git checkout main

# Create transformation branch
Write-Host "Creating transformation branch..." -ForegroundColor Cyan
git checkout -b ml-architecture-transform

Write-Host "✅ Backup complete!" -ForegroundColor Green
Write-Host ""

# Phase 2: Create new structure
Write-Host "📁 Phase 2: Creating New Structure" -ForegroundColor Green
Write-Host "-" * 50

# Main directories
$mainDirs = @(
    "src",
    "config",
    "ml_experiments",
    "mlops",
    "tests",
    "models",
    "data",
    "requirements"
)

foreach ($dir in $mainDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# Src subdirectories
$srcDirs = @(
    "src/api",
    "src/api/routes",
    "src/api/middleware",
    "src/api/schemas",
    "src/core",
    "src/core/services",
    "src/ml",
    "src/ml/pipelines",
    "src/ml/models",
    "src/ml/features",
    "src/ml/serving",
    "src/ml/utils",
    "src/data",
    "src/data/models",
    "src/data/repositories",
    "src/data/cache",
    "src/data/storage",
    "src/ui",
    "src/ui/desktop",
    "src/ui/web",
    "src/utils"
)

foreach ($dir in $srcDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# ML experiments
$mlDirs = @(
    "ml_experiments/notebooks",
    "ml_experiments/experiments",
    "ml_experiments/datasets/raw",
    "ml_experiments/datasets/processed",
    "ml_experiments/datasets/features"
)

foreach ($dir in $mlDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# MLOps
$mlopsDirs = @(
    "mlops/docker",
    "mlops/kubernetes",
    "mlops/airflow/dags",
    "mlops/monitoring/prometheus",
    "mlops/monitoring/grafana"
)

foreach ($dir in $mlopsDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# Tests
$testDirs = @(
    "tests/unit/test_services",
    "tests/unit/test_models",
    "tests/unit/test_ml",
    "tests/integration/test_api",
    "tests/integration/test_pipelines",
    "tests/e2e"
)

foreach ($dir in $testDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# Data
$dataDirs = @(
    "data/databases",
    "data/uploads",
    "data/exports"
)

foreach ($dir in $dataDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# Models
$modelDirs = @(
    "models/intent_classifier",
    "models/priority_predictor",
    "models/sentiment_analyzer"
)

foreach ($dir in $modelDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

Write-Host "✅ Directory structure created!" -ForegroundColor Green
Write-Host ""

# Phase 3: Create __init__.py files
Write-Host "📝 Phase 3: Creating __init__.py Files" -ForegroundColor Green
Write-Host "-" * 50

Get-ChildItem -Path src, tests -Recurse -Directory | ForEach-Object {
    $initFile = Join-Path $_.FullName "__init__.py"
    if (!(Test-Path $initFile)) {
        New-Item -ItemType File -Path $initFile -Force | Out-Null
        Write-Host "  ✓ Created __init__.py in $($_.Name)" -ForegroundColor Gray
    }
}

Write-Host "✅ __init__.py files created!" -ForegroundColor Green
Write-Host ""

# Phase 4: Move existing files
Write-Host "📦 Phase 4: Moving Existing Files" -ForegroundColor Green
Write-Host "-" * 50

# Move desktop app
if (Test-Path "desktop/MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)") {
    Copy-Item -Path "desktop/MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)" -Destination "src/ui/desktop/app.py" -Force
    Write-Host "  ✓ Moved desktop app" -ForegroundColor Gray
}

# Move web files
if (Test-Path "web") {
    Copy-Item -Path "web/*" -Destination "src/ui/web/" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Moved web files" -ForegroundColor Gray
}

# Move database
if (Test-Path "chatbot_data/chatbot.db") {
    Copy-Item -Path "chatbot_data/chatbot.db" -Destination "data/databases/" -Force
    Write-Host "  ✓ Moved database" -ForegroundColor Gray
}

if (Test-Path "chatbot_data/uploads") {
    Copy-Item -Path "chatbot_data/uploads/*" -Destination "data/uploads/" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Moved uploads" -ForegroundColor Gray
}

Write-Host "✅ Files moved!" -ForegroundColor Green
Write-Host ""

# Phase 5: Create configuration files
Write-Host "⚙️  Phase 5: Creating Configuration Files" -ForegroundColor Green
Write-Host "-" * 50

# Create .env.example
$envExample = @"
# Application
APP_NAME=AI Chatbot ML
APP_VERSION=3.0.0
DEBUG=True

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatbot

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=change-this-in-production-use-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ML
MODEL_PATH=./models
FEATURE_STORE_PATH=./data/features

# Storage
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760
"@

$envExample | Out-File -FilePath ".env.example" -Encoding utf8
Write-Host "  ✓ Created .env.example" -ForegroundColor Gray

# Create config/settings.py
$settingsContent = @"
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "AI Chatbot ML"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/chatbot"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # ML
    MODEL_PATH: str = "./models"
    FEATURE_STORE_PATH: str = "./data/features"
    
    # Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"

settings = Settings()
"@

$settingsContent | Out-File -FilePath "config/settings.py" -Encoding utf8
Write-Host "  ✓ Created config/settings.py" -ForegroundColor Gray

# Create requirements/base.txt
$baseReqs = @"
# API Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy>=2.0.25
alembic>=1.13.0
psycopg2-binary>=2.9.9

# Cache
redis>=5.0.1

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.1
"@

$baseReqs | Out-File -FilePath "requirements/base.txt" -Encoding utf8
Write-Host "  ✓ Created requirements/base.txt" -ForegroundColor Gray

# Create requirements/ml.txt
$mlReqs = @"
# Deep Learning
torch>=2.1.2
transformers>=4.37.0

# ML Libraries
scikit-learn>=1.4.0
xgboost>=2.0.3
numpy>=1.26.3
pandas>=2.2.0

# ML Ops
mlflow>=2.10.0
evidently>=0.4.14
"@

$mlReqs | Out-File -FilePath "requirements/ml.txt" -Encoding utf8
Write-Host "  ✓ Created requirements/ml.txt" -ForegroundColor Gray

# Create setup.py
$setupContent = @"
from setuptools import setup, find_packages

setup(
    name="ai-chatbot-ml",
    version="3.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
)
"@

$setupContent | Out-File -FilePath "setup.py" -Encoding utf8
Write-Host "  ✓ Created setup.py" -ForegroundColor Gray

Write-Host "✅ Configuration files created!" -ForegroundColor Green
Write-Host ""

# Phase 6: Create starter files
Write-Host "🎨 Phase 6: Creating Starter Files" -ForegroundColor Green
Write-Host "-" * 50

# Create src/api/main.py
$apiMain = @"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Chatbot API",
    description="ML-powered task and note management",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Chatbot ML API", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
"@

$apiMain | Out-File -FilePath "src/api/main.py" -Encoding utf8
Write-Host "  ✓ Created src/api/main.py" -ForegroundColor Gray

# Create README update
$readmeContent = @"
# AI Chatbot - ML Workflow Architecture

Production-grade ML-powered chatbot with microservices architecture.

## 🚀 Quick Start

### Using Docker
``````bash
docker-compose up
``````

### Local Development
``````bash
# Install dependencies
pip install -e ".[dev,ml]"

# Copy environment variables
cp .env.example .env

# Run API server
uvicorn src.api.main:app --reload
``````

Visit: http://localhost:8000/docs

## 📁 Project Structure

``````
src/
├── api/          # REST API (FastAPI)
├── core/         # Business logic
├── ml/           # ML pipelines and models
├── data/         # Data layer
└── ui/           # User interfaces
``````

## 📚 Documentation

- [Architecture](docs/architecture/ML_WORKFLOW_ARCHITECTURE.md)
- [ML Diagrams](docs/architecture/ML_ARCHITECTURE_DIAGRAMS.md)
- [API Reference](docs/api/api_reference.md)

## 🧪 Testing

``````bash
pytest tests/
``````

## 📝 License

MIT License - See LICENSE file
"@

$readmeContent | Out-File -FilePath "README_NEW.md" -Encoding utf8
Write-Host "  ✓ Created README_NEW.md" -ForegroundColor Gray

Write-Host "✅ Starter files created!" -ForegroundColor Green
Write-Host ""

# Final summary
Write-Host "=" -ForegroundColor Cyan
Write-Host "✅ Transformation Complete!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review the new structure" -ForegroundColor White
Write-Host "  2. Copy .env.example to .env and configure" -ForegroundColor White
Write-Host "  3. Start refactoring code into new modules" -ForegroundColor White
Write-Host "  4. Test the API: uvicorn src.api.main:app --reload" -ForegroundColor White
Write-Host "  5. Commit changes: git add . && git commit" -ForegroundColor White
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "  - RESTRUCTURING_PLAN.md - Complete migration guide" -ForegroundColor White
Write-Host "  - ML_WORKFLOW_ARCHITECTURE.md - Architecture details" -ForegroundColor White
Write-Host "  - IMPLEMENTATION_GUIDE.md - Code examples" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Happy coding!" -ForegroundColor Green
