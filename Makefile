.PHONY: help install test test-unit test-integration test-smoke coverage lint format type-check security clean docs run

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-smoke       Run smoke tests only"
	@echo "  coverage         Run tests with coverage report"
	@echo "  lint             Run all linting tools"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run mypy type checking"
	@echo "  security         Run security checks"
	@echo "  clean            Clean up generated files"
	@echo "  docs             Build documentation"
	@echo "  run              Run the application"

# Installation
install:
	poetry install

install-dev:
	poetry install --with dev,docs

# Testing
test:
	poetry run pytest

test-unit:
	poetry run pytest -m "unit or not integration"

test-integration:
	poetry run pytest -m integration

test-smoke:
	poetry run pytest -m smoke

test-parallel:
	poetry run pytest -n auto

test-verbose:
	poetry run pytest -v

# Coverage
coverage:
	poetry run pytest --cov --cov-report=html --cov-report=term

coverage-xml:
	poetry run pytest --cov --cov-report=xml

# Code Quality
lint: format type-check security
	poetry run flake8

format:
	poetry run black .
	poetry run isort .

format-check:
	poetry run black --check .
	poetry run isort --check-only .

type-check:
	poetry run mypy .

security:
	poetry run bandit -r . -f json -o reports/bandit.json
	poetry run safety check --json --output reports/safety.json

# Pre-commit
pre-commit-install:
	poetry run pre-commit install

pre-commit-run:
	poetry run pre-commit run --all-files

# Cleanup
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf reports
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	cd docs && poetry run sphinx-build -b html . _build/html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Application
run:
	poetry run streamlit run main_integrated.py

run-dev:
	poetry run streamlit run main_integrated.py --server.runOnSave=true

# CI/CD helpers
ci-test:
	poetry run pytest --junitxml=reports/junit.xml --cov --cov-report=xml

ci-quality:
	mkdir -p reports
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 --output-file=reports/flake8.txt
	poetry run mypy . --junit-xml=reports/mypy.xml
	poetry run bandit -r . -f json -o reports/bandit.json || true
	poetry run safety check --json --output reports/safety.json || true