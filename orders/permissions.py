from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from .models import Order, Shipment
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from accounts.models import Delivery, Supplier

class IsOrderPending(BasePermission):
    message = _("Updating or deleting a closed order is not allowed.")

    def has_object_permission(self, request, view, obj):
        if view.action in ("retrieve",):
            return True
        return obj.status == Order.OrderStatus.CREATED

class IsOrderItemByBuyerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        order_id = view.kwargs.get("order_id")
        if not order_id:
            return False
        order = get_object_or_404(Order, id=order_id)
        return order.user == request.user or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return obj.order.user == request.user or request.user.is_staff

class IsSupplier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'supplier_profile')

class DeliveryContractProvided(BasePermission):
    message = "Your delivery account has not been accepted yet. Administrators will accept your documents soon."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'delivery_profile'):
            return False

        delivery = user.delivery_profile
        if not delivery.contract or not delivery.identity:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{request.user.id}",
                {
                    "type": "send_notification",
                    "message": "Please upload your contract and identity documents."
                }
            )
            return False

        if not delivery.is_accepted:
            raise ValidationError(self.message)

        return True