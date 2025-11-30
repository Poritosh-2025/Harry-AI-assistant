from django.urls import path
from .views import ProfileView, ProfileUpdateView

urlpatterns = [
    path('view/', ProfileView.as_view(), name='profile-view'),
    path('update/', ProfileUpdateView.as_view(), name='profile-update'),
]
