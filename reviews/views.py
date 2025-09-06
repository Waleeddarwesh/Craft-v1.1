from rest_framework import generics, viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from .models import Review
from .serializers import ReviewSerializer
from accounts.permissions import IsAuthenticated, IsCustomer
from products.models import Product
from course.models import Course
from accounts.models import Delivery, Supplier
from rest_framework.pagination import PageNumberPagination
import uuid

# Assume StandardResultsSetPagination is defined elsewhere or imported from another app
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ReviewViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    
    queryset = Review.objects.all().select_related(
        'customer__user', 'product', 'course', 'delivery', 'supplier'
    )
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsCustomer]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        try:
            user.customer_profile
        except Customer.DoesNotExist:
            raise PermissionDenied("You must be a customer to create a review.")
            
        serializer.save()

    def get_object(self):
        try:
            instance = super().get_object()
        except Review.DoesNotExist:
            raise NotFound({"detail": "Review not found."})
        
        if instance.customer.user != self.request.user:
            raise PermissionDenied("You do not have permission to perform this action.")
            
        return instance

class ReviewListAPIView(generics.ListAPIView):
    """
    API view to list reviews for a specific object (product, course, etc.).
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        course_id = self.kwargs.get('course_id')
        delivery_id = self.kwargs.get('delivery_id')
        supplier_id = self.kwargs.get('supplier_id')

        # Use a single, clear conditional block to filter the queryset
        if product_id:
            try:
                uuid.UUID(product_id)
                Product.objects.get(id=product_id) # Check if product exists
                return Review.objects.filter(product__id=product_id)
            except (ValueError, Product.DoesNotExist):
                raise NotFound({"detail": "Invalid product ID or product not found."})

        elif course_id:
            try:
                uuid.UUID(course_id)
                Course.objects.get(id=course_id)
                return Review.objects.filter(course__id=course_id)
            except (ValueError, Course.DoesNotExist):
                raise NotFound({"detail": "Invalid course ID or course not found."})

        elif delivery_id:
            try:
                uuid.UUID(delivery_id)
                Delivery.objects.get(id=delivery_id)
                return Review.objects.filter(delivery__id=delivery_id)
            except (ValueError, Delivery.DoesNotExist):
                raise NotFound({"detail": "Invalid delivery ID or delivery person not found."})
        
        elif supplier_id:
            try:
                uuid.UUID(supplier_id)
                supplier_instance = Supplier.objects.get(id=supplier_id)
                
                # Filter for both reviews on the supplier and reviews on their products
                product_reviews = Review.objects.filter(product__supplier=supplier_instance)
                supplier_reviews = Review.objects.filter(supplier=supplier_instance)
                
                return (product_reviews | supplier_reviews).distinct()
            except (ValueError, Supplier.DoesNotExist):
                raise NotFound({"detail": "Invalid supplier ID or supplier not found."})

        return Review.objects.none()