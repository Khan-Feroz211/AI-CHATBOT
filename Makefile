.PHONY: help install dev prod test lint format clean db-init db-seed run serve

help:
	@echo "WhatsApp Inventory Bot - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make venv         - Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run development server"
	@echo "  make serve        - Run production server (gunicorn)"
	@echo ""
	@echo "Database:"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-seed      - Populate test data"
	@echo "  make db-clean     - Drop all tables"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-int     - Run integration tests only"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters (flake8, pylint)"
	@echo "  make type         - Run type checker (mypy)"
	@echo "  make format       - Format code (black, isort)"
	@echo "  make check        - Run all checks (lint, type, format)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Remove cache files and build artifacts"
	@echo "  make logs         - Tail application logs"

venv:
	python -m venv .venv
	.venv/Scripts/activate
	@echo "Virtual environment created. Run: source .venv/bin/activate (Unix) or .venv\Scripts\activate (Windows)"

install: venv
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

dev:
	FLASK_ENV=development FLASK_DEBUG=True python -m flask run --port 5000

serve:
	gunicorn --worker-class sync --workers 4 --bind 0.0.0.0:8000 "src.main:create_app()"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated: htmlcov/index.html"

lint:
	flake8 src/
	pylint src/ --disable=R,C

type:
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

check: lint type
	@echo "All checks passed!"

db-init:
	python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.core.database import get_db; get_db().init_db(); print('Database initialized')"

db-seed:
	python scripts/setup/seed_data.py

db-clean:
	python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.core.database import get_db; get_db().drop_db(); print('Database cleaned')"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cache cleaned"

logs:
	tail -f data/logs/app.log

.DEFAULT_GOAL := help
