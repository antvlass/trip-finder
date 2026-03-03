import logging
import os

from django.contrib import messages
from django.shortcuts import render

from .forms import FlightSearchForm
from .services.flight_client import FlightAPIClient
from .services.trip_finder import TripFinder
from .services.utils import generate_months

logger = logging.getLogger(__name__)


def index(request):
    """Main search page"""
    form = FlightSearchForm()
    return render(request, "flights/index.html", {"form": form})


def search_flights(request):
    """Search for flights based on form criteria"""
    if request.method != "POST":
        return index(request)

    form = FlightSearchForm(request.POST)
    if not form.is_valid():
        return render(request, "flights/index.html", {"form": form})

    try:
        api_url = os.environ.get("URL_API")
        if not api_url:
            messages.error(
                request, "API URL not configured. Please set URL_API environment variable."
            )
            return render(request, "flights/index.html", {"form": form})

        promo_code = form.cleaned_data.get("promo_code", "").strip()

        inbound = form.cleaned_data["inbound"].upper()
        outbound = form.cleaned_data["outbound"].upper()
        duration_min = form.cleaned_data["duration_min"]
        duration_max = form.cleaned_data["duration_max"]
        start_month = form.cleaned_data.get("start_month", "")
        num_months = form.cleaned_data["num_months"]
        top = form.cleaned_data["top"]
        only_weekends = form.cleaned_data["only_weekends"]

        months = generate_months(start_month, num_months)
        logger.info(f"Scanning months: {months}")

        client = FlightAPIClient(api_url)

        direct_flights = client.fetch_direct_flights(inbound, outbound)

        if not direct_flights.get("outbound") or not direct_flights.get("inbound"):
            messages.warning(request, "No direct flights available for this route.")
            return render(request, "flights/index.html", {"form": form})

        flight_data_list = []
        for month in months:
            try:
                flight_data = client.fetch_monthly_flights(month, inbound, outbound, promo_code)
                flight_data_list.append(flight_data)
            except Exception as e:
                logger.warning(f"Failed to fetch flights for {month}: {e}")

        if not flight_data_list:
            messages.error(request, "No flight data available for the selected months.")
            return render(request, "flights/index.html", {"form": form})

        merged_flights = TripFinder.merge_flights_data(flight_data_list)

        trips = TripFinder.find_cheapest(
            merged_flights, direct_flights, duration_min, duration_max, only_weekends, top
        )

        if not trips:
            messages.info(request, "No trips found matching your criteria.")
            return render(request, "flights/index.html", {"form": form})

        for trip in trips:
            trip["outbound_airport"] = inbound
            trip["inbound_airport"] = outbound

        context = {
            "form": form,
            "trips": trips,
            "total_count": len(trips),
            "promo_code_used": bool(promo_code),
        }

        return render(request, "flights/results.html", context)

    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        messages.error(request, f"An error occurred while searching for flights: {str(e)}")
        return render(request, "flights/index.html", {"form": form})
