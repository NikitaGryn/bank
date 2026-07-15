from decimal import Decimal
from unittest.mock import patch

import requests
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DemoAccount, Holding, Security


class BrokerApiTests(APITestCase):
    def setUp(self):
        self.account = DemoAccount.objects.create(
            name='Демо-счёт', cash_balance=Decimal('100000.00')
        )
        self.sber = Security.objects.create(
            ticker='SBER',
            name='Сбер Банк',
            security_type=Security.SecurityType.STOCK,
            current_price=Decimal('300.00'),
            previous_close=Decimal('295.00'),
        )
        self.bond = Security.objects.create(
            ticker='OFZ1',
            name='ОФЗ тестовая',
            security_type=Security.SecurityType.BOND,
            current_price=Decimal('980.00'),
            previous_close=Decimal('979.00'),
        )
        self.holding = Holding.objects.create(
            account=self.account,
            security=self.sber,
            quantity=Decimal('10'),
            average_price=Decimal('280.00'),
        )

    def test_health(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    def test_portfolio(self):
        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_value'], Decimal('103000.00'))
        self.assertEqual(response.data['holdings'][0]['ticker'], 'SBER')

    def test_successful_buy(self):
        response = self.client.post(
            '/api/trade/', {'ticker': 'SBER', 'side': 'BUY', 'quantity': '2'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.holding.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.holding.quantity, Decimal('12'))
        self.assertEqual(self.account.cash_balance, Decimal('99398.50'))

    def test_buy_with_insufficient_funds(self):
        response = self.client.post(
            '/api/trade/',
            {'ticker': 'SBER', 'side': 'BUY', 'quantity': '1000'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Недостаточно', response.data['detail'])

    def test_successful_sell(self):
        response = self.client.post(
            '/api/trade/', {'ticker': 'SBER', 'side': 'SELL', 'quantity': '3'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.holding.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.holding.quantity, Decimal('7'))
        self.assertEqual(self.account.cash_balance, Decimal('100897.75'))

    def test_sell_with_insufficient_holding(self):
        response = self.client.post(
            '/api/trade/', {'ticker': 'SBER', 'side': 'SELL', 'quantity': '11'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Недостаточно', response.data['detail'])

    def test_deposit(self):
        response = self.client.post('/api/deposit/', {'amount': '5000.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cash_balance'], Decimal('105000.00'))

    def test_withdrawal(self):
        response = self.client.post('/api/withdraw/', {'amount': '2500.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cash_balance'], Decimal('97500.00'))

    @patch('broker.services.requests.get', side_effect=requests.Timeout)
    def test_market_fallback_shape(self, mocked_get):
        response = self.client.get('/api/market/SBER/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data), {'ticker', 'error', 'currency', 'source'}
        )
        self.assertEqual(response.data['source'], 'unavailable')

    def test_security_search_and_type_filters(self):
        search_response = self.client.get('/api/securities/', {'search': 'сбер'})
        self.assertEqual(len(search_response.data), 1)
        self.assertEqual(search_response.data[0]['ticker'], 'SBER')

        type_response = self.client.get('/api/securities/', {'type': 'BOND'})
        self.assertEqual(len(type_response.data), 1)
        self.assertEqual(type_response.data[0]['ticker'], 'OFZ1')
