from django.urls import path
from .views import ConversationListCreateView, ConversationRetrieveView

urlpatterns = [
    path('conversations/', ConversationListCreateView.as_view(), name='conversations'),
    path('conversations/<uuid:id>/', ConversationRetrieveView.as_view(), name='conversation-detail'),
]