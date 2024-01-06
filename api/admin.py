# api/admin.py
from django.contrib import admin
from .models import Exchange, Symbol, MarketData, OrderBook

@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'symbol', 'timestamp', 'best_bid_price', 'best_bid_size', 'best_offer_price', 'best_offer_size')
    search_fields = ('symbol__name',)

@admin.register(OrderBook)
class OrderBookAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'symbol', 'order_id', 'limit_price', 'order_type', 'quantity')
    search_fields = ('symbol__name', 'order_id')
