.PHONY: install run test lint format docker-up

install:
	uv sync --all-extras

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

docker-up:
	docker compose up --build

