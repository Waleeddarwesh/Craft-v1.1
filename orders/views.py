from rest_framework import viewsets, mixins, status, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from .models import CartItem, Cart, Order, OrderItem, Warehouse, Shipment, ShipmentItem, Coupon
from .serializers import (
    WishlistSerializer, AddWishlistItemSerializer, WishlistItemSerializer,
    CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer, CartItemSerializer,
    OrderCreateSerializer, OrderListRetrieveSerializer, SupplierOrderListSerializer,
    SupplierOrderRetrieveSerializer, ShipmentSerializer, CouponSerializer,
    ReturnRequestListRetrieveSerializer, WarehouseSerializer
)
from .permissions import IsSupplier, DeliveryContractProvided
from .Help import get_craft_user_by_email, get_warehouse_by_name
from returnrequest.models import Transaction
from accounts.models import Address
from decimal import Decimal
from collections import defaultdict
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid

Craft = get_craft_user_by_email("CraftEG@craft.com")

class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        if Wishlist.objects.filter(user=user).exists():
            raise ValidationError("A wishlist already exists for this user.")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response({"message": "Wishlist created successfully."}, status=status.HTTP_201_CREATED)

class WishlistItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(wishlist__user=self.request.user).select_related('product')

    def get_serializer_class(self):
        if self.action == "create":
            return AddWishlistItemSerializer
        return WishlistItemSerializer

    def perform_create(self, serializer):
        user = self.request.user
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        serializer.save(wishlist=wishlist)

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product')

    def create(self, request, *args, **kwargs):
        user = request.user
        if Cart.objects.filter(user=user).exists():
            raise ValidationError("A cart already exists for this user.")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response({"message": "Cart created successfully."}, status=status.HTTP_201_CREATED)

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related('product')

    def get_serializer_class(self):
        if self.action == "create":
            return AddCartItemSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateCartItemSerializer
        return CartItemSerializer

    def perform_create(self, serializer):
        user = self.request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        serializer.save(cart=cart)

    def perform_destroy(self, instance):
        if instance.cart.user != self.request.user:
            raise ValidationError("You cannot delete items from another user's cart.")
        instance.delete()

