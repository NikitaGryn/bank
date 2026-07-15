from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import requests


DEMO_SECURITIES = [
    {"ticker": "SBER", "name": "Сбер Банк", "type": "Акции", "price": 11.18, "change_percent": 0.86, "currency": "BYN"},
    {"ticker": "GAZP", "name": "Газпром", "type": "Акции", "price": 4.92, "change_percent": -0.99, "currency": "BYN"},
    {"ticker": "LKOH", "name": "ЛУКОЙЛ", "type": "Акции", "price": 257.35, "change_percent": 1.18, "currency": "BYN"},
    {"ticker": "YNDX", "name": "Яндекс", "type": "Акции", "price": 148.50, "change_percent": 0.89, "currency": "BYN"},
]

DEMO_PORTFOLIO = {
    "currency": "BYN",
    "total_value": 5686.06,
    "cash": 5000.00,
    "profit": 52.30,
    "profit_percent": 0.93,
    "holdings": [
        {"ticker": "SBER", "name": "Сбер Банк", "quantity": 12, "price": 11.18, "value": 134.16, "profit": 12.60, "change_percent": 10.36},
        {"ticker": "GAZP", "name": "Газпром", "quantity": 20, "price": 4.92, "value": 98.40, "profit": -6.20, "change_percent": -5.93},
        {"ticker": "LKOH", "name": "ЛУКОЙЛ", "quantity": 2, "price": 257.35, "value": 514.70, "profit": 24.38, "change_percent": 4.97},
    ],
}

DEMO_ORDERS = [
    {"id": 1042, "ticker": "SBER", "side": "buy", "quantity": 2, "price": 10.13, "status": "Исполнена", "created_at": "Сегодня, 14:32"},
    {"id": 1038, "ticker": "GAZP", "side": "buy", "quantity": 5, "price": 5.23, "status": "Исполнена", "created_at": "Сегодня, 10:15"},
]

DEMO_TRANSACTIONS = [
    {"id": 1, "type": "deposit", "description": "Пополнение брокерского счёта", "amount": 5000, "created_at": "14 июля, 10:05"},
    {"id": 2, "type": "buy", "description": "Покупка SBER", "amount": -20.31, "created_at": "12 июля, 16:48"},
]

DEMO_EVENTS = [
    {"date": "18 июля", "type": "Отчётность", "title": "Сбер Банк SBER"},
    {"date": "24 июля", "type": "Дивиденды", "title": "ЛУКОЙЛ LKOH"},
]


