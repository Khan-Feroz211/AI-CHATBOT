# 🔄 Repository Restructuring Plan - ML Workflow Architecture

## Current Structure Analysis

Your current structure is:
```
project-assistant-bot/
├── desktop/                  # Desktop app code
├── web/                      # Web interface
├── docs/                     # Documentation
├── legacy/                   # Old versions
├── chatbot_data/            # SQLite database
└── Various root files
```

---

## Target ML Architecture Structure

```
project-assistant-bot/
├── README.md
├── LICENSE
├── .gitignore
├── setup.py
├── pyproject.toml
├── docker-compose.yml
│
├── config/                          # Configuration files
│   ├── __init__.py
│   ├── settings.py                  # Base settings
│   ├── development.py               # Dev config
│   ├── production.py                # Prod config
│   └── ml_config.yaml               # ML-specific configs
│
├── src/                             # Main source code
│   ├── __init__.py
│   │
│   ├── api/                         # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── dependencies.py          # Shared dependencies
│   │   │
│   │   ├── routes/                  # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── tasks.py
│   │   │   ├── notes.py
│   │   │   ├── chat.py
│   │   │   ├── files.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── middleware/              # API middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── logging.py
│   │   │   └── cors.py
│   │   │
│   │   └── schemas/                 # Pydantic models
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── task.py
│   │       ├── note.py
│   │       └── chat.py
│   │
│   ├── core/                        # Business logic
│   │   ├── __init__.py
│   │   │
│   │   ├── services/                # Service layer
│   │   │   ├── __init__.py
│   │   │   ├── base_service.py
│   │   │   ├── task_service.py
│   │   │   ├── note_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── file_service.py
│   │   │   ├── export_service.py
│   │   │   └── analytics_service.py
│   │   │
│   │   ├── orchestrator.py          # Workflow orchestration
│   │   └── events.py                # Event bus
│   │
│   ├── ml/                          # ML Pipeline
│   │   ├── __init__.py
│   │   │
│   │   ├── pipelines/               # ML pipelines
│   │   │   ├── __init__.py
│   │   │   ├── training_pipeline.py
│   │   │   ├── inference_pipeline.py
│   │   │   └── evaluation_pipeline.py
│   │   │
│   │   ├── models/                  # ML models
│   │   │   ├── __init__.py
│   │   │   ├── base_model.py
│   │   │   ├── intent_classifier.py
│   │   │   ├── priority_predictor.py
│   │   │   ├── sentiment_analyzer.py
│   │   │   ├── duration_estimator.py
│   │   │   └── response_generator.py
│   │   │
│   │   ├── features/                # Feature engineering
│   │   │   ├── __init__.py
│   │   │   ├── text_features.py
│   │   │   ├── user_features.py
│   │   │   ├── temporal_features.py
│   │   │   └── feature_store.py
│   │   │
│   │   ├── serving/                 # Model serving
│   │   │   ├── __init__.py
│   │   │   ├── model_server.py
│   │   │   ├── predictor.py
│   │   │   └── model_registry.py
│   │   │
│   │   └── utils/                   # ML utilities
│   │       ├── __init__.py
│   │       ├── preprocessing.py
│   │       ├── postprocessing.py
│   │       └── metrics.py
│   │
│   ├── data/                        # Data layer
│   │   ├── __init__.py
│   │   │
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── note.py
│   │   │   ├── conversation.py
│   │   │   └── file.py
│   │   │
│   │   ├── repositories/            # Data repositories
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── task_repository.py
│   │   │   ├── note_repository.py
│   │   │   └── conversation_repository.py
│   │   │
│   │   ├── cache/                   # Caching layer
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py
│   │   │
│   │   ├── storage/                 # File storage
│   │   │   ├── __init__.py
│   │   │   ├── local_storage.py
│   │   │   └── s3_storage.py
│   │   │
│   │   └── database.py              # DB connection
│   │
│   ├── ui/                          # User interfaces
│   │   ├── __init__.py
│   │   │
│   │   ├── desktop/                 # Desktop UI (Tkinter)
│   │   │   ├── __init__.py
│   │   │   ├── app.py               # Main desktop app
│   │   │   ├── components/
│   │   │   └── styles/
│   │   │
│   │   └── web/                     # Web UI (React/HTML)
│   │       ├── templates/
│   │       ├── static/
│   │       └── components/
│   │
│   └── utils/                       # Shared utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── metrics.py
│       ├── crypto.py
│       └── helpers.py
│
├── ml_experiments/                  # ML experimentation
│   ├── notebooks/                   # Jupyter notebooks
│   │   ├── 01_data_exploration.ipynb
│   │   ├── 02_feature_engineering.ipynb
│   │   ├── 03_model_training.ipynb
│   │   └── 04_model_evaluation.ipynb
│   │
│   ├── experiments/                 # Experiment tracking
│   │   └── configs/
│   │
│   └── datasets/                    # Training data
│       ├── raw/
│       ├── processed/
│       └── features/
│
├── mlops/                           # MLOps infrastructure
│   ├── docker/                      # Docker configs
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.ml
│   │   ├── Dockerfile.worker
│   │   └── docker-compose.yml
│   │
│   ├── kubernetes/                  # K8s manifests
│   │   ├── api-deployment.yaml
│   │   ├── ml-deployment.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── postgres-deployment.yaml
│   │   └── ingress.yaml
│   │
│   ├── airflow/                     # Airflow DAGs
│   │   └── dags/
│   │       ├── training_dag.py
│   │       └── inference_dag.py
│   │
│   └── monitoring/                  # Monitoring configs
│       ├── prometheus/
│       │   └── prometheus.yml
│       └── grafana/
│           └── dashboards/
│
├── tests/                           # Test suite
│   ├── __init__.py
│   │
│   ├── unit/                        # Unit tests
│   │   ├── test_services/
│   │   ├── test_models/
│   │   └── test_ml/
│   │
│   ├── integration/                 # Integration tests
│   │   ├── test_api/
│   │   └── test_pipelines/
│   │
│   └── e2e/                         # End-to-end tests
│       └── test_workflows/
│
├── scripts/                         # Utility scripts
│   ├── setup_db.py
│   ├── migrate_data.py
│   ├── train_models.py
│   ├── deploy.sh
│   └── seed_data.py
│
├── models/                          # Saved ML models
│   ├── intent_classifier/
│   │   ├── v1/
│   │   └── v2/
│   ├── priority_predictor/
│   └── metadata/
│
├── data/                            # Data storage
│   ├── databases/                   # SQLite files (dev)
│   ├── uploads/                     # User uploads
│   └── exports/                     # Export files
│
├── docs/                            # Documentation
│   ├── architecture/
│   │   ├── ML_WORKFLOW_ARCHITECTURE.md
│   │   ├── ML_ARCHITECTURE_DIAGRAMS.md
│   │   └── system_design.md
│   │
│   ├── api/
│   │   ├── api_reference.md
│   │   └── authentication.md
│   │
│   ├── ml/
│   │   ├── ml_pipeline.md
│   │   ├── feature_engineering.md
│   │   └── model_cards/
│   │
│   ├── deployment/
│   │   ├── docker_deployment.md
│   │   └── kubernetes_deployment.md
│   │
│   └── user_guides/
│       ├── quick_start.md
│       ├── user_manual.md
│       └── faq.md
│
├── legacy/                          # Old code (archived)
│   └── old_implementations/
│
└── requirements/                    # Dependencies
    ├── base.txt                     # Core dependencies
    ├── dev.txt                      # Development
    ├── prod.txt                     # Production
    └── ml.txt                       # ML-specific
```

