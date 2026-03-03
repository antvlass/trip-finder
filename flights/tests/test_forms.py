from django.test import TestCase

from flights.forms import FlightSearchForm


class FlightSearchFormTest(TestCase):
    def test_form_valid_with_all_fields(self):
        """Test form is valid with all fields"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "start_month": "202603",
            "num_months": 3,
            "top": 10,
            "only_weekends": False,
            "promo_code": "SUMMER2026",
        }
        form = FlightSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_required_fields_only(self):
        """Test form is valid with only required fields"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        form = FlightSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_required_fields(self):
        """Test form is invalid without required fields"""
        form = FlightSearchForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("inbound", form.errors)
        self.assertIn("outbound", form.errors)

    def test_form_has_correct_fields(self):
        """Test form has all expected fields"""
        form = FlightSearchForm()
        expected_fields = [
            "inbound",
            "outbound",
            "duration_min",
            "duration_max",
            "start_month",
            "num_months",
            "top",
            "only_weekends",
            "promo_code",
        ]
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_promo_code_is_optional(self):
        """Test promo code field is optional"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        form = FlightSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_start_month_is_optional(self):
        """Test start_month field is optional"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        form = FlightSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_only_weekends_is_optional(self):
        """Test only_weekends field is optional"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 3,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        form = FlightSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duration_min_validation(self):
        """Test duration_min must be positive"""
        form_data = {
            "inbound": "ARN",
            "outbound": "BRU",
            "duration_min": 0,
            "duration_max": 10,
            "num_months": 3,
            "top": 10,
        }
        form = FlightSearchForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_initial_values(self):
        """Test form has correct initial values"""
        form = FlightSearchForm()
        self.assertEqual(form.fields["inbound"].initial, "ARN")
        self.assertEqual(form.fields["outbound"].initial, "BRU")
        self.assertEqual(form.fields["duration_min"].initial, 3)
        self.assertEqual(form.fields["duration_max"].initial, 10)
        self.assertEqual(form.fields["num_months"].initial, 3)
        self.assertEqual(form.fields["top"].initial, 10)
