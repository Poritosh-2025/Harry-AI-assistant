"""
Permissions for administrators.
"""
from rest_framework import permissions
from authentication.models import UserRole


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


class CanUpdateAdmin(permissions.BasePermission):
    """Check if user can update admin profile."""
    
    def has_object_permission(self, request, view, obj):
        # Super Admin can update any admin
        if request.user.role == UserRole.SUPER_ADMIN:
            return True
        # Staff Admin can only update their own profile
        return obj == request.user
