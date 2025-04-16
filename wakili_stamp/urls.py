from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from core.admin import custom_admin

urlpatterns = [
    path('admin/', custom_admin.urls),
    path('', include('core.urls')), 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


