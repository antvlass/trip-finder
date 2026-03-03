from datetime import datetime

from django.test import TestCase

from flights.services.utils import format_price, generate_months


class GenerateMonthsTest(TestCase):
    def test_generate_months_with_start_month(self):
        """Test generating months from specific start month"""
        months = generate_months("202603", 3)
        self.assertEqual(len(months), 3)
        self.assertEqual(months[0], "202603")
        self.assertEqual(months[1], "202604")
        self.assertEqual(months[2], "202605")

    def test_generate_months_year_rollover(self):
        """Test generating months with year rollover"""
        months = generate_months("202611", 3)
        self.assertEqual(len(months), 3)
        self.assertEqual(months[0], "202611")
        self.assertEqual(months[1], "202612")
        self.assertEqual(months[2], "202701")

    def test_generate_months_without_start_month(self):
        """Test generating months from current month"""
        months = generate_months(None, 3)
        self.assertEqual(len(months), 3)
        current_month = datetime.now().strftime("%Y%m")
        self.assertEqual(months[0], current_month)

    def test_generate_months_single_month(self):
        """Test generating single month"""
        months = generate_months("202603", 1)
        self.assertEqual(len(months), 1)
        self.assertEqual(months[0], "202603")

    def test_generate_months_many_months(self):
        """Test generating many months"""
        months = generate_months("202601", 12)
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0], "202601")
        self.assertEqual(months[11], "202612")

    def test_generate_months_invalid_format(self):
        """Test handling invalid month format"""
        # Should fall back to current month
        months = generate_months("invalid", 3)
        self.assertEqual(len(months), 3)


class FormatPriceTest(TestCase):
    def test_format_price_with_thousands(self):
        """Test formatting price with thousands separator"""
        self.assertEqual(format_price(1234), "1,234")

    def test_format_price_without_thousands(self):
        """Test formatting price without thousands"""
        self.assertEqual(format_price(999), "999")

    def test_format_price_large_number(self):
        """Test formatting large price"""
        self.assertEqual(format_price(12345), "12,345")

    def test_format_price_zero(self):
        """Test formatting zero"""
        self.assertEqual(format_price(0), "0")

    def test_format_price_negative(self):
        """Test formatting negative price"""
        self.assertEqual(format_price(-1234), "-1,234")
