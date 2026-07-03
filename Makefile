export PATH := $(HOME)/.cargo/bin:$(PATH)

AI ?=
LOG := .ci-ai.log
RUST_VERSION := 1.96.0
CARGO_DENY_VERSION := 0.19.7
REFRESH_BRANCH := automation/dependency-refresh

ifdef AI
_goals := $(or $(MAKECMDGOALS),ci)
.PHONY: $(_goals)
$(_goals):
	@rm -f $(LOG)
	@$(MAKE) --no-print-directory AI= $@ > $(LOG) 2>&1 \
		&& echo "$@ passed (log: $(LOG))" \
		|| (echo "$@ failed:"; uv run --group dev scripts/ai_filter_log.py $(LOG); echo "(full log: $(LOG))"; exit 1)

else

.PHONY: help bootstrap-rust setup setup-env setup-hooks develop test test-rust test-py coverage lint lint-fix py-lint py-lint-fix \
	rust-lint rust-lint-fix md-lint md-lint-fix format format-check typecheck \
	rust-deny py-audit-lock dependency-audit dependency-refresh-check refresh-actions accept-refresh-pr pre-commit-check \
	third-party-notices third-party-notices-check build wheel clean clean-cache reset remove-venv upgrade-deps api-matrix ci

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

bootstrap-rust: ## Install rustup, Rust toolchain, and cargo-deny if missing
	@if ! command -v rustup >/dev/null 2>&1; then \
		echo "Installing rustup"; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain none; \
	fi
	rustup toolchain install $(RUST_VERSION) --profile minimal --component rustfmt --component clippy
	rustup default $(RUST_VERSION)
	@if ! command -v cargo-deny >/dev/null 2>&1 || ! cargo-deny --version | grep -Fqx "cargo-deny $(CARGO_DENY_VERSION)"; then \
		cargo install --locked cargo-deny --version $(CARGO_DENY_VERSION); \
	fi

setup-env: bootstrap-rust ## Install toolchains, sync deps, and build editable extension (no hook install)
	uv lock --check
	uv sync --locked --group dev --reinstall
	@$(MAKE) --no-print-directory develop

setup-hooks: ## Install pre-commit hooks (skipped silently when core.hooksPath is set or git worktree)
	@if git config --get core.hooksPath >/dev/null 2>&1 || [ -f .git ]; then \
		echo "Note: core.hooksPath is set or git worktree; skipping pre-commit hook install (hooks run via make pre-commit-check)"; \
	else \
		uv run --group dev pre-commit install --install-hooks; \
		uv run --group dev pre-commit install --hook-type commit-msg; \
	fi

setup: setup-env setup-hooks ## Install toolchains, sync deps, build editable extension, and install pre-commit hooks

develop: ## Build and install the editable extension
	uv run --group dev maturin develop

test: test-rust test-py ## Run all tests

test-rust: ## Run Rust tests
	cargo test

test-py: ## Run Python tests against editable extension
	uv run --group dev maturin develop --quiet
	uv run --no-sync --group dev pytest -v -ra -n auto --cov=oxipng --cov=scripts --cov-branch --cov-report=term-missing:skip-covered --cov-fail-under=60

coverage: ## Run pytest with branch coverage and HTML report
	uv run --group dev maturin develop --quiet
	uv run --no-sync --group dev pytest --cov=oxipng --cov=scripts --cov-branch --cov-report=term-missing --cov-report=html --cov-fail-under=60

api-matrix: ## Run focused public API tests on all supported Python versions
	printf '%s\n' 3.10 3.11 3.12 3.13 3.14 | xargs -P 5 -I {} sh -c '\
		case "{}" in 3.10) features=abi3-py310 ;; *) features=abi3-py311 ;; esac; \
		UV_PROJECT_ENV=.venv-api-{} UV_PYTHON={} uv sync --locked --group dev && \
		UV_PROJECT_ENV=.venv-api-{} UV_PYTHON={} CARGO_TARGET_DIR=target/api-matrix-{} uv run --locked --group dev maturin develop --no-default-features --features "$$features" && \
		UV_PROJECT_ENV=.venv-api-{} UV_PYTHON={} uv run --locked --group dev pytest tests/test_api_surface.py tests/test_optimize_file_api.py tests/test_optimize_memory_api.py tests/test_option_validation.py tests/test_pyoxipng_compat.py tests/test_raw_image_api.py -v -ra \
	'

