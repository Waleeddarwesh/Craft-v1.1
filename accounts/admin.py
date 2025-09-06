from django.contrib import admin
from .models import User, Customer, Supplier, Delivery, Address, Follow, OneTimePassword

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_verified', 'is_customer', 'is_supplier', 'is_delivery')
    ordering = ('email',)

class CustomerAdmin(admin.ModelAdmin):
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ['user']

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('user', 'category_title', 'rating', 'orders_count', 'followers_count')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'category_title')
    list_filter = ('category_title', 'rating', 'is_accepted')
    ordering = ('-rating',)
    raw_id_fields = ['user']

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_model', 'vehicle_color', 'plate_number', 'rating', 'orders_count', 'experience_years')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'vehicle_model', 'plate_number')
    list_filter = ('rating', 'experience_years', 'is_accepted')
    ordering = ('-rating',)
    raw_id_fields = ['user']

class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'building_number', 'street', 'city', 'state')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'street', 'city', 'state')
    list_filter = ('city', 'state')
    raw_id_fields = ['user']

class FollowAdmin(admin.ModelAdmin):
    def get_follower_name(self, obj):
        return obj.follower.user.get_full_name if obj.follower else 'N/A'
    get_follower_name.admin_order_field = 'follower_object_id'
    get_follower_name.short_description = 'Follower'

    list_display = ('get_follower_name', 'supplier', 'created_at')
    search_fields = (
        'follower_object_id',
        'supplier__user__email',
        'supplier__user__first_name',
        'follower_content_type__model',
    )
    list_filter = ('follower_content_type', 'supplier')
    raw_id_fields = ['supplier']

class OneTimePasswordAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'otp')
    raw_id_fields = ['user']

admin.site.register(User, UserAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(OneTimePassword, OneTimePasswordAdmin)