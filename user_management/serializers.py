"""
Serializers for user management.
"""
from rest_framework import serializers
from authentication.models import User


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list."""
    sl_no = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['sl_no', 'id', 'full_name', 'email', 'mobile_number', 'is_active', 'created_at']
    
    def get_sl_no(self, obj):
        return self.context.get('sl_no', 0)


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user detail."""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'mobile_number', 'is_active', 'is_verified', 'created_at']


class ConfirmDeleteSerializer(serializers.Serializer):
    """Serializer for confirming user deletion."""
    confirmation = serializers.BooleanField()
