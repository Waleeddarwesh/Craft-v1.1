from django.contrib import admin
from .models import Product, ProductImage, ProductAttribute, Category, Collection, CollectionItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_active', 'slug')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'unit_price', 'stock', 'out_of_stock', 'discount_available', 'rating', 'publish_date')
    search_fields = ('name', 'supplier__user__email', 'supplier__user__first_name', 'supplier__user__last_name')
    list_filter = ('out_of_stock', 'discount_available', 'rating', 'publish_date')
    ordering = ('-publish_date',)
    inlines = [ProductImageInline, ProductAttributeInline]

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier')
    search_fields = ('name', 'supplier__user__email', 'supplier__user__first_name', 'supplier__user__last_name')

@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ('collection', 'product')
    search_fields = ('collection__name', 'product__name')