.PHONY: help dev test lint format check

help:
	@echo "Available commands:"
	@echo "  make dev      - Start FastAPI development server"
	@echo "  make test     - Run pytest with service coverage"
	@echo "  make lint     - Run ruff linter and mypy type checks"
	@echo "  make format   - Format code with ruff"

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --cov=app.services -v

lint:
	ruff check app tests
	mypy app tests

format:
	ruff check --fix app tests
	ruff format app tests

check: lint test
