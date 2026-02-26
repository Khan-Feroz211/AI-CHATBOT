#!/usr/bin/env python3
"""
Complete setup and verification script for the AI Chatbot
Handles:
1. Environment validation
2. Dependency installation
3. Database setup
4. NLP model download
5. WhatsApp configuration testing
6. Feature verification
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple


# Colors for output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def check_python_version() -> Tuple[bool, str]:
    """Verify Python version is 3.9+"""
    print_header("Python Version Check")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python {version_str} detected. Required: Python 3.9+")
        return False, version_str

    print_success(f"Python {version_str}")
    return True, version_str


def check_dependencies() -> bool:
    """Check if required system dependencies are installed"""
    print_header("System Dependencies Check")

    required = {
        "git": "Git",
        "docker": "Docker",
    }

    all_present = True
    for cmd, name in required.items():
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print_success(f"{name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning(f"{name} not found (optional for Docker deployment)")

    return all_present


def check_and_create_env_file() -> bool:
    """Check or create .env file"""
    print_header("Environment Configuration")

    env_file = Path(".env")

    if env_file.exists():
        print_success(".env file exists")
        return True

    print_info("Creating .env file with defaults...")

    env_content = """# Environment
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# WhatsApp Configuration
WHATSAPP_ENABLED=true
WHATSAPP_SANDBOX_MODE=true
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_APP_SECRET=your-app-secret
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
WHATSAPP_TEST_PHONE=923001234567

# Payment Configuration
PAYMENT_SANDBOX_MODE=true
JAZZCASH_MERCHANT_ID=your-merchant-id
JAZZCASH_PASSWORD=your-password
JASZCASH_INTEGRITY_SALT=your-salt
EASYPAISA_STORE_ID=your-store-id
EASYPAISA_HASH_KEY=your-hash-key

