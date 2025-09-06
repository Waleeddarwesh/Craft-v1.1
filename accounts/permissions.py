from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        # The user's profile is linked via `customer_profile`
        return request.user.is_authenticated and hasattr(request.user, 'customer_profile')

class IsSupplier(BasePermission):
    def has_permission(self, request, view):
        # The user's profile is linked via `supplier_profile`
        return request.user.is_authenticated and hasattr(request.user, 'supplier_profile')

class IsCustomerOrSupplier(BasePermission):
    def has_permission(self, request, view):
        # A user can be either a customer or a supplier, but not both at the same time
        return request.user.is_authenticated and (hasattr(request.user, 'customer_profile') or hasattr(request.user, 'supplier_profile'))