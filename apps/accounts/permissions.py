from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Only super admins can access"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == 'super_admin'
        )


class IsAdmin(BasePermission):
    """Super admin or staff admin can access"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in ['super_admin', 'staff_admin']
        )


class IsVerified(BasePermission):
    """Only verified users can access"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_verified
        )
