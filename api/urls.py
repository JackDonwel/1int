from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

app_name = 'api'


router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'stamp-applications', views.StampApplicationViewSet, basename='stamp-application')
router.register(r'support-tickets', views.SupportTicketViewSet, basename='support-ticket')
router.register(r'inquiries', views.InquiryViewSet, basename='inquiry')
router.register(r'stamp-orders', views.StampOrderViewSet, basename='stamp-order')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'admin/settings', views.AdminSettingViewSet, basename='admin-setting')
router.register(r'profile', views.UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]