# api/serializers.py
# api/serializers.py
from rest_framework import serializers
from .models import MarketData, OrderBook, Symbol, Exchange

class MarketDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketData
        fields = '__all__'

class OrderBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBook
        fields = '__all__'

class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = '__all__'

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = '__all__'