lint: rust-lint py-lint md-lint ## Run all lint checks

lint-fix: rust-lint-fix py-lint-fix md-lint-fix ## Apply automatic lint fixes

rust-lint: ## Run cargo clippy
	cargo clippy --workspace --all-targets -- -D warnings

rust-lint-fix: ## Run cargo clippy --fix
	cargo clippy --workspace --all-targets --fix --allow-dirty --allow-staged -- -D warnings

py-lint: ## Run ruff check
	uv run --group dev ruff check .

py-lint-fix: ## Run ruff format and ruff check --fix
	uv run --group dev ruff format
	uv run --group dev ruff check --fix .

md-lint: ## Run markdownlint via pre-commit
	uv run --group dev pre-commit run markdownlint-cli2 --all-files

md-lint-fix: ## Run markdownlint auto-fix via pre-commit
	uv run --group dev pre-commit run markdownlint-cli2-fix --hook-stage manual --all-files

format: ## Format Rust and Python, then run lint
	cargo fmt --all
	uv run --group dev ruff format
	@$(MAKE) --no-print-directory lint

format-check: ## Check formatting without writes
	cargo fmt --all -- --check
	uv run --group dev ruff format --check .

typecheck: ## Run basedpyright
	uv run --group dev basedpyright

rust-deny: ## Run cargo deny
	cargo deny check

py-audit-lock: ## Audit locked Python dependency set for known vulnerabilities
	uv audit --locked

dependency-audit: rust-deny py-audit-lock ## Run Rust and Python dependency vulnerability checks

third-party-notices: ## Regenerate third-party notices
	uv run --group dev scripts/generate_third_party_notices.py --write

third-party-notices-check: ## Check third-party notices for drift
	uv run --group dev scripts/generate_third_party_notices.py --check

dependency-refresh-check: ## Refresh lockfiles, then run audits and full CI
	uv lock --upgrade
	cargo update
	uv sync --locked --group dev
	@$(MAKE) --no-print-directory develop
	@$(MAKE) --no-print-directory dependency-audit
	@$(MAKE) --no-print-directory ci

refresh-actions: ## Refresh reviewed GitHub Action pins and sync the allowlist for local sign-off
	uv run --locked --group dev python scripts/update_github_actions.py --sync-reviewed-refs
	uv run --no-sync --group dev pytest tests/test_workflow_security.py tests/test_update_github_actions.py tests/test_makefile.py -q

accept-refresh-pr: ## Rebase the dependency-refresh PR on main, sync pins, run CI, and push; prints the merge command
	@git diff --quiet && git diff --cached --quiet || { echo "Working tree not clean; commit or stash first."; exit 1; }
	git fetch origin $(REFRESH_BRANCH) main
	git checkout -B $(REFRESH_BRANCH) origin/$(REFRESH_BRANCH)
	git rebase origin/main
	uv run --locked --group dev python scripts/update_github_actions.py --sync-reviewed-refs
	@git diff --quiet || git commit -am "test(workflows): approve reviewed action refs for dependency refresh"
	@$(MAKE) --no-print-directory ci
	git push --force-with-lease origin $(REFRESH_BRANCH)
	@pr=$$(gh pr list --head $(REFRESH_BRANCH) --state open --json number --jq '.[0].number'); \
		echo ""; \
		echo "PR #$$pr is green and ready. Review the changelog links above, then merge with:"; \
		echo "  gh pr merge $$pr --rebase"

pre-commit-check: ## Run all pre-commit hooks
	uv run --group dev pre-commit run --all-files

build: wheel ## Build release artifacts

wheel: ## Build optimized Python wheel
	uv run --group dev maturin build --release --locked

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
	uv run --group dev maturin develop

ci: ## Run full CI
	@$(MAKE) --no-print-directory setup-env
	@$(MAKE) --no-print-directory pre-commit-check
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory rust-deny
	@$(MAKE) --no-print-directory py-audit-lock
	@$(MAKE) --no-print-directory third-party-notices-check
	@$(MAKE) --no-print-directory typecheck
	@$(MAKE) --no-print-directory test
	@$(MAKE) --no-print-directory build

.DEFAULT_GOAL := help

-include Makefile.local

endif
