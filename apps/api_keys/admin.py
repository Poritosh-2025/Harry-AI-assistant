from django.contrib import admin
from .models import APIKey, APIKeyLog


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['key_name', 'masked_key', 'created_by', 'is_active', 'usage_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['key_name', 'created_by__email']
    readonly_fields = ['key', 'usage_count', 'last_used']


@admin.register(APIKeyLog)
class APIKeyLogAdmin(admin.ModelAdmin):
    list_display = ['api_key', 'endpoint', 'method', 'status_code', 'ip_address', 'timestamp']
    list_filter = ['method', 'status_code']
    search_fields = ['api_key__key_name', 'endpoint']
    readonly_fields = ['api_key', 'endpoint', 'method', 'status_code', 'ip_address', 'timestamp']