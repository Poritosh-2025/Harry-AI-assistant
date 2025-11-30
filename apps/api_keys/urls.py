from django.urls import path
from .views import APIKeyListView, APIKeyCreateView, APIKeyRevokeView, APIKeyLogsView

urlpatterns = [
    path('', APIKeyListView.as_view(), name='api-key-list'),
    path('create/', APIKeyCreateView.as_view(), name='api-key-create'),
    path('<uuid:api_key_id>/revoke/', APIKeyRevokeView.as_view(), name='api-key-revoke'),
    path('<uuid:api_key_id>/logs/', APIKeyLogsView.as_view(), name='api-key-logs'),
]
