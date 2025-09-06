from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Review
from accounts.models import Customer, Delivery, Supplier
from products.models import Product
from course.models import Course

class ReviewSerializer(serializers.ModelSerializer):
    # Customer field is read-only and will be set in the view
    customer = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Review
        fields = [
            'id', 'customer', 'product', 'course', 'delivery', 'supplier',
            'rating', 'comment', 'image', 'ease_of_place_order',
            'speed_of_delivery', 'product_packaging', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'customer']
    
    def validate(self, data):
        # Ensure a review is for exactly one of the four types
        related_fields = [
            data.get('product'),
            data.get('course'),
            data.get('delivery'),
            data.get('supplier')
        ]
        
        provided_count = sum(1 for field in related_fields if field is not None)
        
        if provided_count != 1:
            raise ValidationError("A review must be for exactly one of a product, course, delivery, or supplier.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            customer_instance = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            raise ValidationError("You must be a customer to create a review.")

        # Check for existing review to prevent duplicates
        if validated_data.get('product') and Review.objects.filter(customer=customer_instance, product=validated_data['product']).exists():
            raise ValidationError("You have already reviewed this product.")
        if validated_data.get('course') and Review.objects.filter(customer=customer_instance, course=validated_data['course']).exists():
            raise ValidationError("You have already reviewed this course.")
        if validated_data.get('delivery') and Review.objects.filter(customer=customer_instance, delivery=validated_data['delivery']).exists():
            raise ValidationError("You have already reviewed this delivery person.")
        if validated_data.get('supplier') and Review.objects.filter(customer=customer_instance, supplier=validated_data['supplier']).exists():
            raise ValidationError("You have already reviewed this supplier.")
        
        return Review.objects.create(customer=customer_instance, **validated_data)