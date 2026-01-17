"""
Views for authentication.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from datetime import timedelta

from .models import User, OTP, OTPType
from .serializers import (
    UserSerializer, RegisterSerializer, SuperAdminRegisterSerializer,
    OTPVerifySerializer, ResendOTPSerializer, LoginSerializer,
    PasswordResetRequestSerializer, VerifyResetOTPSerializer,
    PasswordResetSerializer, ChangePasswordSerializer, ProfileUpdateSerializer,
    LogoutSerializer, TokenRefreshSerializer
)
from .utils import api_response, generate_otp, generate_reset_token


def send_email_task(task_func, *args):
    """Send email task - handles both Celery and non-Celery environments."""
    try:
        task_func.delay(*args)
    except Exception:
        # If Celery/Redis not available, run synchronously or skip in dev
        from django.conf import settings
        if settings.DEBUG:
            print(f"[DEBUG] Email task called with args: {args}")
        else:
            task_func(*args)


class RegisterSuperAdminView(APIView):
    """Register Super Admin."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .tasks import send_otp_email
        
        # Check if super admin already exists
        if User.objects.filter(role='SUPER_ADMIN').exists():
            return api_response(
                False, 'Super Admin already exists',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SuperAdminRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'registration failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        # Generate and send OTP
        otp_code = generate_otp()
        OTP.objects.create(user=user, otp_code=otp_code, otp_type=OTPType.registration)
        send_email_task(send_otp_email, user.email, otp_code, OTPType.registration)
        
        return api_response(
            True,
            'Super Admin registered successfully. Please verify your email with the OTP sent.',
            data={'user': UserSerializer(user).data},
            status_code=status.HTTP_201_CREATED
        )


class RegisterView(APIView):
    """Register User."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .tasks import send_otp_email
        
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'registration failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        # Generate and send OTP
        otp_code = generate_otp()
        OTP.objects.create(user=user, otp_code=otp_code, otp_type=OTPType.registration)
        send_email_task(send_otp_email, user.email, otp_code, OTPType.registration)
        
        return api_response(
            True,
            'User registered successfully. Please check your email for OTP verification.',
            data={'user': UserSerializer(user).data},
            status_code=status.HTTP_201_CREATED
        )


class ResendOTPView(APIView):
    """Resend OTP."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .tasks import send_otp_email
        
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Cannot resend OTP',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp_type = serializer.validated_data['otp_type']
        
        user = User.objects.get(email=email)
        
        # Invalidate old OTPs
        OTP.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp_code = generate_otp()
        OTP.objects.create(user=user, otp_code=otp_code, otp_type=otp_type)
        send_email_task(send_otp_email, email, otp_code, otp_type)
        
        return api_response(
            True,
            'OTP has been resent to your email.',
            data={'email': email, 'otp_type': otp_type}
        )


class VerifyOTPView(APIView):
    """Verify OTP."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .tasks import send_welcome_email
        
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'OTP verification failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        otp_type = serializer.validated_data['otp_type']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return api_response(
                False, 'OTP verification failed',
                errors={'email': ['User not found.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        otp = OTP.objects.filter(
            user=user, otp_code=otp_code, otp_type=otp_type, is_used=False
        ).first()
        
        if not otp or not otp.is_valid():
            return api_response(
                False, 'OTP verification failed',
                errors={'otp_code': ['Invalid or expired OTP code.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        otp.is_used = True
        otp.save()
        
        if otp_type == OTPType.registration:
            user.is_verified = True
            user.save()
            send_email_task(send_welcome_email, user.email, user.full_name)
            return api_response(
                True,
                'Email verified successfully. You can now login.',
                data={'email': email, 'is_verified': True}
            )
        
        return api_response(
            True,
            'OTP verified successfully.',
            data={'email': email}
        )


class LoginView(APIView):
    """User Login."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            # Check for unverified email
            errors = serializer.errors
            if 'detail' in errors and 'not verified' in str(errors['detail']):
                return api_response(
                    False,
                    'Email not verified. Please verify your email before logging in.',
                    errors={'detail': ['Account not verified.']},
                    status_code=status.HTTP_403_FORBIDDEN
                )
            return api_response(
                False, 'Authentication failed',
                errors=serializer.errors,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return api_response(
            True,
            'Login successful',
            data={
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }
        )


class LogoutView(APIView):
    """User Logout."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Logout failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh_token = RefreshToken(serializer.validated_data['refresh'])
            refresh_token.blacklist()
        except TokenError:
            return api_response(
                False, 'Invalid token',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return api_response(True, 'Logout successful', data={})


class PasswordResetRequestView(APIView):
    """Request Password Reset."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .tasks import send_otp_email
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Password reset request failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate and send OTP
        otp_code = generate_otp()
        OTP.objects.create(user=user, otp_code=otp_code, otp_type=OTPType.password_reset)
        send_email_task(send_otp_email, email, otp_code, OTPType.password_reset)
        
        return api_response(
            True,
            'Password reset OTP has been sent to your email.',
            data={'email': email}
        )


class VerifyResetOTPView(APIView):
    """Verify Reset OTP."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'OTP verification failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return api_response(
                False, 'OTP verification failed',
                errors={'email': ['User not found.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        otp = OTP.objects.filter(
            user=user, otp_code=otp_code, otp_type=OTPType.password_reset, is_used=False
        ).first()
        
        if not otp or not otp.is_valid():
            return api_response(
                False, 'OTP verification failed',
                errors={'otp_code': ['Invalid or expired OTP code.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        otp.is_used = True
        otp.save()
        
        # Generate reset token
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = timezone.now() + timedelta(minutes=15)
        user.save()
        
        return api_response(
            True,
            'OTP verified successfully. You can now reset your password.',
            data={'email': email, 'reset_token': reset_token}
        )


class PasswordResetView(APIView):
    """Reset Password."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Password reset failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return api_response(
                False, 'Password reset failed',
                errors={'email': ['User not found.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if (user.reset_token != reset_token or 
            not user.reset_token_expires or 
            timezone.now() > user.reset_token_expires):
            return api_response(
                False, 'Password reset failed',
                errors={'reset_token': ['Invalid or expired reset token.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.save()
        
        return api_response(
            True,
            'Password has been reset successfully. Please login with your new password.',
            data={}
        )


class ChangePasswordView(APIView):
    """Change Password."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Password change failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(serializer.validated_data['old_password']):
            return api_response(
                False, 'Password change failed',
                errors={'old_password': ['Current password is incorrect.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return api_response(True, 'Password changed successfully.', data={})


class TokenRefreshView(APIView):
    """Refresh Access Token."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False, 'Token refresh failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            return api_response(
                True,
                'Token refreshed successfully',
                data={'access': str(refresh.access_token)}
            )
        except TokenError:
            return api_response(
                False, 'Invalid or expired refresh token',
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class ProfileView(APIView):
    """View and Update Profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return api_response(
            True,
            'Profile retrieved successfully',
            data={'user': UserSerializer(request.user).data}
        )
    
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response(
                False, 'Profile update failed',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        return api_response(
            True,
            'Profile updated successfully',
            data={'user': UserSerializer(user).data}
        )
