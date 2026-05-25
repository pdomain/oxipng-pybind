export PATH := $(HOME)/.cargo/bin:$(PATH)

AI ?=
LOG := .ci-ai.log

ifdef AI
_goals := $(or $(MAKECMDGOALS),ci)
.PHONY: $(_goals)
$(_goals):
	@rm -f $(LOG)
	@$(MAKE) --no-print-directory AI= $@ > $(LOG) 2>&1 \
		&& echo "$@ passed (log: $(LOG))" \
		|| (echo "$@ failed:"; uv run scripts/ai_filter_log.py $(LOG); echo "(full log: $(LOG))"; exit 1)

else

.PHONY: help setup develop test test-rust test-py lint lint-fix py-lint py-lint-fix \
	rust-lint rust-lint-fix md-lint md-lint-fix format format-check typecheck \
	rust-deny pre-commit-check build wheel clean clean-cache reset remove-venv \
	upgrade-deps ci

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

setup: ## Sync deps, build editable extension, and install pre-commit hooks
	uv sync --group dev
	uv run maturin develop
	uv run pre-commit install

develop: ## Build and install the editable extension
	uv run maturin develop

test: test-rust test-py ## Run all tests

test-rust: ## Run Rust tests
	cargo test

test-py: ## Run Python tests against editable extension
	uv run maturin develop --quiet
	uv run pytest -v -ra -n auto

lint: rust-lint py-lint md-lint ## Run all lint checks

lint-fix: rust-lint-fix py-lint-fix md-lint-fix ## Apply automatic lint fixes

rust-lint: ## Run cargo clippy
	cargo clippy --workspace --all-targets -- -D warnings

rust-lint-fix: ## Run cargo clippy --fix
	cargo clippy --workspace --all-targets --fix --allow-dirty --allow-staged -- -D warnings

py-lint: ## Run ruff check
	uv run ruff check .

py-lint-fix: ## Run ruff format and ruff check --fix
	uv run ruff format
	uv run ruff check --fix .

md-lint: ## Run markdownlint via pre-commit
	uv run pre-commit run markdownlint-cli2 --all-files

md-lint-fix: ## Run markdownlint auto-fix via pre-commit
	@echo "No markdownlint auto-fix hook is configured."

format: ## Format Rust and Python, then run lint
	cargo fmt --all
	uv run ruff format
	@$(MAKE) --no-print-directory lint

format-check: ## Check formatting without writes
	cargo fmt --all -- --check
	uv run ruff format --check .

typecheck: ## Run basedpyright
	uv run basedpyright

rust-deny: ## Run cargo deny
	cargo deny check

pre-commit-check: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

build: wheel ## Build release artifacts

wheel: ## Build optimized Python wheel
	uv run maturin build --release

clean: ## Remove generated files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ target/wheels/ 2>/dev/null || true
	@$(MAKE) --no-print-directory clean-cache

clean-cache: ## Remove project cache
	rm -rf .cache/ 2>/dev/null || true

remove-venv: ## Remove virtual environment
	rm -rf .venv

reset: clean remove-venv setup ## Rebuild local environment

upgrade-deps: ## Upgrade Python and Rust lockfiles
	uv lock --upgrade
	cargo update
	uv sync --group dev
	uv run maturin develop

ci: ## Run full CI
	@$(MAKE) --no-print-directory setup
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory rust-deny
	@$(MAKE) --no-print-directory typecheck
	@$(MAKE) --no-print-directory test
	@$(MAKE) --no-print-directory build

.DEFAULT_GOAL := help

-include Makefile.local

endif
