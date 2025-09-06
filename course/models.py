# course/models.py
import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg
from accounts.models import Supplier, User
from products.models import Category

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thumbnail = models.ImageField(upload_to='course_thumbnails/%Y/%m/%d', blank=True, null=True)
    title = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=5.0, validators=(MinValueValidator(0.0), MaxValueValidator(5.0)))
    is_completed = models.BooleanField(default=False)
    number_of_ratings = models.IntegerField(default=0)
    from_date = models.DateTimeField(blank=True, null=True)
    to_date = models.DateTimeField(blank=True, null=True)
    course_hours = models.IntegerField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    number_of_lectures = models.IntegerField(default=0, blank=True, null=True)
    number_of_uploaded_lectures = models.IntegerField(default=0, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True, related_name='courses')

    def __str__(self):
        return self.title

    def update_rating(self):
        avg_rating = self.course_ratings.aggregate(Avg('rating'))['rating__avg']
        self.rating = avg_rating if avg_rating is not None else 0
        self.save()

class CourseVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    lecture_title = models.CharField(max_length=100)
    video_number = models.IntegerField()
    description = models.TextField()
    video_file = models.FileField(upload_to='course_videos/%y/%m/%d')

    class Meta:
        unique_together = ('course', 'video_number')
        verbose_name_plural = "Course Videos"

    def __str__(self):
        return self.lecture_title

class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Enrollment for {self.enrolled_user.get_full_name} in {self.course.title}"