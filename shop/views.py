from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.conf import settings
import os
import json

from .models import (
    ServiceCategory, Service, ServiceOrder, ServiceLog,
    Ticket, TicketMessage, TicketLog
)


def is_admin_or_moderator(user):
    """Проверка прав администратора/модератора"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ============================================================
# Публичная часть магазина
# ============================================================

@login_required
def shop_index(request):
    """Главная страница магазина"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        'services'
    ).annotate(
        active_services_count=Count('services', filter=Q(services__is_active=True))
    )
    
    featured_services = Service.objects.filter(
        is_active=True, is_featured=True
    ).select_related('category')[:6]
    
    # Последние заказы и тикеты пользователя
    user_orders = ServiceOrder.objects.filter(
        user=request.user
    ).select_related('service')[:5]
    
    user_tickets = Ticket.objects.filter(
        user=request.user
    ).select_related('assigned_to')[:5]
    
    context = {
        'categories': categories,
        'featured_services': featured_services,
        'user_orders': user_orders,
        'user_tickets': user_tickets,
    }
    return render(request, 'shop/index.html', context)


@login_required
def service_list(request):
    """Список услуг"""
    services = Service.objects.filter(is_active=True).select_related('category')
    
    # Фильтр по категории
    category_slug = request.GET.get('category')
    if category_slug:
        services = services.filter(category__slug=category_slug)
    
    # Фильтр по типу обработки
    processing_type = request.GET.get('type')
    if processing_type:
        services = services.filter(processing_type=processing_type)
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'services': services,
        'categories': categories,
        'current_category': category_slug,
        'current_type': processing_type,
    }
    return render(request, 'shop/service_list.html', context)


@login_required
def service_detail(request, service_id):
    """Детальная страница услуги"""
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    can_use, message = service.can_user_use(request.user)
    
    # История использования
    user_orders = ServiceOrder.objects.filter(
        user=request.user, service=service
    ).order_by('-created_at')[:5]
    
    context = {
        'service': service,
        'can_use': can_use,
        'use_message': message,
        'user_orders': user_orders,
    }
    return render(request, 'shop/service_detail.html', context)


@login_required
def service_request(request, service_id):
    """Запрос услуги"""
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    can_use, message = service.can_user_use(request.user)
    if not can_use:
        messages.error(request, f'Невозможно запросить услугу: {message}')
        return redirect('shop:service_detail', service_id=service.id)
    
    if request.method == 'POST':
        order_data = {}
        additional_info = request.POST.get('additional_info', '').strip()
        
        # Специфичные данные для разных услуг
        if service.auto_action == 'change_nickname':
            new_nickname = request.POST.get('new_nickname', '').strip()
            if not new_nickname:
                messages.error(request, 'Укажите новый никнейм')
                return redirect('shop:service_request', service_id=service.id)
            if len(new_nickname) < 3:
                messages.error(request, 'Никнейм должен быть не менее 3 символов')
                return redirect('shop:service_request', service_id=service.id)
            order_data['new_nickname'] = new_nickname
        
        if additional_info:
            order_data['additional_info'] = additional_info
        
        # Создаем заказ
        order = ServiceOrder.objects.create(
            user=request.user,
            service=service,
            status='pending',
            order_data=order_data
        )
        
        # Логируем создание заказа
        ServiceLog.objects.create(
            order=order,
            action='create',
            description=f'Создан заказ на услугу "{service.name}"',
            performed_by=request.user
        )
        
        # Автоматическая обработка
        if service.processing_type == 'auto':
            success, result_message = order.process_auto_action()
            if success:
                messages.success(request, f'✅ {result_message}')
                return redirect('shop:my_orders')
            else:
                messages.error(request, f'❌ {result_message}')
                return redirect('shop:order_detail', order_id=order.id)
        
        # Ручная обработка - создаем тикет
        else:
            ticket = Ticket.objects.create(
                user=request.user,
                category='purchase',
                title=f'{service.name}',
                description=f'Заказ услуги: {service.name}\n\n{additional_info}' if additional_info else f'Заказ услуги: {service.name}',
                order=order,
                priority='medium'
            )
            
            TicketLog.objects.create(
                ticket=ticket,
                action='create',
                description=f'Тикет создан для заказа #{order.id}',
                performed_by=request.user
            )
            
            ServiceLog.objects.create(
                order=order,
                action='ticket_created',
                description=f'Создан тикет #{ticket.id}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ Заказ #{order.id} создан. Тикет #{ticket.id} передан администраторам.')
            return redirect('shop:ticket_detail', ticket_id=ticket.id)
    
    context = {
        'service': service,
    }
    return render(request, 'shop/service_request.html', context)


