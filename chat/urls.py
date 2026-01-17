"""
URL configuration for chat app.
"""
from django.urls import path
from .views import (
    ChatSessionListView,
    CreateChatSessionView,
    ChatSessionDetailView,
    SendMessageView,
    ConversationHistoryView,
    ClearSessionView,
    ArchiveSessionView,
    AIHealthCheckView
)

urlpatterns = [
    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='chat-session-list'),
    path('sessions/create/', CreateChatSessionView.as_view(), name='chat-session-create'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
    path('sessions/<uuid:session_id>/history/', ConversationHistoryView.as_view(), name='chat-history'),
    path('sessions/<uuid:session_id>/clear/', ClearSessionView.as_view(), name='chat-session-clear'),
    path('sessions/<uuid:session_id>/archive/', ArchiveSessionView.as_view(), name='chat-session-archive'),
    
    # Chat functionality
    path('send/', SendMessageView.as_view(), name='chat-send-message'),
    
    # Health check
    path('health/', AIHealthCheckView.as_view(), name='chat-ai-health'),
]
