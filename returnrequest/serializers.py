from rest_framework import serializers
from products.models import Product
from .models import ReturnRequest, BalanceWithdrawRequest, Transaction
from accounts.models import User
from products.serializers import SimpleProductSerializer
from orders.models import OrderItem, Order

class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(write_only=True)
    quantity = serializers.IntegerField()
    order_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ReturnRequest
        fields = ['product_id', 'quantity', 'order_id']

    def validate(self, data):
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        order_id = data.get('order_id')
        user = self.context['request'].user

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product does not exist."})
        
        try:
            order = OrderItem.objects.get(order__id=order_id, product=product)
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError({"order_id": "Product not found in this order."})

        if quantity <= 0 or quantity > order.quantity:
            raise serializers.ValidationError({"quantity": f"Quantity must be a positive number and not exceed your ordered quantity ({order.quantity})."})

        if product.supplier.user == user:
            raise serializers.ValidationError({"detail": "You cannot create a return request for your own product."})

        if ReturnRequest.objects.filter(user=user, product=product, order=order.order).exists():
            raise serializers.ValidationError({"detail": "You have already submitted a return request for this product."})
            
        data['product_id'] = product
        data['order_id'] = order.order
        return data

class ReturnRequestListRetrieveSerializer(serializers.ModelSerializer):
    user_details = serializers.CharField(source='user.get_full_name', read_only=True)
    product_details = SimpleProductSerializer(source='product', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ReturnRequest
        fields = ("id", "user", "user_details", "from_state", "to_state", "product_details", "amount", "status_display", "created_at")

class ReturnRequestDeliverSerializer(serializers.ModelSerializer):
    confirmation_code = serializers.CharField(write_only=True)
    class Meta:
        model = ReturnRequest
        fields = ['confirmation_code']

class BalanceWithdrawRequestSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BalanceWithdrawRequest
        fields = ['id', 'user', 'transfer_number', 'transfer_type', 'transfer_status', 'amount', 'notes']
        read_only_fields = ['id', 'transfer_status']
   
class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'user_email', 'transaction_type_display', 'amount', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']