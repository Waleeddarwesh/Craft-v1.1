# reviews/models.py
import uuid
from django.db import models
from products.models import Product
from course.models import Course
from accounts.models import Customer, Delivery, Supplier

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    DELIVERY_CHOICES = [
        ('Dissatisfied', 'Dissatisfied'),
        ('Satisfied', 'Satisfied'),
        ('Very Satisfied', 'Very Satisfied')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_reviews')
    product = models.ForeignKey(Product, related_name='product_ratings', on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, related_name='course_ratings', on_delete=models.CASCADE, null=True, blank=True)
    delivery = models.ForeignKey(Delivery, related_name='delivery_ratings', on_delete=models.CASCADE, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, related_name='supplier_ratings', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    image = models.ImageField(upload_to="product_reviews_images/%y/%m/%d", blank=True, null=True)
    ease_of_place_order = models.CharField(choices=DELIVERY_CHOICES, null=True, blank=True, max_length=50)
    speed_of_delivery = models.CharField(choices=DELIVERY_CHOICES, null=True, blank=True, max_length=50)
    product_packaging = models.CharField(choices=DELIVERY_CHOICES, null=True, blank=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.product:
            return f"Review for {self.product.name} by {self.customer.user.get_full_name}"
        elif self.course:
            return f"Review for {self.course.title} by {self.customer.user.get_full_name}"
        elif self.delivery:
            return f"Review for Delivery Person {self.delivery.user.get_full_name}"
        elif self.supplier:
            return f"Review for Supplier {self.supplier.user.get_full_name}"
        return f"Review by {self.customer.user.get_full_name}"