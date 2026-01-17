"""
Admin configuration for chat app.
"""
from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['id', 'role', 'content', 'tokens_used', 'response_time_ms', 'is_error', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_active', 'get_message_count', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ChatMessageInline]
    
    def get_message_count(self, obj):
        return obj.get_message_count()
    get_message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'short_content', 'tokens_used', 'response_time_ms', 'is_error', 'created_at']
    list_filter = ['role', 'is_error', 'created_at']
    search_fields = ['session__user__email', 'content']
    readonly_fields = ['id', 'created_at']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
