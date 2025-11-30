from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from .models import User, OTP, PasswordResetToken
from .serializers import (
    RegisterSerializer, SuperAdminRegisterSerializer, LoginSerializer,
    OTPVerifySerializer, ResendOTPSerializer, PasswordResetRequestSerializer,
    PasswordResetSerializer, ChangePasswordSerializer, UserSerializer, LogoutSerializer
)
from .tasks import send_otp_email


def api_response(status_type, message, data=None, errors=None):
    """Standard API response format"""
    response = {"status": status_type, "message": message}
    if data:
        response["data"] = data
    if errors:
        response["error"] = {"code": "VALIDATION_ERROR", "details": errors}
    return response


class RegisterSuperAdminView(APIView):
    """POST /api/auth/register-superadmin/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Check if super admin exists
        if User.objects.filter(role='super_admin').exists():
            return Response(
                api_response("error", "Super admin already exists"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SuperAdminRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate and send OTP
            otp = OTP.generate_otp(user, 'registration')
            send_otp_email.delay(user.email, otp.code, 'registration')
            
            return Response(
                api_response("success", "Super admin registered. Please verify your email with OTP.", {
                    "user_id": str(user.id),
                    "email": user.email
                }),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            api_response("error", "Validation failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate and send OTP
            otp = OTP.generate_otp(user, 'registration')
            send_otp_email.delay(user.email, otp.code, 'registration')
            
            return Response(
                api_response("success", "User registered. OTP sent to your email.", {
                    "user_id": str(user.id),
                    "email": user.email,
                    "otp_expires_at": otp.expires_at.isoformat()
                }),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            api_response("error", "Validation failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyOTPView(APIView):
    """POST /api/auth/verify-otp/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        otp_code = serializer.validated_data['otp_code']
        otp_type = serializer.validated_data['otp_type']
        
        try:
            otp = OTP.objects.get(
                code=otp_code,
                otp_type=otp_type,
                is_used=False
            )
        except OTP.DoesNotExist:
            return Response(
                api_response("error", "Invalid OTP code"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if otp.is_expired:
            return Response(
                api_response("error", "OTP has expired"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark OTP as used
        otp.is_used = True
        otp.save()
        
        user = otp.user
        
        if otp_type == 'registration':
            user.is_verified = True
            user.save()
            
            return Response(
                api_response("success", "Email verified successfully. You can now login.", {
                    "user_id": str(user.id),
                    "email": user.email,
                    "is_verified": True
                })
            )
        else:
            # Password reset - create reset token
            reset_token = PasswordResetToken.create_token(user)
            return Response(
                api_response("success", "OTP verified. You can now reset your password.", {
                    "reset_token": str(reset_token.token),
                    "email": user.email
                })
            )


class ResendOTPView(APIView):
    """POST /api/auth/resend-otp/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email'].lower()
        otp_type = serializer.validated_data['otp_type']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                api_response("error", "No account found with this email"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate and send new OTP
        otp = OTP.generate_otp(user, otp_type)
        send_otp_email.delay(user.email, otp.code, otp_type)
        
        return Response(
            api_response("success", "OTP resent successfully.", {
                "email": user.email,
                "otp_expires_at": otp.expires_at.isoformat()
            })
        )


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response(
            api_response("success", "Login successful.", {
                "user": {
                    "user_id": str(user.id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            })
        )


class LogoutView(APIView):
    """POST /api/auth/logout/"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh_token = serializer.validated_data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                api_response("success", "Logged out successfully.")
            )
        except Exception:
            return Response(
                api_response("error", "Invalid token"),
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset-request/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate and send OTP
        otp = OTP.generate_otp(user, 'password_reset')
        send_otp_email.delay(user.email, otp.code, 'password_reset')
        
        return Response(
            api_response("success", "Password reset OTP sent to your email.", {
                "email": user.email,
                "otp_expires_at": otp.expires_at.isoformat()
            })
        )


class VerifyResetOTPView(APIView):
    """POST /api/auth/verify-reset-otp/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        otp_code = request.data.get('otp_code')
        
        if not otp_code or len(otp_code) != 6:
            return Response(
                api_response("error", "Invalid OTP format"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            otp = OTP.objects.get(
                code=otp_code,
                otp_type='password_reset',
                is_used=False
            )
        except OTP.DoesNotExist:
            return Response(
                api_response("error", "Invalid OTP code"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if otp.is_expired:
            return Response(
                api_response("error", "OTP has expired"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        otp.is_used = True
        otp.save()
        
        # Create reset token
        reset_token = PasswordResetToken.create_token(otp.user)
        
        return Response(
            api_response("success", "OTP verified. You can now reset your password.", {
                "reset_token": str(reset_token.token),
                "email": otp.user.email
            })
        )


class PasswordResetView(APIView):
    """POST /api/auth/password-reset/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        try:
            token_obj = PasswordResetToken.objects.get(
                token=reset_token,
                is_used=False
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                api_response("error", "Invalid or expired reset token"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if token_obj.expires_at < timezone.now():
            return Response(
                api_response("error", "Reset token has expired"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        token_obj.is_used = True
        token_obj.save()
        
        return Response(
            api_response("success", "Password reset successfully. Please login with your new password.")
        )


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                api_response("error", "Validation failed", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                api_response("error", "Current password is incorrect"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            api_response("success", "Password changed successfully.")
        )


class TokenRefreshView(APIView):
    """POST /api/auth/token-refresh/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh = request.data.get('refresh')
        
        if not refresh:
            return Response(
                api_response("error", "Refresh token required"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh)
            return Response(
                api_response("success", "Token refreshed", {
                    "access": str(token.access_token)
                })
            )
        except Exception:
            return Response(
                api_response("error", "Invalid refresh token"),
                status=status.HTTP_400_BAD_REQUEST
            )
