# api/models.py
from django.db import models

class Exchange(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Symbol(models.Model):
    name = models.CharField(max_length=255)
    exchanges = models.ManyToManyField(Exchange, related_name='symbols')

    # Add constraints if needed
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False),
                name='not_null_name'
            ),
        ]

    def __str__(self):
        return self.name

class MarketData(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    best_bid_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    best_bid_size = models.IntegerField()
    best_offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    best_offer_size = models.IntegerField()

    def __str__(self):
        return f"{self.symbol.name} - {self.timestamp}"

class OrderBook(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    limit_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_type = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    quantity = models.IntegerField()

    # Add constraints if needed
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(limit_price__gt=0),
                name='positive_limit_price'
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='positive_quantity'
            ),
        ]

    def __str__(self):
        return f"{self.symbol.name} - {self.order_id}"
