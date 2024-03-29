# Generated by Django 4.0.4 on 2024-01-04 07:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exchange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Symbol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('exchanges', models.ManyToManyField(related_name='symbols', to='api.exchange')),
            ],
        ),
        migrations.CreateModel(
            name='OrderBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=255, unique=True)),
                ('limit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order_type', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell')], max_length=4)),
                ('quantity', models.IntegerField()),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.exchange')),
                ('symbol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.symbol')),
            ],
        ),
        migrations.CreateModel(
            name='MarketData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('best_bid_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('best_bid_size', models.IntegerField()),
                ('best_offer_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('best_offer_size', models.IntegerField()),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.exchange')),
                ('symbol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.symbol')),
            ],
        ),
        migrations.AddConstraint(
            model_name='symbol',
            constraint=models.CheckConstraint(check=models.Q(('name__isnull', False)), name='not_null_name'),
        ),
        migrations.AddConstraint(
            model_name='orderbook',
            constraint=models.CheckConstraint(check=models.Q(('limit_price__gt', 0)), name='positive_limit_price'),
        ),
        migrations.AddConstraint(
            model_name='orderbook',
            constraint=models.CheckConstraint(check=models.Q(('quantity__gt', 0)), name='positive_quantity'),
        ),
    ]
