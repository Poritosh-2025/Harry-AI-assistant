from rest_framework import serializers
from apps.accounts.models import User


class ProfileViewSerializer(serializers.ModelSerializer):
    """Profile view serializer"""
    
    user_id = serializers.UUIDField(source='id', read_only=True)
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'mobile_number', 'role', 'profile_picture', 'options']
    
    def get_options(self, obj):
        return {
            "profile_edit": True,
            "change_password": True,
            "logout": True
        }


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Profile update serializer"""
    
    class Meta:
        model = User
        fields = ['full_name', 'mobile_number', 'profile_picture']
    
    def to_representation(self, instance):
        return ProfileViewSerializer(instance).data
