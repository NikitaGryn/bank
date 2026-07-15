import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api import ApiClient


class ApiClientTests(unittest.TestCase):
    def test_trade_normalizes_side_for_backend(self):
        client = ApiClient()
        client._request = Mock(return_value={"order": {"id": 1}})

        ok, _ = client.trade("SBER", "buy", 2, 300)

        self.assertTrue(ok)
        client._request.assert_called_once_with(
            "POST",
            "trade",
            {"ticker": "SBER", "side": "BUY", "quantity": 2, "price": 300},
        )

    def test_offline_buy_updates_demo_account(self):
        client = ApiClient()
        client._request = Mock(return_value=None)
        cash_before = client.demo_portfolio["cash"]

        ok, message = client.trade("GAZP", "buy", 2, 5.21)

        self.assertTrue(ok)
        self.assertIn("исполнена", message)
        self.assertLess(client.demo_portfolio["cash"], cash_before)
        self.assertEqual(client.demo_orders[0]["ticker"], "GAZP")

    def test_offline_sell_checks_holding(self):
        client = ApiClient()
        client._request = Mock(return_value=None)

        ok, message = client.trade("GAZP", "sell", 100, 5.21)

        self.assertFalse(ok)
        self.assertIn("Недостаточно", message)

    def test_offline_deposit_updates_balance(self):
        client = ApiClient()
        client._request = Mock(return_value=None)
        cash_before = client.demo_portfolio["cash"]

        ok, _ = client.deposit(1000)

        self.assertTrue(ok)
        self.assertEqual(client.demo_portfolio["cash"], cash_before + 1000)


if __name__ == "__main__":
    unittest.main()
