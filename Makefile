SHELL := /bin/bash
PYTHON ?= python3

.PHONY: install install-dev doctor infra-up infra-down bootstrap run dev lint test migrate clean

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

doctor:
	bash scripts/doctor.sh

infra-up:
	bash scripts/infra_up.sh

infra-down:
	bash scripts/infra_down.sh

bootstrap:
	bash scripts/bootstrap.sh

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev:
	bash scripts/bootstrap.sh
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .

test:
	pytest

migrate:
	alembic upgrade head

clean:
	bash scripts/clean.sh

