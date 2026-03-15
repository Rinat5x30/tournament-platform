from django.contrib import admin
from .models import ServiceCategory, Service, ServiceOrder, ServiceLog, Ticket, TicketMessage, TicketLog


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'is_active', 'order']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'processing_type', 'is_active', 'is_featured', 'order']
    list_filter = ['category', 'processing_type', 'is_active', 'is_featured']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Обработка', {
            'fields': ('processing_type', 'auto_action')
        }),
        ('Ограничения', {
            'fields': ('max_uses_per_user', 'cooldown_days')
        }),
        ('Настройки', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'service__category', 'created_at']
    search_fields = ['user__username', 'service__name']
    readonly_fields = ['created_at', 'processed_at', 'completed_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'service', 'status')
        }),
        ('Данные заказа', {
            'fields': ('order_data', 'admin_notes')
        }),
        ('Обработка', {
            'fields': ('processed_by', 'created_at', 'processed_at', 'completed_at')
        }),
    )


@admin.register(ServiceLog)
class ServiceLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['order__id', 'description']
    readonly_fields = ['created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'category', 'status', 'priority', 'assigned_to', 'created_at']
    list_filter = ['status', 'category', 'priority', 'is_deleted', 'created_at']
    search_fields = ['id', 'title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'deleted_at']
    raw_id_fields = ['user', 'assigned_to', 'order', 'deleted_by']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'category', 'title', 'description')
        }),
        ('Статус', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Связи', {
            'fields': ('order',)
        }),
        ('Удаление', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Показываем все тикеты, включая удалённые
        return Ticket.all_objects.all()


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'user', 'is_admin', 'created_at']
    list_filter = ['is_admin', 'created_at']
    search_fields = ['ticket__id', 'user__username', 'message']
    readonly_fields = ['created_at']
    raw_id_fields = ['ticket', 'user']


@admin.register(TicketLog)
class TicketLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['ticket__id', 'description']
    readonly_fields = ['created_at']
    raw_id_fields = ['ticket', 'performed_by']