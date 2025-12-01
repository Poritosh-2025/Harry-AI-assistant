from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Routes
    path('api/', include('apps.accounts.urls')),
    path('api/profile/', include('apps.profiles.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),
    path('api/admin/api-keys/', include('apps.api_keys.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