class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderCreateSerializer
    queryset = Order.objects.all().select_related('user', 'address').prefetch_related('items__product')
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'delivery_profile'):
            return Order.objects.for_delivery_person(user)
        return Order.objects.for_customer(user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListRetrieveSerializer
        elif self.action == 'orders_for_me':
            return SupplierOrderListSerializer
        elif self.action == 'retrieve_supplier_order':
            return SupplierOrderRetrieveSerializer
        return self.serializer_class

    @action(detail=False, methods=['post'], url_path='calculate-totals')
    def calculate_totals(self, request):
        cart, address, coupon_code, payment_method = self._validate_request_for_order(request)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product__supplier__user')
        self._validate_cart_stock(cart_items)
        totals = self._calculate_all_order_totals(cart_items, coupon_code, address)
        return Response({
            "message": "Order totals calculated successfully",
            "total_amount": totals['total_amount'],
            "discount_amount": totals['discount_amount'],
            "delivery_fee": totals['delivery_fee'],
            "final_amount": totals['final_amount']
        }, status=status.HTTP_200_OK)

    def create(self, request):
        with transaction.atomic():
            cart, address, coupon_code, payment_method = self._validate_request_for_order(request)
            cart_items = CartItem.objects.filter(cart=cart).select_related('product__supplier__user')
            self._validate_cart_stock(cart_items)
            totals = self._calculate_all_order_totals(cart_items, coupon_code, address)

            order = Order.objects.create(
                user=request.user, address=address, payment_method=payment_method,
                total_amount=totals['total_amount'], discount_amount=totals['discount_amount'],
                delivery_fee=totals['delivery_fee'], final_amount=totals['final_amount']
            )

            order_items_map = {item.product.id: OrderItem.objects.create(
                order=order, product=item.product, quantity=item.quantity,
                price=item.product.unit_price, color=item.color, size=item.size
            ) for item in cart_items}

            items_by_supplier = defaultdict(list)
            for item in cart_items:
                items_by_supplier[item.product.supplier.user.id].append(item)
            supplier_addresses = self._get_supplier_addresses(cart_items)

            self._create_shipments_for_suppliers(order, items_by_supplier, supplier_addresses, address, order_items_map)
            self._handle_payment_and_Transaction(request.user, payment_method, totals['final_amount'], cart_items)

            cart_items.delete()
            self._send_order_notification(request.user, order.id)

        return Response({
            "message": "Order Created Successfully",
            "order_id": str(order.id),
            "total_amount": order.total_amount,
            "discount_amount": order.discount_amount,
            "delivery_fee": order.delivery_fee,
            "final_amount": order.final_amount
        }, status=status.HTTP_201_CREATED)

    def _validate_request_for_order(self, request):
        address_id = request.data.get("address_id")
        coupon_code = request.data.get("coupon_code")
        payment_method = request.data.get("payment_method", "").strip()

        if not address_id:
            raise ValidationError({"message": "Address ID is required."})
        
        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                raise ValidationError({"message": "Cart is empty. Cannot create order."})
            address = Address.objects.get(id=address_id, user=request.user)
        except (Cart.DoesNotExist, Address.DoesNotExist):
            raise NotFound({"message": "Cart or address not found."})

        if payment_method and payment_method not in Order.PaymentMethod.values:
            raise ValidationError({"message": "Invalid or missing payment method."})

        return cart, address, coupon_code, payment_method

    def _create_shipments_for_suppliers(self, order, items_by_supplier, supplier_addresses, customer_address, order_items_map):
        for supplier_id, items in items_by_supplier.items():
            supplier_address = supplier_addresses[supplier_id]
            supplier_state = supplier_address.state
            customer_state = customer_address.state
            
            shipment_total = sum(item.product.unit_price * item.quantity for item in items)
            
            if supplier_state == customer_state:
                warehouse = get_warehouse_by_name(customer_state)
                shipment_status = Shipment.ShipmentStatus.CREATED
                self._create_shipment_instance(order, items[0].product.supplier, supplier_address, customer_address, items, shipment_status, warehouse.delivery_fee, order_items_map, shipment_total)
            else:
                warehouse_dest = get_warehouse_by_name(customer_state)
                warehouse_source = get_warehouse_by_name(supplier_state)
                
                # First leg: Supplier to Source Warehouse
                shipment_status_1 = Shipment.ShipmentStatus.CREATED
                self._create_shipment_instance(order, items[0].product.supplier, supplier_address, warehouse_source.address, items, shipment_status_1, warehouse_source.delivery_fee, order_items_map, shipment_total)

                # Second leg: Source Warehouse to Destination Warehouse
                shipment_status_2 = Shipment.ShipmentStatus.IN_TRANSMIT
                self._create_shipment_instance(order, items[0].product.supplier, warehouse_source.address, warehouse_dest.address, items, shipment_status_2, Decimal('20.00'), order_items_map, shipment_total)
                
                # Third leg: Destination Warehouse to Customer
                shipment_status_3 = Shipment.ShipmentStatus.DELIVERED_TO_SECOND_WAREHOUSE
                self._create_shipment_instance(order, items[0].product.supplier, warehouse_dest.address, customer_address, items, shipment_status_3, warehouse_dest.delivery_fee, order_items_map, shipment_total)
    
    def _create_shipment_instance(self, order, supplier, from_address, to_address, cart_items, status, delivery_fee, order_items_map, shipment_total):
        shipment = Shipment.objects.create(
            order=order,
            supplier=supplier,
            from_state=from_address.state,
            to_state=to_address.state,
            from_address=from_address,
            to_address=to_address,
            status=status,
            order_total_value=shipment_total
        )
        ShipmentItem.objects.bulk_create([
            ShipmentItem(
                shipment=shipment,
                order_item=order_items_map[item.product.id],
                quantity=item.quantity
            ) for item in cart_items
        ])
        return shipment

    def _validate_cart_stock(self, cart_items):
        for item in cart_items:
            if item.quantity > item.product.stock:
                raise ValidationError({"message": f"Quantity of {item.product.name} exceeds available stock."})
    
    def _get_supplier_addresses(self, cart_items):
        supplier_addresses = {}
        supplier_ids = {item.product.supplier.user.id for item in cart_items}
        for supplier_id in supplier_ids:
            try:
                supplier_address = Address.objects.get(user__id=supplier_id)
                supplier_addresses[supplier_id] = supplier_address
            except Address.DoesNotExist:
                raise ValidationError({"message": f"Address not found for supplier with ID {supplier_id}."})
        return supplier_addresses
    
    def _calculate_all_order_totals(self, cart_items, coupon_code, customer_address):
        total_amount = Decimal('0.00')
        discount_amount = Decimal('0.00')
        delivery_fee = Decimal('0.00')

        items_by_supplier = defaultdict(list)
        for item in cart_items:
            items_by_supplier[item.product.supplier.user.id].append(item)
        
        supplier_addresses = self._get_supplier_addresses(cart_items)

        for supplier_id, items in items_by_supplier.items():
            supplier_address = supplier_addresses[supplier_id]
            supplier_state = supplier_address.state
            customer_state = customer_address.state
            
            shipment_total, shipment_discount = self._calculate_shipment_totals(items, coupon_code)
            
            current_delivery_fee = Decimal('0.00')
            if supplier_state == customer_state:
                warehouse = get_warehouse_by_name(customer_state)
                current_delivery_fee = warehouse.delivery_fee
            else:
                warehouse_dest = get_warehouse_by_name(customer_state)
                warehouse_source = get_warehouse_by_name(supplier_state)
                current_delivery_fee = warehouse_dest.delivery_fee + warehouse_source.delivery_fee + Decimal('20.00')
            
            total_amount += shipment_total
            discount_amount += shipment_discount
            delivery_fee += current_delivery_fee
        
        final_amount = total_amount - discount_amount + delivery_fee
        
        return {
            'total_amount': total_amount,
            'discount_amount': discount_amount,
            'delivery_fee': delivery_fee,
            'final_amount': final_amount
        }

    def _calculate_shipment_totals(self, cart_items, coupon_code):
        total_amount = sum(item.product.unit_price * item.quantity for item in cart_items)
        discount_amount = Decimal('0.00')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_to__gte=timezone.now()
                )
                if any(item.product.supplier.id == coupon.supplier.id for item in cart_items):
                    discount_amount = (coupon.discount / Decimal('100.00')) * total_amount
            except Coupon.DoesNotExist:
                raise ValidationError({"message": "Invalid or expired coupon."})
        return total_amount, discount_amount

    def _handle_payment_and_Transaction(self, user, payment_method, final_amount, cart_items):
        if payment_method == Order.PaymentMethod.BALANCE:
            if user.balance < final_amount:
                raise ValidationError({"message": "Insufficient balance for this order. Your Payment Method will turn into Cash on Delivery."})
            
            user.balance -= final_amount
            user.save()
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=-final_amount)
            
        # The cashback amount is 5% of the final amount
        cashback_amount = final_amount * Decimal('0.05')
        Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.CASH_BACK, amount=cashback_amount)
        
        self._update_product_stock(cart_items)

    def _update_product_stock(self, cart_items):
        for item in cart_items:
            product = item.product
            product.stock = F('stock') - item.quantity
            product.save(update_fields=['stock'])

    def _send_order_notification(self, user, order_id):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "send_notification",
                "message": f"Your order with ID {order_id} has been created."
            }
        )

    @action(detail=False, methods=['get'], url_path='orders-for-me', permission_classes=[IsAuthenticated, IsSupplier])
    def orders_for_me(self, request):
        user = request.user
        queryset = Order.objects.filter(shipments__supplier__user=user).distinct().order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='orders-for-me-details', permission_classes=[IsAuthenticated, IsSupplier])
    def retrieve_supplier_order(self, request, pk=None):
        user = request.user
        try:
            order = Order.objects.get(pk=pk, shipments__supplier__user=user)
        except Order.DoesNotExist:
            return Response({"message": "Order not found or you don't have permission to view it."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='ready-to-ship', permission_classes=[IsAuthenticated, IsSupplier])
    def ready_to_ship(self, request, pk=None):
        try:
            shipment = Shipment.objects.get(
                order__pk=pk, 
                supplier=request.user.supplier_profile,
                status=Shipment.ShipmentStatus.CREATED
            )
        except Shipment.DoesNotExist:
            return Response({"message": "Shipment not found or is not in a 'created' state."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            shipment.status = Shipment.ShipmentStatus.READY_TO_SHIP
            shipment.save(update_fields=['status'])
        
        return Response({"message": f"Shipment for order {pk} is now ready to ship."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel', url_name='cancel-order')
    def cancel_order(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            if order.status not in [Order.OrderStatus.CREATED, Order.OrderStatus.IN_TRANSMIT]:
                return Response({"message": "Cannot cancel this order at its current status."}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            order.status = Order.OrderStatus.CANCELLED
            order.save()
            
            # The logic for refunding balance and handling Transaction is moved here.
            # This is a good practice to keep related logic together within a single action.
            if order.payment_method == Order.PaymentMethod.BALANCE:
                request.user.balance += order.final_amount
                request.user.save()
                Transaction.objects.create(
                    user=request.user,
                    transaction_type=Transaction.TransactionType.RETURNED_PRODUCT,
                    amount=order.final_amount
                )
            # Other payment methods could be handled here as well.
            
            return Response({"message": "Order has been cancelled."}, status=status.HTTP_200_OK)


class ShipmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, DeliveryContractProvided]
    queryset = Shipment.objects.all().select_related('order__user', 'delivery_person__user', 'supplier__user')

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'delivery_profile'):
            return Shipment.objects.none()

        return Shipment.objects.filter(
            Q(status=Shipment.ShipmentStatus.READY_TO_SHIP) & Q(to_state=user.delivery_profile.governorate) |
            Q(status=Shipment.ShipmentStatus.DELIVERED_TO_SECOND_WAREHOUSE) & Q(to_state=user.delivery_profile.governorate) |
            Q(delivery_person=user.delivery_profile) & Q(status=Shipment.ShipmentStatus.ON_MY_WAY)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        try:
            shipment = self.get_queryset().get(pk=pk, delivery_person__isnull=True)
        except Shipment.DoesNotExist:
            return Response({'message': 'Shipment not found or is already taken.'}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            shipment.delivery_person = request.user.delivery_profile
            shipment.status = Shipment.ShipmentStatus.ON_MY_WAY
            shipment.save(update_fields=['delivery_person', 'status'])
            
            order = shipment.order
            if all(s.status == Shipment.ShipmentStatus.ON_MY_WAY for s in order.shipments.filter(Q(status=Shipment.ShipmentStatus.ON_MY_WAY))):
                order.status = Order.OrderStatus.ON_MY_WAY
                order.save(update_fields=['status'])

        return Response({'status': 'Shipment accepted and status updated to on my way'})

    @action(detail=True, methods=['post'], url_path='delivered')
    def delivered(self, request, pk=None):
        try:
            shipment = self.get_queryset().get(pk=pk, delivery_person=request.user.delivery_profile)
        except Shipment.DoesNotExist:
            return Response({'message': 'Shipment not found or you are not assigned to it.'}, status=status.HTTP_404_NOT_FOUND)

        confirmation_code = request.data.get('confirmation_code')
        if confirmation_code != shipment.confirmation_code:
            return Response({"message": "Invalid confirmation code."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            shipment.status = Shipment.ShipmentStatus.DELIVERED_SUCCESSFULLY
            shipment.delivery_confirmed_at = timezone.now()
            shipment.save(update_fields=['status', 'delivery_confirmed_at'])
            
            order = shipment.order
            if all(s.status == Shipment.ShipmentStatus.DELIVERED_SUCCESSFULLY for s in order.shipments.all()):
                order.status = Order.OrderStatus.DELIVERED_SUCCESSFULLY
                order.save(update_fields=['status'])
            
            self._process_payments(request.user, shipment)
        
        return Response({'message': 'Shipment status updated to delivered successfully'}, status=status.HTTP_200_OK)

    def _process_payments(self, user, shipment):
        warehouse = get_warehouse_by_name(shipment.to_state)
        # Delivery person's share and Craft's cut from the delivery fee
        delivery_fee_share = warehouse.delivery_fee * Decimal('0.85')
        craft_delivery_cut = warehouse.delivery_fee * Decimal('0.15')
        
        # Supplier and Craft's cut from the order items
        order_items = shipment.items.all().select_related('order_item__product')
        supplier_total = sum(item.order_item.price * item.order_item.quantity for item in order_items)
        
        supplier_revenue = supplier_total * Decimal('0.85')
        craft_supplier_cut = supplier_total * Decimal('0.15')

        if shipment.order.payment_method in [Order.PaymentMethod.BALANCE, Order.PaymentMethod.CREDIT_CARD]:
            user.balance += delivery_fee_share
            Craft.balance += craft_delivery_cut
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=delivery_fee_share)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=craft_delivery_cut)

            shipment.supplier.user.balance += supplier_revenue
            Craft.balance += craft_supplier_cut
            Transaction.objects.create(user=shipment.supplier.user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=supplier_revenue)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.SUPPLIER_TRANSFORM, amount=craft_supplier_cut)
                
        elif shipment.order.payment_method == Order.PaymentMethod.CASH_ON_DELIVERY:
            user.balance -= (supplier_total + warehouse.delivery_fee)
            shipment.supplier.user.balance += supplier_revenue
            Craft.balance += craft_supplier_cut + craft_delivery_cut
            
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=-(supplier_total + warehouse.delivery_fee))
            Transaction.objects.create(user=shipment.supplier.user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=supplier_revenue)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.SUPPLIER_TRANSFORM, amount=craft_supplier_cut)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=craft_delivery_cut)
        
        user.save()
        shipment.supplier.user.save()
        Craft.save()

class OrdersHistoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderListRetrieveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user).order_by('-created_at').select_related('address').prefetch_related('items__product')
        return Order.objects.none()

class ReturnOrdersProductsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ReturnRequestListRetrieveSerializer  
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        fourteen_days_ago = timezone.now() - timezone.timedelta(days=14)
        if hasattr(user, 'customer_profile'):
            return Order.objects.filter(user=user, updated_at__gte=fourteen_days_ago).prefetch_related('items__product')
        return Order.objects.none()

class CouponViewSet(viewsets.ModelViewSet):
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_queryset(self):
        return Coupon.objects.filter(supplier=self.request.user.supplier_profile)

    def perform_create(self, serializer):
        coupon = serializer.save(supplier=self.request.user.supplier_profile)
        supplier_products = Product.objects.filter(supplier=self.request.user.supplier_profile)
        coupon.products.set(supplier_products)
    
    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.supplier != self.request.user.supplier_profile:
            raise ValidationError("You do not have permission to perform this action.")
        serializer.save()
        supplier_products = Product.objects.filter(supplier=self.request.user.supplier_profile)
        instance.products.set(supplier_products)

    def perform_destroy(self, instance):
        if instance.supplier != self.request.user.supplier_profile:
            raise ValidationError("You do not have permission to perform this action.")
        instance.delete()

class WarehouseListView(generics.ListAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]