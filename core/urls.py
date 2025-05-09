from django.urls import path, include
from . import views
from .views import initiate_payment
from core.views import custom_login_view
#from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from .admin import admin_orders, admin_statistics, admin_queue


app_name = 'core'

urlpatterns = [
    # Public routes
    path('', views.home, name='home'),
    
    # Authentication
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', custom_login_view, name='login'),
    path('signup/', views.signup, name='signup'),

    # Order management
    path('orders/', views.order_list, name='order_list'),
    

    # Public order functionality
    path('order/', views.order_ink, name='order_ink'),
    path('apply/', views.apply_stamp, name='apply_stamp'),
    path('submit-support/', views.submit_support_ticket, name='submit_support_ticket'),

    # User-facing features
    path('error/', views.error, name='error'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('support/', views.user_chat, name='user_chat'),
    path('application_status/', views.application_status, name='application_status'),
    path('verify_stamp/<str:control_number>/', views.verify_stamp, name='verify_stamp'),
    
    # Data endpoints
    path('admin/chart-data/', views.stamp_chart_data, name='chart_data'),
    
    #payment
    path('payment/initiate/', initiate_payment, name='initiate_payment'),
    path('payment/complete/', views.payment_complete, name='payment_complete'),
]