---

## Migration Steps

### Phase 1: Backup and Prepare (30 minutes)

```powershell
# 1. Backup current state
git add .
git commit -m "Backup before ML architecture transformation"
git push origin main

# 2. Create backup branch
git checkout -b backup-before-ml-transform
git push origin backup-before-ml-transform
git checkout main

# 3. Create new branch for transformation
git checkout -b ml-architecture-transform
```

### Phase 2: Create New Structure (1 hour)

```powershell
# Create main directories
New-Item -ItemType Directory -Force -Path src, config, ml_experiments, mlops, tests, models, data

# Create src subdirectories
New-Item -ItemType Directory -Force -Path src/api, src/core, src/ml, src/data, src/ui, src/utils

# Create API structure
New-Item -ItemType Directory -Force -Path src/api/routes, src/api/middleware, src/api/schemas

# Create Core structure
New-Item -ItemType Directory -Force -Path src/core/services

# Create ML structure
New-Item -ItemType Directory -Force -Path src/ml/pipelines, src/ml/models, src/ml/features, src/ml/serving, src/ml/utils

# Create Data structure
New-Item -ItemType Directory -Force -Path src/data/models, src/data/repositories, src/data/cache, src/data/storage

# Create UI structure
New-Item -ItemType Directory -Force -Path src/ui/desktop, src/ui/web

# Create ML experiments structure
New-Item -ItemType Directory -Force -Path ml_experiments/notebooks, ml_experiments/experiments, ml_experiments/datasets

# Create MLOps structure
New-Item -ItemType Directory -Force -Path mlops/docker, mlops/kubernetes, mlops/airflow/dags, mlops/monitoring

# Create tests structure
New-Item -ItemType Directory -Force -Path tests/unit, tests/integration, tests/e2e

# Create models structure
New-Item -ItemType Directory -Force -Path models/intent_classifier, models/priority_predictor

# Create data structure
New-Item -ItemType Directory -Force -Path data/databases, data/uploads, data/exports

# Create requirements directory
New-Item -ItemType Directory -Force -Path requirements

# Create __init__.py files
Get-ChildItem -Path src -Recurse -Directory | ForEach-Object {
    New-Item -ItemType File -Path "$($_.FullName)/__init__.py" -Force
}
```

