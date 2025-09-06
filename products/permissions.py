from rest_framework import permissions
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.exceptions import ValidationError

class IsSupplier(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'supplier_profile')

class SupplierContractProvided(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated and hasattr(user, 'supplier_profile'):
            supplier = user.supplier_profile
            if not supplier.contract and not supplier.identity:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{request.user.id}",
                    {
                        "type": "send_notification",
                        "message": "Upload your contract and identity documents, please."
                    }
                )
                return False
            
            if not supplier.is_accepted:
                raise ValidationError("Your supplier account has not been accepted yet. The administrators will accept your documents soon.")
            
        return True

class DeliveryContractProvided(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated and hasattr(user, 'delivery_profile'):
            delivery = user.delivery_profile
            if not delivery.contract and not delivery.identity:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{request.user.id}",
                    {
                        "type": "send_notification",
                        "message": "Upload your contract and identity documents, please."
                    }
                )
                return False
            
            if not delivery.is_accepted:
                raise ValidationError("Your delivery account has not been accepted yet. The administrators will accept your documents soon.")
            
        return True

class IsCustomerOrSupplier(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (hasattr(request.user, 'customer_profile') or hasattr(request.user, 'supplier_profile'))