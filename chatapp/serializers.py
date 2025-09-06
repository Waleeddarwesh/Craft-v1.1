from rest_framework import serializers
from accounts.models import User
from .models import Conversation, Message

class UserChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'email'] # Added email for better user identification

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        exclude = ('conversation',) # Changed conversation_id to conversation
        
    def get_sender(self, obj):
        return UserChatSerializer(obj.sender).data

class ConversationListSerializer(serializers.ModelSerializer):
    initiator = UserChatSerializer()
    receiver = UserChatSerializer()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'initiator', 'receiver', 'last_message', 'start_time']

    def get_last_message(self, instance):
        message = instance.messages.first() # Changed message_set to messages as per refactored model
        if message:
            return MessageSerializer(instance=message).data
        return None

class ConversationSerializer(serializers.ModelSerializer):
    initiator = UserChatSerializer()
    receiver = UserChatSerializer()
    messages = MessageSerializer(many=True, read_only=True) # Changed message_set to messages

    class Meta:
        model = Conversation
        fields = ['id', 'initiator', 'receiver', 'messages', 'start_time']