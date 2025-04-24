from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'support-tickets', views.SupportTicketViewSet, basename='support-ticket')
router.register(r'stamp-orders', views.StampOrderViewSet, basename='stamp-order')
router.register(r'inquiries', views.InquiryViewSet)
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'advocate-profiles', views.AdvocateProfileViewSet, basename='advocate-profile')
router.register(r'advocates', views.AdvocateViewSet, basename='advocate')
router.register(r'stamp-applications', views.StampApplicationViewSet, basename='stamp-application')
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'admin-settings', views.AdminSettingViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'user-profiles', views.UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    
    # Custom action endpoints for quick access
    path('api/v1/me/', views.UserViewSet.as_view({'get': 'me'}), name='me'),
    path('api/v1/my-profile/', views.UserProfileViewSet.as_view({'get': 'my_profile'}), name='my-profile'),
    path('api/v1/my-advocate-profile/', views.AdvocateViewSet.as_view({'get': 'my_advocate_profile'}), name='my-advocate-profile'),
    path('api/v1/my-advocate-profile/', views.AdvocateProfileViewSet.as_view({'get': 'my_profile'}), name='my-advocate-detail'),
    
    # Authentication URLs (assuming you're using Django REST framework's token authentication)
    path('api-auth/', include('rest_framework.urls')),
]

# Add the following to your project's urls.py file to include these URLs:
# path('', include('your_app_name.urls')),