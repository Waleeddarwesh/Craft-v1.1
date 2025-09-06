# accounts/utils.py
from django.conf import settings
from django.core.mail import EmailMessage
from .models import User, OneTimePassword
import random
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.contenttypes.models import ContentType
from .models import Customer, Supplier

def generate_otp_and_send_email(email, is_verification=True):
    """
    Generates a new OTP for the given email and sends it.
    If is_verification is True, sends a verification email.
    Otherwise, sends a password reset email.
    """
    try:
        user = User.objects.get(email=email)
        otp = random.randint(1000, 9999)
        OneTimePassword.objects.update_or_create(user=user, defaults={'otp': otp})

        subject = "One-Time Passcode for Email Verification" if is_verification else "One-Time Passcode for Password Reset"
        body = (
            f"Dear {user.first_name},\n\n"
            f"Your one-time passcode is: {otp}\n\n"
            "If you did not request this, please disregard this message.\n\n"
            "Best regards,\n"
            "The CraftEG Team"
        )
        email_message = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [email])
        email_message.send()

        return True
    except User.DoesNotExist:
        return False

def get_tokens_for_user(user):
    """
    Generates and returns JWT access and refresh tokens for a user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_follower_content_type(user):
    """
    Determines the correct content type for a user based on their profile.
    """
    if hasattr(user, 'customer_profile'):
        return ContentType.objects.get_for_model(Customer), user.customer_profile.id
    elif hasattr(user, 'supplier_profile'):
        return ContentType.objects.get_for_model(Supplier), user.supplier_profile.id
    return None, None