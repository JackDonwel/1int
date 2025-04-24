
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from .admin import custom_dashboard, admin_orders, admin_statistics, admin_queue

urlpatterns = [
    path('', views.home, name='home'),

    # Authentication
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', views.logout_confirmation, name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', views.signup, name='signup'),

    # Order and Application
    path('order/', views.order_ink, name='order_ink'), 
    path('apply/', views.apply_stamp, name='apply_stamp'),
    path('error/', views.error, name='error'),
    path('admin/chart-data/', views.stamp_chart_data, name='chart_data'),
    
    # User & Admin Shared Views
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('admin/support/<int:user_id>/', views.staff_chat, name='staff_chat'),
    path('support/', views.user_chat, name='user_chat'),
    path('application_status/', views.application_status, name='application_status'),
    path('verify_stamp/<str:control_number>/', views.verify_stamp, name='verify_stamp'),

    # stamp application
    path('orders/new/', views.create_stamp_order, name='create_stamp_order'),
    path('orders/', views.order_list, name='order_list'),

    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    # Inquiries (Admin)
    
    path('inquiries/', views.inquiry_list, name='inquiry_list'),
    path('admin/inquiries/', views.view_inquiries, name='inquiries'),
    path('admin/inquiries/<int:ticket_id>/reply/', views.reply_inquiry, name='reply_inquiry'),

    # Admin Dashboard
   
    path('dashboard/statistics/', admin_statistics, name='admin_statistics'),
    path('dashboard/orders/', admin_orders, name='orders'),
    path('dashboard/queue/', admin_queue, name='admin_queue'),
    path('dashboard/', views.custom_dashboard, name='custom_dashboard'),
]
