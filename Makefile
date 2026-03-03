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
	uv run pytest -m "not bench" --benchmark-disable

.PHONY: bench
bench:
	uv run pytest -m bench

.PHONY: bench-report
bench-report:
	uv run python scripts/bench_report.py