# returnrequest/models.py
import uuid
import random
import string
from django.db import models
from django.db.models import Q
from django.utils import timezone
from accounts.models import User, Supplier, Delivery, Address
from orders.models import Order
from products.models import Product

class ReturnRequest(models.Model):
    class ReturnStatus(models.TextChoices):
        CREATED = 'created'
        PICKUP_SCHEDULED = 'pickup_scheduled'
        IN_TRANSIT_TO_WAREHOUSE = 'in_transit_to_warehouse'
        DELIVERED_TO_WAREHOUSE = 'delivered_to_warehouse'
        IN_TRANSIT_TO_SUPPLIER = 'in_transit_to_supplier'
        DELIVERED_SUCCESSFULLY = 'delivered_successfully'
        FAILED_DELIVERY = 'failed_delivery'
        CANCELLED = 'cancelled'
        ACCEPTED_BY_SUPPLIER = 'accepted_by_supplier'
        REJECTED_BY_SUPPLIER = 'rejected_by_supplier'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, related_name='return_requests')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='product_returns')
    quantity = models.IntegerField()
    delivery_person = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_shipments')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_returns", null=True)
    from_address = models.ForeignKey(Address, on_delete=models.SET_NULL, related_name="return_from_address", null=True)
    to_address = models.ForeignKey(Address, on_delete=models.SET_NULL, related_name="return_to_address", null=True)
    from_state = models.CharField(max_length=250, blank=True)
    to_state = models.CharField(max_length=250, blank=True)
    confirmation_code = models.CharField(max_length=6, null=True, blank=True)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=ReturnStatus.choices, default=ReturnStatus.CREATED)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Return Request #{self.pk} - {self.user.get_full_name}"

class BalanceWithdrawRequest(models.Model):
    class TransferStatus(models.TextChoices):
        CREATED = 'Created'
        DONE = 'Done'
        REFUSED = 'Refused'

    class TransferType(models.TextChoices):
        BANK_TRANSFER = 'Bank Transfer'
        INSTAPAY = 'Instapay'
        PHONE_WALLET = 'Phone Wallet'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balance_withdraw_requests')
    transfer_number = models.CharField(max_length=50)
    transfer_type = models.CharField(max_length=50, choices=TransferType.choices, default=TransferType.BANK_TRANSFER)
    transfer_status = models.CharField(max_length=50, choices=TransferStatus.choices, default=TransferStatus.CREATED)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal request for {self.user.get_full_name}"

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        WITHDRAW = 'Withdraw'
        CASH_BACK = 'Cash Back'
        RETURNED_CASH_BACK = 'Returned Cash Back'
        RETURNED_PRODUCT = 'Returned Product'
        PURCHASED_PRODUCTS = 'Purchased Products'
        REFUND_FAILED = 'Refund Failed'
        DELIVERY_FEE = 'Delivery Fee'
        PURCHASED_COURSE = 'Purchased Course'
        SUPPLIER_TRANSFORM = 'Supplier Transform'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.user.email}"