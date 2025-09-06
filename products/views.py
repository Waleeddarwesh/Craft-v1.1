from rest_framework import viewsets, mixins, status, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import Category, Product, Collection, CollectionItem
from accounts.models import Supplier, Follow, User
from .serializers import (
    CategorySerializer, ProductSerializer, SimpleProductSerializer, 
    CollectionSerializer, CollectionCreateUpdateSerializer, 
    LatestCollectionSerializer, ProductCreateUpdateSerializer
)
from .permissions import IsSupplier, IsCustomerOrSupplier
from .filters import ProductFilter
import uuid

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True).order_by('title')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
class MaterialListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True).order_by('title')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().filter(stock__gt=0).select_related(
        'supplier__user', 'category', 'material_category'
    ).prefetch_related('images', 'attributes')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['unit_price', 'rating', 'publish_date']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsSupplier]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.supplier.user != self.request.user:
            raise ValidationError("You are not allowed to update this product.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.supplier.user != self.request.user:
            raise ValidationError("You are not allowed to delete this product.")
        instance.delete()

class SupplierProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('supplier__user').prefetch_related('images')
    serializer_class = SimpleProductSerializer
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(supplier__user=self.request.user)

class ProductsByFollowedSuppliersView(generics.ListAPIView):
    serializer_class = SimpleProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsCustomerOrSupplier]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Product.objects.none()
            
        follower_profile = user.customer_profile if hasattr(user, 'customer_profile') else user.supplier_profile
        follower_content_type = ContentType.objects.get_for_model(type(follower_profile))
        
        followed_suppliers = Follow.objects.filter(
            follower_content_type=follower_content_type,
            follower_object_id=follower_profile.id
        ).values_list('supplier_id', flat=True)
        
        queryset = Product.objects.filter(supplier__in=followed_suppliers).order_by('-publish_date')[:10]
        return queryset

class ProductsByCategoryViewSet(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        category_id = self.kwargs.get("category_id")
        try:
            uuid.UUID(category_id)
            return Product.objects.filter(category__id=category_id, out_of_stock=False).select_related('supplier__user').prefetch_related('images', 'attributes')
        except (ValueError, Category.DoesNotExist):
            return Product.objects.none()

class ProductsByMaterialViewSet(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        material_id = self.kwargs.get("material_id")
        try:
            uuid.UUID(material_id)
            return Product.objects.filter(material_category__id=material_id, out_of_stock=False).select_related('supplier__user').prefetch_related('images', 'attributes')
        except (ValueError, Category.DoesNotExist):
            return Product.objects.none()

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all().select_related('supplier__user').prefetch_related('products')
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(supplier__user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CollectionCreateUpdateSerializer
        return CollectionSerializer

    @action(detail=True, methods=['get'])
    def get_products(self, request, pk=None):
        try:
            collection = self.get_object()
            serializer = CollectionProductSerializer(collection.products.all(), many=True)
            return Response(serializer.data)
        except Collection.DoesNotExist:
            raise NotFound("Collection not found.")

class LatestFollowedSuppliersCollectionsView(generics.ListAPIView):
    serializer_class = LatestCollectionSerializer
    permission_classes = [IsAuthenticated, IsCustomerOrSupplier]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Collection.objects.none()
            
        follower_profile = user.customer_profile if hasattr(user, 'customer_profile') else user.supplier_profile
        follower_content_type = ContentType.objects.get_for_model(type(follower_profile))
        
        followed_supplier_ids = Follow.objects.filter(
            follower_content_type=follower_content_type,
            follower_object_id=follower_profile.id
        ).values_list('supplier_id', flat=True)

        return Collection.objects.filter(
            supplier_id__in=followed_supplier_ids
        ).order_by('-created_at').select_related('supplier__user').prefetch_related('items__product__images')[:10]