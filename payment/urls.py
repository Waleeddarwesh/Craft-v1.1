from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, payment_completed, payment_canceled
from . import webhook

app_name = "payment"

router = DefaultRouter()
router.register('payments', PaymentViewSet, basename="payment")

urlpatterns = [
    path('success/', payment_completed, name='success'),
    path('canceled/', payment_canceled, name='cancel'),
    path('webhook/', webhook.stripe_webhook, name='stripe-webhook'),
    path('', include(router.urls)),
]