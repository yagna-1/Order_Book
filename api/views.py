# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Exchange, Symbol, OrderBook, MarketData
from decimal import Decimal
import requests
from django.db.models import Q
from rest_framework import status
from django.http import JsonResponse
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.middleware.csrf import get_token
import logging
logger=logging.getLogger(__name__)


@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])

class ConsolidatedBookAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            access_key = 'sk_b8aa3dcd2c4e4fc396a9d7388a6b8b00'
            search_query = request.query_params.get('search', '')
            
            symbols = Symbol.objects.all()
            symbol_names = [symbol.name for symbol in symbols]

            filtered_symbols = symbols.filter(Q(name__icontains=search_query))

            consolidated_data = {}

            for symbol in filtered_symbols:
                consolidated_data[symbol.name] = self.get_consolidated_data(symbol, access_key)

            logger.info(f"Consolidated Data: {consolidated_data}")

            return Response({'consolidated_data': consolidated_data, 'symbol_suggestions': symbol_names})
        except Exception as e:
            logger.exception(f"Error in ConsolidatedBookAPIView: {e}")
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    def fetch_marketstack_data(self, exchange, symbol, access_key):
        try:
            # Update the URL to the new API endpoint
            url = f'https://api.iex.cloud/v1/data/core/historical_prices/{symbol.name}?token=sk_b8aa3dcd2c4e4fc396a9d7388a6b8b00'

            response = requests.get(url)

            if response.status_code == 200:
                market_data = response.json()
                
                # Extract relevant data from the response and update your database models accordingly
                best_bid_price = Decimal(market_data.get("best_bid_price")) if market_data.get("best_bid_price") is not None else None
                best_offer_price = Decimal(market_data.get("best_offer_price")) if market_data.get("best_offer_price") is not None else None

                MarketData.objects.create(
                    exchange=exchange,
                    symbol=symbol,
                    best_bid_price=best_bid_price,
                    best_bid_size=market_data.get("best_bid_size", 0),
                    best_offer_price=best_offer_price,
                    best_offer_size=market_data.get("best_offer_size", 0),
                )
            else:
                # Handle the case where the API request fails
                return {}
        except Exception as e:
            logger.exception(f"Error in fetch_marketstack_data: {e}")
            return {}

    def consolidate_data(self, symbol):
        consolidated_data = {'bids': [], 'asks': []}

        # Fetch data from MarketData model or wherever you are getting it
        market_data = MarketData.objects.filter(symbol=symbol).values()

        for entry in market_data:
            # Check if the bid price is not None before adding to bids list
            if entry['best_bid_price'] is not None:
                consolidated_data['bids'].append({
                    'price': entry['best_bid_price'],
                    'size': entry['best_bid_size']
                })

            # Check if the ask price is not None before adding to asks list
            if entry['best_offer_price'] is not None:
                consolidated_data['asks'].append({
                    'price': entry['best_offer_price'],
                    'size': entry['best_offer_size']
                })

        # Sort bids and asks lists separately
        consolidated_data['bids'] = sorted(consolidated_data['bids'], key=lambda x: x['price'], reverse=True)
        consolidated_data['asks'] = sorted(consolidated_data['asks'], key=lambda x: x['price'], reverse=True)

        # Take the top 5 levels
        consolidated_data['bids'] = consolidated_data['bids'][:5]
        consolidated_data['asks'] = consolidated_data['asks'][:5]

        return consolidated_data

    def sum_sizes_at_price_levels(self, data):
        consolidated_levels = []
        level_dict = {}

        for entry in data:
            price = entry['price']
            size = entry['size']

            if price in level_dict:
                level_dict[price] += size
            else:
                level_dict[price] = size

        for price, size in level_dict.items():
            consolidated_levels.append({'price': price, 'size': size})

        # Sort consolidated levels by price
        consolidated_levels = sorted(consolidated_levels, key=lambda x: x['price'], reverse=True)

        return consolidated_levels

    def get_consolidated_data(self, symbol, access_key):
        # Fetch market data from multiple exchanges (in this case, only one exchange is considered)
        exchanges = Exchange.objects.all()

        for exchange in exchanges:
            self.fetch_marketstack_data(exchange, symbol, access_key)

        # Consolidate data for the symbol
        consolidated_data = self.consolidate_data(symbol)

        return consolidated_data
    def handle_order_message(self, order_message):
        try:
            symbol_name = order_message.get('SYMBOL')
            limit_price = order_message.get('LIMIT_PRICE')
            side = order_message.get('SIDE')
            quantity = order_message.get('QUANTITY')
            order_id = order_message.get('ORDER_ID')

            if not all([symbol_name, limit_price, side, quantity, order_id]):
                return JsonResponse({'error': 'All fields (SYMBOL, LIMIT_PRICE, SIDE, QUANTITY, ORDER_ID) must be provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the Symbol object based on the symbol_name
            symbol = Symbol.objects.get(name=symbol_name)

            if not (Decimal(quantity) > 0 and Decimal(limit_price) > 0):
                return JsonResponse({'error': 'Quantity and limit price must be positive'}, status=status.HTTP_400_BAD_REQUEST)

            if OrderBook.objects.filter(symbol=symbol, order_id=order_id).exists():
                return JsonResponse({'error': f'Order with ID {order_id} already exists'}, status=status.HTTP_400_BAD_REQUEST)

            if side not in ('BUY', 'SELL'):
                return JsonResponse({'error': 'Invalid order side. Must be BUY or SELL'}, status=status.HTTP_400_BAD_REQUEST)

            order_book_entry, created = OrderBook.objects.get_or_create(
                symbol=symbol,
                order_id=order_id,
                defaults={
                    'limit_price': limit_price,
                    'order_type': side,
                    'quantity': quantity
                }
            )

            if not created:
                message_type = order_message.get('MESSAGE_TYPE')

                if message_type == 'NEW_ORDER':
                    order_book_entry.quantity = quantity
                    order_book_entry.save()
                elif message_type == 'CANCEL_ORDER':
                    order_book_entry.delete()
                elif message_type == 'MODIFY_ORDER':
                    order_book_entry.quantity = quantity
                    order_book_entry.save()

            return JsonResponse({'success': 'Order message processed successfully'})
        except Symbol.DoesNotExist:
            return JsonResponse({'error': f'Symbol with name {symbol_name} not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, *args, **kwargs):
        order_message = request.data.get('order_message', {})

        if order_message:
            # Extract the symbol name from the order_message
            symbol_name = order_message.get('SYMBOL')

            if not symbol_name:
                return Response({'error': 'Symbol name is missing in the order message'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Retrieve the Symbol object based on the symbol_name
                symbol = Symbol.objects.get(name=symbol_name)
            except Symbol.DoesNotExist:
                return Response({'error': f'Symbol with name {symbol_name} not found'}, status=status.HTTP_404_NOT_FOUND)

            # Handle the order message
            self.handle_order_message(order_message)

            # Consolidate data for the symbol
            consolidated_data = self.consolidate_data(symbol)

            return Response({'consolidated_book': consolidated_data})
        else:
            return Response({'error': 'Invalid order message'}, status=status.HTTP_400_BAD_REQUEST)


class OrderMessageAPIView(APIView):
    def post(self, request, *args, **kwargs):
        order_message = request.data.get('order_message', {})

        if order_message:
            ConsolidatedBookAPIView().handle_order_message(order_message)

            # Extracting symbol and access_key from order_message
            symbol_name = order_message.get('SYMBOL')
            access_key = 'fbe98c306ec209556b40ebe43fdc7c2c' # Replace with your access key

            if symbol_name:
                symbol = Symbol.objects.get(name=symbol_name)
                consolidated_book = ConsolidatedBookAPIView().get_consolidated_data(symbol, access_key)
                return Response({'consolidated_book': consolidated_book})
            else:
                return Response({'error': 'Symbol name is missing in the order message'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid order message'}, status=status.HTTP_400_BAD_REQUEST)
