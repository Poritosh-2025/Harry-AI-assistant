from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from apps.accounts.models import User
from apps.accounts.permissions import IsSuperAdmin, IsAdmin
from .serializers import (
    CreateStaffAdminSerializer, AdminListSerializer, 
    UserListSerializer, CurrentUserSerializer
)


def api_response(status_type, message, data=None, errors=None):
    """Standard API response"""
    response = {"status": status_type, "message": message}
    if data:
        response["data"] = data
    if errors:
        response["error"] = {"code": "VALIDATION_ERROR", "details": errors}
    return response


def get_pagination(queryset, request, page_size=20):
    """Simple pagination helper"""
    page = int(request.query_params.get('page', 1))
    size = int(request.query_params.get('page_size', page_size))
    
    total = queryset.count()
    total_pages = (total + size - 1) // size
    
    start = (page - 1) * size
    end = start + size
    
    return {
        'items': queryset[start:end],
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'total_count': total
        }
    }


# ========== Dashboard ==========

class DashboardView(APIView):
    """GET /api/admin/dashboard/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        today = timezone.now().date()
        
        total_users = User.objects.filter(role='user').count()
        today_users = User.objects.filter(
            role='user',
            created_at__date=today
        ).count()
        
        return Response(
            api_response("success", "Dashboard data", {
                "current_user": CurrentUserSerializer(request.user).data,
                "statistics": {
                    "total_chat_users": total_users,
                    "todays_chat_users": today_users
                }
            })
        )


# ========== Admin Management ==========

class CreateStaffAdminView(APIView):
    """POST /api/admin/create-staff-admin/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request):
        serializer = CreateStaffAdminSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.save()
            return Response(
                api_response("success", "Staff admin created successfully.", {
                    "admin_id": str(admin.id),
                    "email": admin.email,
                    "role": admin.role
                }),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            api_response("error", "Validation failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminListView(APIView):
    """GET /api/admin/administrators/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        admins = User.objects.filter(
            role__in=['super_admin', 'staff_admin']
        ).order_by('-created_at')
        
        paginated = get_pagination(admins, request)
        
        admin_data = []
        for i, admin in enumerate(paginated['items']):
            serializer = AdminListSerializer(admin, context={'request': request, 'index': i})
            admin_data.append(serializer.data)
        
        return Response(
            api_response("success", "Administrators retrieved", {
                "current_user": CurrentUserSerializer(request.user).data,
                "administrators": admin_data,
                "pagination": paginated['pagination']
            })
        )


class DisableAdminView(APIView):
    """POST /api/admin/administrators/{admin_id}/disable/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role='staff_admin')
        except User.DoesNotExist:
            return Response(
                api_response("error", "Administrator not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin.is_active = False
        admin.save()
        
        return Response(
            api_response("success", "Administrator access disabled successfully.")
        )


class EnableAdminView(APIView):
    """POST /api/admin/administrators/{admin_id}/enable/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role='staff_admin')
        except User.DoesNotExist:
            return Response(
                api_response("error", "Administrator not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin.is_active = True
        admin.save()
        
        return Response(
            api_response("success", "Administrator access enabled successfully.")
        )


class DeleteAdminView(APIView):
    """DELETE /api/admin/administrators/{admin_id}/delete/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def delete(self, request, admin_id):
        confirm = request.data.get('confirm_deletion', False)
        
        if not confirm:
            return Response(
                api_response("error", "Please confirm deletion"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            admin = User.objects.get(id=admin_id, role='staff_admin')
        except User.DoesNotExist:
            return Response(
                api_response("error", "Administrator not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin.delete()
        
        return Response(
            api_response("success", "Administrator account deleted successfully.")
        )


# ========== User Management ==========

class UserListView(APIView):
    """GET /api/admin/user-management/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        search = request.query_params.get('search', '')
        
        users = User.objects.filter(role='user').order_by('-created_at')
        
        if search:
            users = users.filter(
                Q(full_name__icontains=search) | Q(email__icontains=search)
            )
        
        paginated = get_pagination(users, request)
        
        user_data = []
        for i, user in enumerate(paginated['items']):
            serializer = UserListSerializer(user, context={'request': request, 'index': i})
            user_data.append(serializer.data)
        
        return Response(
            api_response("success", "Users retrieved", {
                "current_user": CurrentUserSerializer(request.user).data,
                "users": user_data,
                "pagination": paginated['pagination']
            })
        )


class DisableUserView(APIView):
    """POST /api/admin/user-management/{user_id}/disable/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role='user')
        except User.DoesNotExist:
            return Response(
                api_response("error", "User not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        user.is_active = False
        user.save()
        
        return Response(
            api_response("success", "User access disabled successfully.")
        )


class EnableUserView(APIView):
    """POST /api/admin/user-management/{user_id}/enable/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role='user')
        except User.DoesNotExist:
            return Response(
                api_response("error", "User not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        user.is_active = True
        user.save()
        
        return Response(
            api_response("success", "User access enabled successfully.")
        )


class DeleteUserView(APIView):
    """DELETE /api/admin/user-management/{user_id}/delete/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def delete(self, request, user_id):
        confirm = request.data.get('confirm_deletion', False)
        
        if not confirm:
            return Response(
                api_response("error", "Please confirm deletion"),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id, role='user')
        except User.DoesNotExist:
            return Response(
                api_response("error", "User not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        user.delete()
        
        return Response(
            api_response("success", "User account deleted successfully.")
        )