# ============================================================
# Заказы пользователя
# ============================================================

@login_required
def my_orders(request):
    """Мои заказы"""
    orders = ServiceOrder.objects.filter(
        user=request.user
    ).select_related('service', 'service__category', 'processed_by')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
    }
    return render(request, 'shop/my_orders.html', context)


@login_required
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(ServiceOrder, id=order_id)
    
    # Проверка доступа
    if order.user != request.user and not is_admin_or_moderator(request.user):
        messages.error(request, 'У вас нет доступа к этому заказу')
        return redirect('shop:my_orders')
    
    logs = order.logs.select_related('performed_by')
    
    # Связанный тикет
    ticket = getattr(order, 'ticket', None)
    
    context = {
        'order': order,
        'logs': logs,
        'ticket': ticket,
    }
    return render(request, 'shop/order_detail.html', context)


# ============================================================
# Тикеты пользователя
# ============================================================

@login_required
def my_tickets(request):
    """Мои тикеты"""
    all_tickets = Ticket.objects.filter(user=request.user)
    
    # Статистика
    stats = {
        'total': all_tickets.count(),
        'new': all_tickets.filter(status='new').count(),
        'in_progress': all_tickets.filter(status='in_progress').count(),
        'resolved': all_tickets.filter(status='resolved').count(),
        'rejected': all_tickets.filter(status='rejected').count(),
    }
    
    tickets = all_tickets.select_related('assigned_to', 'order')
    
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if category_filter:
        tickets = tickets.filter(category=category_filter)
    
    paginator = Paginator(tickets, 20)
    page = request.GET.get('page')
    tickets = paginator.get_page(page)
    
    context = {
        'tickets': tickets,
        'stats': stats,
        'current_status': status_filter,
        'current_category': category_filter,
    }
    return render(request, 'shop/my_tickets.html', context)


@login_required
def ticket_create(request):
    """Создание тикета"""
    if request.method == 'POST':
        category = request.POST.get('category')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        
        if category not in ['request', 'complaint']:
            messages.error(request, 'Недопустимая категория')
            return redirect('shop:ticket_create')
        
        if not subject or not description:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('shop:ticket_create')
        
        if priority not in ['low', 'medium', 'high']:
            priority = 'medium'
        
        ticket = Ticket.objects.create(
            user=request.user,
            category=category,
            title=subject,
            description=description,
            priority=priority
        )
        
        TicketLog.objects.create(
            ticket=ticket,
            action='create',
            description=f'Тикет создан пользователем. Категория: {ticket.get_category_display()}',
            performed_by=request.user
        )
        
        messages.success(request, f'✅ Тикет #{ticket.id} успешно создан')
        return redirect('shop:ticket_detail', ticket_id=ticket.id)
    
    return render(request, 'shop/ticket_create.html')


@login_required
def ticket_detail(request, ticket_id):
    """Детали тикета"""
    ticket = get_object_or_404(Ticket.objects.select_related('user', 'assigned_to', 'order'), id=ticket_id)
    
    # Проверка доступа
    if ticket.user != request.user and not is_admin_or_moderator(request.user):
        messages.error(request, 'У вас нет доступа к этому тикету')
        return redirect('shop:my_tickets')
    
    # Добавление сообщения
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'message':
            message_text = request.POST.get('message', '').strip()
            if message_text:
                TicketMessage.objects.create(
                    ticket=ticket,
                    user=request.user,
                    message=message_text,
                    is_admin=is_admin_or_moderator(request.user)
                )
                
                TicketLog.objects.create(
                    ticket=ticket,
                    action='message',
                    description=f'Новое сообщение от {request.user.username}',
                    performed_by=request.user
                )
                
                messages.success(request, 'Сообщение отправлено')
        
        elif action == 'close' and ticket.user == request.user:
            if ticket.status not in ['resolved', 'rejected']:
                ticket.close_by_user()
                messages.success(request, 'Тикет закрыт')
        
        return redirect('shop:ticket_detail', ticket_id=ticket.id)
    
    ticket_messages = ticket.messages.select_related('user')
    logs = ticket.logs.select_related('performed_by')
    
    context = {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
        'logs': logs,
        'can_close': ticket.user == request.user and ticket.status not in ['resolved', 'rejected'],
    }
    return render(request, 'shop/ticket_detail.html', context)


# ============================================================
# Админ-панель магазина
# ============================================================

