from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from core.admin import custom_admin
from core import views

urlpatterns = [
    path('admin/dashboard/', views.custom_dashboard, name='custom_dashboard'),

    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin/', custom_admin.urls),
    path('admin/custom-admin/', custom_admin.urls),
    path('', include('core.urls')), 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



