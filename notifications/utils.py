# notifications/utils.py
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from accounts.models import User
from .models import Notification

def send_notification_to_user(user, message):
    """
    Saves a notification to the database and sends a real-time message via WebSockets.
    """
    # Save the notification to the database
    Notification.objects.create(user=user, message=message)

    # Send the notification over the WebSocket
    channel_layer = get_channel_layer()
    group_name = f"user_{user.id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_notification',
            'message': message,
        }
    )

def send_notification_to_suppliers(message):
    """
    Sends a notification to all users who are suppliers.
    """
    suppliers = User.objects.filter(is_supplier=True)
    for supplier in suppliers:
        send_notification_to_user(supplier, message)