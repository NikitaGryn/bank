import sys
import unittest
from decimal import Decimal
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers import money, percent, to_decimal, trade_calculation


class FormattingTests(unittest.TestCase):
    def test_money_uses_belarusian_style(self):
        self.assertEqual(money("12345.6"), "12 345,60 BYN")
        self.assertEqual(money("-7.1", "USD"), "-7,10 USD")

    def test_percent_adds_positive_sign(self):
        self.assertEqual(percent("4.645"), "+4,65%")
        self.assertEqual(percent("-1.2"), "-1,20%")

    def test_decimal_accepts_comma_and_spaces(self):
        self.assertEqual(to_decimal("1 250,25"), Decimal("1250.25"))


class TradeCalculationTests(unittest.TestCase):
    def test_calculates_commission_and_total(self):
        result = trade_calculation(10, "740,35")
        self.assertEqual(result["subtotal"], Decimal("7403.50"))
        self.assertEqual(result["commission"], Decimal("18.51"))
        self.assertEqual(result["total"], Decimal("7422.01"))

    def test_rejects_non_positive_values(self):
        with self.assertRaises(ValueError):
            trade_calculation(0, 100)
        with self.assertRaises(ValueError):
            trade_calculation(2, -1)


if __name__ == "__main__":
    unittest.main()
