IMAGE ?= trip-finder:latest
NETWORK ?=
NETWORK_FLAG = $(if $(NETWORK),--network $(NETWORK),)

.PHONY: test lint format check run docker-build docker-run docker-stop docker-restart

test: ## Run tests
	poetry run python manage.py test flights

check: ## Run Django system checks
	poetry run python manage.py check

lint: ## Lint code with ruff
	poetry run ruff check .

format: ## Format code with black
	poetry run black .

build: test check lint format

run: ## Run development server
	poetry run python manage.py runserver 0.0.0.0:8000

docker-build: ## Build Docker image
	docker build -t $(IMAGE) .

docker-run: ## Run Docker container using .env file (IMAGE=trip-finder:latest, NETWORK=appnet)
	@if [ ! -f .env ]; then echo "Error: .env file not found. Copy .env.example and fill in the values."; exit 1; fi
	docker run -d -p 7000:8000 --env-file .env --name trip-finder --restart unless-stopped $(NETWORK_FLAG) $(IMAGE)

docker-stop: ## Stop and remove the trip-finder container
	docker stop trip-finder && docker rm trip-finder

docker-restart: docker-stop docker-run ## Restart the trip-finder container
