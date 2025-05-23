from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Legal Services API",
        default_version='v1',
        description="API for managing legal stamps, orders, and advocates",
        terms_of_service="https://your-terms-url.com/",
        contact=openapi.Contact(email="contact@legal.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger/OpenAPI endpoints (ADD THESE FIRST)
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Existing URLs (keep these as-is)
    # path('djadmin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Development static/media config
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
