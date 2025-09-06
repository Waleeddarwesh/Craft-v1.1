from rest_framework import serializers
from .models import Course, CourseVideo, Enrollment
from accounts.serializers import SupplierProfileSummarySerializer
from accounts.models import User

class BaseCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "thumbnail",
            "title",
            "number_of_lectures",
            "is_completed",
        ]

class CourseSerializer(BaseCourseSerializer):
    supplier = SupplierProfileSummarySerializer(read_only=True)

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + [
            "category",
            "rating",
            "number_of_ratings",
            "from_date",
            "to_date",
            "course_hours",
            "address",
            "price",
            "description",
            "supplier",
        ]
        read_only_fields = ['id', 'rating', 'number_of_ratings', 'is_completed']


class OwnCourseSerializer(BaseCourseSerializer):
    supplier_name = serializers.CharField(source="supplier.user.get_full_name", read_only=True)
    supplier_photo = serializers.ImageField(source="supplier.photo", read_only=True)

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + [
            "number_of_uploaded_lectures",
            "supplier_name",
            "supplier_photo",
        ]

class SimpleCoursesSerializer(BaseCourseSerializer):
    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + [
            "category",
            "rating",
            "number_of_ratings",
            "from_date",
            "address",
            "price",
        ]

class CourseVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseVideo
        fields = [
            "id",
            "course",
            "video_number",
            "lecture_title",
            "description",
            "video_file",
        ]
        read_only_fields = ("video_number",)

class EnrollmentSerializer(serializers.ModelSerializer):
    course = serializers.UUIDField(write_only=True)
    course_details = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "course_details",
            "enrolled_user",
            "enrollment_date",
        ]
        read_only_fields = ['id', 'enrolled_user', 'enrollment_date']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['enrolled_user'] = user
        return super().create(validated_data)