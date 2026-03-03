# Trip Finder

A flight search Django application

## Quick Start

```bash
# Install dependencies
poetry install

# Set environment variable
export URL_API="your-flight-api-url"

# Run migrations
poetry run python manage.py migrate

# Start server
make run
```

Open http://localhost:8000/flights/

## Available Commands

```bash
make test           # Run tests
make check          # Run Django system checks
make lint           # Lint code
make format         # Format code
make build          # Run full build (test + check + lint + format)
make run            # Start development server
make docker-build   # Build Docker image
make docker-run     # Run Docker container
```

## Docker

```bash
make docker-build
URL_API="your-flight-api-url"  make docker-run
```

## Requirements

- Python 3.12+
- Poetry for dependency management
- Django 6.0+

## Environment Variables

- `URL_API` (required): Flight API base URL
- `DEBUG` (optional): Set to `False` for production
- `SECRET_KEY` (optional): Django secret key
- `ALLOWED_HOSTS` (optional): Comma-separated hostnames/IPs
