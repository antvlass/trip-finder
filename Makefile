.PHONY: test lint format check run docker-build docker-run

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
	poetry run python manage.py runserver

docker-build: ## Build Docker image
	docker build -t flight-finder:latest .

docker-run: ## Run Docker container (set URL_API first)
	@if [ -z "$$URL_API" ]; then echo "Error: URL_API not set. Use: export URL_API=your-api-url"; exit 1; fi
	@ALLOWED_HOSTS_VALUE=$${ALLOWED_HOSTS:-localhost,127.0.0.1}; \
	echo "Starting container with ALLOWED_HOSTS=$$ALLOWED_HOSTS_VALUE"; \
	docker run -d -p 8001:8000 -e URL_API="$$URL_API" -e ALLOWED_HOSTS="$$ALLOWED_HOSTS_VALUE" --name flight-finder flight-finder:latest
