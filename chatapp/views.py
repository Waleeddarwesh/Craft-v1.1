from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from .models import Conversation, Message
from .serializers import ConversationListSerializer, ConversationSerializer, MessageSerializer

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return a list of conversations for the current user
        return Conversation.objects.filter(
            Q(initiator=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-start_time')

    def create(self, request, *args, **kwargs):
        # Override the create method to handle conversation creation logic
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'message': 'You cannot chat with a non-existent user'}, status=status.HTTP_404_NOT_FOUND)

        # Check if a conversation already exists between the two users
        conversation = Conversation.objects.filter(
            Q(initiator=self.request.user, receiver=participant) |
            Q(initiator=participant, receiver=self.request.user)
        ).first()

        if conversation:
            serializer = ConversationSerializer(conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create a new conversation
            new_conversation = Conversation.objects.create(
                initiator=self.request.user,
                receiver=participant
            )
            serializer = ConversationSerializer(new_conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class ConversationRetrieveView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        # Ensure the user has access to this conversation
        return Conversation.objects.filter(
            Q(initiator=self.request.user) | Q(receiver=self.request.user)
        )