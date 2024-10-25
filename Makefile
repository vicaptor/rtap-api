# Makefile for rtap-api

.PHONY: setup install test clean docker-build docker-run all

# Variables
PYTHON = python
PIP = pip
VENV = venv
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Default target
all: setup install test

# Create virtual environment and install dependencies
setup:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt

# Install dependencies in existing environment
install:
	$(PIP) install -r requirements.txt

# Run tests
test:
	cd tests && ./annotation.sh

# Clean up generated files and virtual environment
clean:
	rm -rf $(VENV)
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Docker commands
docker-build:
	$(DOCKER) build -t rtap-api .

docker-run:
	$(DOCKER_COMPOSE) up

# Start the application
run:
	$(PYTHON) rtap.py

# Create .env from demo
init:
	cp .env.demo .env

# Check code style
lint:
	pylint rtap.py

# Run security checks
security-check:
	bandit -r .

# Help target
help:
	@echo "Available targets:"
	@echo "  setup          - Create virtual environment and install dependencies"
	@echo "  install        - Install dependencies in existing environment"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up generated files"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run with Docker Compose"
	@echo "  run            - Start the application"
	@echo "  init           - Initialize .env file"
	@echo "  lint           - Check code style"
	@echo "  security-check - Run security checks"
	@echo "  all            - Run setup, install, and test"
