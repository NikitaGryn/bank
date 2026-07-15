import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api import DEMO_EVENTS, DEMO_ORDERS, DEMO_PORTFOLIO, DEMO_SECURITIES, DEMO_TRANSACTIONS
from main import InvestmentsApp


class FakePage:
    def __init__(self, width=390):
        self.width = width
        self.controls = []
        self.navigation_bar = None

    def clean(self):
        self.controls.clear()

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        pass

    def show_dialog(self, dialog):
        self.last_dialog = dialog


class FakeApi:
    offline = True

    def security(self, ticker):
        return next(item for item in DEMO_SECURITIES if item["ticker"] == ticker)

    def market(self, ticker):
        return {}

    def orderbook(self, ticker):
        return {
            "bids": [{"price": 740.30, "quantity": 100}],
            "asks": [{"price": 740.40, "quantity": 120}],
        }


class UiConstructionTests(unittest.TestCase):
    def setUp(self):
        self.page = FakePage()
        self.app = InvestmentsApp(self.page)
        self.app.api = FakeApi()
        self.app.logged_in = True
        self.app.portfolio = DEMO_PORTFOLIO
        self.app.securities = DEMO_SECURITIES
        self.app.orders = DEMO_ORDERS
        self.app.transactions = DEMO_TRANSACTIONS
        self.app.events = DEMO_EVENTS

    def test_constructs_all_mobile_screens(self):
        screens = [
            self.app.portfolio_screen(),
            self.app.market_screen(),
            self.app.orders_screen(),
            self.app.services_screen(),
            self.app.profile_screen(),
            self.app.security_detail("SBER"),
        ]
        self.assertEqual(len(screens), 6)

    def test_constructs_mobile_and_desktop_shells(self):
        self.app.render_shell()
        self.assertIsNotNone(self.page.navigation_bar)
        self.page.width = 1200
        self.app.render_shell()
        self.assertIsNone(self.page.navigation_bar)
        self.assertTrue(self.page.controls)


if __name__ == "__main__":
    unittest.main()
