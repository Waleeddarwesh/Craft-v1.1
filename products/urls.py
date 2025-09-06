from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, SupplierProductViewSet, CollectionViewSet, 
    ProductsByFollowedSuppliersView, LatestFollowedSuppliersCollectionsView, 
    ProductsByCategoryViewSet, ProductsByMaterialViewSet, 
    CategoryListView, MaterialListView
)

router = DefaultRouter()
router.register('products', ProductViewSet)
router.register('supplier-products', SupplierProductViewSet, basename='supplier-products')
router.register('collections', CollectionViewSet, basename='collection')

urlpatterns = [
    path('', include(router.urls)),
    path('products-by-followed-suppliers/', ProductsByFollowedSuppliersView.as_view(), name='products-by-followed-suppliers'),
    path('latest-followed-collections/', LatestFollowedSuppliersCollectionsView.as_view(), name='latest-followed-collections'),
    path('products-by-category/<uuid:category_id>/', ProductsByCategoryViewSet.as_view(), name='products-by-category'),
    path('products-by-material/<uuid:material_id>/', ProductsByMaterialViewSet.as_view(), name='products-by-material'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('materials/', MaterialListView.as_view(), name='material-list'),
]