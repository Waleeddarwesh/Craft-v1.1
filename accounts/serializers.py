from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate
from django.conf import settings
import re

from .models import User, Customer, Supplier, Delivery, Address, OneTimePassword
from products.models import Product
from products.serializers import ProductImageSerializer

class UserSerializer(serializers.ModelSerializer):
    """
    A simple serializer for the core User model fields.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'date_joined', 'balance']
        read_only_fields = ['balance', 'date_joined']

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for the Address model.
    """
    class Meta:
        model = Address
        fields = ['id', 'building_number', 'street', 'city', 'state']

class AccountProductSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying a simplified product view on an account page.
    Includes only the first image.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'images', 'name', 'unit_price', 'discount_percentage']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Display only the first image
        if data['images']:
            data['images'] = [data['images'][0]]
        return data

class BaseRegistrationSerializer(serializers.ModelSerializer):
    """
    Base serializer for user registration with common validation logic.
    """
    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"error": "Passwords do not match."})
        if len(attrs['password']) < 8 or not re.search(r'\d', attrs['password']):
            raise serializers.ValidationError({"error": "Password must be at least 8 characters long and contain at least one digit."})
        if not re.match(r'^(010|011|012|015)\d{8}$', str(attrs.get('phone_number'))):
            raise serializers.ValidationError({"error": "Phone number must be in the format 01*********."})
        if User.objects.filter(phone_number=attrs.get('phone_number')).exists():
            raise serializers.ValidationError({"error": "Phone number already exists."})
        return attrs

    def create(self, validated_data, is_customer=False, is_supplier=False, is_delivery=False, **extra_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            phone_number=validated_data['phone_number'],
            is_customer=is_customer,
            is_supplier=is_supplier,
            is_delivery=is_delivery
        )
        return user

class CustomerRegistrationSerializer(BaseRegistrationSerializer):
    def create(self, validated_data):
        user = super().create(validated_data, is_customer=True)
        Customer.objects.create(user=user)
        return user

class SupplierRegistrationSerializer(BaseRegistrationSerializer):
    category_title = serializers.CharField(required=True)
    experience_years = serializers.IntegerField(required=True)
    
    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ('category_title', 'experience_years')

    def create(self, validated_data):
        category_title = validated_data.pop('category_title')
        experience_years = validated_data.pop('experience_years')
        user = super().create(validated_data, is_supplier=True)
        Supplier.objects.create(
            user=user,
            category_title=category_title,
            experience_years=experience_years,
        )
        return user

class DeliveryRegistrationSerializer(BaseRegistrationSerializer):
    plate_number = serializers.CharField(required=True)
    vehicle_model = serializers.CharField(required=True)
    governorate = serializers.CharField(required=True)
    
    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ('plate_number', 'vehicle_model', 'governorate')

    def create(self, validated_data):
        plate_number = validated_data.pop('plate_number')
        vehicle_model = validated_data.pop('vehicle_model')
        governorate = validated_data.pop('governorate')
        user = super().create(validated_data, is_delivery=True)
        Delivery.objects.create(
            user=user,
            plate_number=plate_number,
            vehicle_model=vehicle_model,
            governorate=governorate,
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        user = authenticate(request=self.context.get('request'), email=email, password=password)
        
        if not user:
            raise AuthenticationFailed({"message": "Invalid credentials, please try again."})
        if not user.is_verified:
            raise AuthenticationFailed({"message": "Email is not verified."})
            
        tokens = user.tokens()
        return {
            'email': user.email,
            'first_name': user.first_name,
            'access': str(tokens['access']),
            'refresh': str(tokens['refresh']),
        }

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user', 'photo', 'credit_card_number', 'credit_card_type', 'credit_card_month', 'credit_card_year', 'credit_cvv']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        # Update Customer profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class SupplierProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    products = AccountProductSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'user', 'cover_photo', 'photo', 'category_title', 
            'experience_years', 'rating', 'orders_count', 'products', 'is_accepted',
        ]
        read_only_fields = ['id', 'rating', 'orders_count', 'is_accepted']

    def update(self, instance, validated_data):
        # Update Supplier profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class DeliveryProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'id', 'user', 'photo', 'rating', 'orders_count', 'experience_years', 
            'vehicle_model', 'plate_number', 'governorate',
        ]
        read_only_fields = ['id', 'rating', 'orders_count']

    def update(self, instance, validated_data):
        # Update Delivery profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
class SupplierProfileSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Supplier
        fields = ['id', 'full_name', 'photo', 'category_title']

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

class SetNewPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=4, min_length=4, write_only=True)
    new_password = serializers.CharField(max_length=100, min_length=8, write_only=True)
    confirm_password = serializers.CharField(max_length=100, min_length=8, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({"error": "Passwords do not match."})
        if len(attrs['new_password']) < 8 or not re.search(r'\d', attrs['new_password']):
            raise serializers.ValidationError({"error": "New password must be at least 8 characters long and contain at least one digit."})
        return attrs

class LogoutUserSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError("Token is expired or invalid.")

class SupplierDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['contract', 'identity']

    def validate(self, attrs):
        if not attrs.get('contract') and not attrs.get('identity'):
            raise serializers.ValidationError("At least one document (contract or identity) must be uploaded.")
        return attrs

class DeliveryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['contract', 'identity']

    def validate(self, attrs):
        if not attrs.get('contract') and not attrs.get('identity'):
            raise serializers.ValidationError("At least one document (contract or identity) must be uploaded.")
        return attrs