@login_required
@user_passes_test(is_admin_or_moderator)
def admin_dashboard(request):
    """Дашборд администратора"""
    stats = {
        'new_tickets': Ticket.objects.filter(status='new').count(),
        'in_progress_tickets': Ticket.objects.filter(status='in_progress').count(),
        'pending_orders': ServiceOrder.objects.filter(status='pending').count(),
        'resolved_today': Ticket.objects.filter(
            status='resolved',
            resolved_at__date=timezone.now().date()
        ).count(),
    }
    
    recent_tickets = Ticket.objects.filter(
        status__in=['new', 'in_progress']
    ).select_related('user', 'assigned_to')[:10]
    
    pending_orders = ServiceOrder.objects.filter(
        status='pending'
    ).select_related('user', 'service')[:10]
    
    context = {
        'stats': stats,
        'recent_tickets': recent_tickets,
        'pending_orders': pending_orders,
    }
    return render(request, 'shop/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_tickets_list(request):
    """Список тикетов (админ)"""
    show_deleted = request.GET.get('show_deleted') == '1'
    
    if show_deleted:
        tickets = Ticket.all_objects.all()
    else:
        tickets = Ticket.objects.all()
    
    tickets = tickets.select_related('user', 'assigned_to', 'order')
    
    # Фильтры
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('search', '').strip()
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if category_filter:
        tickets = tickets.filter(category=category_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search:
        tickets = tickets.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(id__icontains=search)
        )
    
    paginator = Paginator(tickets, 30)
    page = request.GET.get('page')
    tickets = paginator.get_page(page)
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'priority_filter': priority_filter,
        'search': search,
        'show_deleted': show_deleted,
    }
    return render(request, 'shop/admin/tickets_list.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_ticket_manage(request, ticket_id):
    """Управление тикетом (админ)"""
    ticket = get_object_or_404(Ticket.all_objects.select_related('user', 'assigned_to', 'order'), id=ticket_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assign':
            old_assigned = ticket.assigned_to.username if ticket.assigned_to else 'Никто'
            ticket.assigned_to = request.user
            ticket.status = 'in_progress'
            ticket.save()
            
            TicketLog.objects.create(
                ticket=ticket,
                action='assign',
                description=f'Тикет назначен на {request.user.username}',
                old_value=old_assigned,
                new_value=request.user.username,
                performed_by=request.user
            )
            messages.success(request, 'Тикет назначен на вас')
        
        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                old_status = ticket.status
                ticket.status = new_status
                if new_status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save()
                
                TicketLog.objects.create(
                    ticket=ticket,
                    action='status_change',
                    description=f'Статус изменён администратором',
                    old_value=old_status,
                    new_value=new_status,
                    performed_by=request.user
                )
                messages.success(request, 'Статус изменён')
        
        elif action == 'change_priority':
            new_priority = request.POST.get('new_priority')
            if new_priority in dict(Ticket.PRIORITY_CHOICES):
                old_priority = ticket.priority
                ticket.priority = new_priority
                ticket.save()
                
                TicketLog.objects.create(
                    ticket=ticket,
                    action='priority_change',
                    description='Приоритет изменён',
                    old_value=old_priority,
                    new_value=new_priority,
                    performed_by=request.user
                )
                messages.success(request, 'Приоритет изменён')
        
        elif action == 'resolve':
            notes = request.POST.get('notes', '')
            ticket.resolve(request.user, notes)
            messages.success(request, 'Тикет решён')
        
        elif action == 'reject':
            notes = request.POST.get('notes', '')
            old_status = ticket.status
            ticket.status = 'rejected'
            ticket.save()
            
            TicketLog.objects.create(
                ticket=ticket,
                action='status_change',
                description=f'Тикет отклонён. {notes}',
                old_value=old_status,
                new_value='rejected',
                performed_by=request.user
            )
            
            # Если есть связанный заказ - отклоняем его тоже
            if ticket.order:
                ticket.order.status = 'rejected'
                ticket.order.admin_notes = notes
                ticket.order.processed_by = request.user
                ticket.order.save()
            
            messages.warning(request, 'Тикет отклонён')
        
        elif action == 'delete':
            if not ticket.is_deleted:
                archive_filename = ticket.soft_delete(request.user)
                messages.success(request, f'Тикет удалён и сохранён в архив: {archive_filename}')
                return redirect('shop:admin_tickets_list')
        
        elif action == 'message':
            message_text = request.POST.get('message', '').strip()
            if message_text:
                TicketMessage.objects.create(
                    ticket=ticket,
                    user=request.user,
                    message=message_text,
                    is_admin=True
                )
                
                TicketLog.objects.create(
                    ticket=ticket,
                    action='message',
                    description=f'Сообщение от администратора {request.user.username}',
                    performed_by=request.user
                )
                messages.success(request, 'Сообщение отправлено')
        
        return redirect('shop:admin_ticket_manage', ticket_id=ticket.id)
    
    ticket_messages = ticket.messages.select_related('user')
    logs = ticket.logs.select_related('performed_by')
    
    context = {
        'ticket': ticket,
        'ticket_messages': ticket_messages,
        'logs': logs,
    }
    return render(request, 'shop/admin/ticket_manage.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_orders_list(request):
    """Список заказов (админ)"""
    orders = ServiceOrder.objects.all().select_related(
        'user', 'service', 'service__category', 'processed_by'
    )
    
    status_filter = request.GET.get('status')
    service_filter = request.GET.get('service')
    search = request.GET.get('search', '').strip()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    if service_filter:
        orders = orders.filter(service_id=service_filter)
    if search:
        orders = orders.filter(
            Q(user__username__icontains=search) |
            Q(id__icontains=search)
        )
    
    paginator = Paginator(orders, 30)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    services = Service.objects.all()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'search': search,
        'services': services,
    }
    return render(request, 'shop/admin/orders_list.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_order_process(request, order_id):
    """Обработка заказа (админ)"""
    order = get_object_or_404(ServiceOrder.objects.select_related('user', 'service'), id=order_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'complete':
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.processed_by = request.user
            order.admin_notes = notes
            order.save()
            
            ServiceLog.objects.create(
                order=order,
                action='admin_complete',
                description=f'Заказ выполнен. {notes}',
                performed_by=request.user
            )
            
            # Если есть связанный тикет
            if hasattr(order, 'ticket'):
                order.ticket.status = 'resolved'
                order.ticket.resolved_at = timezone.now()
                order.ticket.save()
            
            messages.success(request, f'Заказ #{order.id} выполнен')
        
        elif action == 'reject':
            order.status = 'rejected'
            order.processed_by = request.user
            order.admin_notes = notes
            order.save()
            
            ServiceLog.objects.create(
                order=order,
                action='admin_reject',
                description=f'Заказ отклонён. {notes}',
                performed_by=request.user
            )
            
            if hasattr(order, 'ticket'):
                order.ticket.status = 'rejected'
                order.ticket.save()
            
            messages.warning(request, f'Заказ #{order.id} отклонён')
        
        elif action == 'cancel':
            order.status = 'cancelled'
            order.admin_notes = notes
            order.save()
            
            ServiceLog.objects.create(
                order=order,
                action='admin_cancel',
                description=f'Заказ отменён. {notes}',
                performed_by=request.user
            )
            
            messages.info(request, f'Заказ #{order.id} отменён')
        
        return redirect('shop:admin_orders_list')
    
    logs = order.logs.select_related('performed_by')
    ticket = getattr(order, 'ticket', None)
    
    context = {
        'order': order,
        'logs': logs,
        'ticket': ticket,
    }
    return render(request, 'shop/admin/order_process.html', context)


# ============================================================
# Управление услугами (админ)
# ============================================================

@login_required
@user_passes_test(is_admin_or_moderator)
def admin_services_list(request):
    """Список услуг (админ)"""
    services = Service.objects.all().select_related('category').annotate(
        orders_count=Count('orders')
    )
    
    context = {
        'services': services,
    }
    return render(request, 'shop/admin/services_list.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_service_create(request):
    """Создание услуги"""
    if request.method == 'POST':
        try:
            service = Service.objects.create(
                category_id=request.POST.get('category'),
                name=request.POST.get('name'),
                slug=request.POST.get('slug'),
                description=request.POST.get('description'),
                processing_type=request.POST.get('processing_type'),
                auto_action=request.POST.get('auto_action', ''),
                is_active=request.POST.get('is_active') == 'on',
                is_featured=request.POST.get('is_featured') == 'on',
                order=int(request.POST.get('order', 0)),
                max_uses_per_user=int(request.POST.get('max_uses_per_user')) if request.POST.get('max_uses_per_user') else None,
                cooldown_days=int(request.POST.get('cooldown_days')) if request.POST.get('cooldown_days') else None,
            )
            messages.success(request, f'Услуга "{service.name}" создана')
            return redirect('shop:admin_services_list')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'auto_actions': Service.AUTO_ACTIONS,
    }
    return render(request, 'shop/admin/service_form.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_service_edit(request, service_id):
    """Редактирование услуги"""
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        try:
            service.category_id = request.POST.get('category')
            service.name = request.POST.get('name')
            service.slug = request.POST.get('slug')
            service.description = request.POST.get('description')
            service.processing_type = request.POST.get('processing_type')
            service.auto_action = request.POST.get('auto_action', '')
            service.is_active = request.POST.get('is_active') == 'on'
            service.is_featured = request.POST.get('is_featured') == 'on'
            service.order = int(request.POST.get('order', 0))
            service.max_uses_per_user = int(request.POST.get('max_uses_per_user')) if request.POST.get('max_uses_per_user') else None
            service.cooldown_days = int(request.POST.get('cooldown_days')) if request.POST.get('cooldown_days') else None
            service.save()
            
            messages.success(request, 'Услуга обновлена')
            return redirect('shop:admin_services_list')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'service': service,
        'categories': categories,
        'auto_actions': Service.AUTO_ACTIONS,
    }
    return render(request, 'shop/admin/service_form.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_service_toggle(request, service_id):
    """Переключение активности услуги"""
    service = get_object_or_404(Service, id=service_id)
    service.is_active = not service.is_active
    service.save()
    
    status = 'активирована' if service.is_active else 'деактивирована'
    messages.success(request, f'Услуга "{service.name}" {status}')
    
    return redirect('shop:admin_services_list')


# ============================================================
# Управление категориями (админ)
# ============================================================

@login_required
@user_passes_test(is_admin_or_moderator)
def admin_categories_list(request):
    """Список категорий"""
    categories = ServiceCategory.objects.annotate(
        services_count=Count('services')
    )
    
    context = {
        'categories': categories,
    }
    return render(request, 'shop/admin/categories_list.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_category_create(request):
    """Создание категории"""
    if request.method == 'POST':
        try:
            category = ServiceCategory.objects.create(
                name=request.POST.get('name'),
                slug=request.POST.get('slug'),
                category_type=request.POST.get('category_type'),
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', ''),
                order=int(request.POST.get('order', 0)),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f'Категория "{category.name}" создана')
            return redirect('shop:admin_categories_list')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'shop/admin/category_form.html')


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_category_edit(request, category_id):
    """Редактирование категории"""
    category = get_object_or_404(ServiceCategory, id=category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.slug = request.POST.get('slug')
            category.category_type = request.POST.get('category_type')
            category.description = request.POST.get('description', '')
            category.icon = request.POST.get('icon', '')
            category.order = int(request.POST.get('order', 0))
            category.is_active = request.POST.get('is_active') == 'on'
            category.save()
            
            messages.success(request, 'Категория обновлена')
            return redirect('shop:admin_categories_list')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    context = {
        'category': category,
    }
    return render(request, 'shop/admin/category_form.html', context)


# ============================================================
# Журнал и архивы (админ)
# ============================================================

@login_required
@user_passes_test(is_admin_or_moderator)
def admin_logs(request):
    """Журнал действий"""
    log_type = request.GET.get('type', 'ticket')
    
    if log_type == 'service':
        logs = ServiceLog.objects.select_related(
            'order', 'order__user', 'performed_by'
        ).order_by('-created_at')
    else:
        logs = TicketLog.objects.select_related(
            'ticket', 'ticket__user', 'performed_by'
        ).order_by('-created_at')
    
    # Фильтры
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'log_type': log_type,
        'action_filter': action_filter,
    }
    return render(request, 'shop/admin/logs.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_ticket_archives(request):
    """Архив удалённых тикетов"""
    archive_dir = os.path.join(settings.MEDIA_ROOT, 'ticket_archives')
    
    archives = []
    if os.path.exists(archive_dir):
        for filename in sorted(os.listdir(archive_dir), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(archive_dir, filename)
                stat = os.stat(filepath)
                archives.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': timezone.datetime.fromtimestamp(stat.st_mtime),
                })
    
    paginator = Paginator(archives, 50)
    page = request.GET.get('page')
    archives = paginator.get_page(page)
    
    context = {
        'archives': archives,
    }
    return render(request, 'shop/admin/ticket_archives.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def admin_ticket_archive_view(request, filename):
    """Просмотр архива тикета"""
    archive_dir = os.path.join(settings.MEDIA_ROOT, 'ticket_archives')
    filepath = os.path.join(archive_dir, filename)
    
    if not os.path.exists(filepath) or not filename.endswith('.json'):
        raise Http404("Архив не найден")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    context = {
        'filename': filename,
        'data': data,
    }
    return render(request, 'shop/admin/ticket_archive_view.html', context)