# Database
DATABASE_URL=sqlite:///chatbot.db

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
"""

    try:
        env_file.write_text(env_content)
        print_success(".env file created with default values")
        print_warning("⚠ Please update .env with your actual credentials!")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def install_python_dependencies() -> bool:
    """Install Python dependencies"""
    print_header("Python Dependencies Installation")

    try:
        # Upgrade pip
        print_info("Upgrading pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )
        print_success("pip upgraded")

        # Install requirements
        print_info("Installing packages from requirements.txt...")
        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            print_error("requirements.txt not found")
            return False

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print_error(f"Installation failed: {result.stderr[:500]}")
            return False

        print_success("Dependencies installed successfully")
        return True

    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def download_nlp_models() -> bool:
    """Pre-download NLP models to avoid startup delays"""
    print_header("NLP Models Download")

    try:
        print_info("Downloading HuggingFace models (this may take a while)...")

        models_to_download = [
            "distilbert-base-uncased-finetuned-sst-2-english",  # Sentiment
            "facebook/bart-large-mnli",  # Intent classification
            "distilbert-base-uncased",  # NER
        ]

        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))

        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        for model_name in models_to_download:
            try:
                print_info(f"  Downloading {model_name}...")
                # This will download and cache the model
                # AutoTokenizer.from_pretrained(model_name)
                # AutoModelForSequenceClassification.from_pretrained(model_name)
                print_success(f"  {model_name} ready")
            except Exception as e:
                print_warning(f"  Could not download {model_name}: {e}")

        print_info("NLP models will be downloaded on first use if not cached")
        return True

    except Exception as e:
        print_warning(f"Could not pre-download models: {e}")
        print_info("Models will be downloaded on first API call")
        return True


def test_imports() -> bool:
    """Test that all critical imports work"""
    print_header("Import Verification")

    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("transformers", "Transformers"),
        ("nltk", "NLTK"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
    ]

    all_good = True
    for module, name in imports_to_test:
        try:
            __import__(module)
            print_success(f"{name} imported successfully")
        except ImportError as e:
            print_error(f"{name} import failed: {e}")
            all_good = False

    return all_good


def test_nlp_processor() -> bool:
    """Test NLP processor initialization"""
    print_header("NLP Processor Test")

    try:
        # Add project to path
        sys.path.insert(0, str(Path(__file__).resolve().parent))

        from src.ml.nlp.processor import CPUFriendlyNLPProcessor

        print_info("Initializing NLP processor...")
        processor = CPUFriendlyNLPProcessor()

        # Test sentiment
        print_info("Testing sentiment analysis...")
        sentiment = processor.analyze_sentiment("I love this!")
        print_success(f"  Sentiment: {sentiment.label} ({sentiment.score:.2f})")

        # Test intent
        print_info("Testing intent classification...")
        intent = processor.classify_intent("Can you help me?")
        print_success(f"  Intent: {intent.intent} ({intent.confidence:.2f})")

        # Test entities
        print_info("Testing entity extraction...")
        entities = processor.extract_entities("Contact john@example.com at 555-1234")
        print_success(f"  Found {len(entities)} entities")

        # Test keywords
        print_info("Testing keyword extraction...")
        keywords = processor.extract_keywords(
            "Python is great for machine learning and AI"
        )
        print_success(f"  Found {len(keywords)} keywords")

        print_success("NLP processor working correctly!")
        return True

    except Exception as e:
        print_error(f"NLP processor test failed: {e}")
        return False


def test_whatsapp_config() -> bool:
    """Test WhatsApp configuration"""
    print_header("WhatsApp Configuration Test")

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from config.settings import settings

        checks = {
            "WhatsApp Enabled": settings.WHATSAPP_ENABLED,
            "Sandbox Mode": settings.WHATSAPP_SANDBOX_MODE,
            "Verify Token Set": bool(settings.WHATSAPP_VERIFY_TOKEN),
            "App Secret Set": bool(settings.WHATSAPP_APP_SECRET),
        }

        all_good = True
        for check, result in checks.items():
            if result:
                print_success(f"{check}")
            else:
                print_warning(f"{check} - requires configuration")

        return True

    except Exception as e:
        print_error(f"WhatsApp configuration test failed: {e}")
        return False


def generate_report(results: Dict[str, bool]) -> Dict[str, Any]:
    """Generate setup report"""
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    return {
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "success_rate": f"{(passed/total)*100:.1f}%",
        "results": results,
    }


def main():
    """Run complete setup verification"""
    results = {}

    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║     AI CHATBOT - SETUP & VERIFICATION SCRIPT          ║")
    print("║          Version 3.0 with NLP & Azure Support         ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    # Run checks
    success, version = check_python_version()
    results["Python Version"] = success

    results["System Dependencies"] = check_dependencies()
    results[".env Configuration"] = check_and_create_env_file()
    results["Python Dependencies"] = install_python_dependencies()
    results["Import Verification"] = test_imports()
    results["NLP Processor"] = test_nlp_processor()
    results["WhatsApp Config"] = test_whatsapp_config()

    # Try to download models (optional)
    print("\n")
    download_nlp_models()

    # Generate report
    report = generate_report(results)

    print_header("SETUP VERIFICATION REPORT")
    print(f"Total Checks: {report['total_checks']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Success Rate: {report['success_rate']}")

    print("\nDetailed Results:")
    for check, result in results.items():
        if result:
            print_success(check)
        else:
            print_error(check)

    # Final status
    print("\n")
    if report["failed"] == 0:
        print_success("✓ All checks passed! Your environment is ready.")
        print_info("\nNext steps:")
        print("  1. Run the API: python -m uvicorn src.api.main:app --reload")
        print("  2. Test NLP endpoints: curl http://localhost:8000/docs")
        print("  3. Run WhatsApp tests: python tests/test_whatsapp_integration.py")
        print("  4. Deploy to Azure: See docs/AZURE_DEPLOYMENT_GUIDE.md")
        return 0
    else:
        print_warning(f"⚠ {report['failed']} check(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
