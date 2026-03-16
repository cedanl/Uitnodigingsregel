
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
	quarto render notebooks

## Install Python Dependencies
.PHONY: requirements
requirements:
	uv sync

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	uv run flake8 module
	uv run isort --check --diff --profile black module
	uv run black --check --config pyproject.toml module

## Format source code with black
.PHONY: format
format:
	uv run black --config pyproject.toml module

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Run the pipeline
.PHONY: run
run:
	uv run python main.py

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
