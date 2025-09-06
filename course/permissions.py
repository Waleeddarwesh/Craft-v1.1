from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'customer_profile')

class IsSupplier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'supplier_profile')

    def has_object_permission(self, request, view, obj):
        # A supplier can only modify their own courses
        return hasattr(obj, 'supplier') and obj.supplier.user == request.user

class IsSupplierOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (hasattr(request.user, 'supplier_profile') or hasattr(request.user, 'customer_profile'))