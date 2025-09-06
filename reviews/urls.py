from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ReviewListAPIView

# Create a router for the main ReviewViewSet
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Main review endpoints for creating, retrieving, updating, and deleting a review.
    path('', include(router.urls)),

    # Endpoints to list reviews for a specific object type.
    # These URLs are nested under the parent resource, which is a standard REST practice.
    path('products/<uuid:product_id>/reviews/', ReviewListAPIView.as_view(), name='product-review-list'),
    path('courses/<uuid:course_id>/reviews/', ReviewListAPIView.as_view(), name='course-review-list'),
    path('deliveries/<uuid:delivery_id>/reviews/', ReviewListAPIView.as_view(), name='delivery-review-list'),
    path('suppliers/<uuid:supplier_id>/reviews/', ReviewListAPIView.as_view(), name='supplier-review-list'),
]