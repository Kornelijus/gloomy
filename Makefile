.PHONY: lint
lint:
	uv run ruff format --check
	uv run ruff check .
	uv run mypy .

.PHONY: lint-fix
lint-fix:
	uv run ruff format
	uv run ruff check --fix .

.PHONY: test
test:
	uv run pytest tests
