from django.urls import path
from .views import (
    DashboardView, CreateStaffAdminView, AdminListView,
    DisableAdminView, EnableAdminView, DeleteAdminView,
    UserListView, DisableUserView, EnableUserView, DeleteUserView
)

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Admin Management
    path('create-staff-admin/', CreateStaffAdminView.as_view(), name='create-staff-admin'),
    path('administrators/', AdminListView.as_view(), name='admin-list'),
    path('administrators/<uuid:admin_id>/disable/', DisableAdminView.as_view(), name='disable-admin'),
    path('administrators/<uuid:admin_id>/enable/', EnableAdminView.as_view(), name='enable-admin'),
    path('administrators/<uuid:admin_id>/delete/', DeleteAdminView.as_view(), name='delete-admin'),
    
    # User Management
    path('user-management/', UserListView.as_view(), name='user-list'),
    path('user-management/<uuid:user_id>/disable/', DisableUserView.as_view(), name='disable-user'),
    path('user-management/<uuid:user_id>/enable/', EnableUserView.as_view(), name='enable-user'),
    path('user-management/<uuid:user_id>/delete/', DeleteUserView.as_view(), name='delete-user'),
]
