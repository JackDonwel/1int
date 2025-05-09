# adminpanel/urls.py
from django.urls import path
from core import views

app_name = 'adminpanel'

urlpatterns = [
    path('dashboard/', views.custom_dashboard, name='custom_dashboard'),
    path('dashboard/statistics/', views.admin_statistics, name='admin_statistics'),
    path('dashboard/products/', views.admin_products, name='dashboard_products'),
    path('dashboard/stamps/', views.admin_stamps, name='dashboard_stamps'),
    path('dashboard/orders/', views.admin_orders, name='dashboard_orders'),
    path('dashboard/queue/', views.admin_queue, name='dashboard_queue'),

    path('stamp-orders/', views.order_list, name='stamp_orders'),
    path('stamp-orders/new/', views.create_stamp_order, name='new_stamp_order'),

    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),

    path('inquiries/', views.view_inquiries, name='inquiries_list'),
    path('inquiries/<int:ticket_id>/reply/', views.reply_inquiry, name='reply_inquiry'),

    path('settings/', views.admin_settings, name='admin_settings'),

    path('chart-data/', views.stamp_chart_data, name='chart_data'),
]
