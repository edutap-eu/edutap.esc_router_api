# One entry point for every routine of this repository, so that CI can call the same
# targets a developer calls. A CI job that restates the commands drifts from them, and
# it drifts silently -- nobody reads two files side by side.

PYTHON    := .venv/bin/python
VENV      := .venv
DOCS_VENV := docs/.venv
DOCS_BIN  := $(DOCS_VENV)/bin

# The specification the models and the API surface are checked against. The sandbox
# host is named here rather than the production one because production answers 403 to
# anonymous requests -- it is reachable only from a whitelisted address, so nobody
# could run this target. Sandbox and production serve the same V2 surface; measured on
# 2026-08-14, sandbox and dev returned byte-identical documents.
SPEC_URL  := https://sandbox.europeanstudentcard.eu/esc-rest/v3/api-docs/V2
SPEC_FILE := tests/data/esc-router-v2.json

.DEFAULT_GOAL := help
.PHONY: help venv lint reformat test-local test-integration refresh-spec build \
        docs-venv docs docs-live docs-linkcheck docs-clean clean

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk -F':.*?## ' '{printf "  %-16s %s\n", $$1, $$2}'

venv: ## Create .venv and install the package with its dev dependency group
	test -d $(VENV) || uv venv
	uv pip install -U -e . --group dev

lint: venv ## Run ruff checks and the type checker
	$(PYTHON) -m ruff check src tests tools
	$(PYTHON) -m ruff format --check src tests tools
	$(PYTHON) -m ty check src

reformat: venv ## Autoformat and autofix
	$(PYTHON) -m ruff format src tests tools
	$(PYTHON) -m ruff check --fix src tests tools

test-local: venv ## Run the unit test suite -- no network
	$(PYTHON) -m pytest -v

# `--run-integration` is what pytest-explicit wants; `-m integration` alone leaves
# them skipped, which reads like a pass. The marker is added so that *only* they run.
test-integration: venv ## Run the tests that talk to the real router -- needs ESC_API_KEY
	$(PYTHON) -m pytest -v --run-integration -m integration

refresh-spec: ## Fetch the current OpenAPI specification into tests/data
	@curl -fsS $(SPEC_URL) \
		| python3 -c 'import json,sys; json.dump(json.load(sys.stdin), sys.stdout, indent=2, sort_keys=True); print()' \
		> $(SPEC_FILE)
	@echo "$(SPEC_FILE) updated -- run 'make test-local' to see what moved"

build: venv ## Build the distributions and check their metadata
	uv build
	uvx twine check dist/*

# Documentation (Sphinx + MyST). The environment lives under docs/ rather than in the
# package venv: a documentation build pulls in Sphinx and a theme, and none of that
# belongs in the environment the test suite runs in.
$(DOCS_BIN)/sphinx-build:
	test -d $(DOCS_VENV) || uv venv $(DOCS_VENV)
	VIRTUAL_ENV=$(DOCS_VENV) uv pip install -e ".[docs]"

docs-venv: $(DOCS_BIN)/sphinx-build ## Create docs/.venv and install the docs extra

docs: docs-venv ## Build the HTML documentation, warnings are errors
	$(DOCS_BIN)/sphinx-build -W -b html docs docs/_build/html
	@echo "docs ready: docs/_build/html/index.html"

docs-live: docs-venv ## Serve the docs with live reload on http://127.0.0.1:8000
	$(DOCS_BIN)/sphinx-autobuild docs docs/_build/html --ignore '*/_build/*'

docs-linkcheck: docs-venv ## Check every link in the documentation
	$(DOCS_BIN)/sphinx-build -b linkcheck docs docs/_build/linkcheck

docs-clean: ## Remove the documentation build output
	rm -rf docs/_build

clean: docs-clean ## Remove build output and caches
	rm -rf dist build .pytest_cache .ruff_cache
	find src tests -name '__pycache__' -type d -exec rm -rf {} +
