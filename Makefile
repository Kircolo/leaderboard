PYTHON ?= python3

.PHONY: install install-dev run lint test migrate

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .

test:
	pytest

migrate:
	alembic upgrade head

