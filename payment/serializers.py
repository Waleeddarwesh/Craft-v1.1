from rest_framework import serializers
from orders.models import Order
from course.models import Course

class OrderInformationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order with the given ID does not exist.")
        
        if order.paid:
            raise serializers.ValidationError("This order has already been paid.")
        
        return value

class CourseInformationSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course with the given ID does not exist.")
        return value