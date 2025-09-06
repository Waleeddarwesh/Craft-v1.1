from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WishlistViewSet, WishlistItemViewSet, CartViewSet, CartItemViewSet,
    OrderViewSet, ShipmentViewSet, OrdersHistoryViewSet,
    ReturnOrdersProductsViewSet, CouponViewSet, WarehouseListView
)

router = DefaultRouter()
router.register('wishlists', WishlistViewSet, basename='wishlist')
router.register('wishlistitems', WishlistItemViewSet, basename='wishlistitem')
router.register('carts', CartViewSet, basename='cart')
router.register('cartitems', CartItemViewSet, basename='cartitem')
router.register('orders', OrderViewSet, basename="order")
router.register('shipments', ShipmentViewSet, basename='shipment')
router.register('orders-history', OrdersHistoryViewSet, basename="orders-history")
router.register('return-orders-products', ReturnOrdersProductsViewSet, basename='return-orders-products')
router.register('coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    path('', include(router.urls)),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
]