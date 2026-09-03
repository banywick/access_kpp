# backend/access_control/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import timedelta
from .models import Contractor, AccessList, AccessLog
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def normalize_phone_number(phone):
    """Нормализация номера телефона"""
    if not phone:
        return None
    
    # Убираем все не цифры
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    
    # Проверяем длину
    if len(cleaned) < 9:
        return None
    
    # Если номер начинается с 8 и длина 11 (например 80291234510)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '375' + cleaned[1:]
    
    # Если номер начинается с 375 и длина 12 (например 375291234510)
    elif cleaned.startswith('375') and len(cleaned) == 12:
        pass  # Уже правильный формат
    
    # Если номер начинается с 0 (например 0291234510)
    elif cleaned.startswith('0') and len(cleaned) == 10:
        cleaned = '375' + cleaned[1:]
    
    # Если номер состоит из 9 цифр и начинается с кода оператора (29, 33, 44, 25)
    elif len(cleaned) == 9 and cleaned[:2] in ['29', '33', '44', '25']:
        cleaned = '375' + cleaned
    
    # Если номер состоит из 10 цифр и начинается с 0 и кода оператора (029, 033, 044, 025)
    elif len(cleaned) == 10 and cleaned.startswith('0') and cleaned[1:3] in ['29', '33', '44', '25']:
        cleaned = '375' + cleaned[1:]
    
    else:
        return None
    
    # Проверяем код оператора для белорусских номеров
    if len(cleaned) >= 12:
        operator_code = cleaned[3:5]
        valid_codes = ['29', '33', '44', '25']
        if operator_code not in valid_codes:
            return None
    
    # Добавляем + если нет
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # Финальная проверка формата +375XXXXXXXXX
    if not cleaned.startswith('+375') or len(cleaned) != 13:
        return None
    
    return cleaned


