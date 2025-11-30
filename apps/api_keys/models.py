import uuid
import secrets
from django.db import models
from apps.accounts.models import User


class APIKey(models.Model):
    """API Key model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, editable=False)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.key_name
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)  # 64 character hex string
        super().save(*args, **kwargs)
    
    @property
    def masked_key(self):
        """Return masked API key"""
        return f"{self.key[:8]}...{self.key[-4:]}"


class APIKeyLog(models.Model):
    """API Key usage logs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='logs')
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
