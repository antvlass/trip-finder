# Trip Finder

A Django web application that helps you find the cheapest round-trip flight combinations for your next trip.

## About

Trip Finder is designed to take the hassle out of searching for affordable flights by automatically scanning multiple months and finding the best price combinations for round-trip travel. 
Instead of manually checking flight prices day by day, Trip Finder does the heavy lifting for you.

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
