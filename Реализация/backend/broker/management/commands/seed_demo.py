from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from broker.models import DemoAccount, Holding, MarketEvent, Order, Security, Transaction


SECURITIES = [
    ('SBER', 'Сбер Банк', '11.18', '11.08', 'Крупнейший универсальный банк России.'),
    ('GAZP', 'Газпром', '4.92', '4.97', 'Глобальная энергетическая компания.'),
    ('LKOH', 'ЛУКОЙЛ', '257.35', '254.34', 'Нефтегазовая компания полного цикла.'),
    ('YNDX', 'Яндекс', '148.50', '147.19', 'Технологическая компания и цифровые сервисы.'),
    ('ROSN', 'Роснефть', '18.95', '18.78', 'Одна из крупнейших нефтяных компаний.'),
    ('AFLT', 'Аэрофлот', '2.25', '2.23', 'Крупнейшая российская авиакомпания.'),
    ('MOEX', 'Московская биржа', '8.00', '7.91', 'Оператор основной торговой площадки России.'),
]


class Command(BaseCommand):
    help = 'Создаёт или обновляет демонстрационные данные брокера'

    @transaction.atomic
    def handle(self, *args, **options):
        securities = {}
        for ticker, name, price, previous, description in SECURITIES:
            security, _ = Security.objects.update_or_create(
                ticker=ticker,
                defaults={
                    'name': name,
                    'security_type': Security.SecurityType.STOCK,
                    'currency': 'BYN',
                    'current_price': Decimal(price),
                    'previous_close': Decimal(previous),
                    'lot_size': 1,
                    'description': description,
                    'is_active': True,
                },
            )
            securities[ticker] = security

        account, created = DemoAccount.objects.get_or_create(
            name='Брокерский счёт',
            defaults={'cash_balance': Decimal('5000.00'), 'currency': 'BYN'},
        )
        converted = account.currency != 'BYN'
        if converted:
            account.orders.all().delete()
            account.transactions.all().delete()
            account.holdings.all().delete()
            account.cash_balance = Decimal('5000.00')
            account.currency = 'BYN'
            account.save(update_fields=['cash_balance', 'currency'])
        if created or converted:
            Transaction.objects.create(
                account=account,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                amount=Decimal('5000.00'),
                balance_after=Decimal('5000.00'),
                description='Начальное пополнение',
            )
        DemoAccount.objects.exclude(pk=account.pk).delete()

        positions = {
            'SBER': ('12', '10.13'),
            'GAZP': ('20', '5.23'),
            'LKOH': ('2', '245.16'),
            'MOEX': ('10', '7.11'),
        }
        for ticker, (quantity, average_price) in positions.items():
            Holding.objects.update_or_create(
                account=account,
                security=securities[ticker],
                defaults={
                    'quantity': Decimal(quantity),
                    'average_price': Decimal(average_price),
                },
            )

        self._create_sample_trade(account, securities['SBER'])
        self._create_events(securities)
        self.stdout.write(
            self.style.SUCCESS(
                f'Демо-данные готовы: {len(securities)} бумаг, счёт «{account.name}».'
            )
        )

    def _create_sample_trade(self, account, security):
        marker = 'Покупка SBER'
        if Transaction.objects.filter(account=account, description=marker).exists():
            return
        price = Decimal('10.13')
        quantity = Decimal('2')
        gross = price * quantity
        commission = (gross * Decimal('0.0025')).quantize(Decimal('0.01'))
        order = Order.objects.create(
            account=account,
            security=security,
            side=Order.Side.BUY,
            quantity=quantity,
            price=price,
            commission=commission,
            total=gross,
        )
        Transaction.objects.create(
            account=account,
            security=security,
            order=order,
            transaction_type=Transaction.TransactionType.BUY,
            amount=-(gross + commission),
            balance_after=account.cash_balance,
            description=marker,
        )

    def _create_events(self, securities):
        today = timezone.localdate()
        rows = [
            ('Отчётность Сбер Банка', 7, 'REPORT', 'SBER', 'Публикация финансовых результатов.'),
            ('Дивидендная отсечка ЛУКОЙЛ', 18, 'DIVIDEND', 'LKOH', 'Дата закрытия реестра.'),
            ('Собрание акционеров Газпрома', 32, 'MEETING', 'GAZP', 'Годовое общее собрание.'),
            ('Отчёт об объёмах торгов MOEX', 45, 'REPORT', 'MOEX', 'Ежемесячная статистика торгов.'),
        ]
        for title, offset, event_type, ticker, description in rows:
            MarketEvent.objects.update_or_create(
                title=title,
                defaults={
                    'event_date': today + timedelta(days=offset),
                    'event_type': event_type,
                    'security': securities[ticker],
                    'description': description,
                },
            )
