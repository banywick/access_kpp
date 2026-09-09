# backend/access_control/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.template.response import TemplateResponse
from .models import Contractor, AccessList, AccessLog
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ========== НОРМАЛИЗАЦИЯ ТЕЛЕФОНА ==========
def normalize_phone_number(phone):
    """Нормализация номера телефона"""
    if not phone:
        return None
    
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    
    if len(cleaned) < 9:
        return None
    
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '375' + cleaned[1:]
    elif cleaned.startswith('375') and len(cleaned) == 12:
        pass
    elif cleaned.startswith(('29', '33', '44', '25')) and len(cleaned) == 9:
        cleaned = '375' + cleaned
    elif cleaned.startswith(('029', '033', '044', '025')) and len(cleaned) == 10:
        cleaned = '375' + cleaned[1:]
    else:
        return None
    
    if len(cleaned) >= 12:
        operator_code = cleaned[3:5]
        valid_codes = ['29', '33', '44', '25']
        if operator_code not in valid_codes:
            return None
    
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    if not cleaned.startswith('+375') or len(cleaned) != 13:
        return None
    
    return cleaned


# ========== ФОРМЫ ==========
class ContractorCreationForm(UserCreationForm):
    """Форма создания пользователя"""
    
    class Meta:
        model = Contractor
        fields = ('phone_number', 'first_name', 'last_name', 'patronymic', 'organization', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].help_text = 'Оставьте пустым для подрядчиков. Для охранников/админов - обязателен.'
        self.fields['password2'].help_text = 'Подтверждение пароля'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if role in ['guard', 'admin']:
            if not password1:
                self.add_error('password1', 'Для охранников и администраторов пароль обязателен')
            if password1 != password2:
                self.add_error('password2', 'Пароли не совпадают')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        if commit:
            user.save()
        return user


class ContractorChangeForm(UserChangeForm):
    """Форма изменения пользователя"""
    
    class Meta:
        model = Contractor
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['password'].help_text = 'Оставьте пустым, чтобы не менять пароль'


