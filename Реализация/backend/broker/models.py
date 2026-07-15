from django.core.validators import MinValueValidator
from django.db import models


class Security(models.Model):
    class SecurityType(models.TextChoices):
        STOCK = 'STOCK', 'Акция'
        BOND = 'BOND', 'Облигация'
        FUND = 'FUND', 'Фонд'

    ticker = models.CharField('Тикер', max_length=12, unique=True)
    name = models.CharField('Название', max_length=160)
    security_type = models.CharField(
        'Тип бумаги', max_length=12, choices=SecurityType.choices, default=SecurityType.STOCK
    )
    currency = models.CharField('Валюта', max_length=3, default='RUB')
    current_price = models.DecimalField('Текущая цена', max_digits=16, decimal_places=2)
    previous_close = models.DecimalField('Предыдущее закрытие', max_digits=16, decimal_places=2)
    lot_size = models.PositiveIntegerField('Размер лота', default=1)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Доступна', default=True)

    class Meta:
        ordering = ['ticker']
        verbose_name = 'Ценная бумага'
        verbose_name_plural = 'Ценные бумаги'

    def __str__(self):
        return f'{self.ticker} — {self.name}'


class DemoAccount(models.Model):
    name = models.CharField('Название счёта', max_length=120, default='Демо-счёт')
    cash_balance = models.DecimalField('Денежный баланс', max_digits=18, decimal_places=2, default=0)
    currency = models.CharField('Валюта', max_length=3, default='RUB')
    created_at = models.DateTimeField('Дата открытия', auto_now_add=True)

    class Meta:
        verbose_name = 'Демо-счёт'
        verbose_name_plural = 'Демо-счета'

    def __str__(self):
        return self.name


class Holding(models.Model):
    account = models.ForeignKey(
        DemoAccount, verbose_name='Счёт', related_name='holdings', on_delete=models.CASCADE
    )
    security = models.ForeignKey(
        Security, verbose_name='Ценная бумага', related_name='holdings', on_delete=models.CASCADE
    )
    quantity = models.DecimalField(
        'Количество', max_digits=18, decimal_places=4, validators=[MinValueValidator(0)]
    )
    average_price = models.DecimalField(
        'Средняя цена', max_digits=16, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account', 'security'], name='unique_account_security')
        ]
        verbose_name = 'Позиция'
        verbose_name_plural = 'Позиции'

    def __str__(self):
        return f'{self.security.ticker}: {self.quantity}'


class Order(models.Model):
    class Side(models.TextChoices):
        BUY = 'BUY', 'Покупка'
        SELL = 'SELL', 'Продажа'

    class Status(models.TextChoices):
        EXECUTED = 'EXECUTED', 'Исполнена'
        REJECTED = 'REJECTED', 'Отклонена'

    account = models.ForeignKey(
        DemoAccount, verbose_name='Счёт', related_name='orders', on_delete=models.CASCADE
    )
    security = models.ForeignKey(
        Security, verbose_name='Ценная бумага', related_name='orders', on_delete=models.PROTECT
    )
    side = models.CharField('Сторона', max_length=4, choices=Side.choices)
    quantity = models.DecimalField('Количество', max_digits=18, decimal_places=4)
    price = models.DecimalField('Цена исполнения', max_digits=16, decimal_places=2)
    commission = models.DecimalField('Комиссия', max_digits=16, decimal_places=2)
    total = models.DecimalField('Сумма сделки', max_digits=18, decimal_places=2)
    status = models.CharField(
        'Статус', max_length=12, choices=Status.choices, default=Status.EXECUTED
    )
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f'{self.side} {self.security.ticker} × {self.quantity}'


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        BUY = 'BUY', 'Покупка'
        SELL = 'SELL', 'Продажа'
        DEPOSIT = 'DEPOSIT', 'Пополнение'
        WITHDRAWAL = 'WITHDRAWAL', 'Вывод'

    account = models.ForeignKey(
        DemoAccount, verbose_name='Счёт', related_name='transactions', on_delete=models.CASCADE
    )
    transaction_type = models.CharField('Тип', max_length=12, choices=TransactionType.choices)
    amount = models.DecimalField('Изменение баланса', max_digits=18, decimal_places=2)
    balance_after = models.DecimalField('Баланс после операции', max_digits=18, decimal_places=2)
    security = models.ForeignKey(
        Security,
        verbose_name='Ценная бумага',
        related_name='transactions',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    order = models.OneToOneField(
        Order,
        verbose_name='Заявка',
        related_name='transaction',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    description = models.CharField('Описание', max_length=255, blank=True)
    created_at = models.DateTimeField('Дата операции', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'

    def __str__(self):
        return f'{self.get_transaction_type_display()}: {self.amount}'


class MarketEvent(models.Model):
    class EventType(models.TextChoices):
        DIVIDEND = 'DIVIDEND', 'Дивиденды'
        REPORT = 'REPORT', 'Отчётность'
        MEETING = 'MEETING', 'Собрание акционеров'
        OTHER = 'OTHER', 'Другое'

    title = models.CharField('Событие', max_length=180)
    event_date = models.DateField('Дата')
    event_type = models.CharField(
        'Тип события', max_length=12, choices=EventType.choices, default=EventType.OTHER
    )
    security = models.ForeignKey(
        Security,
        verbose_name='Ценная бумага',
        related_name='events',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    description = models.TextField('Описание', blank=True)

    class Meta:
        ordering = ['event_date', 'title']
        verbose_name = 'Рыночное событие'
        verbose_name_plural = 'Рыночные события'

    def __str__(self):
        return self.title
