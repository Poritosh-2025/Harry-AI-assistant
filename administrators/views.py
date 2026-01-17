"""
Views for administrators.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.paginator import Paginator

from authentication.models import User, UserRole
from authentication.utils import api_response
from authentication.tasks import send_admin_credentials_email
from .serializers import AdminListSerializer, AdminDetailSerializer, CreateStaffAdminSerializer, UpdateAdminSerializer
from .permissions import IsSuperAdmin, IsStaffOrSuperAdmin


class AdminListView(APIView):
    """List all administrators with pagination and search."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get(self, request):
        # Query params
        page = request.query_params.get('page', 1)
        page_size = min(int(request.query_params.get('page_size', 10)), 100)
        search = request.query_params.get('search', '')
        role = request.query_params.get('role')
        is_active = request.query_params.get('is_active')
        
        # Filter administrators only
        queryset = User.objects.filter(role__in=[UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN])
        
        # Search
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile_number__icontains=search)
            )
        
        # Filter by role
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Build admin list with serial numbers
        administrators = []
        start_index = (page_obj.number - 1) * page_size
        for idx, admin in enumerate(page_obj.object_list, start=start_index + 1):
            serializer = AdminListSerializer(admin, context={'sl_no': idx})
            administrators.append(serializer.data)
        
        # Admin info
        admin_info = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'profile_picture': request.build_absolute_uri(request.user.profile_picture.url) 
                if request.user.profile_picture else None
        }
        
        return api_response(
            True,
            'Administrators retrieved successfully',
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
                'administrators': administrators
            }
        )


class CreateStaffAdminView(APIView):
    """Create a new Staff Admin."""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request):
        serializer = CreateStaffAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                'Failed to create staff admin',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Create staff admin
        admin = User.objects.create_user(
            email=email,
            password=password,
            role=UserRole.STAFF_ADMIN,
            is_verified=True  # Staff admins are auto-verified
        )
        
        # Send credentials email
        send_admin_credentials_email.delay(email, password)
        
        return api_response(
            True,
            'Staff Admin created successfully. Credentials have been sent to their email.',
            data={'admin': AdminDetailSerializer(admin).data},
            status_code=status.HTTP_201_CREATED
        )


class UpdateAdminView(APIView):
    """Update administrator profile."""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def patch(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role__in=[UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN])
        except User.DoesNotExist:
            return api_response(
                False,
                'Administrator not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: Super Admin can update any, Staff Admin only self
        if request.user.role != UserRole.SUPER_ADMIN and admin != request.user:
            return api_response(
                False,
                'You do not have permission to update this administrator',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Only Super Admin can change role
        if 'role' in request.data and request.user.role != UserRole.SUPER_ADMIN:
            return api_response(
                False,
                'Only Super Admin can change roles',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateAdminSerializer(admin, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response(
                False,
                'Failed to update administrator',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        admin = serializer.save()
        
        return api_response(
            True,
            'Administrator profile updated successfully',
            data={'admin': AdminDetailSerializer(admin).data}
        )


class DisableAdminView(APIView):
    """Disable administrator access."""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role__in=[UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN])
        except User.DoesNotExist:
            return api_response(
                False,
                'Administrator not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot disable yourself
        if admin == request.user:
            return api_response(
                False,
                'You cannot disable your own account',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        admin.is_active = False
        admin.save()
        
        return api_response(
            True,
            'Administrator access disabled successfully',
            data={
                'admin_id': str(admin.id),
                'full_name': admin.full_name,
                'email': admin.email,
                'is_active': False
            }
        )


class EnableAdminView(APIView):
    """Enable administrator access."""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role__in=[UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN])
        except User.DoesNotExist:
            return api_response(
                False,
                'Administrator not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        admin.is_active = True
        admin.save()
        
        return api_response(
            True,
            'Administrator access enabled successfully',
            data={
                'admin_id': str(admin.id),
                'full_name': admin.full_name,
                'email': admin.email,
                'is_active': True
            }
        )


class DeleteAdminView(APIView):
    """Delete administrator account."""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def delete(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role__in=[UserRole.STAFF_ADMIN, UserRole.SUPER_ADMIN])
        except User.DoesNotExist:
            return api_response(
                False,
                'Administrator not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot delete yourself
        if admin == request.user:
            return api_response(
                False,
                'You cannot delete your own account',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure at least one Super Admin exists
        if admin.role == UserRole.SUPER_ADMIN:
            super_admin_count = User.objects.filter(role=UserRole.SUPER_ADMIN, is_active=True).count()
            if super_admin_count <= 1:
                return api_response(
                    False,
                    'Cannot delete the last Super Admin',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        admin.delete()
        
        return api_response(
            True,
            'Administrator account deleted successfully',
            data={}
        )
