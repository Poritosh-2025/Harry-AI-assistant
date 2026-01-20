"""
Serializers for authentication.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, OTP, UserRole, OTPType
from .utils import validate_password


class UserSerializer(serializers.ModelSerializer):
    """User serializer for responses."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'mobile_number', 'role', 
                  'profile_picture', 'is_verified', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    mobile_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    re_type_password = serializers.CharField(write_only=True)
    
    def validate_email(self, value):
        email = value.lower()
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user:
            # Only block if the user is verified
            if existing_user.is_verified:
                raise serializers.ValidationError("User with this email already exists.")
            # If user exists but is NOT verified, we'll handle it in the view
            # Store the existing user for later use in create()
            self._existing_unverified_user = existing_user
        
        return email
    
    def validate(self, data):
        if data['password'] != data['re_type_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        
        password_errors = validate_password(data['password'])
        if password_errors:
            raise serializers.ValidationError({'password': password_errors})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('re_type_password')
        
        # Check if there's an existing unverified user
        existing_user = getattr(self, '_existing_unverified_user', None)
        
        if existing_user:
            # Update the existing unverified user instead of creating a new one
            existing_user.full_name = validated_data['full_name']
            existing_user.mobile_number = validated_data.get('mobile_number', '')
            existing_user.set_password(validated_data['password'])
            existing_user.save()
            
            # Delete any old OTPs for this user
            OTP.objects.filter(user=existing_user).delete()
            
            return existing_user
        
        # Create new user if no existing unverified user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            mobile_number=validated_data.get('mobile_number', ''),
            role=UserRole.USER
        )
        return user


class SuperAdminRegisterSerializer(RegisterSerializer):
    """Serializer for super admin registration."""
    
    def create(self, validated_data):
        validated_data.pop('re_type_password')
        
        # Check if there's an existing unverified user
        existing_user = getattr(self, '_existing_unverified_user', None)
        
        if existing_user:
            # Update the existing unverified user to super admin
            existing_user.full_name = validated_data['full_name']
            existing_user.mobile_number = validated_data.get('mobile_number', '')
            existing_user.set_password(validated_data['password'])
            existing_user.role = UserRole.SUPER_ADMIN
            existing_user.save()
            
            # Delete any old OTPs for this user
            OTP.objects.filter(user=existing_user).delete()
            
            return existing_user
        
        # Create new super admin user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            mobile_number=validated_data.get('mobile_number', ''),
            role=UserRole.SUPER_ADMIN
        )
        return user


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    otp_type = serializers.ChoiceField(choices=OTPType.choices)
    
    def validate_email(self, value):
        return value.lower()


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP."""
    
    email = serializers.EmailField()
    otp_type = serializers.ChoiceField(choices=OTPType.choices)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})
        
        if not user.is_verified:
            raise serializers.ValidationError({
                'detail': 'Email not verified. Please verify your email before logging in.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Account is disabled.'})
        
        data['user'] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()


class VerifyResetOTPSerializer(serializers.Serializer):
    """Serializer for verifying reset OTP."""
    
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    
    def validate_email(self, value):
        return value.lower()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset."""
    
    email = serializers.EmailField()
    reset_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_email(self, value):
        return value.lower()
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        
        password_errors = validate_password(data['new_password'])
        if password_errors:
            raise serializers.ValidationError({'new_password': password_errors})
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    re_type_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['re_type_password']:
            raise serializers.ValidationError({'new_password': 'New passwords do not match.'})
        
        password_errors = validate_password(data['new_password'])
        if password_errors:
            raise serializers.ValidationError({'new_password': password_errors})
        
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for profile update."""
    
    class Meta:
        model = User
        fields = ['full_name', 'mobile_number', 'profile_picture']
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout."""
    
    refresh = serializers.CharField()


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh."""
    
    refresh = serializers.CharField()
