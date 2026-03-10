import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Literal

from .flight_client import FlightAPIClient
from .trip_finder import TripFinder

logger = logging.getLogger(__name__)


@dataclass
class SearchParams:
    inbound: str
    destinations: list[str]
    months: list[str]
    promo_code: str
    duration_min: int
    duration_max: int
    only_weekends: bool
    top: int


@dataclass
class SearchOutcome:
    trips: list[dict] = field(default_factory=list)
    no_route: list[str] = field(default_factory=list)  # no direct flights
    no_data: list[str] = field(default_factory=list)  # all month fetches failed
    errors: list[str] = field(default_factory=list)  # unexpected exceptions


def _search_destination(
    client: FlightAPIClient,
    params: SearchParams,
    destination: str,
) -> tuple[list[dict] | None | Literal[False], list[str]]:
    """Fetch and rank trips for one destination.

    Returns:
        (None, _)         — no direct route exists
        (False, warnings) — route exists but all monthly fetches failed
        (trips, warnings) — ranked trip list (may be empty if criteria unmet)
    """
    warnings: list[str] = []

    direct_flights = client.fetch_direct_flights(params.inbound, destination)
    if not direct_flights.get("outbound") or not direct_flights.get("inbound"):
        return None, warnings

    def fetch_month(month: str) -> dict:
        return client.fetch_monthly_flights(month, params.inbound, destination, params.promo_code)

    flight_data_list: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_month = {executor.submit(fetch_month, m): m for m in params.months}
        for future in as_completed(future_to_month):
            month = future_to_month[future]
            try:
                flight_data_list.append(future.result())
            except Exception as e:
                warnings.append(f"Failed to fetch {destination} for {month}: {e}")

    if not flight_data_list:
        return False, warnings

    merged = TripFinder.merge_flights_data(flight_data_list)
    trips = TripFinder.find_cheapest(
        merged,
        direct_flights,
        params.duration_min,
        params.duration_max,
        params.only_weekends,
        params.top,
    )
    for trip in trips:
        trip["outbound_airport"] = params.inbound
        trip["inbound_airport"] = destination

    return trips, warnings


def run_search(params: SearchParams) -> SearchOutcome:
    """Run a parallel search across all destinations and return a SearchOutcome."""
    client = FlightAPIClient()
    outcome = SearchOutcome()

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_dest = {
            executor.submit(_search_destination, client, params, dest): dest
            for dest in params.destinations
        }
        for future in as_completed(future_to_dest):
            dest = future_to_dest[future]
            try:
                result, warnings = future.result()
                for w in warnings:
                    logger.warning(w)
                if result is None:
                    outcome.no_route.append(dest)
                elif result is False:
                    outcome.no_data.append(dest)
                else:
                    outcome.trips.extend(result)
            except Exception as e:
                logger.error(f"Unexpected error searching {dest}: {e}")
                outcome.errors.append(dest)

    outcome.trips.sort(key=lambda x: x["price"])
    return outcome
