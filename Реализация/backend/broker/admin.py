from django.contrib import admin

from .models import DemoAccount, Holding, MarketEvent, Order, Security, Transaction


@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'security_type', 'current_price', 'currency', 'is_active')
    list_filter = ('security_type', 'currency', 'is_active')
    search_fields = ('ticker', 'name')


@admin.register(DemoAccount)
class DemoAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'cash_balance', 'currency', 'created_at')


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('account', 'security', 'quantity', 'average_price')
    list_select_related = ('account', 'security')
    search_fields = ('security__ticker', 'security__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'security', 'side', 'quantity', 'price', 'commission', 'status')
    list_filter = ('side', 'status', 'created_at')
    search_fields = ('security__ticker',)
    list_select_related = ('security', 'account')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'transaction_type', 'amount', 'balance_after', 'security')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('security__ticker', 'description')
    list_select_related = ('security', 'account')


@admin.register(MarketEvent)
class MarketEventAdmin(admin.ModelAdmin):
    list_display = ('event_date', 'title', 'event_type', 'security')
    list_filter = ('event_type', 'event_date')
    search_fields = ('title', 'security__ticker')
