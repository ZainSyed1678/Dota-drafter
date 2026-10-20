.PHONY: help data train eval test lint up down clean

PYTHON ?= python

help:  ## Show this help message
	@echo "Dota Drafter - Development & Pipeline Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  data     Clean raw match dataset and prepare 5v5 records"
	@echo "  train    Train LightGBM model, shrink matrices, and fit combiner"
	@echo "  eval     Evaluate models with strict time-based splits (no leakage)"
	@echo "  test     Run pytest test suite on unit, leakage, and API tests"
	@echo "  lint     Run ruff linter on backend, ml_pipeline, and tests"
	@echo "  up       Build and run local services via Docker Compose"
	@echo "  down     Stop Docker Compose containers"
	@echo "  clean    Remove Python and build caches"

data:  ## Clean and prepare match dataset
	$(PYTHON) ml_pipeline/prepare_data.py --input tests/fixtures/matches_fixture.csv --output data/clean_matches.csv

train:  ## Train model pipeline with shrinkage and stacking
	$(PYTHON) ml_pipeline/train.py --input_csv tests/fixtures/matches_fixture.csv --output_dir backend/model --version v2.2.0

eval:  ## Evaluate model baselines on temporal splits
	$(PYTHON) ml_pipeline/evaluate.py --csv tests/fixtures/matches_fixture.csv --reports_dir ml_pipeline/reports

test:  ## Run comprehensive pytest test suite
	pytest tests/

lint:  ## Run ruff linter
	ruff check backend ml_pipeline tests scripts

up:  ## Build and start full stack with docker compose
	docker compose up --build

down:  ## Stop docker compose stack
	docker compose down

clean:  ## Clean temporary cache files
	rm -rf .pytest_cache .ruff_cache htmlcov **/__pycache__
