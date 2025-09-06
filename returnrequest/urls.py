from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReturnRequestViewSet,
    BalanceWithdrawRequestListCreateView,
    BalanceWithdrawRequestDetailView,
    TransactionListView,
)

router = DefaultRouter()
router.register('return-requests', ReturnRequestViewSet, basename='return-request')

urlpatterns = [
    path('', include(router.urls)),
    path('withdraw-requests/', BalanceWithdrawRequestListCreateView.as_view(), name='balance-withdraw-request-list-create'),
    path('withdraw-requests/<uuid:pk>/', BalanceWithdrawRequestDetailView.as_view(), name='balance-withdraw-request-detail'),
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
]