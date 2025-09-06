# accounts/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.timezone import now
from datetime import datetime
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .maneger import UserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

AUTH_PROVIDERS = {'email': 'email', 'google': 'google', 'github': 'github', 'linkedin': 'linkedin'}

class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True, editable=False)
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    phone_number = models.CharField(max_length=14, verbose_name=_("Phone number"), blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    is_delivery = models.BooleanField(default=False)
    last_password_reset_request = models.DateTimeField(null=True, blank=True)
    auth_provider = models.CharField(max_length=50, default=AUTH_PROVIDERS.get('email'))

    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]
    objects = UserManager()
    USERNAME_FIELD = "email"

    @property
    def get_full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if not self.pk or not self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    photo = models.ImageField(upload_to='customer_photos/%y/%m/%d', blank=True, null=True)

    def __str__(self):
        return f"Customer: {self.user.get_full_name}"

class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    photo = models.ImageField(upload_to='supplier_photos/%y/%m/%d', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='supplier_covers/%y/%m/%d', blank=True, null=True)
    category_title = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='supplier_logos/%y/%m/%d', blank=True, null=True)
    contract = models.FileField(upload_to='supplier_contracts/%y/%m/%d', blank=True, null=True)
    identity = models.FileField(upload_to='supplier_identities/%y/%m/%d', blank=True, null=True)
    followers_count = models.PositiveIntegerField(default=0)
    experience_years = models.IntegerField(blank=True, null=True)
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=5.0, validators=(MinValueValidator(0.0), MaxValueValidator(5.0)))
    orders_count = models.IntegerField(blank=True, null=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Supplier: {self.user.get_full_name}"

    def update_rating(self):
        avg_rating = self.supplier_ratings.aggregate(models.Avg('rating'))['rating__avg']
        self.rating = avg_rating if avg_rating is not None else 0
        self.save()

class Delivery(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="delivery_profile")
    photo = models.ImageField(upload_to='shipper_photos/%y/%m/%d', blank=True, null=True)
    contract = models.ImageField(upload_to='shipper_contracts/%y/%m/%d', blank=True, null=True)
    identity = models.ImageField(upload_to='shipper_identities/%y/%m/%d', blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_color = models.CharField(max_length=100, blank=True, null=True)
    plate_number = models.CharField(max_length=100, blank=True)
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=5.0, validators=(MinValueValidator(0.0), MaxValueValidator(5.0)))
    orders_count = models.IntegerField(blank=True, null=True)
    experience_years = models.IntegerField(blank=True, null=True)
    governorate = models.CharField(max_length=100, default='default_governorate')
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Delivery: {self.user.get_full_name}"

    def update_rating(self):
        avg_rating = self.delivery_ratings.aggregate(models.Avg('rating'))['rating__avg']
        self.rating = avg_rating if avg_rating is not None else 0
        self.save()

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    building_number = models.CharField(max_length=10, null=True)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    def __str__(self):
        return f"Address for {self.user.get_full_name}"

class Follow(models.Model):
    follower_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    follower_object_id = models.PositiveIntegerField()
    follower = GenericForeignKey('follower_content_type', 'follower_object_id')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower_content_type', 'follower_object_id', 'supplier')

    def __str__(self):
        return f"{self.follower} follows {self.supplier.user.get_full_name}"

@receiver(post_save, sender=Follow)
def update_followers_count_on_create(sender, instance, created, **kwargs):
    if created:
        instance.supplier.followers_count += 1
        instance.supplier.save()

@receiver(post_delete, sender=Follow)
def update_followers_count_on_delete(sender, instance, **kwargs):
    instance.supplier.followers_count -= 1
    instance.supplier.save()

class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.first_name} - OTP code"