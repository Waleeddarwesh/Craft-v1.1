import json
import base64
import secrets
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.files.base import ContentFile
from .models import Message, Conversation
from .serializers import MessageSerializer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        
        # Prepare the message event to send to the group
        event = {
            "type": "chat_message",
            **text_data_json
        }
        
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            event,
        )

    def chat_message(self, event):
        message_text = event.get("message")
        attachment_data = event.get("attachment")
        
        try:
            conversation = Conversation.objects.get(id=self.room_name)
            sender = self.scope['user']
            
            if attachment_data:
                file_str = attachment_data.get("data")
                file_ext = attachment_data.get("format")
                
                # Decode base64 data and create a Django ContentFile
                file_data = ContentFile(
                    base64.b64decode(file_str), 
                    name=f"{secrets.token_hex(8)}.{file_ext}"
                )
                
                new_message = Message.objects.create(
                    sender=sender,
                    attachment=file_data,
                    text=message_text,
                    conversation=conversation,
                )
            else:
                new_message = Message.objects.create(
                    sender=sender,
                    text=message_text,
                    conversation=conversation,
                )

            serializer = MessageSerializer(instance=new_message)
            self.send(text_data=json.dumps(serializer.data))

        except Conversation.DoesNotExist:
            # Handle the case where the conversation doesn't exist
            self.send(text_data=json.dumps({"error": "Conversation does not exist."}))
        except Exception as e:
            # Handle other potential errors
            self.send(text_data=json.dumps({"error": str(e)}))