from rest_framework import serializers
from .models import APIKey, APIKeyLog


class APIKeyListSerializer(serializers.ModelSerializer):
    """API key list serializer"""
    
    api_key_id = serializers.UUIDField(source='id')
    api_key = serializers.CharField(source='masked_key')
    created_by = serializers.CharField(source='created_by.email')
    
    class Meta:
        model = APIKey
        fields = ['api_key_id', 'key_name', 'api_key', 'created_by', 
                  'created_at', 'last_used', 'usage_count', 'is_active']


class APIKeyCreateSerializer(serializers.Serializer):
    """Create API key serializer"""
    
    key_name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=['read', 'write']),
        default=['read']
    )


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """API key detail with full key (shown once on creation)"""
    
    api_key_id = serializers.UUIDField(source='id')
    api_key = serializers.CharField(source='key')
    
    class Meta:
        model = APIKey
        fields = ['api_key_id', 'key_name', 'api_key', 'created_at']


class APIKeyLogSerializer(serializers.ModelSerializer):
    """API key log serializer"""
    
    log_id = serializers.UUIDField(source='id')
    
    class Meta:
        model = APIKeyLog
        fields = ['log_id', 'endpoint', 'method', 'status_code', 'timestamp', 'ip_address']
