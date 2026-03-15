from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'shop'

urlpatterns = [
    # Публичная часть
    path('', views.shop_index, name='index'),
    path('services/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('service/<int:service_id>/request/', views.service_request, name='service_request'),
    
    # Мои заказы
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Мои тикеты
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/create/', views.ticket_create, name='ticket_create'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # Админ-панель магазина - редирект с /admin/ на /admin/dashboard/
    path('admin/', lambda request: redirect('shop:admin_dashboard'), name='admin_index'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Управление тикетами (админ)
    path('admin/tickets/', views.admin_tickets_list, name='admin_tickets_list'),
    path('admin/ticket/<int:ticket_id>/', views.admin_ticket_manage, name='admin_ticket_manage'),
    
    # Управление заказами (админ)
    path('admin/orders/', views.admin_orders_list, name='admin_orders_list'),
    path('admin/order/<int:order_id>/process/', views.admin_order_process, name='admin_order_process'),
    
    # Управление услугами (админ)
    path('admin/services/', views.admin_services_list, name='admin_services_list'),
    path('admin/services/create/', views.admin_service_create, name='admin_service_create'),
    path('admin/services/<int:service_id>/edit/', views.admin_service_edit, name='admin_service_edit'),
    path('admin/services/<int:service_id>/toggle/', views.admin_service_toggle, name='admin_service_toggle'),
    
    # Управление категориями (админ)
    path('admin/categories/', views.admin_categories_list, name='admin_categories_list'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/<int:category_id>/edit/', views.admin_category_edit, name='admin_category_edit'),
    
    # Журналы и архивы (админ)
    path('admin/logs/', views.admin_logs, name='admin_logs'),
    path('admin/archives/', views.admin_ticket_archives, name='admin_ticket_archives'),
    path('admin/archives/<str:filename>/', views.admin_ticket_archive_view, name='admin_ticket_archive_view'),
]