### Phase 3: Move Existing Code (1 hour)

```powershell
# Move desktop app
Copy-Item -Path "desktop/MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)" -Destination "src/ui/desktop/app.py"

# Move web files
Copy-Item -Path "web/*" -Destination "src/ui/web/" -Recurse

# Move documentation (reorganize)
Copy-Item -Path "docs/ML_WORKFLOW_ARCHITECTURE.md" -Destination "docs/architecture/"
Copy-Item -Path "docs/ML_ARCHITECTURE_DIAGRAMS.md" -Destination "docs/architecture/"
Copy-Item -Path "docs/PRO_FEATURES_GUIDE.md" -Destination "docs/user_guides/"
Copy-Item -Path "docs/QUICK_START.md" -Destination "docs/user_guides/"

# Move database
Copy-Item -Path "chatbot_data/chatbot.db" -Destination "data/databases/"
Copy-Item -Path "chatbot_data/uploads/*" -Destination "data/uploads/" -Recurse

# Move legacy code
Move-Item -Path "legacy/*" -Destination "legacy/old_implementations/" -Force

# Move scripts
Copy-Item -Path "scripts/*" -Destination "scripts/" -Force
```

### Phase 4: Create Configuration Files (30 minutes)

Create these new files:

**1. config/settings.py**
```python
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
    DB_POOL_SIZE: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
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
```

**2. requirements/base.txt**
```txt
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
hiredis>=2.3.2

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.1
```

**3. requirements/ml.txt**
```txt
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

# NLP
nltk>=3.8.1
spacy>=3.7.2
```

**4. docker-compose.yml**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: mlops/docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/chatbot
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./models:/app/models
      - ./data:/app/data
  
  ml-worker:
    build:
      context: .
      dockerfile: mlops/docker/Dockerfile.ml
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/chatbot
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./models:/app/models
      - ./data:/app/data
  
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=chatbot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**5. setup.py**
```python
from setuptools import setup, find_packages

setup(
    name="ai-chatbot-ml",
    version="3.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        line.strip()
        for line in open("requirements/base.txt")
        if line.strip() and not line.startswith("#")
    ],
    extras_require={
        "dev": [
            line.strip()
            for line in open("requirements/dev.txt")
            if line.strip() and not line.startswith("#")
        ],
        "ml": [
            line.strip()
            for line in open("requirements/ml.txt")
            if line.strip() and not line.startswith("#")
        ],
    },
    python_requires=">=3.8",
)
```

### Phase 5: Extract and Refactor Code (2-3 hours)

This is the most important step. Here's how to refactor your existing code:

**5.1 Extract Data Models**

From `MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)`, extract database models to `src/data/models/`:

```python
# src/data/models/user.py
from sqlalchemy import Column, String, Boolean, Integer
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
```

**5.2 Extract Services**

Move business logic to services:

```python
# src/core/services/task_service.py
from typing import List, Optional
from ...data.repositories.task_repository import TaskRepository
from ...data.models.task import Task

class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo
    
    def create_task(self, user_id: int, text: str, priority: str) -> Task:
        task_data = {
            "user_id": user_id,
            "text": text,
            "priority": priority,
        }
        return self.task_repo.create(task_data)
    
    def get_user_tasks(self, user_id: int) -> List[Task]:
        return self.task_repo.get_by_user(user_id)
```

**5.3 Create API Endpoints**

```python
# src/api/routes/tasks.py
from fastapi import APIRouter, Depends
from ..schemas.task import TaskCreate, TaskResponse
from ..dependencies import get_current_user, get_task_service

router = APIRouter()

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    current_user = Depends(get_current_user),
    task_service = Depends(get_task_service)
):
    return await task_service.create_task(current_user.id, task)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    current_user = Depends(get_current_user),
    task_service = Depends(get_task_service)
):
    return await task_service.get_user_tasks(current_user.id)
```

### Phase 6: Create ML Components (2-3 hours)

**6.1 Feature Engineering**

