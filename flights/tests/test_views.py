from datetime import datetime
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from flights.services.search import SearchOutcome


class IndexViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.url = reverse("flights:index")

    def test_index_view_get(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")
        self.assertIn("form", response.context)

    def test_index_view_contains_form(self) -> None:
        response = self.client.get(self.url)
        self.assertContains(response, "Search Flights")
        self.assertContains(response, "inbound")
        self.assertContains(response, "outbound")


@override_settings(
    DEBUG=True,
    FLIGHT_CALENDAR_ENDPOINT="https://example.com/calendar",
    FLIGHT_SCHEDULE_ENDPOINT="https://example.com/schedule",
)
class SearchFlightsViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.url = reverse("flights:search")
        self.base_form: dict = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }

    def test_search_view_get_redirects(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")

    def test_search_view_invalid_form(self) -> None:
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")

    @patch("flights.views.run_search")
    def test_search_view_no_direct_flights(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome(no_route=["BRU"])
        response = self.client.post(self.url, self.base_form)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No direct flights available to BRU.")

    @patch("flights.views.run_search")
    def test_search_view_no_flight_data(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome(no_data=["BRU"])
        response = self.client.post(self.url, self.base_form)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No flight data available for BRU.")

    @patch("flights.views.run_search")
    def test_search_view_no_trips_found(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome()
        response = self.client.post(self.url, self.base_form)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No trips found")

    @patch("flights.views.run_search")
    def test_search_view_success(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome(
            trips=[
                {
                    "outbound": datetime(2026, 4, 15),
                    "inbound": datetime(2026, 4, 22),
                    "price": 2100,
                    "normal_price": 2500,
                    "discount": 16.0,
                    "duration": 7,
                    "outbound_airport": "ARN",
                    "inbound_airport": "BRU",
                }
            ]
        )
        response = self.client.post(self.url, self.base_form)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/results.html")
        self.assertEqual(len(response.context["trips"]), 1)
        self.assertEqual(response.context["total_count"], 1)

    @patch("flights.views.run_search")
    def test_search_view_with_promo_code(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome(
            trips=[
                {
                    "outbound": datetime(2026, 4, 15),
                    "inbound": datetime(2026, 4, 22),
                    "price": 1800,
                    "normal_price": 2500,
                    "discount": 28.0,
                    "duration": 7,
                    "outbound_airport": "ARN",
                    "inbound_airport": "BRU",
                }
            ]
        )
        form = {**self.base_form, "promo_code": "SUMMER2026"}
        response = self.client.post(self.url, form)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["promo_code_used"])
        # Verify the promo code was passed through to the service
        params = mock_run_search.call_args[0][0]
        self.assertEqual(params.promo_code, "SUMMER2026")

    @patch("flights.views.run_search")
    def test_search_view_handles_exception(self, mock_run_search) -> None:
        mock_run_search.side_effect = Exception("Unexpected error")
        response = self.client.post(self.url, self.base_form)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "error occurred")

    @patch("flights.views.run_search")
    def test_search_view_airport_codes_uppercased(self, mock_run_search) -> None:
        mock_run_search.return_value = SearchOutcome()
        form = {**self.base_form, "inbound": "arn", "outbound": "bru"}
        self.client.post(self.url, form)
        params = mock_run_search.call_args[0][0]
        self.assertEqual(params.inbound, "ARN")
        self.assertEqual(params.destinations, ["BRU"])
