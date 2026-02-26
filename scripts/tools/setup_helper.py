# setup_helper.py
"""
Helper script to set up the project
Run: python setup_helper.py
"""

import os
import subprocess
import sys
from pathlib import Path


def print_step(step_num, message):
    print(f"\n📦 Step {step_num}: {message}")
    print("-" * 50)


def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success: {result.stdout[:200]}...")
    return True


def main():
    print("=" * 60)
    print("🤖 AI Chatbot ML - Setup Helper")
    print("=" * 60)

    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    python_version = sys.version_info
    print(
        f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    if python_version.major < 3 or (
        python_version.major == 3 and python_version.minor < 8
    ):
        print("❌ Python 3.8+ required")
        return
    print("✅ Python version OK")

    # Step 2: Upgrade pip
    print_step(2, "Upgrading pip and installing build tools")
    run_command(f"{sys.executable} -m pip install --upgrade pip setuptools wheel")

    # Step 3: Install requirements
    print_step(3, "Installing basic requirements")
    run_command(f"{sys.executable} -m pip install -r requirements-simple.txt")

    # Step 4: Create directories
    print_step(4, "Creating project directories")
    directories = [
        "config",
        "src/api/routers",
        "src/api/schemas",
        "src/ml/local",
        "src/ml/colab",
        "src/core",
        "src/services",
        "data/vectors",
        "data/uploads",
        "data/embeddings_cache",
        "models/local",
        "models/colab",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {directory}/")

    # Step 5: Create __init__.py files
    print_step(5, "Creating __init__.py files")
    for root, dirs, files in os.walk("src"):
        init_file = Path(root) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"✅ Created {init_file}")

    # Step 6: Test the setup
    print_step(6, "Running test script")
    run_command(f"{sys.executable} test_setup.py")

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Activate your virtual environment")
    print("2. Run: python test_setup.py")
    print("3. Start building your chatbot!")
    print("=" * 60)


if __name__ == "__main__":
    main()
