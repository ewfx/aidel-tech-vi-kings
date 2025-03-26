# File: tests/Makefile

.PHONY: setup test-all bdd unit api report clean

# Variables
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
BEHAVE := $(VENV)/bin/behave
PYTEST := $(VENV)/bin/pytest
REPORT_DIR := reports

# Setup virtual environment and install dependencies
setup:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

# Run all tests
test-all: bdd unit api

# Run BDD tests with Behave
bdd:
	mkdir -p $(REPORT_DIR)
	$(BEHAVE) features/ --junit --junit-directory $(REPORT_DIR)

# Run unit tests
unit:
	mkdir -p $(REPORT_DIR)
	$(PYTEST) -m unit --html=$(REPORT_DIR)/unit-report.html --junitxml=$(REPORT_DIR)/unit-results.xml

# Run API tests
api:
	mkdir -p $(REPORT_DIR)
	$(PYTEST) -m api --html=$(REPORT_DIR)/api-report.html --junitxml=$(REPORT_DIR)/api-results.xml

# Generate coverage report
report:
	mkdir -p $(REPORT_DIR)
	$(PYTEST) --cov=. --cov-report=html:$(REPORT_DIR)/coverage

# Clean up generated files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf $(REPORT_DIR)
	rm -rf .coverage