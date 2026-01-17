"""
URL configuration for user management app.
"""
from django.urls import path
from .views import (
    UserListView, DisableUserView, EnableUserView,
    DeleteUserView, ConfirmDeleteUserView, CancelDeleteUserView
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:user_id>/disable/', DisableUserView.as_view(), name='disable-user'),
    path('users/<uuid:user_id>/enable/', EnableUserView.as_view(), name='enable-user'),
    path('users/<uuid:user_id>/', DeleteUserView.as_view(), name='delete-user'),
    path('users/<uuid:user_id>/confirm-delete/', ConfirmDeleteUserView.as_view(), name='confirm-delete-user'),
    path('users/<uuid:user_id>/cancel-delete/', CancelDeleteUserView.as_view(), name='cancel-delete-user'),
]
