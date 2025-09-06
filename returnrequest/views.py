from rest_framework import generics, serializers, viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
from .models import BalanceWithdrawRequest, Transaction, ReturnRequest
from accounts.models import Address
from products.models import Product
from orders.models import Order, OrderItem
from orders.Help import get_craft_user_by_email, get_warehouse_by_name
from .serializers import (
    BalanceWithdrawRequestSerializer, TransactionSerializer,
    ReturnRequestListRetrieveSerializer, ReturnRequestCreateSerializer,
    ReturnRequestDeliverSerializer
)

Craft = get_craft_user_by_email("CraftEG@craft.com")

class ReturnRequestViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReturnRequestCreateSerializer
    queryset = ReturnRequest.objects.all().select_related('user', 'order', 'product', 'delivery_person', 'supplier', 'from_address', 'to_address')
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ReturnRequest.objects.none()

        if hasattr(user, 'delivery_profile'):
            return ReturnRequest.objects.filter(
                Q(status=ReturnRequest.ReturnStatus.PICKUP_SCHEDULED) & Q(from_state=user.delivery_profile.governorate) |
                Q(status=ReturnRequest.ReturnStatus.IN_TRANSIT_TO_WAREHOUSE) & Q(delivery_person=user.delivery_profile) |
                Q(status=ReturnRequest.ReturnStatus.DELIVERED_TO_WAREHOUSE) & Q(delivery_person=user.delivery_profile) |
                Q(status=ReturnRequest.ReturnStatus.IN_TRANSIT_TO_SUPPLIER) & Q(delivery_person=user.delivery_profile)
            )
        elif hasattr(user, 'supplier_profile'):
            return ReturnRequest.objects.filter(
                Q(supplier=user.supplier_profile) |
                Q(status=ReturnRequest.ReturnStatus.DELIVERED_SUCCESSFULLY) & Q(supplier=user.supplier_profile)
            )
        else: # Customer
            return ReturnRequest.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ReturnRequestListRetrieveSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data.get('product_id')
        order = serializer.validated_data.get('order_id')
        quantity = serializer.validated_data.get('quantity')
        user = request.user
        
        try:
            order_instance = Order.objects.get(id=order)
            customer_address = Address.objects.get(id=order_instance.address.id)
            supplier_address = Address.objects.get(user=product.supplier.user)
        except (Order.DoesNotExist, Address.DoesNotExist):
            raise serializers.ValidationError("Order or address not found.")

        with transaction.atomic():
            amount = product.unit_price * Decimal(quantity)

            if customer_address.state == supplier_address.state:
                return_request = ReturnRequest.objects.create(
                    user=user,
                    supplier=product.supplier,
                    product=product,
                    order=order_instance,
                    quantity=quantity,
                    amount=amount,
                    from_address=customer_address,
                    to_address=supplier_address,
                    from_state=customer_address.state,
                    to_state=supplier_address.state,
                    status=ReturnRequest.ReturnStatus.PICKUP_SCHEDULED,
                )
            else:
                warehouse_address = get_warehouse_by_name(customer_address.state).address
                return_request = ReturnRequest.objects.create(
                    user=user,
                    supplier=product.supplier,
                    product=product,
                    order=order_instance,
                    quantity=quantity,
                    amount=amount,
                    from_address=customer_address,
                    to_address=warehouse_address,
                    from_state=customer_address.state,
                    to_state=warehouse_address.state,
                    status=ReturnRequest.ReturnStatus.PICKUP_SCHEDULED,
                )

        return Response({
            "message": "Return request created successfully. Our shipping driver will contact you.",
            "return_request_id": return_request.id,
            "total_amount": return_request.amount,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='delivery-accept')
    def delivery_accept(self, request, pk=None):
        try:
            return_request = self.get_queryset().get(pk=pk, delivery_person=None)
        except ReturnRequest.DoesNotExist:
            return Response({'detail': 'Return request not found or is already taken.'}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            return_request.delivery_person = request.user.delivery_profile
            return_request.status = ReturnRequest.ReturnStatus.IN_TRANSIT_TO_WAREHOUSE
            return_request.save()
        
        return Response({'status': 'Return request accepted and status updated to in transit to warehouse.'})

    @action(detail=True, methods=['post'], url_path='delivered-to-warehouse')
    def delivered_to_warehouse(self, request, pk=None):
        try:
            return_request = self.get_queryset().get(pk=pk, delivery_person=request.user.delivery_profile)
        except ReturnRequest.DoesNotExist:
            return Response({'detail': 'Return request not found or you are not assigned to it.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReturnRequestDeliverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation_code = serializer.validated_data.get('confirmation_code')

        if confirmation_code != return_request.confirmation_code:
            return Response({"detail": "Invalid confirmation code."}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            return_request.status = ReturnRequest.ReturnStatus.DELIVERED_TO_WAREHOUSE
            return_request.delivery_confirmed_at = timezone.now()
            return_request.save()
        
        return Response({'status': 'Return request status updated to delivered to warehouse.'})

    @action(detail=True, methods=['post'], url_path='supplier-accept')
    def supplier_accept(self, request, pk=None):
        return_request = self.get_object()
        user = request.user

        if not hasattr(user, 'supplier_profile') or return_request.supplier.user != user:
            return Response({'detail': 'You are not authorized to accept this return request.'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            return_amount = return_request.amount
            return_request.user.balance += return_amount
            user.supplier_profile.user.balance -= return_amount
            
            Transaction.objects.create(user=return_request.user, transaction_type=Transaction.TransactionType.RETURNED_PRODUCT, amount=return_amount)
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.RETURNED_PRODUCT, amount=-return_amount)
            return_request.status = ReturnRequest.ReturnStatus.ACCEPTED_BY_SUPPLIER
            return_request.save()

        return Response({'status': 'Return request accepted and balances updated'})
    
    @action(detail=True, methods=['post'], url_path='supplier-reject')
    def supplier_reject(self, request, pk=None):
        return_request = self.get_object()
        user = request.user

        if not hasattr(user, 'supplier_profile') or return_request.supplier.user != user:
            return Response({'detail': 'You are not authorized to reject this return request.'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            return_request.status = ReturnRequest.ReturnStatus.REJECTED_BY_SUPPLIER
            return_request.save()
        
        return Response({'status': 'Return request rejected'})
    
    @action(detail=True, methods=['post'], url_path='cancel', url_name='cancel-request')
    def cancel_request(self, request, pk=None):
        try:
            user = request.user
            return_request = ReturnRequest.objects.get(pk=pk, user=user)

            if return_request.status != ReturnRequest.ReturnStatus.CREATED:
                return Response({"detail": "Cannot cancel a return request after it has been shipped."}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                return_request.status = ReturnRequest.ReturnStatus.CANCELLED
                return_request.save()
            
            return Response({"detail": "Return request has been cancelled."}, status=status.HTTP_200_OK)
        except ReturnRequest.DoesNotExist:
            return Response({"detail": "Return request not found."}, status=status.HTTP_404_NOT_FOUND)        

class BalanceWithdrawRequestListCreateView(generics.ListCreateAPIView):
    queryset = BalanceWithdrawRequest.objects.all()
    serializer_class = BalanceWithdrawRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        amount = serializer.validated_data.get("amount")
        
        if user.balance < amount:
            raise serializers.ValidationError({"amount": "Insufficient balance for this withdrawal."})
        
        with transaction.atomic():
            user.balance -= amount
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.WITHDRAW, amount=-amount)
            user.save()

        serializer.save(user=user)
   
class BalanceWithdrawRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BalanceWithdrawRequest.objects.all()
    serializer_class = BalanceWithdrawRequestSerializer
    permission_classes = [IsAuthenticated]

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')