@admin.register(Contractor)
class ContractorAdmin(UserAdmin):
    """Админка для подрядчиков с возможностью импорта Excel"""
    
    # Настройки для UserAdmin
    list_display = [
        'id', 'phone_number', 'get_full_name', 'organization', 
        'role', 'is_verified', 'is_active', 'access_code', 'created_at'
    ]
    list_filter = [
        'role', 'is_verified', 'is_active', 'organization', 'created_at'
    ]
    search_fields = [
        'phone_number', 'first_name', 'last_name', 'patronymic', 
        'organization', 'access_code'
    ]
    readonly_fields = [
        'qr_code', 'access_code', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'phone_number', 'first_name', 'last_name', 'patronymic', 
                'organization', 'photo'
            )
        }),
        ('Права доступа', {
            'fields': (
                'role', 'is_active', 'is_verified', 
                'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            )
        }),
        ('Коды доступа', {
            'fields': ('qr_code', 'access_code'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number', 'first_name', 'last_name', 'patronymic', 
                'organization', 'password1', 'password2', 'role'
            ),
        }),
    )
    
    ordering = ['-created_at']
    
    # Кастомные действия
    actions = ['generate_codes_for_selected', 'verify_selected', 'deactivate_selected']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'last_name'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['password']
        return self.readonly_fields
    
    def generate_codes_for_selected(self, request, queryset):
        """Генерация кодов доступа для выбранных пользователей"""
        updated = 0
        for contractor in queryset:
            contractor.generate_access_code()
            contractor.generate_qr_code()
            updated += 1
        self.message_user(
            request, 
            f'Сгенерированы коды доступа для {updated} пользователей'
        )
    generate_codes_for_selected.short_description = "Сгенерировать коды доступа для выбранных"
    
    def verify_selected(self, request, queryset):
        """Верификация выбранных пользователей"""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request, 
            f'Верифицированы {updated} пользователей'
        )
    verify_selected.short_description = "Верифицировать выбранных"
    
    def deactivate_selected(self, request, queryset):
        """Деактивация выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Деактивированы {updated} пользователей'
        )
    deactivate_selected.short_description = "Деактивировать выбранных"
    
    # ========== Методы для импорта Excel ==========
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel_view, name='import_excel'),
            path('process-excel/', self.process_excel_view, name='process_excel'),
        ]
        return custom_urls + urls
    
    def import_excel_view(self, request):
        """Страница загрузки Excel файла"""
        context = {
            'title': 'Загрузка подрядчиков из Excel',
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }
        return TemplateResponse(request, 'admin/access_control/import_excel.html', context)
    
    def process_excel_view(self, request):
        """Обработка загруженного Excel файла"""
        if request.method != 'POST':
            return redirect('admin:access_control_contractor_changelist')
        
        if 'excel_file' not in request.FILES:
            messages.error(request, 'Файл не выбран')
            return redirect('admin:access_control_contractor_changelist')
        
        excel_file = request.FILES['excel_file']
        
        # Проверка расширения файла
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Поддерживаются только файлы .xlsx и .xls')
            return redirect('admin:access_control_contractor_changelist')
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(excel_file)
            
            # Проверка наличия необходимых колонок
            required_columns = ['Телефон', 'Имя', 'Фамилия', 'Организация']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(
                    request, 
                    f'В файле отсутствуют необходимые колонки: {", ".join(missing_columns)}. '
                    f'Доступные колонки: {", ".join(df.columns)}'
                )
                return redirect('admin:access_control_contractor_changelist')
            
            # Обработка данных
            created_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            success_items = []
            
            for index, row in df.iterrows():
                try:
                    # Нормализация номера телефона
                    phone_raw = str(row['Телефон']).strip()
                    phone_normalized = normalize_phone_number(phone_raw)
                    
                    if not phone_normalized:
                        errors.append(f'Строка {index + 2}: Неверный формат номера телефона "{phone_raw}"')
                        error_count += 1
                        continue
                    
                    # Проверка существования пользователя
                    if Contractor.objects.filter(phone_number=phone_normalized).exists():
                        skipped_count += 1
                        continue
                    
                    # Создание пользователя
                    first_name = str(row.get('Имя', '')).strip()
                    last_name = str(row.get('Фамилия', '')).strip()
                    patronymic = str(row.get('Отчество', '')).strip() if 'Отчество' in row else ''
                    organization = str(row.get('Организация', '')).strip()
                    
                    if not first_name or not last_name or not organization:
                        errors.append(
                            f'Строка {index + 2}: Не заполнены обязательные поля '
                            f'(Имя: "{first_name}", Фамилия: "{last_name}", Организация: "{organization}")'
                        )
                        error_count += 1
                        continue
                    
                    # Создаем пользователя
                    contractor = Contractor.objects.create_user(
                        phone_number=phone_normalized,
                        password=None,
                        first_name=first_name,
                        last_name=last_name,
                        patronymic=patronymic if patronymic else None,
                        organization=organization,
                        is_active=True,
                        is_verified=False,
                        role='contractor'
                    )
                    
                    # Генерируем QR код и код доступа
                    contractor.generate_access_code()
                    contractor.generate_qr_code()
                    
                    created_count += 1
                    success_items.append(f"{last_name} {first_name} ({phone_normalized})")
                    
                except Exception as e:
                    errors.append(f'Строка {index + 2}: {str(e)}')
                    error_count += 1
            
            # Формируем сообщение
            if created_count > 0:
                messages.success(
                    request, 
                    f'✅ Создано подрядчиков: {created_count}'
                )
                if success_items:
                    messages.info(
                        request, 
                        f'Созданы: {", ".join(success_items[:5])}{"..." if len(success_items) > 5 else ""}'
                    )
            
            if skipped_count > 0:
                messages.info(request, f'⏭️ Пропущено (уже существуют): {skipped_count}')
            
            if error_count > 0:
                messages.warning(
                    request, 
                    f'❌ Ошибок: {error_count}'
                )
                if errors:
                    messages.error(
                        request, 
                        f'Детали ошибок:\n' + '\n'.join(errors[:10])
                    )
                    if len(errors) > 10:
                        messages.info(request, f'... и еще {len(errors) - 10} ошибок')
            
            if created_count == 0 and skipped_count == 0 and error_count == 0:
                messages.warning(request, 'Нет данных для импорта')
            
        except Exception as e:
            logger.error(f'Error importing Excel: {str(e)}')
            messages.error(request, f'Ошибка при обработке файла: {str(e)}')
        
        return redirect('admin:access_control_contractor_changelist')


@admin.register(AccessList)
class AccessListAdmin(admin.ModelAdmin):
    """Админка для списка доступа с удобным управлением статусами"""
    
    list_display = [
        'contractor', 'date', 'status_colored', 'territory_status',
        'is_allowed_badge', 'valid_from', 'valid_until', 'is_valid_badge'
    ]
    list_filter = [
        ('status', admin.AllValuesFieldListFilter),
        'is_on_territory',
        'is_allowed',
        'date',
        'valid_from',
        'valid_until',
    ]
    search_fields = [
        'contractor__phone_number', 
        'contractor__first_name', 
        'contractor__last_name',
        'contractor__organization',
        'ban_reason'
    ]
    readonly_fields = ['created_at', 'updated_at', 'last_entry_time', 'last_exit_time']
    ordering = ['-date', 'contractor']
    
    fieldsets = (
        ('Информация о доступе', {
            'fields': (
                'contractor', 'date', 'status', 'is_allowed', 'ban_reason'
            ),
            'description': 'Управление доступом подрядчика'
        }),
        ('Статус на территории', {
            'fields': (
                'is_on_territory', 'last_entry_time', 'last_exit_time'
            ),
            'description': 'Информация о текущем местоположении'
        }),
        ('Срок действия', {
            'fields': (
                'valid_from', 'valid_until'
            )
        }),
        ('Информация об обновлении', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Действия для массового обновления
    actions = [
        'set_on_territory',
        'set_off_territory', 
        'set_temporary_1_day',
        'set_temporary_3_days',
        'set_temporary_7_days',
        'set_banned',
        'extend_validity_30_days',
    ]
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('contractor', 'updated_by')
    
    # ========== Кастомные методы для отображения ==========
    
    def status_colored(self, obj):
        """Цветной статус доступа"""
        status_colors = {
            'on_territory': '#28a745',
            'off_territory': '#ffc107',
            'temporary': '#17a2b8',
            'banned': '#dc3545',
        }
        status_icons = {
            'on_territory': '📍',
            'off_territory': '⏳',
            'temporary': '⏰',
            'banned': '🚫',
        }
        color = status_colors.get(obj.status, '#6c757d')
        icon = status_icons.get(obj.status, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-weight: 500; display: inline-block;">'
            '{} {} {}</span>',
            color,
            icon,
            obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status,
            ''
        )
    status_colored.short_description = 'Статус'
    status_colored.admin_order_field = 'status'
    
    def territory_status(self, obj):
        """Отображение статуса на территории"""
        if obj.is_on_territory:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ На территории</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">❌ Не на территории</span>'
        )
    territory_status.short_description = 'Местоположение'
    territory_status.admin_order_field = 'is_on_territory'
    
    def is_allowed_badge(self, obj):
        """Отображение разрешения доступа"""
        if obj.is_allowed:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ Разрешен</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">❌ Запрещен</span>'
        )
    is_allowed_badge.short_description = 'Доступ'
    is_allowed_badge.admin_order_field = 'is_allowed'
    
    def is_valid_badge(self, obj):
        """Проверка действительности доступа"""
        if obj.is_valid():
            return format_html(
                '<span style="color: #28a745;">✅ Действителен</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">❌ Просрочен</span>'
        )
    is_valid_badge.short_description = 'Актуальность'
    
    # ========== Кастомные действия ==========
    
    def set_on_territory(self, request, queryset):
        """Установить статус 'На территории' для выбранных записей"""
        updated = 0
        for access in queryset:
            access.set_on_territory(updated_by=request.user)
            updated += 1
        self.message_user(
            request, 
            f'✅ Установлен статус "На территории" для {updated} записей'
        )
    set_on_territory.short_description = "📍 Установить 'На территории'"
    
    def set_off_territory(self, request, queryset):
        """Установить статус 'Не на территории' для выбранных записей"""
        updated = 0
        for access in queryset:
            access.set_off_territory(updated_by=request.user)
            updated += 1
        self.message_user(
            request, 
            f'⏳ Установлен статус "Не на территории" для {updated} записей'
        )
    set_off_territory.short_description = "⏳ Установить 'Не на территории'"
    
    def set_temporary_1_day(self, request, queryset):
        """Установить временный доступ на 1 день"""
        updated = 0
        for access in queryset:
            access.set_temporary(days=1, updated_by=request.user)
            updated += 1
        self.message_user(
            request, 
            f'⏰ Установлен временный доступ (1 день) для {updated} записей'
        )
    set_temporary_1_day.short_description = "⏰ Временный доступ (1 день)"
    
    def set_temporary_3_days(self, request, queryset):
        """Установить временный доступ на 3 дня"""
        updated = 0
        for access in queryset:
            access.set_temporary(days=3, updated_by=request.user)
            updated += 1
        self.message_user(
            request, 
            f'⏰ Установлен временный доступ (3 дня) для {updated} записей'
        )
    set_temporary_3_days.short_description = "⏰ Временный доступ (3 дня)"
    
    def set_temporary_7_days(self, request, queryset):
        """Установить временный доступ на 7 дней"""
        updated = 0
        for access in queryset:
            access.set_temporary(days=7, updated_by=request.user)
            updated += 1
        self.message_user(
            request, 
            f'⏰ Установлен временный доступ (7 дней) для {updated} записей'
        )
    set_temporary_7_days.short_description = "⏰ Временный доступ (7 дней)"
    
    def set_banned(self, request, queryset):
        """Заблокировать доступ для выбранных записей"""
        if 'apply' in request.POST:
            reason = request.POST.get('ban_reason', 'Блокировка доступа')
            updated = 0
            for access in queryset:
                access.set_banned(reason=reason, updated_by=request.user)
                updated += 1
            self.message_user(
                request, 
                f'🚫 Заблокирован доступ для {updated} записей. Причина: {reason}'
            )
            return None
        
        # Показываем форму для ввода причины блокировки
        context = {
            'title': 'Блокировка доступа',
            'queryset': queryset,
            'action': 'set_banned',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/access_control/ban_confirm.html', context)
    set_banned.short_description = "🚫 Заблокировать доступ"
    
    def extend_validity_30_days(self, request, queryset):
        """Продлить срок действия на 30 дней"""
        updated = 0
        for access in queryset:
            access.valid_until = timezone.now().date() + timedelta(days=30)
            access.updated_by = request.user
            access.save()
            updated += 1
        self.message_user(
            request, 
            f'📅 Продлен срок действия на 30 дней для {updated} записей'
        )
    extend_validity_30_days.short_description = "📅 Продлить на 30 дней"
    
    # ========== Кастомные кнопки в админке ==========
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('quick-action/<int:pk>/<str:action>/', 
                 self.quick_action_view, 
                 name='quick_action'),
        ]
        return custom_urls + urls
    
    def quick_action_view(self, request, pk, action):
        """Быстрое действие для отдельной записи"""
        access = get_object_or_404(AccessList, pk=pk)
        
        if action == 'on_territory':
            access.set_on_territory(updated_by=request.user)
            messages.success(request, f'✅ {access.contractor} - На территории')
        elif action == 'off_territory':
            access.set_off_territory(updated_by=request.user)
            messages.success(request, f'⏳ {access.contractor} - Не на территории')
        elif action == 'temporary':
            access.set_temporary(days=1, updated_by=request.user)
            messages.success(request, f'⏰ {access.contractor} - Временный доступ (1 день)')
        elif action == 'ban':
            access.set_banned(reason="Блокировка через быстрый доступ", updated_by=request.user)
            messages.success(request, f'🚫 {access.contractor} - Доступ заблокирован')
        else:
            messages.error(request, f'Неизвестное действие: {action}')
        
        return redirect(request.META.get('HTTP_REFERER', 'admin:access_control_accesslist_changelist'))
    
    def changelist_view(self, request, extra_context=None):
        """Добавляем статистику в список"""
        extra_context = extra_context or {}
        
        # Статистика по статусам
        stats = {
            'on_territory': AccessList.objects.filter(status='on_territory').count(),
            'off_territory': AccessList.objects.filter(status='off_territory').count(),
            'temporary': AccessList.objects.filter(status='temporary').count(),
            'banned': AccessList.objects.filter(status='banned').count(),
            'total': AccessList.objects.count(),
        }
        extra_context['status_stats'] = stats
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Админка для логов доступа"""
    list_display = [
        'contractor', 'scanned_at', 'access_method', 'access_type', 
        'is_successful_badge', 'ip_address'
    ]
    list_filter = [
        'access_method', 'access_type', 'is_successful', 'scanned_at'
    ]
    search_fields = [
        'contractor__phone_number', 'contractor__first_name', 
        'contractor__last_name', 'qr_code_scanned', 'access_code_entered'
    ]
    readonly_fields = [
        'contractor', 'scanned_at', 'scanned_by', 'qr_code_scanned',
        'access_code_entered', 'access_method', 'access_type', 
        'is_successful', 'ip_address'
    ]
    ordering = ['-scanned_at']
    
    def is_successful_badge(self, obj):
        if obj.is_successful:
            return format_html(
                '<span style="color: #28a745;">✅ Успешно</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">❌ Отказ</span>'
        )
    is_successful_badge.short_description = 'Результат'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False