from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import json
import os


class TicketManager(models.Manager):
    """Менеджер для тикетов с поддержкой soft delete"""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        return super().get_queryset()
    
    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)


class ServiceCategory(models.Model):
    """Категория услуг"""
    CATEGORY_TYPES = [
        ('league', 'Лига'),
        ('server', 'Игровой сервер'),
        ('other', 'Другое'),
    ]
    
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    category_type = models.CharField('Тип категории', max_length=20, choices=CATEGORY_TYPES, default='other')
    description = models.TextField('Описание', blank=True)
    icon = models.CharField('Иконка (CSS класс)', max_length=50, blank=True)
    order = models.IntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Активна', default=True)
    
    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """Услуга в магазине"""
    PROCESSING_TYPES = [
        ('auto', 'Автоматическая'),
        ('manual', 'Требует обработки администратором'),
    ]
    
    AUTO_ACTIONS = [
        ('remove_league_ban', 'Снятие бана в лиге'),
        ('change_nickname', 'Смена никнейма'),
    ]
    
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, 
                                 related_name='services', verbose_name='Категория')
    name = models.CharField('Название услуги', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Описание')
    
    processing_type = models.CharField('Тип обработки', max_length=20, 
                                       choices=PROCESSING_TYPES, default='manual')
    auto_action = models.CharField('Автоматическое действие', max_length=50, blank=True,
                                   choices=AUTO_ACTIONS,
                                   help_text='Для автоматических услуг')
    
    is_active = models.BooleanField('Активна', default=True)
    is_featured = models.BooleanField('Рекомендуемая', default=False)
    order = models.IntegerField('Порядок сортировки', default=0)
    
    # Ограничения
    max_uses_per_user = models.IntegerField('Максимум использований на пользователя', 
                                            null=True, blank=True)
    cooldown_days = models.IntegerField('Период ожидания (дней)', null=True, blank=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['processing_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_processing_type_display()})"
    
    def can_user_use(self, user):
        """Проверка возможности использования услуги"""
        if not self.is_active:
            return False, "Услуга недоступна"
        
        if self.max_uses_per_user:
            completed_orders = ServiceOrder.objects.filter(
                user=user, service=self, status='completed'
            ).count()
            if completed_orders >= self.max_uses_per_user:
                return False, f"Достигнут лимит использований ({self.max_uses_per_user})"
        
        if self.cooldown_days:
            last_order = ServiceOrder.objects.filter(
                user=user, service=self, status='completed'
            ).order_by('-completed_at').first()
            
            if last_order and last_order.completed_at:
                days_passed = (timezone.now() - last_order.completed_at).days
                if days_passed < self.cooldown_days:
                    days_left = self.cooldown_days - days_passed
                    return False, f"Доступно через {days_left} дн."
        
        return True, "OK"


class ServiceOrder(models.Model):
    """Заказ услуги"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
        ('rejected', 'Отклонено'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='service_orders', verbose_name='Пользователь')
    service = models.ForeignKey(Service, on_delete=models.PROTECT,
                                related_name='orders', verbose_name='Услуга')
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    order_data = models.JSONField('Данные заказа', default=dict, blank=True)
    
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='processed_orders',
                                     verbose_name='Обработал')
    admin_notes = models.TextField('Заметки администратора', blank=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    processed_at = models.DateTimeField('Обработано', null=True, blank=True)
    completed_at = models.DateTimeField('Завершено', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Заказ услуги'
        verbose_name_plural = 'Заказы услуг'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Заказ #{self.id}: {self.service.name} - {self.user.username}"
    
    def process_auto_action(self):
        """Автоматическая обработка заказа"""
        if self.service.processing_type != 'auto':
            return False, "Услуга требует ручной обработки"
        
        action = self.service.auto_action
        
        try:
            if action == 'remove_league_ban':
                from tournaments.models import Sanction
                active_bans = Sanction.objects.filter(
                    player=self.user,
                    sanction_type='ban',
                    is_active=True
                )
                
                if active_bans.exists():
                    count = active_bans.count()
                    active_bans.update(is_active=False, expires_at=timezone.now())
                    self.admin_notes = f"Автоматически снято {count} активных банов"
                else:
                    self.admin_notes = "Активных банов не найдено"
                
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save()
                
                ServiceLog.objects.create(
                    order=self,
                    action='auto_complete',
                    description=self.admin_notes,
                    performed_by=self.user
                )
                
                return True, "Бан успешно снят"
            
            elif action == 'change_nickname':
                User = get_user_model()
                new_nickname = self.order_data.get('new_nickname')
                
                if not new_nickname:
                    return False, "Не указан новый никнейм"
                
                old_nickname = self.user.username
                
                if User.objects.filter(username=new_nickname).exclude(id=self.user.id).exists():
                    self.status = 'rejected'
                    self.admin_notes = "Никнейм уже занят"
                    self.save()
                    return False, "Никнейм уже занят"
                
                self.user.username = new_nickname
                self.user.save()
                
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.admin_notes = f"Никнейм изменен: {old_nickname} → {new_nickname}"
                self.save()
                
                ServiceLog.objects.create(
                    order=self,
                    action='auto_complete',
                    description=self.admin_notes,
                    performed_by=self.user
                )
                
                return True, "Никнейм успешно изменен"
            
            else:
                return False, f"Неизвестное действие: {action}"
        
        except Exception as e:
            self.status = 'rejected'
            self.admin_notes = f"Ошибка автообработки: {str(e)}"
            self.save()
            return False, str(e)


class Ticket(models.Model):
    """Универсальная тикет-система"""
    CATEGORY_CHOICES = [
        ('request', 'Запрос'),
        ('complaint', 'Жалоба'),
        ('purchase', 'Покупка'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решён'),
        ('rejected', 'Отклонён'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    # Основные поля
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='tickets', verbose_name='Пользователь')
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    
    # Статус и приоритет
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField('Приоритет', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Связи
    order = models.OneToOneField(ServiceOrder, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='ticket', verbose_name='Связанный заказ')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='assigned_tickets',
                                    verbose_name='Назначен')
    
    # Soft delete
    is_deleted = models.BooleanField('Удалён', default=False)
    deleted_at = models.DateTimeField('Дата удаления', null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='deleted_tickets',
                                   verbose_name='Удалил')
    
    # Временные метки
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    resolved_at = models.DateTimeField('Решён', null=True, blank=True)
    
    # Менеджеры
    objects = TicketManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = 'Тикет'
        verbose_name_plural = 'Тикеты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['is_deleted', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"#{self.id}: {self.title}"
    
    def save_to_archive(self):
        """Сохранение тикета в JSON архив перед удалением"""
        archive_dir = os.path.join(settings.MEDIA_ROOT, 'ticket_archives')
        os.makedirs(archive_dir, exist_ok=True)
        
        # Собираем все данные тикета
        data = {
            'id': self.id,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
            },
            'category': self.category,
            'category_display': self.get_category_display(),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'assigned_to': {
                'id': self.assigned_to.id,
                'username': self.assigned_to.username,
            } if self.assigned_to else None,
            'order_id': self.order.id if self.order else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'archived_at': timezone.now().isoformat(),
            'deleted_by': {
                'id': self.deleted_by.id,
                'username': self.deleted_by.username,
            } if self.deleted_by else None,
            'messages': [],
            'logs': [],
        }
        
        # Сообщения
        for msg in self.messages.all():
            data['messages'].append({
                'id': msg.id,
                'user': msg.user.username,
                'message': msg.message,
                'is_admin': msg.is_admin,
                'created_at': msg.created_at.isoformat(),
            })
        
        # Логи
        for log in self.logs.all():
            data['logs'].append({
                'id': log.id,
                'action': log.action,
                'description': log.description,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'performed_by': log.performed_by.username if log.performed_by else None,
                'created_at': log.created_at.isoformat(),
            })
        
        # Сохраняем в файл
        filename = f"ticket_{self.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(archive_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def soft_delete(self, user):
        """Мягкое удаление тикета"""
        # Сохраняем в архив
        archive_filename = self.save_to_archive()
        
        # Логируем удаление
        TicketLog.objects.create(
            ticket=self,
            action='delete',
            description=f'Тикет удалён и сохранён в архив: {archive_filename}',
            performed_by=user
        )
        
        # Помечаем как удалённый
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
        
        return archive_filename
    
    def close_by_user(self):
        """Закрытие тикета пользователем"""
        old_status = self.status
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
        
        TicketLog.objects.create(
            ticket=self,
            action='status_change',
            description='Тикет закрыт пользователем',
            old_value=old_status,
            new_value='resolved',
            performed_by=self.user
        )
    
    def resolve(self, admin_user, notes=""):
        """Решить тикет (админ)"""
        old_status = self.status
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
        
        TicketLog.objects.create(
            ticket=self,
            action='status_change',
            description=f'Тикет решён администратором. {notes}',
            old_value=old_status,
            new_value='resolved',
            performed_by=admin_user
        )
        
        # Если есть связанный заказ - завершаем его тоже
        if self.order:
            self.order.status = 'completed'
            self.order.completed_at = timezone.now()
            self.order.processed_by = admin_user
            self.order.admin_notes = notes
            self.order.save()


class TicketMessage(models.Model):
    """Сообщение в тикете"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, 
                               related_name='messages', verbose_name='Тикет')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name='Отправитель')
    message = models.TextField('Сообщение')
    is_admin = models.BooleanField('От администратора', default=False)
    created_at = models.DateTimeField('Отправлено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Сообщение тикета'
        verbose_name_plural = 'Сообщения тикетов'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]
    
    def __str__(self):
        return f"Сообщение от {self.user.username} в тикете #{self.ticket.id}"


class TicketLog(models.Model):
    """Журнал действий с тикетами"""
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('status_change', 'Изменение статуса'),
        ('assign', 'Назначение'),
        ('message', 'Сообщение'),
        ('delete', 'Удаление'),
        ('restore', 'Восстановление'),
        ('priority_change', 'Изменение приоритета'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE,
                               related_name='logs', verbose_name='Тикет')
    action = models.CharField('Действие', max_length=30, choices=ACTION_CHOICES)
    description = models.TextField('Описание')
    old_value = models.CharField('Старое значение', max_length=100, blank=True)
    new_value = models.CharField('Новое значение', max_length=100, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name='Выполнил')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запись журнала тикетов'
        verbose_name_plural = 'Журнал тикетов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - Тикет #{self.ticket.id}"


class ServiceLog(models.Model):
    """Журнал действий с услугами"""
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE,
                              related_name='logs', verbose_name='Заказ')
    action = models.CharField('Действие', max_length=50)
    description = models.TextField('Описание')
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name='Выполнил')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запись журнала услуг'
        verbose_name_plural = 'Журнал услуг'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - Заказ #{self.order.id}"