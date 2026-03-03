from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from flights.services.flight_client import FlightAPIClient


class FlightAPIClientTest(TestCase):
    def setUp(self):
        self.client = FlightAPIClient("https://api.example.com", max_retries=2)

    def test_client_initialization(self):
        """Test client is initialized correctly"""
        self.assertEqual(self.client.base_url, "https://api.example.com")
        self.assertEqual(self.client.max_retries, 2)
        self.assertIsInstance(self.client.session, requests.Session)

    @patch("flights.services.flight_client.requests.Session.get")
    def test_fetch_with_retries_success(self, mock_get):
        """Test successful API call"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = self.client._fetch_with_retries("/test", {"param": "value"})

        self.assertEqual(result, {"data": "test"})
        mock_get.assert_called_once()

    @patch("flights.services.flight_client.requests.Session.get")
    @patch("flights.services.flight_client.time.sleep")
    def test_fetch_with_retries_failure(self, mock_sleep, mock_get):
        """Test API call failure after retries"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.client._fetch_with_retries("/test", {"param": "value"})

        self.assertIn("Failed after", str(context.exception))
        self.assertEqual(mock_get.call_count, 2)  # max_retries

    @patch("flights.services.flight_client.requests.Session.get")
    @patch("flights.services.flight_client.time.sleep")
    def test_fetch_with_retries_request_exception(self, mock_sleep, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with self.assertRaises(Exception) as context:
            self.client._fetch_with_retries("/test", {"param": "value"})

        self.assertIn("Failed after", str(context.exception))
        self.assertEqual(mock_get.call_count, 2)

    @patch("flights.services.flight_client.requests.Session.get")
    @patch("flights.services.flight_client.time.sleep")
    def test_fetch_with_retries_eventually_succeeds(self, mock_sleep, mock_get):
        """Test API call succeeds after initial failures"""
        mock_fail = Mock()
        mock_fail.status_code = 500
        mock_fail.reason = "Internal Server Error"

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_get.side_effect = [mock_fail, mock_success]

        result = self.client._fetch_with_retries("/test", {"param": "value"})

        self.assertEqual(result, {"data": "success"})
        self.assertEqual(mock_get.call_count, 2)

    @patch.object(FlightAPIClient, "_fetch_with_retries")
    def test_fetch_monthly_flights(self, mock_fetch):
        """Test fetch_monthly_flights calls API with correct parameters"""
        mock_fetch.return_value = {"outbound": {}, "inbound": {}}

        result = self.client.fetch_monthly_flights("202603", "ARN", "BRU", "PROMO")

        mock_fetch.assert_called_once_with(
            "/flights/calendar/prices",
            {
                "cepId": "PROMO",
                "flow": "",
                "from": "ARN",
                "market": "se-sv",
                "month": "202603,202603",
                "product": "All,All",
                "to": "BRU",
                "type": "adults-children",
            },
        )
        self.assertEqual(result, {"outbound": {}, "inbound": {}})

    @patch.object(FlightAPIClient, "_fetch_with_retries")
    def test_fetch_monthly_flights_without_promo(self, mock_fetch):
        """Test fetch_monthly_flights without promo code"""
        mock_fetch.return_value = {"outbound": {}, "inbound": {}}

        self.client.fetch_monthly_flights("202603", "ARN", "BRU")

        call_args = mock_fetch.call_args[0][1]
        self.assertEqual(call_args["cepId"], "")

    @patch.object(FlightAPIClient, "_fetch_with_retries")
    def test_fetch_direct_flights(self, mock_fetch):
        """Test fetch_direct_flights calls API with correct parameters"""
        mock_fetch.return_value = {"outbound": {}, "inbound": {}}

        result = self.client.fetch_direct_flights("ARN", "BRU")

        mock_fetch.assert_called_once_with(
            "/flights/schedule/direct",
            {"market": "se-sv", "from": "ARN", "to": "BRU", "triptype": "R"},
        )
        self.assertEqual(result, {"outbound": {}, "inbound": {}})

    @patch("flights.services.flight_client.requests.Session.get")
    @patch("flights.services.flight_client.time.sleep")
    def test_exponential_backoff(self, mock_sleep, mock_get):
        """Test exponential backoff timing"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_get.return_value = mock_response

        try:
            self.client._fetch_with_retries("/test", {"param": "value"})
        except Exception:
            pass

        # Check that sleep was called with exponentially increasing times
        # First retry: 2^0 = 1, Second retry: 2^1 = 2
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(len(sleep_calls), 2)
        self.assertEqual(sleep_calls[0], 1)
        self.assertEqual(sleep_calls[1], 2)
