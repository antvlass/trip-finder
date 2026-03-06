from datetime import datetime

from django.test import TestCase

from flights.services.trip_finder import TripFinder


class TripFinderTest(TestCase):
    def test_effective_normal_with_normal_price(self):
        """Test effective normal returns normal price when available"""
        result = TripFinder.effective_normal(1000, 1200)
        self.assertEqual(result, 1200)

    def test_effective_normal_without_normal_price(self):
        """Test effective normal returns total price when normal price is None"""
        result = TripFinder.effective_normal(1000, None)
        self.assertEqual(result, 1000)

    def test_get_leg_prices_with_combi_price(self):
        """Test getting leg prices with combination pricing"""
        detail = {
            "totalPrice": 1000,
            "normalPrice": 1200,
            "combiPrice": {"20260415": {"totalPrice": 900, "normalPrice": 1100}},
        }
        total, normal = TripFinder.get_leg_prices(detail, "20260415")
        self.assertEqual(total, 900)
        self.assertEqual(normal, 1100)

    def test_get_leg_prices_without_combi_price(self):
        """Test getting leg prices without combination pricing"""
        detail = {"totalPrice": 1000, "normalPrice": 1200}
        total, normal = TripFinder.get_leg_prices(detail, "20260415")
        self.assertEqual(total, 1000)
        self.assertEqual(normal, 1200)

    def test_get_leg_prices_missing_combi_key(self):
        """Test getting leg prices when combo key doesn't exist"""
        detail = {
            "totalPrice": 1000,
            "normalPrice": 1200,
            "combiPrice": {"20260420": {"totalPrice": 900, "normalPrice": 1100}},
        }
        total, normal = TripFinder.get_leg_prices(detail, "20260415")
        self.assertEqual(total, 1000)
        self.assertEqual(normal, 1200)

    def test_is_weekend_friday_to_monday(self):
        """Test weekend detection for Friday to Monday"""
        outbound = datetime(2026, 4, 17)  # Friday
        inbound = datetime(2026, 4, 20)  # Monday
        self.assertTrue(TripFinder.is_weekend(outbound, inbound))

    def test_is_weekend_saturday_to_sunday(self):
        """Test weekend detection for Saturday to Sunday"""
        outbound = datetime(2026, 4, 18)  # Saturday
        inbound = datetime(2026, 4, 19)  # Sunday
        self.assertTrue(TripFinder.is_weekend(outbound, inbound))

    def test_is_not_weekend_monday_to_friday(self):
        """Test non-weekend detection for weekday trips"""
        outbound = datetime(2026, 4, 13)  # Monday
        inbound = datetime(2026, 4, 17)  # Friday
        self.assertFalse(TripFinder.is_weekend(outbound, inbound))

    def test_contains_true(self):
        """Test contains returns true when item exists"""
        dates = ["20260415", "20260416", "20260417"]
        self.assertTrue(TripFinder.contains(dates, "20260416"))

    def test_contains_false(self):
        """Test contains returns false when item doesn't exist"""
        dates = ["20260415", "20260416", "20260417"]
        self.assertFalse(TripFinder.contains(dates, "20260420"))

    def test_merge_flights_data(self):
        """Test merging multiple flight data dictionaries"""
        data1 = {
            "outbound": {"20260415": {"totalPrice": 1000}},
            "inbound": {"20260420": {"totalPrice": 1100}},
        }
        data2 = {
            "outbound": {"20260501": {"totalPrice": 1200}},
            "inbound": {"20260505": {"totalPrice": 1300}},
        }
        merged = TripFinder.merge_flights_data([data1, data2])

        self.assertEqual(len(merged["outbound"]), 2)
        self.assertEqual(len(merged["inbound"]), 2)
        self.assertIn("20260415", merged["outbound"])
        self.assertIn("20260501", merged["outbound"])
        self.assertIn("20260420", merged["inbound"])
        self.assertIn("20260505", merged["inbound"])

    def test_find_cheapest_basic(self):
        """Test finding cheapest trips with basic data"""
        all_flights = {
            "outbound": {"20260415": {"totalPrice": 1000, "normalPrice": 1200}},
            "inbound": {"20260422": {"totalPrice": 1100, "normalPrice": 1300}},
        }
        direct_flights = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260422"]},
        }

        trips = TripFinder.find_cheapest(all_flights, direct_flights, 3, 10, False, 10)

        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0]["price"], 2100)
        self.assertEqual(trips[0]["normal_price"], 2500)
        self.assertEqual(trips[0]["duration"], 7)

    def test_find_cheapest_filters_by_duration(self):
        """Test that trips are filtered by duration"""
        all_flights = {
            "outbound": {"20260415": {"totalPrice": 1000, "normalPrice": 1200}},
            "inbound": {
                "20260417": {"totalPrice": 1100, "normalPrice": 1300},  # 2 days
                "20260425": {"totalPrice": 1050, "normalPrice": 1250},  # 10 days
            },
        }
        direct_flights = {
            "outbound": {"202604": ["20260415"]},
            "inbound": {"202604": ["20260417", "20260425"]},
        }

        trips = TripFinder.find_cheapest(all_flights, direct_flights, 3, 9, False, 10)

        # Should exclude 2-day trip (too short) and 10-day trip (too long)
        self.assertEqual(len(trips), 0)

    def test_find_cheapest_weekend_filter(self):
        """Test weekend filtering"""
        all_flights = {
            "outbound": {
                "20260417": {"totalPrice": 1000, "normalPrice": 1200},  # Friday
                "20260413": {"totalPrice": 900, "normalPrice": 1100},  # Monday
            },
            "inbound": {
                "20260420": {"totalPrice": 1100, "normalPrice": 1300},  # Monday
                "20260417": {"totalPrice": 1050, "normalPrice": 1250},  # Friday
            },
        }
        direct_flights = {
            "outbound": {"202604": ["20260417", "20260413"]},
            "inbound": {"202604": ["20260420", "20260417"]},
        }

        trips = TripFinder.find_cheapest(all_flights, direct_flights, 3, 5, True, 10)

        # Should only include Friday to Monday trip
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0]["outbound"].weekday(), 4)  # Friday
        self.assertEqual(trips[0]["inbound"].weekday(), 0)  # Monday

    def test_find_cheapest_sorts_by_price(self):
        """Test that trips are sorted by price"""
        all_flights = {
            "outbound": {
                "20260415": {"totalPrice": 1500, "normalPrice": 1700},
                "20260420": {"totalPrice": 1000, "normalPrice": 1200},
            },
            "inbound": {
                "20260422": {"totalPrice": 1100, "normalPrice": 1300},
                "20260427": {"totalPrice": 1100, "normalPrice": 1300},
            },
        }
        direct_flights = {
            "outbound": {"202604": ["20260415", "20260420"]},
            "inbound": {"202604": ["20260422", "20260427"]},
        }

        trips = TripFinder.find_cheapest(all_flights, direct_flights, 3, 10, False, 10)

        # Should be sorted by price (cheapest first)
        self.assertGreaterEqual(len(trips), 2)
        self.assertLessEqual(trips[0]["price"], trips[1]["price"])

    def test_find_cheapest_limits_results(self):
        """Test that results are limited to max_results"""
        all_flights = {
            "outbound": {
                f"2026041{i}": {"totalPrice": 1000 + i * 10, "normalPrice": 1200}
                for i in range(5, 10)
            },
            "inbound": {
                f"2026042{i}": {"totalPrice": 1100, "normalPrice": 1300} for i in range(0, 5)
            },
        }
        direct_flights = {
            "outbound": {"202604": [f"2026041{i}" for i in range(5, 10)]},
            "inbound": {"202604": [f"2026042{i}" for i in range(0, 5)]},
        }

        trips = TripFinder.find_cheapest(all_flights, direct_flights, 3, 20, False, 3)

        # Should limit to 3 results
        self.assertEqual(len(trips), 3)
