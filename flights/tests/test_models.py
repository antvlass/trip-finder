from datetime import date

from django.test import TestCase

from flights.models import Airport, Trip


class AirportModelTest(TestCase):
    def setUp(self):
        self.airport = Airport.objects.create(
            code="ARN",
            name="Stockholm Arlanda",
            country_code="SE",
            latitude=59.6519,
            longitude=17.9186,
        )

    def test_airport_creation(self):
        """Test airport is created correctly"""
        self.assertEqual(self.airport.code, "ARN")
        self.assertEqual(self.airport.name, "Stockholm Arlanda")
        self.assertEqual(self.airport.country_code, "SE")

    def test_airport_str(self):
        """Test airport string representation"""
        self.assertEqual(str(self.airport), "ARN - Stockholm Arlanda")

    def test_airport_ordering(self):
        """Test airports are ordered by code"""
        Airport.objects.create(
            code="BRU",
            name="Brussels",
            country_code="BE",
            latitude=50.9014,
            longitude=4.4844,
        )
        airports = Airport.objects.all()
        self.assertEqual(airports[0].code, "ARN")
        self.assertEqual(airports[1].code, "BRU")


class TripModelTest(TestCase):
    def setUp(self):
        self.trip = Trip.objects.create(
            outbound_airport="ARN",
            inbound_airport="BRU",
            outbound_date=date(2026, 4, 15),
            inbound_date=date(2026, 4, 22),
            price=1234,
            normal_price=1500,
            discount=17.7,
        )

    def test_trip_creation(self):
        """Test trip is created correctly"""
        self.assertEqual(self.trip.outbound_airport, "ARN")
        self.assertEqual(self.trip.inbound_airport, "BRU")
        self.assertEqual(self.trip.price, 1234)
        self.assertEqual(self.trip.normal_price, 1500)

    def test_trip_str(self):
        """Test trip string representation"""
        expected = "ARN → BRU (2026-04-15 - 2026-04-22)"
        self.assertEqual(str(self.trip), expected)

    def test_duration_days(self):
        """Test duration calculation"""
        self.assertEqual(self.trip.duration_days, 7)

    def test_formatted_price(self):
        """Test price formatting"""
        self.assertEqual(self.trip.formatted_price, "1,234")

    def test_formatted_normal_price(self):
        """Test normal price formatting"""
        self.assertEqual(self.trip.formatted_normal_price, "1,500")

    def test_trip_ordering(self):
        """Test trips are ordered by price then date"""
        Trip.objects.create(
            outbound_airport="ARN",
            inbound_airport="CPH",
            outbound_date=date(2026, 5, 1),
            inbound_date=date(2026, 5, 5),
            price=1000,
            normal_price=1200,
            discount=16.7,
        )
        trips = Trip.objects.all()
        self.assertEqual(trips[0].price, 1000)
        self.assertEqual(trips[1].price, 1234)
