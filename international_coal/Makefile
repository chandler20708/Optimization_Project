.DEFAULT_GOAL := help

PYTHONPATH=
SHELL=/bin/bash
VENV=.venv

ifeq ($(OS),Windows_NT)
	VENV_BIN=$(VENV)/Scripts
else
	VENV_BIN=$(VENV)/bin
endif

.PHONY: .venv
.venv:  ## Set up Python virtual environment and install requirements
	python3 -m venv $(VENV)

.PHONY: activate
activate:
	source "$(VENV_BIN)/activate"

.PHONY: requirements
requirements: .venv  ## Install/refresh Python project requirements
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/pip install --upgrade -r requirements.txt
	$(VENV_BIN)/pip install pipreqs
	$(VENV_BIN)/pip install ipykernel

.PHONY: update-reqs
update-reqs:
	conda init zsh
	-conda deactivate
	-conda deactivate
	$(VENV_BIN)/pip install --upgrade -r requirements.txt

.PHONY: setup
setup:
	-conda deactivate
	-conda deactivate
	make requirements
	make activate

.PHONY: new-pyfile
new-pyfile:
	@read -p "Enter the filename: " filename; \
	echo "#%%" > $$filename.py; \
	echo "import polars as pl" >> $$filename.py; \
	echo "import pandas as pd" >> $$filename.py; \
	echo "from pathlib import Path" >> $$filename.py; \
	echo "" >> $$filename.py; \
	echo 'DATA = Path("")' >> $$filename.py

.PHONY: clean
clean:  ## Clean up caches and build artifacts
	@rm -rf .venv/

.PHONY: help
help:  ## Display this help screen
	@echo -e "\033[1mAvailable commands:\033[0m"
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort
