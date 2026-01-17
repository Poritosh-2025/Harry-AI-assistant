"""
Views for chat functionality.
Handles session management and AI communication.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.paginator import Paginator

from authentication.utils import api_response
from .models import ChatSession, ChatMessage, MessageRole
from .serializers import (
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    CreateChatSessionSerializer,
    SendMessageSerializer,
    UpdateSessionTitleSerializer,
    ChatMessageSerializer
)
from .ai_service import ai_client


class ChatSessionListView(APIView):
    """
    List all chat sessions for the authenticated user.
    GET /api/chat/sessions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Query params
        page = request.query_params.get('page', 1)
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        is_active = request.query_params.get('is_active')
        
        # Get user's sessions
        queryset = ChatSession.objects.filter(user=request.user)
        
        # Filter by active status
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        queryset = queryset.order_by('-updated_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = ChatSessionSerializer(page_obj.object_list, many=True)
        
        return api_response(
            True,
            'Chat sessions retrieved successfully',
            data={
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next()
                },
                'sessions': serializer.data
            }
        )


class CreateChatSessionView(APIView):
    """
    Create a new chat session.
    POST /api/chat/sessions/create/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateChatSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                'Invalid data',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        session = ChatSession.objects.create(
            user=request.user,
            title=serializer.validated_data.get('title', 'New Chat')
        )
        
        return api_response(
            True,
            'Chat session created successfully',
            data={'session': ChatSessionSerializer(session).data},
            status_code=status.HTTP_201_CREATED
        )


class ChatSessionDetailView(APIView):
    """
    Get, update, or delete a specific chat session.
    GET/PATCH/DELETE /api/chat/sessions/<session_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get_session(self, request, session_id):
        """Helper to get session and verify ownership."""
        try:
            return ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return None
    
    def get(self, request, session_id):
        """Get session with all messages."""
        session = self.get_session(request, session_id)
        if not session:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ChatSessionDetailSerializer(session)
        
        return api_response(
            True,
            'Chat session retrieved successfully',
            data={'session': serializer.data}
        )
    
    def patch(self, request, session_id):
        """Update session title."""
        session = self.get_session(request, session_id)
        if not session:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UpdateSessionTitleSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                'Invalid data',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        session.title = serializer.validated_data['title']
        session.save(update_fields=['title', 'updated_at'])
        
        return api_response(
            True,
            'Chat session updated successfully',
            data={'session': ChatSessionSerializer(session).data}
        )
    
    def delete(self, request, session_id):
        """Delete a chat session."""
        session = self.get_session(request, session_id)
        if not session:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        session.delete()
        
        return api_response(
            True,
            'Chat session deleted successfully',
            data={}
        )


class SendMessageView(APIView):
    """
    Send a message to AI and get response.
    POST /api/chat/send/
    
    Creates session if not provided, stores user message,
    sends to AI with full context, stores AI response.
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                'Invalid data',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        
        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return api_response(
                    False,
                    'Chat session not found',
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create new session
            session = ChatSession.objects.create(user=request.user)
        
        # Get conversation history for context
        conversation_history = session.get_conversation_history()
        
        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.USER,
            content=user_message
        )
        
        # Send to AI service with full context
        ai_response_text, metadata = ai_client.send_message(
            conversation_history=conversation_history,
            user_message=user_message
        )
        
        # Save AI response
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=ai_response_text if ai_response_text else metadata.get('error_message', 'No response from AI'),
            tokens_used=metadata.get('tokens_used'),
            model_used=metadata.get('model_used', ''),
            response_time_ms=metadata.get('response_time_ms'),
            is_error=metadata.get('is_error', False),
            error_message=metadata.get('error_message', '')
        )
        
        # Auto-generate title from first message
        if session.title == 'New Chat' and session.messages.filter(role=MessageRole.USER).count() == 1:
            session.generate_title_from_first_message()
        
        # Update session timestamp
        session.save(update_fields=['updated_at'])
        
        # Prepare response
        response_data = {
            'session_id': str(session.id),
            'session_title': session.title,
            'user_message': ChatMessageSerializer(user_msg).data,
            'assistant_message': ChatMessageSerializer(assistant_msg).data
        }
        
        if metadata.get('is_error'):
            return api_response(
                False,
                'AI service error',
                data=response_data,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return api_response(
            True,
            'Message sent successfully',
            data=response_data
        )


class ConversationHistoryView(APIView):
    """
    Get conversation history for a session.
    GET /api/chat/sessions/<session_id>/history/
    
    Returns paginated messages for a session.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        # Verify session ownership
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Query params
        page = request.query_params.get('page', 1)
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        
        # Get messages
        messages = session.messages.order_by('created_at')
        
        # Paginate
        paginator = Paginator(messages, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = ChatMessageSerializer(page_obj.object_list, many=True)
        
        return api_response(
            True,
            'Conversation history retrieved successfully',
            data={
                'session': {
                    'id': str(session.id),
                    'title': session.title
                },
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next()
                },
                'messages': serializer.data
            }
        )


class ClearSessionView(APIView):
    """
    Clear all messages in a session (start fresh).
    POST /api/chat/sessions/<session_id>/clear/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Delete all messages
        deleted_count = session.messages.all().delete()[0]
        
        # Reset title
        session.title = 'New Chat'
        session.save(update_fields=['title', 'updated_at'])
        
        return api_response(
            True,
            f'Session cleared successfully. {deleted_count} messages deleted.',
            data={'session': ChatSessionSerializer(session).data}
        )


class ArchiveSessionView(APIView):
    """
    Archive/unarchive a chat session.
    POST /api/chat/sessions/<session_id>/archive/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return api_response(
                False,
                'Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Toggle active status
        session.is_active = not session.is_active
        session.save(update_fields=['is_active', 'updated_at'])
        
        status_text = 'unarchived' if session.is_active else 'archived'
        
        return api_response(
            True,
            f'Session {status_text} successfully',
            data={'session': ChatSessionSerializer(session).data}
        )


class AIHealthCheckView(APIView):
    """
    Check if AI service is available.
    GET /api/chat/health/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        is_healthy = ai_client.health_check()
        
        return api_response(
            is_healthy,
            'AI service is available' if is_healthy else 'AI service is unavailable',
            data={
                'ai_service_status': 'healthy' if is_healthy else 'unhealthy',
                'ai_service_url': ai_client.base_url
            },
            status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
