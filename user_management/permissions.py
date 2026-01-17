"""
Permissions for user management.
"""
from rest_framework import permissions
from authentication.models import UserRole


class IsStaffOrSuperAdmin(permissions.BasePermission):
    """Staff Admin or Super Admin can access."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in [UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN]
        )