```python
# src/ml/features/text_features.py
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

class TextFeatureExtractor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModel.from_pretrained("distilbert-base-uncased")
        self.model.eval()
    
    def extract(self, text: str) -> dict:
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
            outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        
        return {
            "text_length": len(text),
            "word_count": len(text.split()),
            "embedding": embedding.tolist()
        }
```

**6.2 Model Training Pipeline**

```python
# src/ml/pipelines/training_pipeline.py
from ..models.intent_classifier import IntentClassifier
from ..features.text_features import TextFeatureExtractor
import mlflow

class TrainingPipeline:
    def __init__(self):
        self.feature_extractor = TextFeatureExtractor()
        self.model = IntentClassifier()
    
    def run(self, train_data, val_data):
        mlflow.start_run()
        
        # Extract features
        X_train = [self.feature_extractor.extract(text) for text in train_data]
        
        # Train model
        self.model.train(X_train, val_data)
        
        # Log metrics
        mlflow.log_metrics(self.model.evaluate(val_data))
        
        mlflow.end_run()
```

### Phase 7: Update Documentation (1 hour)

Update main README.md to reflect new structure:

```markdown
# AI Chatbot - ML Workflow Architecture

Production-grade ML-powered chatbot with microservices architecture.

## Quick Start

### Using Docker (Recommended)
```bash
docker-compose up
```

### Local Development
```bash
# Install dependencies
pip install -e ".[dev,ml]"

# Run database migrations
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload
```

## Architecture

See [Architecture Documentation](docs/architecture/ML_WORKFLOW_ARCHITECTURE.md)

## Project Structure

```
src/
├── api/          # REST API (FastAPI)
├── core/         # Business logic
├── ml/           # ML pipelines and models
├── data/         # Data layer
└── ui/           # User interfaces
```

## Development

- [Setup Guide](docs/deployment/development_setup.md)
- [API Documentation](docs/api/api_reference.md)
- [Contributing](docs/CONTRIBUTING.md)
```

### Phase 8: Testing (1-2 hours)

```powershell
# Create test files
New-Item -ItemType File -Path "tests/unit/test_services/test_task_service.py"
New-Item -ItemType File -Path "tests/integration/test_api/test_tasks_endpoint.py"

# Run tests
pytest tests/
```

### Phase 9: Commit and Deploy (30 minutes)

```powershell
# Stage changes
git add .

# Commit
git commit -m "Transform to ML workflow architecture

- Restructure to modular microservices design
- Separate API, Core, ML, and Data layers
- Add FastAPI REST API
- Implement repository pattern
- Add feature store and model registry
- Set up Docker and Kubernetes configs
- Add comprehensive testing
- Update documentation

Breaking changes:
- New project structure
- API endpoints changed
- Database schema updated
- Configuration format changed

Migration guide: docs/migration/v2_to_v3.md"

# Push
git push origin ml-architecture-transform

# Create pull request on GitHub
# Review and merge
```

---

## Migration Checklist

### Preparation
- [ ] Backup current code (git commit + branch)
- [ ] Document current features
- [ ] Export current database
- [ ] Test backup restore

### Structure
- [ ] Create new directory structure
- [ ] Move existing files
- [ ] Create __init__.py files
- [ ] Set up configuration files

### Code Refactoring
- [ ] Extract data models
- [ ] Create repositories
- [ ] Move business logic to services
- [ ] Create API endpoints
- [ ] Set up ML pipeline
- [ ] Create feature extractors

### Infrastructure
- [ ] Create Dockerfiles
- [ ] Set up docker-compose
- [ ] Create Kubernetes manifests
- [ ] Configure CI/CD

### Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write e2e tests
- [ ] Run test suite

### Documentation
- [ ] Update README
- [ ] Update architecture docs
- [ ] Create API documentation
- [ ] Write migration guide

### Deployment
- [ ] Test locally
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production

---

## Estimated Timeline

| Phase | Time | Complexity |
|-------|------|------------|
| Backup & Prepare | 30 min | Easy |
| Create Structure | 1 hour | Easy |
| Move Files | 1 hour | Easy |
| Configuration | 30 min | Medium |
| Code Refactoring | 2-3 hours | Hard |
| ML Components | 2-3 hours | Hard |
| Documentation | 1 hour | Medium |
| Testing | 1-2 hours | Medium |
| Deployment | 30 min | Medium |
| **Total** | **9-13 hours** | |

---

## Next Steps

1. **Review this plan** - Make sure you understand each step
2. **Start with Phase 1** - Backup everything
3. **Follow sequentially** - Don't skip steps
4. **Test frequently** - After each phase
5. **Document issues** - Keep notes of problems

Ready to start? Let me know which phase you'd like detailed code examples for!
