# TripFinder

A Django web application that helps you find the cheapest round-trip flight combinations for your next trip.

### Key Features

- **Smart Flight Combinations**: Automatically matches outbound and inbound flights to find the cheapest round-trip combinations
- **Multi-Month Search**: Scan up to 12 months of flight data at once to find the best deals
- **Flexible Duration**: Set minimum and maximum trip durations to match your schedule
- **Weekend Filter**: Option to search only for weekend getaways (Friday-Monday trips)
- **Direct Flights Only**: Focuses on direct flights for convenience
- **Promo Code Support**: Apply promotional codes to unlock discounted fares
- **Discount Visualization**: See how much you're saving compared to regular prices
- **Top Results**: Configurable number of results to display (top 10, 20, 50, etc.)

### How It Works

1. Enter your origin and destination airports (IATA codes)
2. Specify your preferred trip duration range
3. Choose which months to search
4. Optionally filter for weekend trips or apply a promo code
5. Get a sorted list of the cheapest flight combinations with prices, discounts, and dates


## Quick Start

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env and fill in your values

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
# Build the image
make docker-build

# Configure environment (if not done already)
cp .env.example .env
# Edit .env and fill in your values

# Run the container
make docker-run

# Run a specific image
make docker-run IMAGE=trip-finder:1.2.3

# Connect to a Postgres container running in another Docker network
make docker-run NETWORK=appnet
```

When using `NETWORK=appnet`, the container joins the existing Docker network and can reach other containers by their name. Set `AIRPORTS_DB_HOST=postgres` in your `.env` to use the Postgres container directly by name.

## Requirements

- Python 3.12+
- Poetry for dependency management
- Django 6.0+

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. The `.env` file is used both locally (loaded by Django via `python-dotenv`) and by Docker (`--env-file .env`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `URL_API` | Yes | — | Flight API base URL |
| `SECRET_KEY` | No | insecure default | Django secret key |
| `DEBUG` | No | `True` | Set to `False` for production |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated hostnames/IPs |
| `AIRPORTS_DB_HOST` | No | — | Enables airport autocomplete when set |
| `AIRPORTS_DB_PORT` | No | `5432` | Postgres port |
| `AIRPORTS_DB_NAME` | No | `postgres` | Postgres database name |
| `AIRPORTS_DB_USER` | No | `postgres` | Postgres user |
| `AIRPORTS_DB_PASSWORD` | No | — | Postgres password |

If `AIRPORTS_DB_HOST` is not set, or the server is unreachable, the airport fields fall back to plain text inputs.
