from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, OTP, PasswordResetToken


class RegisterSerializer(serializers.Serializer):
    """User registration serializer"""
    
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    mobile_number = serializers.CharField(max_length=20, required=False)
    password = serializers.CharField(min_length=8, write_only=True)
    re_type_password = serializers.CharField(write_only=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def validate(self, data):
        if data['password'] != data['re_type_password']:
            raise serializers.ValidationError({"re_type_password": "Passwords don't match"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('re_type_password')
        user = User.objects.create_user(**validated_data)
        return user


class SuperAdminRegisterSerializer(RegisterSerializer):
    """Super admin registration"""
    
    def create(self, validated_data):
        validated_data.pop('re_type_password')
        validated_data['role'] = 'super_admin'
        validated_data['is_staff'] = True
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        
        user = authenticate(email=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")
        
        if not user.is_verified:
            raise serializers.ValidationError("Please verify your email first")
        
        data['user'] = user
        return data


class OTPVerifySerializer(serializers.Serializer):
    """OTP verification serializer"""
    
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_type = serializers.ChoiceField(choices=['registration', 'password_reset'])


class ResendOTPSerializer(serializers.Serializer):
    """Resend OTP serializer"""
    
    email = serializers.EmailField()
    otp_type = serializers.ChoiceField(choices=['registration', 'password_reset'])


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("No account found with this email")
        return value.lower()


class PasswordResetSerializer(serializers.Serializer):
    """Password reset serializer"""
    
    reset_token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Change password for logged in user"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    re_type_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['re_type_password']:
            raise serializers.ValidationError({"re_type_password": "Passwords don't match"})
        return data


class UserSerializer(serializers.ModelSerializer):
    """User data serializer"""
    
    user_id = serializers.UUIDField(source='id', read_only=True)
    
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'mobile_number', 'role', 'profile_picture']


class LogoutSerializer(serializers.Serializer):
    """Logout serializer"""
    
    refresh_token = serializers.CharField()
