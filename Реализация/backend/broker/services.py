from decimal import Decimal, InvalidOperation

import requests

from .models import Security


MOEX_URL = (
    'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}.json'
)
NBRB_RUB_URL = 'https://api.nbrb.by/exrates/rates/RUB'


def get_market_price(security: Security) -> dict:
    """Return a MOEX price when possible, otherwise the stored demo quote."""
    try:
        response = requests.get(
            MOEX_URL.format(ticker=security.ticker),
            params={
                'iss.meta': 'off',
                'iss.only': 'marketdata,securities',
                'marketdata.columns': 'SECID,LAST,MARKETPRICE',
                'securities.columns': 'SECID,PREVPRICE',
            },
            timeout=2,
        )
        response.raise_for_status()
        payload = response.json()
        market_row = _first_row(payload.get('marketdata', {}))
        security_row = _first_row(payload.get('securities', {}))
        raw_price = None
        if market_row:
            raw_price = market_row.get('LAST') or market_row.get('MARKETPRICE')
        if raw_price is None and security_row:
            raw_price = security_row.get('PREVPRICE')
        price = Decimal(str(raw_price))
        if price <= 0:
            raise ValueError('MOEX returned a non-positive price')
        rate_response = requests.get(
            NBRB_RUB_URL,
            params={'parammode': 2},
            timeout=2,
        )
        rate_response.raise_for_status()
        rate_data = rate_response.json()
        official_rate = Decimal(str(rate_data['Cur_OfficialRate']))
        scale = Decimal(str(rate_data['Cur_Scale']))
        price_byn = price * official_rate / scale
        return {
            'ticker': security.ticker,
            'price': price_byn.quantize(Decimal('0.01')),
            'currency': 'BYN',
            'source': 'moex+nbrb',
        }
    except (requests.RequestException, ValueError, KeyError, TypeError, InvalidOperation):
        return {
            'ticker': security.ticker,
            'error': 'Не удалось получить котировку.',
            'currency': 'BYN',
            'source': 'unavailable',
        }


def _first_row(block):
    columns = block.get('columns') or []
    data = block.get('data') or []
    return dict(zip(columns, data[0])) if data else None
