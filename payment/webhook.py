import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from course.models import Course, Enrollment
from .models import PaymentHistory
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not sig_header:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except Exception:
        return HttpResponse(status=500)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        session_id = session.get('id')
        payment_intent_id = session.get('payment_intent')
        
        with transaction.atomic():
            payment_history = PaymentHistory.objects.select_for_update().filter(stripe_session_id=session_id).first()
            
            if not payment_history:
                return HttpResponse("Payment history record not found.", status=200)
            
            if payment_history.payment_status == 'succeeded':
                return HttpResponse("Payment already processed.", status=200)

            payment_history.payment_status = 'succeeded'
            payment_history.stripe_payment_intent_id = payment_intent_id
            payment_history.save()

            if client_reference_id and client_reference_id.startswith('order:'):
                order_id = client_reference_id.split(':')[1]
                try:
                    order = Order.objects.get(id=order_id)
                    order.paid = True
                    order.save()
                except Order.DoesNotExist:
                    return HttpResponse(f"Order {order_id} not found.", status=200)

            elif client_reference_id and client_reference_id.startswith('course:'):
                course_id = client_reference_id.split(':')[1]
                try:
                    course = Course.objects.get(id=course_id)
                    buyer = payment_history.user
                    
                    if not buyer:
                        return HttpResponse("Buyer not found.", status=200)
                    
                    Enrollment.objects.get_or_create(course=course, enrolled_user=buyer)
                except Course.DoesNotExist:
                    return HttpResponse(f"Course {course_id} not found.", status=200)
                except Exception as e:
                    return HttpResponse(f"Error enrolling course: {e}", status=500)

    return HttpResponse(status=200)