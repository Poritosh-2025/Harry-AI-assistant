"""
Serializers for administrators.
"""
from rest_framework import serializers
from authentication.models import User, UserRole
from authentication.utils import validate_password


class AdminListSerializer(serializers.ModelSerializer):
    """Serializer for admin list."""
    sl_no = serializers.SerializerMethodField()
    admin_name = serializers.CharField(source='full_name')
    
    class Meta:
        model = User
        fields = ['sl_no', 'id', 'admin_name', 'email', 'mobile_number', 'role', 'is_active', 'created_at']
    
    def get_sl_no(self, obj):
        return self.context.get('sl_no', 0)


class AdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin detail."""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'mobile_number', 'role', 'profile_picture', 'is_active']


class CreateStaffAdminSerializer(serializers.Serializer):
    """Serializer for creating staff admin."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[UserRole.STAFF_ADMIN])
    
    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value.lower()
    
    def validate_password(self, value):
        errors = validate_password(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class UpdateAdminSerializer(serializers.ModelSerializer):
    """Serializer for updating admin."""
    
    class Meta:
        model = User
        fields = ['full_name', 'mobile_number', 'profile_picture', 'role']
        extra_kwargs = {
            'full_name': {'required': False},
            'mobile_number': {'required': False},
            'profile_picture': {'required': False},
            'role': {'required': False}
        }
