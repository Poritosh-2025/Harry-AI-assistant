"""
Custom permissions for authentication.
"""
from rest_framework import permissions
from .models import UserRole


class IsSuperAdmin(permissions.BasePermission):
    """Only Super Admin can access."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == UserRole.SUPER_ADMIN
        )


class IsStaffOrSuperAdmin(permissions.BasePermission):
    """Staff Admin or Super Admin can access."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in [UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN]
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """User can access own data, or admins can access any."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in [UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN]:
            return True
        return obj == request.user or getattr(obj, 'user', None) == request.user
