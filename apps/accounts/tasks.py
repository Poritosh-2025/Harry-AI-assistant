from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_otp_email(email, otp_code, otp_type):
    """Send OTP email asynchronously"""
    
    if otp_type == 'registration':
        subject = 'Verify Your Email - Registration OTP'
        message = f'Your verification OTP is: {otp_code}\n\nThis code expires in 10 minutes.'
    else:
        subject = 'Password Reset OTP'
        message = f'Your password reset OTP is: {otp_code}\n\nThis code expires in 10 minutes.'
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
    return True
