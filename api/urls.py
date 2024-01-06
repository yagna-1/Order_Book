# api/urls.py
from django.urls import path
from .views import ConsolidatedBookAPIView,  OrderMessageAPIView

urlpatterns = [
    path('consolidated-book/', ConsolidatedBookAPIView.as_view(), name='consolidated-book-api'),
    path('order-message/', OrderMessageAPIView.as_view(), name='order-message-api'),
]

