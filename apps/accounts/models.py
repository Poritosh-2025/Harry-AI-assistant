import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model with roles"""
    
    ROLE_CHOICES = (
        ('user', 'User'),
        ('staff_admin', 'Staff Admin'),
        ('super_admin', 'Super Admin'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    def __str__(self):
        return self.email
    
    @property
    def is_admin(self):
        return self.role in ['staff_admin', 'super_admin']
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'


class OTP(models.Model):
    """OTP Model for email verification"""
    
    OTP_TYPE_CHOICES = (
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_otp(cls, user, otp_type):
        """Generate a 6-digit OTP"""
        # Delete old OTPs of same type
        cls.objects.filter(user=user, otp_type=otp_type).delete()
        
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timezone.timedelta(
            minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        )
        
        otp = cls.objects.create(
            user=user,
            code=code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        return otp


class PasswordResetToken(models.Model):
    """Token for password reset after OTP verification"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def create_token(cls, user):
        # Delete old tokens
        cls.objects.filter(user=user).delete()
        
        expires_at = timezone.now() + timezone.timedelta(minutes=30)
        return cls.objects.create(user=user, expires_at=expires_at)
