"""Integration tests: real TripFinder logic, HTTP mocked via responses library."""

import json
from pathlib import Path

import responses as rsps
from django.test import Client, TestCase, override_settings
from django.urls import reverse

SCHEDULE_URL = "https://test-api.example.com/schedule"
CALENDAR_URL = "https://test-api.example.com/calendar"
BOOKING_URL = "https://test-booking.example.com"

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@override_settings(
    FLIGHT_SCHEDULE_ENDPOINT=SCHEDULE_URL,
    FLIGHT_CALENDAR_ENDPOINT=CALENDAR_URL,
    BOOKING_BASE_URL=BOOKING_URL,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
class SearchIntegrationTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.url = reverse("flights:search")
        self.base_form: dict = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 1,
            "start_month": "202604",
            "top": 10,
        }

    @rsps.activate
    def test_full_search_returns_ranked_trips(self) -> None:
        """End-to-end: fixture data flows through TripFinder and renders in the table."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, json=_load("calendar_arn_bru_202604.json"))

        response = self.client.post(self.url, self.base_form)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/results.html")
        # Two trips: 10 Apr→17 Apr (1550 SEK) and 17 Apr→24 Apr (1800 SEK)
        self.assertEqual(response.context["total_count"], 2)
        self.assertContains(response, "1550")
        self.assertContains(response, "1800")

    @rsps.activate
    def test_cheapest_trip_ranked_first(self) -> None:
        """Trips are sorted ascending by price."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, json=_load("calendar_arn_bru_202604.json"))

        response = self.client.post(self.url, self.base_form)

        trips = response.context["trips"]
        prices = [t["price"] for t in trips]
        self.assertEqual(prices, sorted(prices))
        self.assertEqual(trips[0]["price"], 1550)

    @rsps.activate
    def test_duration_filter_excludes_out_of_range(self) -> None:
        """Trips outside the duration window are not included."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, json=_load("calendar_arn_bru_202604.json"))

        # Fixtures only have 7-day and 14-day trips; 15-30 matches nothing
        form = {**self.base_form, "duration_min": 15, "duration_max": 30}
        response = self.client.post(self.url, form)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")
        self.assertContains(response, "No trips found")

    @rsps.activate
    def test_no_direct_flights_shows_warning(self) -> None:
        """When the schedule endpoint returns empty, a warning is shown."""
        rsps.get(SCHEDULE_URL, json={"outbound": {}, "inbound": {}})

        response = self.client.post(self.url, self.base_form)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")
        self.assertContains(response, "No direct flights available to BRU.")

    @rsps.activate
    def test_api_failure_shows_no_data_warning(self) -> None:
        """When the calendar endpoint fails for all months, a warning is shown."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, status=500)

        response = self.client.post(self.url, self.base_form)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")
        self.assertContains(response, "No flight data available for BRU.")

    @rsps.activate
    def test_promo_code_forwarded_to_api(self) -> None:
        """The promo code is included in the calendar API request."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, json=_load("calendar_arn_bru_202604.json"))

        form = {**self.base_form, "promo_code": "SUMMER26"}
        self.client.post(self.url, form)

        calendar_call = next(c for c in rsps.calls if CALENDAR_URL in c.request.url)
        self.assertIn("cepId=SUMMER26", calendar_call.request.url)

    @rsps.activate
    def test_booking_link_contains_dates_and_airports(self) -> None:
        """Each result row links to the booking URL with correct params."""
        rsps.get(SCHEDULE_URL, json=_load("direct_arn_bru.json"))
        rsps.get(CALENDAR_URL, json=_load("calendar_arn_bru_202604.json"))

        response = self.client.post(self.url, self.base_form)

        self.assertContains(response, "origin=ARN")
        self.assertContains(response, "destination=BRU")
        self.assertContains(response, "outboundDate=2026-04-10")
