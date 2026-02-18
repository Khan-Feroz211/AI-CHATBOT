from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Chatbot ML"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 2
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./chatbot_data/chatbot.db"
    
    # Redis (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False
    
    # Vector Store
    VECTOR_STORE_PATH: str = "./data/vectors"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    USE_LOCAL_EMBEDDINGS: bool = True
    
    # Colab Integration
    COLAB_API_URL: Optional[str] = None
    COLAB_API_KEY: Optional[str] = None
    COLAB_ENABLED: bool = False
    COLAB_TIMEOUT: int = 300
    
    # Model Registry
    MODELS_PATH: str = "./models"
    LOCAL_MODELS_PATH: str = "./models/local"
    COLAB_MODELS_PATH: str = "./models/colab"
    DEFAULT_MODEL: str = "local-lightweight"
    
    # ML Pipeline (Local)
    USE_ONNX: bool = True
    MAX_SEQUENCE_LENGTH: int = 256
    BATCH_SIZE: int = 8
    
    # Device (will be set after import)
    DEVICE: str = "cpu"  # Default value
    
    # Async Tasks
    TASK_QUEUE_TYPE: str = "memory"
    TASK_RESULTS_TTL: int = 3600
    
    # Security
    SECRET_KEY: str = ""
    API_KEY_REQUIRED: bool = False
    
    # File Storage
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024
    STORAGE_PATH: str = "./data/uploads"

    # Payments (Pakistan)
    PAYMENT_SANDBOX_MODE: bool = True
    PAYMENT_WEBHOOK_SECRET: str = ""

    JAZZCASH_MERCHANT_ID: str = ""
    JAZZCASH_PASSWORD: str = ""
    JAZZCASH_INTEGRITY_SALT: str = ""
    JAZZCASH_RETURN_URL: str = ""
    JAZZCASH_WEBHOOK_SECRET: str = ""

    EASYPAISA_STORE_ID: str = ""
    EASYPAISA_HASH_KEY: str = ""
    EASYPAISA_RETURN_URL: str = ""
    EASYPAISA_WEBHOOK_SECRET: str = ""

    BANK_TRANSFER_BANK_NAME: str = ""
    BANK_TRANSFER_ACCOUNT_TITLE: str = ""
    BANK_TRANSFER_IBAN: str = ""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

# Create instance
settings = Settings()

if settings.ENVIRONMENT.lower() in {"production", "staging"} and not settings.SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production or staging environments")

# Create necessary directories
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(settings.LOCAL_MODELS_PATH, exist_ok=True)
os.makedirs(settings.COLAB_MODELS_PATH, exist_ok=True)
os.makedirs(settings.STORAGE_PATH, exist_ok=True)

# Device configuration (optional)
try:
    import torch
    if torch.cuda.is_available():
        settings.DEVICE = "cuda"
    elif hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        settings.DEVICE = "mps"
    else:
        settings.DEVICE = "cpu"
except ImportError:
    # Torch not installed, keep default "cpu"
    settings.DEVICE = "cpu"