class ApiClient:
    """Small synchronous client; Flet handlers execute requests with short timeouts."""

    def __init__(self, base_url: str | None = None, timeout: float = 2.5):
        self.base_url = (base_url or os.getenv("BROKER_API_URL") or "http://127.0.0.1:8000/api").rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.offline = False
        self.demo_portfolio = deepcopy(DEMO_PORTFOLIO)
        self.demo_securities = deepcopy(DEMO_SECURITIES)
        self.demo_orders = deepcopy(DEMO_ORDERS)
        self.demo_transactions = deepcopy(DEMO_TRANSACTIONS)
        self.demo_events = deepcopy(DEMO_EVENTS)

    @staticmethod
    def _list(payload: Any, *keys: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in (*keys, "results", "items", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _request(self, method: str, path: str, payload: dict | None = None) -> Any:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}/{path.strip('/')}/",
                json=payload,
                timeout=self.timeout,
            )
            self.offline = False
            if response.status_code >= 400:
                try:
                    error = response.json()
                except ValueError:
                    error = {}
                return {
                    "error": error.get("detail")
                    or error.get("error")
                    or f"Ошибка сервера: {response.status_code}"
                }
            if not response.content:
                return {}
            return response.json()
        except (requests.RequestException, ValueError):
            self.offline = True
            return None

    def health(self) -> bool:
        return self._request("GET", "health") is not None

    def portfolio(self) -> dict[str, Any]:
        data = self._request("GET", "portfolio")
        return data if isinstance(data, dict) and not data.get("error") else deepcopy(self.demo_portfolio)

    def securities(self) -> list[dict[str, Any]]:
        data = self._request("GET", "securities")
        rows = self._list(data, "securities")
        return rows or deepcopy(self.demo_securities)

    def security(self, ticker: str) -> dict[str, Any]:
        data = self._request("GET", f"securities/{ticker}")
        if isinstance(data, dict) and not data.get("error"):
            return data
        return deepcopy(
            next((x for x in self.demo_securities if x["ticker"] == ticker), self.demo_securities[0])
        )

    def market(self, ticker: str) -> dict[str, Any]:
        data = self._request("GET", f"market/{ticker}")
        if isinstance(data, dict) and not data.get("error"):
            return data
        try:
            response = requests.get(
                "https://iss.moex.com/iss/engines/stock/markets/shares/"
                f"securities/{ticker}.json",
                params={
                    "iss.meta": "off",
                    "iss.only": "marketdata",
                    "marketdata.columns": "SECID,LAST,MARKETPRICE",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            block = response.json().get("marketdata", {})
            columns = block.get("columns", [])
            for row in block.get("data", []):
                quote = dict(zip(columns, row))
                price = quote.get("LAST") or quote.get("MARKETPRICE")
                if price:
                    rate_response = requests.get(
                        "https://api.nbrb.by/exrates/rates/RUB",
                        params={"parammode": 2},
                        timeout=self.timeout,
                    )
                    rate_response.raise_for_status()
                    rate_data = rate_response.json()
                    price_byn = (
                        Decimal(str(price))
                        * Decimal(str(rate_data["Cur_OfficialRate"]))
                        / Decimal(str(rate_data["Cur_Scale"]))
                    )
                    return {
                        "ticker": ticker,
                        "price": float(price_byn.quantize(Decimal("0.01"))),
                        "currency": "BYN",
                        "source": "moex+nbrb-direct",
                    }
        except (requests.RequestException, ValueError, TypeError, KeyError, InvalidOperation):
            pass
        return {
            "ticker": ticker,
            "currency": "BYN",
            "source": "unavailable",
            "error": "Не удалось получить цену акции",
        }

    def orderbook(self, ticker: str) -> dict[str, Any]:
        data = self._request("GET", f"securities/{ticker}/orderbook")
        if isinstance(data, dict):
            return data
        return {
            "bids": [{"price": 740.30 - i * .05, "quantity": 1250 + i * 330} for i in range(4)],
            "asks": [{"price": 740.40 + i * .05, "quantity": 1120 + i * 410} for i in range(4)],
        }

    def orders(self) -> list[dict[str, Any]]:
        data = self._request("GET", "orders")
        return self._list(data, "orders") or deepcopy(self.demo_orders)

    def transactions(self) -> list[dict[str, Any]]:
        data = self._request("GET", "transactions")
        return self._list(data, "transactions") or deepcopy(self.demo_transactions)

    def events(self) -> list[dict[str, Any]]:
        data = self._request("GET", "events")
        return self._list(data, "events") or deepcopy(self.demo_events)

    def trade(self, ticker: str, side: str, quantity: float, price: float | None = None) -> tuple[bool, str]:
        normalized_side = side.upper()
        payload: dict[str, Any] = {
            "ticker": ticker,
            "side": normalized_side,
            "quantity": quantity,
        }
        if price is not None:
            payload["price"] = price
        data = self._request("POST", "trade", payload)
        if data is None:
            return self._demo_trade(ticker, normalized_side, quantity, price)
        if isinstance(data, dict) and data.get("error"):
            return False, str(data["error"])
        return True, "Заявка успешно отправлена"

    def deposit(self, amount: float) -> tuple[bool, str]:
        return self._money_action("deposit", amount)

    def withdraw(self, amount: float) -> tuple[bool, str]:
        return self._money_action("withdraw", amount)

    def _money_action(self, path: str, amount: float) -> tuple[bool, str]:
        data = self._request("POST", path, {"amount": amount})
        if data is None:
            value = Decimal(str(amount))
            cash = Decimal(str(self.demo_portfolio["cash"]))
            if path == "withdraw":
                if value > cash:
                    return False, "Недостаточно денежных средств"
                value = -value
            cash += value
            self.demo_portfolio["cash"] = float(cash)
            self.demo_portfolio["total_value"] = float(
                cash
                + sum(
                    Decimal(str(item.get("value", 0)))
                    for item in self.demo_portfolio["holdings"]
                )
            )
            self.demo_transactions.insert(
                0,
                {
                    "id": len(self.demo_transactions) + 1,
                    "type": "deposit" if path == "deposit" else "withdrawal",
                    "description": "Пополнение брокерского счёта"
                    if path == "deposit"
                    else "Вывод средств",
                    "amount": float(value),
                    "created_at": "Только что",
                },
            )
            message = "Счёт пополнен" if path == "deposit" else "Средства выведены"
            return True, message
        if isinstance(data, dict) and data.get("error"):
            return False, str(data["error"])
        message = "Счёт пополнен" if path == "deposit" else "Средства выведены"
        return True, message

    def _demo_trade(
        self, ticker: str, side: str, quantity: float, price: float | None
    ) -> tuple[bool, str]:
        security = next((item for item in self.demo_securities if item["ticker"] == ticker), None)
        if not security:
            return False, "Инструмент не найден"
        qty = Decimal(str(quantity))
        trade_price = Decimal(str(price if price is not None else security["price"]))
        gross = (qty * trade_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        commission = (gross * Decimal("0.0025")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cash = Decimal(str(self.demo_portfolio["cash"]))
        holding = next(
            (item for item in self.demo_portfolio["holdings"] if item["ticker"] == ticker),
            None,
        )
        if side == "BUY":
            total = gross + commission
            if cash < total:
                return False, "Недостаточно денежных средств"
            cash -= total
            if holding is None:
                holding = {
                    "ticker": ticker,
                    "name": security["name"],
                    "quantity": 0,
                    "price": float(trade_price),
                    "value": 0,
                    "profit": 0,
                    "change_percent": security.get("change_percent", 0),
                }
                self.demo_portfolio["holdings"].append(holding)
            holding["quantity"] = float(Decimal(str(holding["quantity"])) + qty)
        else:
            if holding is None or Decimal(str(holding["quantity"])) < qty:
                return False, "Недостаточно ценных бумаг"
            cash += gross - commission
            holding["quantity"] = float(Decimal(str(holding["quantity"])) - qty)
        holding["price"] = float(trade_price)
        holding["value"] = float(
            Decimal(str(holding["quantity"])) * trade_price
        )
        self.demo_portfolio["cash"] = float(cash)
        self.demo_portfolio["total_value"] = float(
            cash
            + sum(
                Decimal(str(item.get("value", 0)))
                for item in self.demo_portfolio["holdings"]
            )
        )
        order_id = max((int(item.get("id", 0)) for item in self.demo_orders), default=1000) + 1
        self.demo_orders.insert(
            0,
            {
                "id": order_id,
                "ticker": ticker,
                "side": side,
                "quantity": float(qty),
                "price": float(trade_price),
                "commission": float(commission),
                "status": "Исполнена",
                "created_at": "Только что",
            },
        )
        cash_change = -(gross + commission) if side == "BUY" else gross - commission
        self.demo_transactions.insert(
            0,
            {
                "id": len(self.demo_transactions) + 1,
                "type": side.lower(),
                "description": f"{'Покупка' if side == 'BUY' else 'Продажа'} {ticker}",
                "amount": float(cash_change),
                "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            },
        )
        return True, "Сделка исполнена"
