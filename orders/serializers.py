from rest_framework import serializers
from .models import *
from rest_framework.exceptions import ValidationError
from collections import defaultdict
from accounts.models import Supplier
from products.serializers import ProductImageSerializer

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class AddWishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['product']

    def create(self, validated_data):
        user = self.context['request'].user
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return WishlistItem.objects.create(wishlist=wishlist, **validated_data)

class WishlistItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'products', 'created_at']
        read_only_fields = ['id', 'user', 'products', 'created_at']

class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['product', 'quantity', 'color', 'size']

    def create(self, validated_data):
        user = self.context['request'].user
        cart, _ = Cart.objects.get_or_create(user=user)
        return CartItem.objects.create(cart=cart, **validated_data)

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity', 'color', 'size']

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'color', 'size']

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['address', 'payment_method']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'price', 'color', 'size']

class OrderListRetrieveSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, source='items')
    user_email = serializers.CharField(source='user.email', read_only=True)
    address_details = serializers.CharField(source='address.get_full_address', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_email', 'address_details', 'payment_method', 'total_amount',
            'discount_amount', 'delivery_fee', 'final_amount', 'status', 'paid',
            'created_at', 'order_items'
        ]

class SimpleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.get_full_name', read_only=True)
    supplier_photo = serializers.ImageField(source='supplier.photo', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'images', 'name', 'unit_price', 'supplier_name', 'supplier_photo']
        ref_name = "OrderSimpleProductSerializer"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['images']:
            data['images'] = [data['images'][0]]
        return data

class SupplierOrderListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'created_at', 'total_amount']

class SupplierOrderRetrieveSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    items = OrderItemSerializer(many=True, read_only=True)
    address = serializers.StringRelatedField()
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'address', 'status', 'created_at', 'items', 'total_amount']

class ShipmentItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)

    class Meta:
        model = ShipmentItem
        fields = ['id', 'product_name', 'quantity']

class ShipmentSerializer(serializers.ModelSerializer):
    delivery_person = serializers.CharField(source='delivery_person.user.get_full_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.get_full_name', read_only=True)
    items = ShipmentItemSerializer(many=True, read_only=True)
    order_id = serializers.CharField(source='order.id', read_only=True)
    customer_name = serializers.CharField(source='order.user.get_full_name', read_only=True)
    to_address_details = serializers.CharField(source='to_address.get_full_address', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'order_id', 'supplier_name', 'from_state', 'to_state', 'to_address_details',
            'status', 'delivery_person', 'items', 'customer_name', 'order_total_value'
        ]

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount', 'valid_from', 'valid_to', 'is_active']
        read_only_fields = ['id']

class ReturnRequestListRetrieveSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, source='items')
    status = serializers.CharField()
    
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'order_items']
        ref_name = "OrderReturnRequestListRetrieveSerializer"

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'contact_person', 'contact_phone', 'delivery_fee']