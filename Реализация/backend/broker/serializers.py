from decimal import Decimal

from rest_framework import serializers

from .models import MarketEvent, Order, Security, Transaction


class SecuritySerializer(serializers.ModelSerializer):
    change = serializers.SerializerMethodField()
    change_percent = serializers.SerializerMethodField()

    class Meta:
        model = Security
        fields = (
            'ticker',
            'name',
            'security_type',
            'currency',
            'current_price',
            'previous_close',
            'change',
            'change_percent',
            'lot_size',
            'description',
        )

    def get_change(self, obj):
        return obj.current_price - obj.previous_close

    def get_change_percent(self, obj):
        if not obj.previous_close:
            return Decimal('0.00')
        return ((obj.current_price - obj.previous_close) / obj.previous_close * 100).quantize(
            Decimal('0.01')
        )


class OrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source='security.ticker', read_only=True)
    security_name = serializers.CharField(source='security.name', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'ticker',
            'security_name',
            'side',
            'quantity',
            'price',
            'commission',
            'total',
            'status',
            'created_at',
        )


class TransactionSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source='security.ticker', read_only=True, allow_null=True)
    type = serializers.CharField(source='transaction_type', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id',
            'type',
            'amount',
            'balance_after',
            'ticker',
            'description',
            'created_at',
        )


class MarketEventSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source='security.ticker', read_only=True, allow_null=True)
    type = serializers.CharField(source='event_type', read_only=True)

    class Meta:
        model = MarketEvent
        fields = ('id', 'title', 'event_date', 'type', 'ticker', 'description')


class TradeSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=12)
    side = serializers.ChoiceField(choices=Order.Side.choices)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    price = serializers.DecimalField(
        max_digits=16, decimal_places=2, min_value=Decimal('0.01'), required=False
    )

    def validate_ticker(self, value):
        return value.upper()


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal('0.01')
    )
