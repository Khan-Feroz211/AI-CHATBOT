.PHONY: help up down build logs shell test celery-logs flower migrate

help:
	@echo "BazaarBot available commands:"
	@echo "  make up           Start all 5 services"
	@echo "  make down         Stop all services"
	@echo "  make build        Rebuild images (no cache)"
	@echo "  make logs         Follow all service logs"
	@echo "  make celery-logs  Follow Celery worker logs"
	@echo "  make flower       Open Flower dashboard"
	@echo "  make migrate      Run DB migrations (alembic upgrade head)"
	@echo "  make test         Run all tests with coverage"
	@echo "  make shell        Open a shell in the app container"

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

celery-logs:
	docker-compose logs -f celery-worker

flower:
	open http://localhost:5555

migrate:
	docker-compose exec app alembic upgrade head

test:
	pytest tests/ -v --cov=bazaarbot \
	  --cov-report=term-missing

shell:
	docker-compose exec app /bin/bash
