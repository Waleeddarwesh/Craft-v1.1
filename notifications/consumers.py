import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            # The group name should be based on a UUID for security
            self.group_name = f"user_{self.user.id}"
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()
        else:
            self.close()

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'mark_as_read':
            notification_id = data.get('id')
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id, user=self.user)
                    notification.is_read = True
                    notification.save()
                    self.send(text_data=json.dumps({
                        'type': 'notification_read',
                        'id': str(notification.id)
                    }))
                except Notification.DoesNotExist:
                    pass
        
    def send_notification(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message,
        }))