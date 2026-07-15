from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


COMMISSION_RATE = Decimal("0.0025")


def to_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
    """Convert API and form values to Decimal without leaking conversion errors."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return default
    try:
        return Decimal(str(value).strip().replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return default


def money(value: object, currency: str = "BYN") -> str:
    amount = to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    integer, fraction = f"{amount:.2f}".split(".")
    grouped = f"{int(integer):,}".replace(",", " ")
    return f"{sign}{grouped},{fraction} {currency}".strip()


def percent(value: object, signed: bool = True) -> str:
    number = to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    prefix = "+" if signed and number > 0 else ""
    return f"{prefix}{str(number).replace('.', ',')}%"


def trade_calculation(
    quantity: object,
    price: object,
    commission_rate: object = COMMISSION_RATE,
) -> dict[str, Decimal]:
    qty = to_decimal(quantity)
    unit_price = to_decimal(price)
    rate = to_decimal(commission_rate)
    if qty <= 0:
        raise ValueError("Количество должно быть больше нуля")
    if unit_price <= 0:
        raise ValueError("Цена должна быть больше нуля")
    subtotal = (qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    commission = (subtotal * rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return {
        "subtotal": subtotal,
        "commission": commission,
        "total": subtotal + commission,
    }
