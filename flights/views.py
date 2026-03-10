import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .forms import FlightSearchForm
from .models import Airport
from .services.search import SearchParams, run_search
from .services.utils import generate_months

logger = logging.getLogger(__name__)

BADGE_COLORS = ["primary", "success", "warning"]


def airport_autocomplete(request: HttpRequest) -> JsonResponse:
    """Return matching airports as JSON from the external airports database.
    Returns an empty list if the database is not configured or unreachable."""
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


def _get_airport_names(codes: set[str]) -> dict[str, str]:
    """Fetch airport names for a set of codes. Returns {} when DB is unavailable."""
    if "airports" not in settings.DATABASES:
        return {}
    try:
        airports = Airport.objects.using("airports").filter(code__in=codes)
        return {a.code: a.name for a in airports}
    except Exception:
        return {}


def _format_month_range(months: list[str]) -> str:
    """Format ['202604', '202606'] as 'Apr – Jun 2026'."""
    if not months:
        return ""
    start = datetime.strptime(months[0], "%Y%m")
    end = datetime.strptime(months[-1], "%Y%m")
    if start == end:
        return start.strftime("%b %Y")
    if start.year == end.year:
        return f"{start.strftime('%b')} – {end.strftime('%b %Y')}"
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"


def index(request: HttpRequest) -> HttpResponse:
    form = FlightSearchForm()
    return render(request, "flights/index.html", {"form": form, "form_has_errors": False})


def search_flights(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = request.POST
    elif request.GET:
        data = request.GET
    else:
        return index(request)

    form = FlightSearchForm(data)
    if not form.is_valid():
        return render(request, "flights/index.html", {"form": form, "form_has_errors": True})

    try:
        promo_code: str = form.cleaned_data.get("promo_code", "")
        inbound: str = form.cleaned_data["inbound"].upper()

        destinations: list[str] = [form.cleaned_data["outbound"].upper()]
        if form.cleaned_data.get("outbound_2"):
            destinations.append(form.cleaned_data["outbound_2"].upper())
        if form.cleaned_data.get("outbound_3"):
            destinations.append(form.cleaned_data["outbound_3"].upper())

        months = generate_months(
            form.cleaned_data.get("start_month", ""), form.cleaned_data["num_months"]
        )
        logger.info(f"Scanning months: {months}, destinations: {destinations}")

        params = SearchParams(
            inbound=inbound,
            destinations=destinations,
            months=months,
            promo_code=promo_code,
            duration_min=form.cleaned_data["duration_min"],
            duration_max=form.cleaned_data["duration_max"],
            only_weekends=form.cleaned_data["only_weekends"],
            top=form.cleaned_data["top"],
        )
        outcome = run_search(params)

        for dest in outcome.no_route:
            messages.warning(request, f"No direct flights available to {dest}.")
        for dest in outcome.no_data:
            messages.warning(request, f"No flight data available for {dest}.")
        for dest in outcome.errors:
            messages.warning(request, f"Error searching flights to {dest}.")

        if not outcome.trips:
            messages.info(request, "No trips found matching your criteria.")
            return render(request, "flights/index.html", {"form": form, "form_has_errors": False})

        all_codes: set[str] = {inbound} | {t["inbound_airport"] for t in outcome.trips}
        airport_names = _get_airport_names(all_codes)
        destination_colors = {dest: BADGE_COLORS[i] for i, dest in enumerate(destinations)}

        search_summary = {
            "inbound": inbound,
            "destinations": destinations,
            "duration": f"{params.duration_min}–{params.duration_max} days",
            "months": _format_month_range(months),
            "top": params.top,
            "only_weekends": params.only_weekends,
            "promo_code": promo_code,
        }

        return render(
            request,
            "flights/results.html",
            {
                "form": form,
                "trips": outcome.trips,
                "total_count": len(outcome.trips),
                "promo_code": promo_code,
                "promo_code_used": bool(promo_code),
                "airport_names": airport_names,
                "destination_colors": destination_colors,
                "multi_destination": len(destinations) > 1,
                "booking_base_url": settings.BOOKING_BASE_URL,
                "search_summary": search_summary,
            },
        )

    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        messages.error(request, f"An error occurred while searching for flights: {str(e)}")
        return render(request, "flights/index.html", {"form": form, "form_has_errors": False})
