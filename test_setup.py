"""
Test script to verify the ML architecture setup
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def log(message: str) -> None:
    """
    Print safely on Windows terminals that may not support emoji characters.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        ascii_message = (
            message.replace("✅", "[OK]")
            .replace("❌", "[ERROR]")
            .replace("📁", "[DIR]")
        )
        print(ascii_message)

print("=" * 50)
print("Testing AI Chatbot ML Architecture Setup")
print("=" * 50)

# Test 1: Import settings
try:
    from config.settings import settings
    log("✅ Successfully imported settings")
    log(f"   - App Name: {settings.APP_NAME}")
    log(f"   - Version: {settings.APP_VERSION}")
    log(f"   - Environment: {settings.ENVIRONMENT}")
    log(f"   - Device: {settings.DEVICE}")
except Exception as e:
    log(f"❌ Failed to import settings: {e}")

# Test 2: Test Local Embedder
try:
    from src.ml.local.embedder import LocalEmbedder
    log("✅ Successfully imported LocalEmbedder")
    
    # Create embedder instance
    embedder = LocalEmbedder()
    log("   - Created embedder instance")
    
    # Test embedding
    test_text = "Hello, how are you?"
    embedding = embedder.embed(test_text)
    log(f"   - Generated embedding of shape: {embedding.shape}")
    
    # Test similarity
    text2 = "Hi, how's it going?"
    similarity = embedder.similarity(test_text, text2)
    log(f"   - Similarity score: {similarity:.4f}")
    
except Exception as e:
    log(f"❌ Failed to test LocalEmbedder: {e}")

# Test 3: Check directories
log("\n📁 Checking directories:")

# We need to import settings again if it failed
try:
    from config.settings import settings
    
    directories = [
        settings.VECTOR_STORE_PATH,
        settings.LOCAL_MODELS_PATH,
        settings.COLAB_MODELS_PATH,
        settings.STORAGE_PATH,
        "./data/embeddings_cache"
    ]
    
    for directory in directories:
        path = Path(directory)
        if path.exists():
            log(f"✅ {directory} exists")
        else:
            log(f"❌ {directory} does not exist")
            # Create it
            path.mkdir(parents=True, exist_ok=True)
            log(f"   - Created {directory}")
            
except Exception as e:
    log(f"❌ Could not check directories: {e}")
    log("   Creating default directories...")
    
    # Create default directories
    default_dirs = [
        "./data/vectors",
        "./models/local",
        "./models/colab",
        "./data/uploads",
        "./data/embeddings_cache"
    ]
    
    for directory in default_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        log(f"✅ Created {directory}")

print("\n" + "=" * 50)
print("Setup test complete!")
print("=" * 50)
