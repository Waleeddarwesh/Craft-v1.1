from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from .utils import send_notification_to_suppliers

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def send_to_suppliers(self, request):
        """
        An API endpoint to send a notification to all suppliers.
        This action requires authentication and is primarily for admin/internal use.
        """
        message = request.data.get('message')
        if not message:
            return Response({'message': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        send_notification_to_suppliers(message)
        return Response({'message': 'Notifications sent to all suppliers.'}, status=status.HTTP_200_OK)