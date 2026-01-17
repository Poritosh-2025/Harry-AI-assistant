"""
Serializers for chat functionality.
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage, MessageRole


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual chat messages."""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'message_count',
            'last_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.get_message_count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for chat session with all messages."""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'is_active', 'message_count',
            'messages', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.get_message_count()


class CreateChatSessionSerializer(serializers.Serializer):
    """Serializer for creating a new chat session."""
    title = serializers.CharField(max_length=255, required=False, default='New Chat')


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to AI."""
    message = serializers.CharField(min_length=1, max_length=10000)
    session_id = serializers.UUIDField(required=False, allow_null=True)


class UpdateSessionTitleSerializer(serializers.Serializer):
    """Serializer for updating session title."""
    title = serializers.CharField(max_length=255, min_length=1)
