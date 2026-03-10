import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render

from .forms import FlightSearchForm
from .models import Airport
from .services.flight_client import FlightAPIClient
from .services.trip_finder import TripFinder
from .services.utils import generate_months

logger = logging.getLogger(__name__)


def airport_autocomplete(request):
    """Return matching airports as JSON from the external airports database.
    Returns empty list if the database is not configured or unreachable."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2 or "airports" not in settings.DATABASES:
        return JsonResponse({"airports": []})
    try:
        qs = Airport.objects.using("airports").filter(
            code__istartswith=q.upper()
        ) | Airport.objects.using("airports").filter(name__icontains=q)
        results = [{"code": a.code, "name": a.name} for a in qs[:10]]
    except Exception:
        results = []
    return JsonResponse({"airports": results})


def _get_airport_names(codes):
    """Fetch airport names for a list of codes. Returns dict {code: name}."""
    if "airports" not in settings.DATABASES:
        return {}
    try:
        airports = Airport.objects.using("airports").filter(code__in=codes)
        return {a.code: a.name for a in airports}
    except Exception:
        return {}


def _search_destination(
    client, inbound, destination, months, promo_code, duration_min, duration_max, only_weekends, top
):
    """Search for trips to a single destination.
    Returns (result, warnings) where result is None / False / list of trips."""
    warnings = []

    direct_flights = client.fetch_direct_flights(inbound, destination)
    if not direct_flights.get("outbound") or not direct_flights.get("inbound"):
        return None, warnings

    def fetch_month(month):
        return client.fetch_monthly_flights(month, inbound, destination, promo_code)

    flight_data_list = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_month = {executor.submit(fetch_month, month): month for month in months}
        for future in as_completed(future_to_month):
            month = future_to_month[future]
            try:
                flight_data_list.append(future.result())
            except Exception as e:
                warnings.append(f"Failed to fetch flights for {month} to {destination}: {e}")

    if not flight_data_list:
        return False, warnings

    merged = TripFinder.merge_flights_data(flight_data_list)
    trips = TripFinder.find_cheapest(
        merged, direct_flights, duration_min, duration_max, only_weekends, top
    )

    for trip in trips:
        trip["outbound_airport"] = inbound
        trip["inbound_airport"] = destination

    return trips, warnings


def index(request):
    """Main search page"""
    form = FlightSearchForm()
    return render(request, "flights/index.html", {"form": form, "form_has_errors": False})


def search_flights(request):
    """Search for flights based on form criteria"""
    if request.method != "POST":
        return index(request)

    form = FlightSearchForm(request.POST)
    if not form.is_valid():
        return render(request, "flights/index.html", {"form": form, "form_has_errors": True})

    try:
        promo_code = form.cleaned_data.get("promo_code", "")
        inbound = form.cleaned_data["inbound"].upper()
        duration_min = form.cleaned_data["duration_min"]
        duration_max = form.cleaned_data["duration_max"]
        start_month = form.cleaned_data.get("start_month", "")
        num_months = form.cleaned_data["num_months"]
        top = form.cleaned_data["top"]
        only_weekends = form.cleaned_data["only_weekends"]

        destinations = [form.cleaned_data["outbound"].upper()]
        if form.cleaned_data.get("outbound_2"):
            destinations.append(form.cleaned_data["outbound_2"].upper())
        if form.cleaned_data.get("outbound_3"):
            destinations.append(form.cleaned_data["outbound_3"].upper())

        months = generate_months(start_month, num_months)
        logger.info(f"Scanning months: {months}, destinations: {destinations}")

        client = FlightAPIClient()
        all_trips = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_dest = {
                executor.submit(
                    _search_destination,
                    client,
                    inbound,
                    dest,
                    months,
                    promo_code,
                    duration_min,
                    duration_max,
                    only_weekends,
                    top,
                ): dest
                for dest in destinations
            }
            for future in as_completed(future_to_dest):
                dest = future_to_dest[future]
                try:
                    result, dest_warnings = future.result()
                    for w in dest_warnings:
                        logger.warning(w)
                    if result is None:
                        messages.warning(request, f"No direct flights available to {dest}.")
                    elif result is False:
                        messages.warning(request, f"No flight data available for {dest}.")
                    elif result:
                        all_trips.extend(result)
                except Exception as e:
                    logger.error(f"Error searching {dest}: {e}")
                    messages.warning(request, f"Error searching flights to {dest}.")

        if not all_trips:
            messages.info(request, "No trips found matching your criteria.")
            return render(request, "flights/index.html", {"form": form, "form_has_errors": False})

        all_trips.sort(key=lambda x: x["price"])

        all_codes = {inbound} | {t["inbound_airport"] for t in all_trips}
        airport_names = _get_airport_names(all_codes)

        badge_colors = ["primary", "success", "warning"]
        destination_colors = {dest: badge_colors[i] for i, dest in enumerate(destinations)}

        context = {
            "form": form,
            "trips": all_trips,
            "total_count": len(all_trips),
            "promo_code": promo_code,
            "promo_code_used": bool(promo_code),
            "airport_names": airport_names,
            "destination_colors": destination_colors,
            "multi_destination": len(destinations) > 1,
            "booking_base_url": settings.BOOKING_BASE_URL,
        }

        return render(request, "flights/results.html", context)

    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        messages.error(request, f"An error occurred while searching for flights: {str(e)}")
        return render(request, "flights/index.html", {"form": form, "form_has_errors": False})