# ========== ФИЛЬТР СТАТУСА НА ТЕРРИТОРИИ ==========
class OnTerritoryFilter(admin.SimpleListFilter):
    """Фильтр для отображения подрядчиков на территории"""
    title = 'На территории'
    parameter_name = 'on_territory'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', '📍 На территории'),
            ('no', '🚫 Не на территории'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            on_territory_ids = []
            for contractor in queryset:
                last_log = AccessLog.objects.filter(
                    contractor=contractor,
                    is_successful=True
                ).order_by('-scanned_at').first()
                if last_log and last_log.access_type == 'entry':
                    on_territory_ids.append(contractor.id)
            return queryset.filter(id__in=on_territory_ids)
        
        if self.value() == 'no':
            off_territory_ids = []
            for contractor in queryset:
                last_log = AccessLog.objects.filter(
                    contractor=contractor,
                    is_successful=True
                ).order_by('-scanned_at').first()
                if not last_log or last_log.access_type == 'exit':
                    off_territory_ids.append(contractor.id)
            return queryset.filter(id__in=off_territory_ids)
        
        return queryset


# ========== АДМИНКА ПОДРЯДЧИКОВ ==========
@admin.register(Contractor)
class ContractorAdmin(UserAdmin):
    """Админка для управления пользователями"""
    
    add_form = ContractorCreationForm
    form = ContractorChangeForm
    
    list_display = [
        'phone_number',
        'get_full_name', 
        'organization',
        'get_role_display',
        'is_verified',
        'has_photo_display',
        'access_code',
        'created_at'
    ]
    list_filter = [
        'role',
        'is_verified',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
        OnTerritoryFilter,
    ]
    search_fields = ['phone_number', 'first_name', 'last_name', 'patronymic', 'organization']
    list_editable = ['is_verified']
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'patronymic', 'organization', 'photo')
        }),
        ('Права доступа', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Верификация', {
            'fields': ('is_verified', 'qr_code', 'access_code'),
            'classes': ('collapse',),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'patronymic', 'organization', 'role'),
        }),
        ('Пароль (для охранников/админов обязателен)', {
            'classes': ('wide',),
            'fields': ('password1', 'password2'),
        }),
    )
    
    ordering = ['-created_at']
    
    actions = ['verify_selected', 'generate_codes_selected', 'deactivate_selected']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "ФИО"
    get_full_name.admin_order_field = 'last_name'
    
    def get_role_display(self, obj):
        role_colors = {
            'contractor': '🟢 Подрядчик',
            'guard': '🟡 Охранник',
            'admin': '🔴 Администратор'
        }
        return role_colors.get(obj.role, obj.role)
    get_role_display.short_description = "Роль"
    
    def has_photo_display(self, obj):
        """Отображение наличия фото"""
        if obj.photo:
            return format_html('<span style="color: #28a745;">✅ Есть</span>')
        return format_html('<span style="color: #dc3545;">❌ Нет</span>')
    has_photo_display.short_description = "Фото"
    
    def on_territory_status(self, obj):
        """Отображает статус нахождения на территории (компактно)"""
        last_log = AccessLog.objects.filter(
            contractor=obj,
            is_successful=True
        ).order_by('-scanned_at').first()
        
        if not last_log:
            return format_html(
                '<span style="color: #6c757d; font-weight: 500;">🚫 Не на тер.</span>'
            )
        
        if last_log.access_type == 'entry':
            return format_html(
                '<span style="color: #0d47a1; font-weight: 600;">📍 На тер.</span>'
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-weight: 500;">🚫 Не на тер.</span>'
            )
    on_territory_status.short_description = "На тер."
    
    def verify_selected(self, request, queryset):
        """Верификация выбранных пользователей с проверкой наличия фото"""
        updated = 0
        no_photo = 0
        already_verified = 0
        
        for contractor in queryset:
            if contractor.role != 'contractor':
                continue
            
            if contractor.is_verified:
                already_verified += 1
                continue
            
            if not contractor.photo:
                no_photo += 1
                continue
            
            contractor.verify_user()
            updated += 1
        
        messages_list = []
        if updated > 0:
            messages_list.append(f'✅ Верифицировано {updated} подрядчиков')
        if no_photo > 0:
            messages_list.append(f'❌ {no_photo} - нет фото')
        if already_verified > 0:
            messages_list.append(f'⏭️ {already_verified} уже верифицированы')
        
        if messages_list:
            self.message_user(request, ' | '.join(messages_list))
        else:
            self.message_user(request, 'Нет подрядчиков для верификации')
    verify_selected.short_description = "Верифицировать (требуется фото)"
    
    def generate_codes_selected(self, request, queryset):
        """Генерация кодов для выбранных"""
        updated = 0
        for contractor in queryset:
            if contractor.is_verified:
                contractor.generate_access_code()
                contractor.generate_qr_code()
                updated += 1
        self.message_user(
            request, 
            f'✅ Сгенерированы коды для {updated} пользователей'
        )
    generate_codes_selected.short_description = "Сгенерировать коды"
    
    def deactivate_selected(self, request, queryset):
        """Деактивация выбранных"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'⛔ Деактивированы {updated} пользователей'
        )
    deactivate_selected.short_description = "Деактивировать"
    
    def save_model(self, request, obj, form, change):
        """При сохранении проверяем пароль и роль"""
        if not change:
            if obj.role in ['guard', 'admin'] and not obj.has_usable_password():
                self.message_user(
                    request, 
                    'Для охранников и администраторов необходимо установить пароль!',
                    level='ERROR'
                )
                return
        
        if obj.role in ['guard', 'admin']:
            obj.is_staff = True
        else:
            obj.is_staff = False
        
        if obj.is_verified and not obj.photo and obj.role == 'contractor':
            obj.is_verified = False
            self.message_user(
                request,
                '⚠️ Верификация снята: требуется фото',
                level='WARNING'
            )
        
        if obj.is_verified and not obj.access_code:
            obj.generate_access_code()
            obj.generate_qr_code()
        
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'updated_at', 'qr_code', 'access_code']
        return []
    
    # ========== ИМПОРТ EXCEL ==========
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel_view, name='import_excel'),
            path('process-excel/', self.process_excel_view, name='process_excel'),
        ]
        return custom_urls + urls
    
    def import_excel_view(self, request):
        context = {
            'title': 'Загрузка подрядчиков из Excel',
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }
        return TemplateResponse(request, 'admin/access_control/import_excel.html', context)
    
    def process_excel_view(self, request):
        if request.method != 'POST':
            return redirect('admin:access_control_contractor_changelist')
        
        if 'excel_file' not in request.FILES:
            messages.error(request, 'Файл не выбран')
            return redirect('admin:access_control_contractor_changelist')
        
        excel_file = request.FILES['excel_file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Поддерживаются только файлы .xlsx и .xls')
            return redirect('admin:access_control_contractor_changelist')
        
        try:
            df = pd.read_excel(excel_file)
            
            required_columns = ['Телефон', 'Имя', 'Фамилия', 'Организация']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(
                    request, 
                    f'В файле отсутствуют колонки: {", ".join(missing_columns)}'
                )
                return redirect('admin:access_control_contractor_changelist')
            
            created_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    phone_raw = str(row['Телефон']).strip()
                    phone_normalized = normalize_phone_number(phone_raw)
                    
                    if not phone_normalized:
                        errors.append(f'Строка {index + 2}: Неверный формат телефона "{phone_raw}"')
                        error_count += 1
                        continue
                    
                    if Contractor.objects.filter(phone_number=phone_normalized).exists():
                        skipped_count += 1
                        continue
                    
                    first_name = str(row.get('Имя', '')).strip()
                    last_name = str(row.get('Фамилия', '')).strip()
                    patronymic = str(row.get('Отчество', '')).strip() if 'Отчество' in row else ''
                    organization = str(row.get('Организация', '')).strip()
                    
                    if not first_name or not last_name or not organization:
                        errors.append(
                            f'Строка {index + 2}: Не заполнены обязательные поля'
                        )
                        error_count += 1
                        continue
                    
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
                    
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f'Строка {index + 2}: {str(e)}')
                    error_count += 1
            
            if created_count > 0:
                messages.success(request, f'✅ Создано подрядчиков: {created_count}')
            
            if skipped_count > 0:
                messages.info(request, f'⏭️ Пропущено: {skipped_count}')
            
            if error_count > 0:
                messages.warning(request, f'❌ Ошибок: {error_count}')
                if errors:
                    messages.error(request, '\n'.join(errors[:5]))
            
        except Exception as e:
            logger.error(f'Error importing Excel: {str(e)}')
            messages.error(request, f'Ошибка при обработке файла: {str(e)}')
        
        return redirect('admin:access_control_contractor_changelist')


# ========== АДМИНКА СПИСКОВ ДОСТУПА ==========
# backend/access_control/admin.py - только исправленная часть AccessListAdmin

# backend/access_control/admin.py

@admin.register(AccessList)
class AccessListAdmin(admin.ModelAdmin):
    """Админка для списка доступа"""
    
    list_display = [
        'contractor',
        'contractor_organization',
        'is_allowed_badge',
        'status_colored',
        'valid_from',
        'valid_until',
        'is_valid_badge',
        'days_remaining',
    ]
    list_filter = [
        'status',
        'is_on_territory',
        'is_allowed',
        'valid_from',
        'valid_until',
    ]
    search_fields = [
        'contractor__phone_number',
        'contractor__first_name',
        'contractor__last_name',
        'contractor__organization',
    ]
    list_editable = ['valid_from', 'valid_until']
    list_per_page = 20
    
    fieldsets = (
        ('Информация о доступе', {
            'fields': ('contractor', 'is_allowed', 'status', 'ban_reason')
        }),
        ('Статус на территории', {
            'fields': ('is_on_territory', 'last_entry_time', 'last_exit_time')
        }),
        ('Срок действия', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Информация об обновлении', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'last_entry_time', 
        'last_exit_time',
        'contractor',
        'is_on_territory',
        'status',
    ]
    
    actions = [
        'set_on_territory',
        'set_off_territory',
        'extend_30_days',
        'extend_90_days',
        'revoke_access',
        'set_temporary_1_day',
        'set_temporary_3_days',
        'set_temporary_7_days',
    ]
    
    def contractor_organization(self, obj):
        return obj.contractor.organization if obj.contractor.organization else '-'
    contractor_organization.short_description = "Организация"
    contractor_organization.admin_order_field = 'contractor__organization'
    
    def is_allowed_badge(self, obj):
        if obj.is_allowed:
            return format_html('<span style="color: #28a745; font-weight: 600;">✅ Разрешен</span>')
        return format_html('<span style="color: #dc3545; font-weight: 600;">❌ Запрещен</span>')
    is_allowed_badge.short_description = "Доступ"
    
    def status_colored(self, obj):
        colors = {
            'on_territory': '#0d47a1',
            'off_territory': '#6c757d',
            'temporary': '#e65100',
            'banned': '#c62828',
        }
        icons = {
            'on_territory': '📍',
            'off_territory': '🚫',
            'temporary': '⏰',
            'banned': '🚫',
        }
        labels = {
            'on_territory': 'На тер.',
            'off_territory': 'Не на тер.',
            'temporary': 'Врем.',
            'banned': 'Заблок.',
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '')
        label = labels.get(obj.status, obj.status)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-weight: 500; font-size: 11px; '
            'white-space: nowrap; display: inline-block;">{} {}</span>',
            color, icon, label
        )
    status_colored.short_description = "Статус"
    
    def is_valid_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: #28a745; font-weight: 600;">✅ Активен</span>')
        return format_html('<span style="color: #dc3545; font-weight: 600;">❌ Истек</span>')
    is_valid_badge.short_description = "Актуальность"
    
    def days_remaining(self, obj):
        if not obj.is_allowed:
            return '—'
        today = timezone.now().date()
        if obj.valid_until < today:
            return '⏰ 0'
        days = (obj.valid_until - today).days
        if days <= 3:
            return f'🔴 {days}д'
        elif days <= 7:
            return f'🟡 {days}д'
        else:
            return f'🟢 {days}д'
    days_remaining.short_description = "Дней"
    
    def get_queryset(self, request):
        """Возвращает только активные записи доступа"""
        return super().get_queryset(request).select_related('contractor', 'updated_by')
    
    def set_on_territory(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_on_territory(updated_by=request.user)
            updated += 1
        self.message_user(request, f'📍 На территории: {updated}')
    set_on_territory.short_description = "📍 На территории"
    
    def set_off_territory(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_off_territory(updated_by=request.user)
            updated += 1
        self.message_user(request, f'🚫 Не на территории: {updated}')
    set_off_territory.short_description = "🚫 Не на территории"
    
    def extend_30_days(self, request, queryset):
        updated = 0
        for item in queryset:
            if item.is_allowed:
                item.valid_until = timezone.now().date() + timedelta(days=30)
                item.updated_by = request.user
                item.save()
                updated += 1
        self.message_user(request, f'📅 +30 дней: {updated}')
    extend_30_days.short_description = "📅 +30 дней"
    
    def extend_90_days(self, request, queryset):
        updated = 0
        for item in queryset:
            if item.is_allowed:
                item.valid_until = timezone.now().date() + timedelta(days=90)
                item.updated_by = request.user
                item.save()
                updated += 1
        self.message_user(request, f'📅 +90 дней: {updated}')
    extend_90_days.short_description = "📅 +90 дней"
    
    def revoke_access(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_banned(reason="Отозвано администратором", updated_by=request.user)
            updated += 1
        self.message_user(request, f'🚫 Отозвано: {updated}')
    revoke_access.short_description = "🚫 Отозвать доступ"
    
    def set_temporary_1_day(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_temporary(days=1, updated_by=request.user)
            updated += 1
        self.message_user(request, f'⏰ Врем. 1 день: {updated}')
    set_temporary_1_day.short_description = "⏰ Врем. 1 день"
    
    def set_temporary_3_days(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_temporary(days=3, updated_by=request.user)
            updated += 1
        self.message_user(request, f'⏰ Врем. 3 дня: {updated}')
    set_temporary_3_days.short_description = "⏰ Врем. 3 дня"
    
    def set_temporary_7_days(self, request, queryset):
        updated = 0
        for item in queryset:
            item.set_temporary(days=7, updated_by=request.user)
            updated += 1
        self.message_user(request, f'⏰ Врем. 7 дней: {updated}')
    set_temporary_7_days.short_description = "⏰ Врем. 7 дней"
    
    def save_model(self, request, obj, form, change):
        if obj.valid_until < obj.valid_from:
            self.message_user(request, 'Дата окончания не может быть раньше даты начала', level='ERROR')
            return
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========== АДМИНКА ЛОГОВ ==========
@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Админка для логов доступа"""
    list_display = [
        'contractor',
        'contractor_organization',
        'scanned_at',
        'scanned_by',
        'access_method',
        'access_type',
        'is_successful_badge'
    ]
    list_filter = ['scanned_at', 'is_successful', 'access_method', 'access_type']
    search_fields = ['contractor__phone_number', 'contractor__first_name', 'contractor__last_name']
    readonly_fields = ['scanned_at', 'qr_code_scanned', 'access_code_entered', 'ip_address']
    list_per_page = 20
    
    def contractor_organization(self, obj):
        return obj.contractor.organization if obj.contractor.organization else '-'
    contractor_organization.short_description = "Организация"
    
    def is_successful_badge(self, obj):
        if obj.is_successful:
            return format_html(
                '<span style="color: #28a745; font-weight: 600;">✅ Успешно</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: 600;">❌ Отказ</span>'
        )
    is_successful_badge.short_description = "Результат"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False