from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import DemoAccount, Holding, MarketEvent, Order, Security, Transaction
from .serializers import (
    AmountSerializer,
    MarketEventSerializer,
    OrderSerializer,
    SecuritySerializer,
    TradeSerializer,
    TransactionSerializer,
)
from .services import get_market_price

MONEY = Decimal('0.01')
COMMISSION_RATE = Decimal('0.0025')


def demo_account():
    account = DemoAccount.objects.order_by('pk').first()
    if account:
        return account
    account = DemoAccount.objects.create(
        name='Брокерский счёт',
        cash_balance=Decimal('5000.00'),
        currency='BYN',
    )
    return account


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'broker-demo'})


@api_view(['GET'])
def portfolio(request):
    account = demo_account()
    holdings = account.holdings.select_related('security').filter(quantity__gt=0)
    rows = []
    holdings_value = Decimal('0')
    profit = Decimal('0')
    for holding in holdings:
        value = (holding.quantity * holding.security.current_price).quantize(MONEY)
        position_profit = (
            holding.quantity * (holding.security.current_price - holding.average_price)
        ).quantize(MONEY)
        holdings_value += value
        profit += position_profit
        rows.append(
            {
                'ticker': holding.security.ticker,
                'name': holding.security.name,
                'quantity': holding.quantity,
                'average_price': holding.average_price,
                'current_price': holding.security.current_price,
                'value': value,
                'profit': position_profit,
                'profit_percent': (
                    (holding.security.current_price - holding.average_price)
                    / holding.average_price
                    * 100
                ).quantize(MONEY)
                if holding.average_price
                else Decimal('0'),
            }
        )
    total_value = (account.cash_balance + holdings_value).quantize(MONEY)
    for row in rows:
        row['allocation'] = (
            (row['value'] / total_value * 100).quantize(MONEY)
            if total_value
            else Decimal('0')
        )
    return Response(
        {
            'account': account.name,
            'currency': account.currency,
            'cash': account.cash_balance,
            'holdings_value': holdings_value.quantize(MONEY),
            'total_value': total_value,
            'profit': profit.quantize(MONEY),
            'holdings': rows,
        }
    )


@api_view(['GET'])
def securities(request):
    queryset = Security.objects.filter(is_active=True)
    search = request.query_params.get('search', '').strip()
    security_type = request.query_params.get('type', '').strip().upper()
    if security_type:
        queryset = queryset.filter(security_type=security_type)
    if search:
        needle = search.casefold()
        queryset = [
            item
            for item in queryset
            if needle in item.ticker.casefold() or needle in item.name.casefold()
        ]
    return Response(SecuritySerializer(queryset, many=True).data)


@api_view(['GET'])
def security_detail(request, ticker):
    security = get_object_or_404(Security, ticker__iexact=ticker, is_active=True)
    data = SecuritySerializer(security).data
    data['chart'] = _chart_points(security)
    return Response(data)


@api_view(['GET'])
def orderbook(request, ticker):
    security = get_object_or_404(Security, ticker__iexact=ticker, is_active=True)
    center = security.current_price
    bids = []
    asks = []
    seed = int(sha256(security.ticker.encode()).hexdigest()[:6], 16)
    for level in range(1, 8):
        offset = Decimal(level) * Decimal('0.001')
        quantity = (seed % 90 + 10) * level
        bids.append(
            {'price': (center * (1 - offset)).quantize(MONEY), 'quantity': quantity}
        )
        asks.append(
            {'price': (center * (1 + offset)).quantize(MONEY), 'quantity': quantity + 7}
        )
    return Response({'ticker': security.ticker, 'bids': bids, 'asks': asks})


