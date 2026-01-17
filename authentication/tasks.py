"""
Celery tasks for authentication.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string


@shared_task
def send_otp_email(email, otp_code, otp_type):
    """Send OTP email to user."""
    if otp_type == 'REGISTRATION':
        subject = 'Email Verification OTP'
        message = f'Your email verification OTP is: {otp_code}. This OTP is valid for 10 minutes.'
    else:
        subject = 'Password Reset OTP'
        message = f'Your password reset OTP is: {otp_code}. This OTP is valid for 10 minutes.'
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def send_welcome_email(email, full_name):
    """Send welcome email after successful verification."""
    subject = 'Welcome to AI Chat Application'
    message = f'Hello {full_name},\n\nWelcome to AI Chat Application! Your account has been verified successfully.'
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def send_admin_credentials_email(email, password):
    """Send credentials to newly created staff admin."""
    subject = 'Your Staff Admin Account Credentials'
    message = f'''Hello,

Your staff admin account has been created.

Email: {email}
Password: {password}

Please login and update your profile.

Thank you.'''
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def cleanup_expired_otps():
    """Clean up expired OTPs."""
    from .models import OTP
    
    expired_count = OTP.objects.filter(expires_at__lt=timezone.now()).delete()[0]
    return f'Deleted {expired_count} expired OTPs'
