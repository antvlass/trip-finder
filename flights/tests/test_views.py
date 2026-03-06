import os
from unittest.mock import Mock, patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("flights:index")

    def test_index_view_get(self):
        """Test GET request to index page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")
        self.assertIn("form", response.context)

    def test_index_view_contains_form(self):
        """Test index view contains search form"""
        response = self.client.get(self.url)
        self.assertContains(response, "Search Flights")
        self.assertContains(response, "inbound")
        self.assertContains(response, "outbound")


@override_settings(DEBUG=True)
class SearchFlightsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("flights:search")

    def test_search_view_get_redirects(self):
        """Test GET request redirects to index"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")

    def test_search_view_invalid_form(self):
        """Test POST with invalid form data"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/index.html")

    @patch.dict(os.environ, {}, clear=True)
    def test_search_view_missing_api_url(self):
        """Test search fails without API URL"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API URL not configured")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    def test_search_view_no_direct_flights(self, mock_client_class):
        """Test search with no direct flights"""
        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {"outbound": {}, "inbound": {}}
        mock_client_class.return_value = mock_client

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No direct flights available")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    def test_search_view_no_flight_data(self, mock_client_class):
        """Test search with no flight data"""
        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }
        mock_client.fetch_monthly_flights.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No flight data available for BRU.")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    @patch("flights.views.TripFinder")
    def test_search_view_no_trips_found(self, mock_finder, mock_client_class):
        """Test search with no matching trips"""
        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }
        mock_client.fetch_monthly_flights.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_client_class.return_value = mock_client

        mock_finder.merge_flights_data.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_finder.find_cheapest.return_value = []

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No trips found")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    @patch("flights.views.TripFinder")
    def test_search_view_success(self, mock_finder, mock_client_class):
        """Test successful search"""
        from datetime import datetime

        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }
        mock_client.fetch_monthly_flights.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_client_class.return_value = mock_client

        mock_finder.merge_flights_data.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_finder.find_cheapest.return_value = [
            {
                "outbound": datetime(2026, 4, 15),
                "inbound": datetime(2026, 4, 22),
                "price": 2100,
                "normal_price": 2500,
                "discount": 16.0,
                "duration": 7,
            }
        ]

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "flights/results.html")
        self.assertIn("trips", response.context)
        self.assertEqual(len(response.context["trips"]), 1)
        self.assertEqual(response.context["total_count"], 1)

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    @patch("flights.views.TripFinder")
    def test_search_view_with_promo_code(self, mock_finder, mock_client_class):
        """Test search with promo code"""
        from datetime import datetime

        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }
        mock_client.fetch_monthly_flights.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_client_class.return_value = mock_client

        mock_finder.merge_flights_data.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_finder.find_cheapest.return_value = [
            {
                "outbound": datetime(2026, 4, 15),
                "inbound": datetime(2026, 4, 22),
                "price": 1800,
                "normal_price": 2500,
                "discount": 28.0,
                "duration": 7,
            }
        ]

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
            "promo_code": "SUMMER2026",
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["promo_code_used"])
        # Verify promo code was passed to API
        mock_client.fetch_monthly_flights.assert_called()
        call_args = mock_client.fetch_monthly_flights.call_args
        self.assertEqual(call_args[0][3], "SUMMER2026")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    def test_search_view_handles_exception(self, mock_client_class):
        """Test search handles unexpected exceptions"""
        mock_client_class.side_effect = Exception("Unexpected error")

        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "error occurred")

    @patch.dict(os.environ, {"URL_API": "https://api.example.com"})
    @patch("flights.views.FlightAPIClient")
    @patch("flights.views.TripFinder")
    def test_search_view_airport_codes_uppercased(self, mock_finder, mock_client_class):
        """Test airport codes are converted to uppercase"""
        mock_client = Mock()
        mock_client.fetch_direct_flights.return_value = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }
        mock_client.fetch_monthly_flights.return_value = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260422": {"totalPrice": 1100}},
        }
        mock_client_class.return_value = mock_client

        mock_finder.merge_flights_data.return_value = {}
        mock_finder.find_cheapest.return_value = []

        form_data = {
            "inbound": "arn",  # lowercase
            "outbound": "bru",  # lowercase
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        self.client.post(self.url, form_data)

        # Verify uppercase was used
        mock_client.fetch_direct_flights.assert_called_with("ARN", "BRU")
