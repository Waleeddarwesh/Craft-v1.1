from decimal import Decimal
import stripe
from django.conf import settings
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.response import Response
from orders.models import Order
from course.models import Course
from .serializers import OrderInformationSerializer, CourseInformationSerializer
from .models import PaymentHistory
from accounts.models import User
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from environ import Env

# Stripe API key
stripe.api_key = Env.str('STRIPE_SECRET_KEY')

class PaymentViewSet(viewsets.ViewSet):
    def _create_checkout_session(self, request, line_items, client_reference_id):
        base_success_url = request.build_absolute_uri(reverse("payment:success"))
        success_url = f"{base_success_url}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse("payment:cancel"))

        session_data = {
            "mode": "payment",
            "client_reference_id": client_reference_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": line_items,
        }
        return stripe.checkout.Session.create(**session_data)

    @action(detail=False, methods=["post"])
    def process_order_payment(self, request):
        serializer = OrderInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]
        order = get_object_or_404(Order, id=order_id)

        payment_history = PaymentHistory.objects.create(
            user=request.user,
            order=order,
            payment_status='pending'
        )
        
        try:
            line_items = []
            delivery_fee = order.delivery_fee if order.delivery_fee else Decimal("0.00")
            total_amount = order.final_amount - delivery_fee
            
            line_items.append({
                "price_data": {
                    "unit_amount": int(total_amount * Decimal("100")),
                    "currency": "EGP",
                    "product_data": {"name": f"Order {order.id}"},
                },
                "quantity": 1,
            })

            if delivery_fee > 0:
                line_items.append({
                    "price_data": {
                        "unit_amount": int(delivery_fee * Decimal("100")),
                        "currency": "EGP",
                        "product_data": {"name": "Delivery Fee"},
                    },
                    "quantity": 1,
                })

            session = self._create_checkout_session(request, line_items, f"order:{order.id}")
            payment_history.stripe_session_id = session.id
            payment_history.save()
            return Response({"status": "success", "url": session.url})
        except stripe.error.StripeError as e:
            payment_history.payment_status = 'failed'
            payment_history.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def process_course_payment(self, request):
        serializer = CourseInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data["course_id"]
        course = get_object_or_404(Course, id=course_id)
        
        buyer = request.user
        
        if buyer == course.supplier.user:
            raise ValidationError({"error": "You cannot purchase your own course."})

        if course.enrollments.filter(enrolled_user=buyer).exists():
            raise ValidationError({"error": "You are already enrolled in this course."})

        payment_history = PaymentHistory.objects.create(
            user=buyer,
            course=course,
            payment_status='pending'
        )

        try:
            line_items = [{
                "price_data": {
                    "unit_amount": int(course.price * Decimal("100")),
                    "currency": "EGP",
                    "product_data": {"name": course.title},
                },
                "quantity": 1,
            }]
            
            session = self._create_checkout_session(request, line_items, f"course:{course.id}")
            payment_history.stripe_session_id = session.id
            payment_history.save()
            return Response({"status": "success", "url": session.url})
        except stripe.error.StripeError as e:
            payment_history.payment_status = 'failed'
            payment_history.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def payment_completed(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return Response({"message": "Session ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Payment accepted, processing...", "session_id": session_id}, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def payment_canceled(request):
    return Response({"message": "Your payment was canceled."}, status=status.HTTP_406_NOT_ACCEPTABLE)