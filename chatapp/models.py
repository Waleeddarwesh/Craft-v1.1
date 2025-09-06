# chatapp/models.py
from django.db import models
from accounts.models import User
import uuid

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    initiator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="conversations_started")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="conversations_received")
    start_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation between {self.initiator} and {self.receiver}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    text = models.CharField(max_length=200, blank=True)
    attachment = models.FileField(blank=True, upload_to='chat_attachments/%Y/%m/%d')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f"Message from {self.sender} in conversation {self.conversation.id}"