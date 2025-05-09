from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    #path('djadmin/', admin.site.urls),  # Django's default admin
    path('api/', include('api.urls', namespace='api')),  # API URLs
     
    # Admin panel URLs
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),

    # Core/public URLs
    path('', include('core.urls', namespace='core')),

    # Django auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serving static/media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
