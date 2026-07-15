from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('securities/', views.securities, name='securities'),
    path('securities/<str:ticker>/', views.security_detail, name='security-detail'),
    path('securities/<str:ticker>/orderbook/', views.orderbook, name='orderbook'),
    path('trade/', views.trade, name='trade'),
    path('orders/', views.orders, name='orders'),
    path('transactions/', views.transactions, name='transactions'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('events/', views.events, name='events'),
    path('market/<str:ticker>/', views.market, name='market'),
]
