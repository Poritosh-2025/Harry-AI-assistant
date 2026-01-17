"""
Chat models for AI conversation management.
"""
import uuid
from django.db import models
from django.conf import settings


class MessageRole(models.TextChoices):
    USER = 'user', 'User'
    ASSISTANT = 'assistant', 'Assistant'
    SYSTEM = 'system', 'System'


class ChatSession(models.Model):
    """
    Chat session model - groups conversations like ChatGPT sessions.
    Each session contains multiple messages and maintains conversation context.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions_v2'
    )
    title = models.CharField(max_length=255, blank=True, default='New Chat')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_sessions_v2'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def get_message_count(self):
        """Get total message count in this session."""
        return self.messages.count()
    
    def get_conversation_history(self):
        """
        Get full conversation history for AI context.
        Returns list of dicts with role and content.
        """
        messages = self.messages.order_by('created_at')
        return [
            {
                'role': msg.role,
                'content': msg.content
            }
            for msg in messages
        ]
    
    def generate_title_from_first_message(self):
        """Auto-generate title from first user message."""
        first_message = self.messages.filter(role=MessageRole.USER).first()
        if first_message:
            # Truncate to 50 chars for title
            content = first_message.content[:50]
            if len(first_message.content) > 50:
                content += '...'
            self.title = content
            self.save(update_fields=['title'])


class ChatMessage(models.Model):
    """
    Individual chat message within a session.
    Stores both user messages and AI assistant responses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        default=MessageRole.USER
    )
    content = models.TextField()
    
    # Optional metadata for AI responses
    tokens_used = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Error handling
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
