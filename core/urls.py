from django.urls import path
from . import views
from .views import view_inquiries
from django.contrib.auth.views import LoginView, LogoutView
from .admin import custom_dashboard, admin_orders, admin_statistics, admin_queue


urlpatterns = [
    path('', views.home, name='home'),
    
    # path to authentication
    
    path('logout/', views.logout_confirmation, name='logout'),
    path('logout/confirm/', views.custom_logout, name='logout_confirm'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    
    # path to user profile
    path('my-inquiries/', views.my_inquiries, name='my_inquiries'),
    path('submit-support/', views.submit_support_ticket, name='submit_support_ticket'),
    path('order/', views.order_ink, name='order_ink'), 
    path('apply/', views.apply_stamp, name='apply_stamp'),
    path('error/', views.error, name='error'),
    
    
    #--- path to both admin and user views
    path('admin/support/<int:user_id>/', views.staff_chat, name='staff_chat'),
    path('support/', views.user_chat, name='user_chat'),
    path('application_status/', views.application_status, name='application_status'),
    path('verify_stamp/<str:control_number>/', views.verify_stamp, name='verify_stamp'),
    
      # custom admin-like views
    path('admin/inquiries/', views.view_inquiries, name='view_inquiries'),
    path('admin/inquiries/<int:ticket_id>/reply/', views.reply_inquiry, name='reply_inquiry'),


    path('dashboard/statistics/', admin_statistics, name='admin_statistics'),
    path('dashboard/orders/', admin_orders, name='orders'),
    path('dashboard/queue/', admin_queue, name='admin_queue'),
    path('dashboard/', custom_dashboard, name='custom_dashboard'),
]
