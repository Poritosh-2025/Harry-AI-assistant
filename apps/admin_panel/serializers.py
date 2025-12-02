from rest_framework import serializers
from apps.accounts.models import User


class CreateStaffAdminSerializer(serializers.Serializer):
    """Create staff admin serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=150)
    
    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            role='staff_admin',
            is_staff=True,
            is_verified=True  # Admin created users are auto-verified
        )
        return user


class AdminListSerializer(serializers.ModelSerializer):
    """Admin list serializer"""
    admin_id = serializers.UUIDField(source='id', read_only=True)
    admin_sl_no = serializers.SerializerMethodField()
    admin_name = serializers.CharField(source='full_name')
    admin_email = serializers.EmailField(source='email')
    admin_contact_number = serializers.CharField(source='mobile_number')
    has_access_to = serializers.CharField(source='role')
    actions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['admin_id', 'admin_sl_no', 'admin_name', 'admin_email', 'admin_contact_number', 
                  'has_access_to', 'is_active', 'actions']
    
    def get_admin_sl_no(self, obj):
        return self.context.get('index', 0) + 1
    
    def get_actions(self, obj):
        request_user = self.context.get('request').user
        is_super = request_user.role == 'super_admin'
        return {
            "disable": is_super and obj.is_active,
            "delete": is_super,
            "enable": is_super and not obj.is_active
        }


class UserListSerializer(serializers.ModelSerializer):
    """User list serializer"""
    
    user_id = serializers.UUIDField(source='id', read_only=True)
    user_sl_no = serializers.SerializerMethodField()
    user_full_name = serializers.CharField(source='full_name')
    user_email = serializers.EmailField(source='email')
    user_phone_number = serializers.CharField(source='mobile_number')
    actions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'user_sl_no', 'user_full_name', 'user_email', 'user_phone_number', 
                  'is_active', 'actions']
    
    def get_user_sl_no(self, obj):
        return self.context.get('index', 0) + 1
    
    def get_actions(self, obj):
        return {
            "disable": obj.is_active,
            "delete": True,
            "enable": not obj.is_active
        }


class CurrentUserSerializer(serializers.ModelSerializer):
    """Current user info for dashboard"""
    
    class Meta:
        model = User
        fields = ['full_name', 'profile_picture', 'role']
