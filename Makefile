
#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = Uitnodigingsregel
PYTHON_VERSION = 3.13

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Render Quarto notebooks
.PHONY: render-notebooks
render-notebooks:
	quarto render Model_analysis.qmd

## Install Python Dependencies
.PHONY: requirements
requirements:
	uv sync

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using ruff
.PHONY: lint
lint:
	uv run ruff check src app

## Format source code with ruff
.PHONY: format
format:
	uv run ruff format src app

## Run tests
.PHONY: test
test:
	uv run pytest

## Regenerate golden master snapshot fixtures (after a deliberate model change)
.PHONY: snapshot-update
snapshot-update:
	uv run python snapshots/update.py --confirm

## Compare current pipeline output to snapshot fixtures (no pass/fail)
.PHONY: snapshot-compare
snapshot-compare:
	uv run python snapshots/compare.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Run the pipeline
.PHONY: run
run:
	uv run python main.py

## Run the Streamlit app
.PHONY: app
app:
	uv run streamlit run app/main.py

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
