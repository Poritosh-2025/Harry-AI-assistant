"""
Views for user management.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.paginator import Paginator

from authentication.models import User, UserRole
from authentication.utils import api_response
from .serializers import UserListSerializer, ConfirmDeleteSerializer
from .permissions import IsStaffOrSuperAdmin


class UserListView(APIView):
    """List all regular users with pagination and search."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get(self, request):
        # Query params
        page = request.query_params.get('page', 1)
        page_size = min(int(request.query_params.get('page_size', 10)), 100)
        search = request.query_params.get('search', '')
        is_active = request.query_params.get('is_active')
        
        # Filter only regular users
        queryset = User.objects.filter(role=UserRole.USER)
        
        # Search
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile_number__icontains=search)
            )
        
        # Filter by active status
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Build user list with serial numbers
        users = []
        start_index = (page_obj.number - 1) * page_size
        for idx, user in enumerate(page_obj.object_list, start=start_index + 1):
            serializer = UserListSerializer(user, context={'sl_no': idx})
            users.append(serializer.data)
        
        # Admin info
        admin_info = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'profile_picture': request.build_absolute_uri(request.user.profile_picture.url) 
                if request.user.profile_picture else None
        }
        
        return api_response(
            True,
            'Users retrieved successfully',
            data={
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next(),
                    'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                    'next_page': page_obj.next_page_number() if page_obj.has_next() else None
                },
                'admin_info': admin_info,
                'users': users
            }
        )


class DisableUserView(APIView):
    """Disable user access."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role=UserRole.USER)
        except User.DoesNotExist:
            return api_response(
                False,
                'User not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        user.is_active = False
        user.save()
        
        return api_response(
            True,
            'User access disabled successfully',
            data={
                'user_id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'is_active': False
            }
        )


class EnableUserView(APIView):
    """Enable user access."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role=UserRole.USER)
        except User.DoesNotExist:
            return api_response(
                False,
                'User not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        user.is_active = True
        user.save()
        
        return api_response(
            True,
            'User access enabled successfully',
            data={
                'user_id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'is_active': True
            }
        )


class DeleteUserView(APIView):
    """Initiate user deletion."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role=UserRole.USER)
        except User.DoesNotExist:
            return api_response(
                False,
                'User not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return api_response(
            True,
            'User deletion initiated. Please confirm to proceed.',
            data={
                'user_id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'deletion_confirmation_required': True
            }
        )


class ConfirmDeleteUserView(APIView):
    """Confirm and delete user."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def post(self, request, user_id):
        serializer = ConfirmDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                'Invalid request',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if not serializer.validated_data['confirmation']:
            return api_response(
                False,
                'Deletion not confirmed',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id, role=UserRole.USER)
        except User.DoesNotExist:
            return api_response(
                False,
                'User not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        user.delete()
        
        return api_response(
            True,
            'User account deleted successfully',
            data={}
        )


class CancelDeleteUserView(APIView):
    """Cancel user deletion."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def post(self, request, user_id):
        try:
            User.objects.get(id=user_id, role=UserRole.USER)
        except User.DoesNotExist:
            return api_response(
                False,
                'User not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return api_response(
            True,
            'User deletion cancelled',
            data={'user_id': str(user_id)}
        )
