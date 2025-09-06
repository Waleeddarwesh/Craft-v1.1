from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from collections import defaultdict
from accounts.serializers import AddressSerializer
from products.serializers import ProductImageSerializer
from products.models import Product, Supplier
from .models import (
    Order, OrderItem, Cart, CartItem, Wishlist, WishlistItem, Warehouse,
    Shipment, ShipmentItem, Coupon
)

class SimpleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", 'images', "name", "unit_price"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['images']:
            data['images'] = [data['images'][0]]
        return data

class OrderItemProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", 'images', "name"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['images']:
            data['images'] = [data['images'][0]]
        return data

class WishlistItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product"]

class WishlistSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "items"]

class AddWishlistItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(write_only=True)

    def validate_product_id(self, value):
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("There is no product associated with the given ID.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        product_id = self.validated_data["product_id"]
        wishlist, _ = Wishlist.objects.get_or_create(user=user)

        product = Product.objects.get(id=product_id)
        if product.supplier.user == user:
            raise serializers.ValidationError("You cannot add your own product to the wishlist.")

        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, product=product
        )
        self.instance = wishlist_item
        return self.instance

    class Meta:
        model = WishlistItem
        fields = ["id", "product_id"]

class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "quantity", "product", "sub_total"]

    def get_sub_total(self, obj):
        return obj.quantity * obj.product.unit_price

class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "grand_total"]

    def get_grand_total(self, obj):
        total = sum(item.quantity * item.product.unit_price for item in obj.items.all())
        return total

class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(write_only=True)
    color = serializers.CharField(required=False, allow_blank=True)
    size = serializers.CharField(required=False, allow_blank=True)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"detail": "There is no product associated with the given ID."})
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]
        color = self.validated_data.get("color", "")
        size = self.validated_data.get("size", "")

        cart, _ = Cart.objects.get_or_create(user=user)
        product = Product.objects.get(id=product_id)

        if product.supplier.user == user:
            raise serializers.ValidationError({"detail": "You cannot add your own product to the cart."})

        if not (0 < quantity <= 10):
            raise serializers.ValidationError({"detail": "Quantity must be between 1 and 10."})
        if quantity > product.stock:
            raise serializers.ValidationError({"detail": f"Quantity of {product.name} exceeds available stock."})

        try:
            cart_item = CartItem.objects.get(product_id=product_id, cart=cart, color=color, size=size)
            if cart_item.quantity + quantity > product.stock:
                raise serializers.ValidationError({"detail": f"Adding this quantity of {product.name} exceeds available stock."})
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                quantity=quantity,
                color=color,
                size=size
            )
        return self.instance

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity", "color", "size"]

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]

class OrderCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        exclude = ("paid", "status")

class OrderItemListRetrieveSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer(read_only=True)
    cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "quantity", "price", "cost")

    def get_cost(self, obj: OrderItem):
        return obj.get_cost()

class ShipmentItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = ShipmentItem
        fields = ["quantity", "product"]

    def get_product(self, obj):
        return SimpleProductSerializer(obj.order_item.product).data

class ShipmentSerializer(serializers.ModelSerializer):
    items = ShipmentItemSerializer(many=True, read_only=True)
    confirmation_code = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Shipment
        fields = ["confirmation_code", "status", "items"]

    def get_confirmation_code(self, obj: Shipment):
        request = self.context.get('request')
        if request and request.user == obj.order.user:
            return obj.confirmation_code
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('confirmation_code') is None:
            data.pop('confirmation_code')
        return data

class OrderListRetrieveSerializer(serializers.ModelSerializer):
    confirmation_code = serializers.SerializerMethodField()
    order_items = OrderItemListRetrieveSerializer(many=True, source='items')

    class Meta:
        model = Order
        fields = ("id", "final_amount", "paid", "created_at", "confirmation_code", "order_items")

    def get_confirmation_code(self, obj: Order):
        latest_shipment = obj.shipments.order_by('-created_at').first()
        if latest_shipment and self.context.get('request').user == obj.user:
            return latest_shipment.confirmation_code
        return None

class SupplierOrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at", "paid", "status", "final_amount")

class SupplierOrderRetrieveSerializer(serializers.ModelSerializer):
    order_items = OrderItemListRetrieveSerializer(many=True, source='items')
    address = AddressSerializer()
    payment_method = serializers.CharField(source='get_payment_method_display')
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Order
        fields = (
            "id", "user", "order_items", "address", "payment_method",
            "total_amount", "discount_amount", "delivery_fee", "final_amount", "status"
        )

class ReturnRequestListRetrieveSerializer(serializers.ModelSerializer):
    items = OrderItemListRetrieveSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["items", ]
        ref_name = 'Orders_ReturnRequestListRetrieveSerializer'

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount', 'valid_from', 'valid_to']
        read_only_fields = ['supplier']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated or not hasattr(user, 'supplier_profile'):
            raise serializers.ValidationError("User is not a supplier.")
        
        validated_data['supplier'] = user.supplier_profile
        return super().create(validated_data)

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address']