.PHONY: help build run stop restart logs clean status lint test

GREEN := \033[0;32m
NC := \033[0m

DOCKER_COMPOSE = docker compose

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

build:
	@echo "$(GREEN)Building Docker container...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache

run:
	@echo "$(GREEN)Starting Instagram bot...$(NC)"
	@$(DOCKER_COMPOSE) up -d

stop:
	@echo "$(GREEN)Stopping Instagram bot...$(NC)"
	@$(DOCKER_COMPOSE) down

restart: stop run

logs:
	@echo "$(GREEN)Showing logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f --timestamps bot

clean: stop
	@echo "$(GREEN)Cleaning up...$(NC)"
	@rm -f geckodriver.log
	@rm -f instabot.log
	@rm -rf __pycache__
	@rm -rf .pytest_cache

status:
	@echo "$(GREEN)Container status:$(NC)"
	@$(DOCKER_COMPOSE) ps

lint:
	@echo "$(GREEN)Running linters...$(NC)"
	@$(DOCKER_COMPOSE) run --rm bot flake8 .
	@$(DOCKER_COMPOSE) run --rm bot black --check .

test:
	@echo "$(GREEN)Running tests...$(NC)"
	@$(DOCKER_COMPOSE) run --rm bot pytest

monitor:
	@echo "$(GREEN)Monitoring container resources...$(NC)"
	@docker stats bot
