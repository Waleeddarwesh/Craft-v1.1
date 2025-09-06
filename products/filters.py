import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='iexact')
    keyword = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='lte')

    class Meta:
        model = Product
        fields = ('category', 'supplier', 'keyword', 'min_price', 'max_price')