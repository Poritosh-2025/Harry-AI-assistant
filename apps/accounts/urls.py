from django.urls import path
from .views import (
    RegisterSuperAdminView, RegisterView, VerifyOTPView, ResendOTPView,
    LoginView, LogoutView, PasswordResetRequestView, VerifyResetOTPView,
    PasswordResetView, ChangePasswordView, TokenRefreshView
)

urlpatterns = [
    # Registration
    path('register-superadmin/', RegisterSuperAdminView.as_view(), name='register-superadmin'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # OTP
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Login/Logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('verify-reset-otp/', VerifyResetOTPView.as_view(), name='verify-reset-otp'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Token
    path('token-refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
