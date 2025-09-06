from rest_framework import serializers
from .models import *
from rest_framework.exceptions import ValidationError
from collections import defaultdict
from accounts.models import Supplier
from django.db import transaction

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ["id", "attribute_type", "value"]

class SimpleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.get_full_name', read_only=True)
    supplier_photo = serializers.ImageField(source='supplier.photo', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'images', 'name', 'unit_price', 'supplier_name', 'supplier_photo']
        ref_name = "ProductsSimpleProductSerializer"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['images']:
            data['images'] = [data['images'][0]]  # Include only the first image
        return data

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.get_full_name', read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "quantity_per_unit", "supplier", "supplier_name", 
            "unit_price", "unit_weight", "stock", "out_of_stock", "discount_available", 
            "discount_percentage", "category", "material_category", "images", "attributes", "rating"
        ]
        read_only_fields = ['supplier', 'out_of_stock', 'rating']

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    uploaded_attributes = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "quantity_per_unit", "unit_price", "unit_weight", 
            "stock", "discount_percentage", "category", "material_category", 
            "uploaded_images", "uploaded_attributes", "width", "height", "watt"
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('uploaded_images', [])
        attributes_data = validated_data.pop('uploaded_attributes', {})
        
        request_user = self.context['request'].user
        if not hasattr(request_user, 'supplier_profile'):
            raise ValidationError("User is not a supplier.")
        
        with transaction.atomic():
            product = Product.objects.create(supplier=request_user.supplier_profile, **validated_data)
            
            for image in images_data:
                ProductImage.objects.create(product=product, image=image)

            for attr_type, values in attributes_data.items():
                for value in values:
                    ProductAttribute.objects.create(
                        product=product, attribute_type=attr_type, value=value
                    )
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('uploaded_images', [])
        attributes_data = validated_data.pop('uploaded_attributes', {})
        
        with transaction.atomic():
            # Update product fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update images and attributes if provided
            if images_data:
                instance.images.all().delete()
                for image in images_data:
                    ProductImage.objects.create(product=instance, image=image)

            if attributes_data:
                instance.attributes.all().delete()
                for attr_type, values in attributes_data.items():
                    for value in values:
                        ProductAttribute.objects.create(
                            product=instance, attribute_type=attr_type, value=value
                        )

        return instance

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'picture']

class CollectionProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'unit_price', 'images']  

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['images']:
            data['images'] = [data['images'][0]]
        return data

class CollectionSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    products = CollectionProductSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'images', 'products'] 
        
    def get_images(self, obj):
        first_items = obj.items.all()[:4]
        image_urls = []
        for item in first_items:
            if item.product and item.product.images.exists():
                first_image = item.product.images.first()
                if first_image.image:
                    image_urls.append(first_image.image.url)
        return image_urls if image_urls else None

class CollectionCreateUpdateSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, write_only=True)
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'products']

    def validate_products(self, products):
        supplier = self.context['request'].user.supplier_profile
        invalid_products = [p for p in products if p.supplier != supplier]
        if invalid_products:
            raise ValidationError("You can only add your own products.")

        product_counts = defaultdict(int)
        for p in products:
            product_counts[p.id] += 1
        
        duplicates = [pid for pid, count in product_counts.items() if count > 1]
        if duplicates:
            raise ValidationError(f"Duplicate products in the list: {duplicates}")
        
        return products

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        supplier = self.context['request'].user.supplier_profile
        collection = Collection.objects.create(supplier=supplier, **validated_data)
        
        for product in products_data:
            CollectionItem.objects.create(collection=collection, product=product)
        return collection

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        instance.name = validated_data.get('name', instance.name)
        
        with transaction.atomic():
            if products_data is not None:
                instance.products.clear()
                for product in products_data:
                    CollectionItem.objects.create(collection=instance, product=product)
        
        instance.save()
        return instance
    
class SupplierProfileSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Supplier
        fields = ['id', 'full_name', 'photo', 'category_title']
        ref_name = "ProductsSupplierProfileSummarySerializer"

class LatestCollectionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    supplier = SupplierProfileSummarySerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'image', 'name', 'supplier']

    def get_image(self, obj):
        first_item = obj.items.first()
        if first_item and first_item.product and first_item.product.images.exists():
            return first_item.product.images.first().image.url
        return None