@api_view(['POST'])
def trade(request):
    serializer = TradeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    security = get_object_or_404(Security, ticker=values['ticker'], is_active=True)
    price = values.get('price', security.current_price)
    quantity = values['quantity']
    gross = (price * quantity).quantize(MONEY, rounding=ROUND_HALF_UP)
    commission = (gross * COMMISSION_RATE).quantize(MONEY, rounding=ROUND_HALF_UP)

    with transaction.atomic():
        account = DemoAccount.objects.select_for_update().get(pk=demo_account().pk)
        holding, _ = Holding.objects.select_for_update().get_or_create(
            account=account,
            security=security,
            defaults={'quantity': Decimal('0'), 'average_price': Decimal('0')},
        )
        if values['side'] == Order.Side.BUY:
            cash_change = -(gross + commission)
            if account.cash_balance < -cash_change:
                return Response(
                    {'detail': 'Недостаточно денежных средств.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            old_cost = holding.quantity * holding.average_price
            holding.quantity += quantity
            holding.average_price = ((old_cost + gross) / holding.quantity).quantize(MONEY)
        else:
            if holding.quantity < quantity:
                return Response(
                    {'detail': 'Недостаточно ценных бумаг.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cash_change = gross - commission
            holding.quantity -= quantity
            if holding.quantity == 0:
                holding.average_price = Decimal('0')

        account.cash_balance = (account.cash_balance + cash_change).quantize(MONEY)
        account.save(update_fields=['cash_balance'])
        holding.save(update_fields=['quantity', 'average_price'])
        order = Order.objects.create(
            account=account,
            security=security,
            side=values['side'],
            quantity=quantity,
            price=price,
            commission=commission,
            total=gross,
        )
        Transaction.objects.create(
            account=account,
            transaction_type=values['side'],
            amount=cash_change,
            balance_after=account.cash_balance,
            security=security,
            order=order,
            description=f'{order.get_side_display()} {quantity} {security.ticker}',
        )
    return Response(
        {
            'order': OrderSerializer(order).data,
            'cash_balance': account.cash_balance,
            'holding_quantity': holding.quantity,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def orders(request):
    queryset = demo_account().orders.select_related('security')
    return Response(OrderSerializer(queryset, many=True).data)


@api_view(['GET'])
def transactions(request):
    queryset = demo_account().transactions.select_related('security')
    return Response(TransactionSerializer(queryset, many=True).data)


@api_view(['POST'])
def deposit(request):
    return _cash_operation(request, Transaction.TransactionType.DEPOSIT)


@api_view(['POST'])
def withdraw(request):
    return _cash_operation(request, Transaction.TransactionType.WITHDRAWAL)


def _cash_operation(request, operation):
    serializer = AmountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    amount = serializer.validated_data['amount']
    with transaction.atomic():
        account = DemoAccount.objects.select_for_update().get(pk=demo_account().pk)
        if operation == Transaction.TransactionType.WITHDRAWAL:
            if account.cash_balance < amount:
                return Response(
                    {'detail': 'Недостаточно денежных средств.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            change = -amount
            description = 'Вывод средств'
        else:
            change = amount
            description = 'Пополнение счёта'
        account.cash_balance = (account.cash_balance + change).quantize(MONEY)
        account.save(update_fields=['cash_balance'])
        item = Transaction.objects.create(
            account=account,
            transaction_type=operation,
            amount=change,
            balance_after=account.cash_balance,
            description=description,
        )
    return Response(
        {'transaction': TransactionSerializer(item).data, 'cash_balance': account.cash_balance},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def events(request):
    return Response(MarketEventSerializer(MarketEvent.objects.select_related('security'), many=True).data)


@api_view(['GET'])
def market(request, ticker):
    security = get_object_or_404(Security, ticker__iexact=ticker, is_active=True)
    return Response(get_market_price(security))


def _chart_points(security):
    today = timezone.localdate()
    seed = int(sha256(security.ticker.encode()).hexdigest()[:8], 16)
    points = []
    for days_ago in range(29, -1, -1):
        wave = Decimal(((seed + days_ago * 17) % 101) - 50) / Decimal('1000')
        price = (security.current_price * (Decimal('1') + wave)).quantize(MONEY)
        points.append({'date': today - timedelta(days=days_ago), 'close': price})
    points[-1]['close'] = security.current_price
    return points
