import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db.models import Avg
from django.utils.timezone import now
from accounts.models import Supplier

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    picture = models.ImageField(upload_to='category_images/%y/%m/%d', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    material_category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name="material_products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name="category_products")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    quantity_per_unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_weight = models.DecimalField(max_digits=5, decimal_places=2)
    stock = models.IntegerField(default=0)
    out_of_stock = models.BooleanField(default=False)
    discount_available = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=5.0, validators=(MinValueValidator(0.0), MaxValueValidator(5.0)))
    publish_date = models.DateTimeField(auto_now_add=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))
    watt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=(MinValueValidator(0.0), MaxValueValidator(1000.0)))

    def __str__(self):
        return self.name

    def update_rating(self):
        avg_rating = self.product_ratings.aggregate(Avg('rating'))['rating__avg']
        self.rating = avg_rating if avg_rating is not None else 0
        self.save()

    def save(self, *args, **kwargs):
        if self.discount_percentage > 0:
            discount_amount = (self.unit_price * self.discount_percentage) / 100
            self.unit_price -= discount_amount
        super().save(*args, **kwargs)

@receiver(pre_save, sender=Product)
def toggle_out_of_stock(sender, instance, **kwargs):
    instance.out_of_stock = instance.stock == 0

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/%y/%m/%d")

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductAttribute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    attribute_type = models.CharField(max_length=50) # e.g., 'Color', 'Size'
    value = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.attribute_type}: {self.value} for {self.product.name}"

class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, related_name='collections', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=now, editable=False)
    products = models.ManyToManyField(Product, through='CollectionItem')

    def __str__(self):
        return self.name

class CollectionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(Collection, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='collection_items', on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return f"{self.product.name} in {self.collection.name}"