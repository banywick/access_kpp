# backend/access_control/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from .models import Contractor, AccessList, AccessLog


class ContractorCreationForm(UserCreationForm):
    """Форма создания пользователя"""
    
    class Meta:
        model = Contractor
        fields = ('phone_number', 'first_name', 'last_name', 'patronymic', 'organization', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].help_text = 'Оставьте пустым, если не хотите устанавливать пароль'
        self.fields['password2'].help_text = 'Оставьте пустым, если не хотите устанавливать пароль'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.cleaned_data.get('password1'):
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
            # Подрядчики, которые находятся на территории
            # Находим всех подрядчиков с последним успешным проходом типа 'entry'
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
            # Подрядчики, которые не на территории
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
        'on_territory_status',
        'has_photo',
        'has_qr',
        'created_at'
    ]
    list_filter = [
        'role',
        'is_verified',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
        OnTerritoryFilter,  # Добавляем кастомный фильтр
    ]
    search_fields = ['phone_number', 'first_name', 'last_name', 'patronymic', 'organization']
    list_editable = ['is_verified']
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'patronymic', 'organization', 'photo')
        }),
        (_('Role and Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'qr_code', 'access_code'),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'patronymic', 'organization', 'role'),
        }),
        (_('Password (optional)'), {
            'classes': ('wide',),
            'fields': ('password1', 'password2'),
            'description': 'Оставьте поля пароля пустыми, чтобы не устанавливать пароль',
        }),
    )
    
    ordering = ['-created_at']
    
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
    
    def on_territory_status(self, obj):
        """Отображает статус нахождения на территории"""
        last_log = AccessLog.objects.filter(
            contractor=obj,
            is_successful=True
        ).order_by('-scanned_at').first()
        
        if not last_log:
            return '🚫 Не на территории'
        
        if last_log.access_type == 'entry':
            return '📍 На территории'
        else:
            return '🚫 Не на территории'
    on_territory_status.short_description = "На территории"
    
    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.boolean = True
    has_photo.short_description = "Фото"
    
    def has_qr(self, obj):
        return bool(obj.qr_code)
    has_qr.boolean = True
    has_qr.short_description = "QR код"
    
    def save_model(self, request, obj, form, change):
        if not change:
            if not form.cleaned_data.get('password1'):
                obj.set_unusable_password()
        
        if obj.role in ['guard', 'admin']:
            obj.is_staff = True
        else:
            obj.is_staff = False
        
        super().save_model(request, obj, form, change)
        
        if not change and obj.role == 'contractor':
            AccessList.objects.create(
                contractor=obj,
                date=timezone.now().date(),
                is_allowed=True,
                valid_from=timezone.now().date(),
                valid_until=timezone.now().date() + timedelta(days=30)
            )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'updated_at', 'qr_code', 'access_code']
        return []


class AccessListForm(forms.ModelForm):
    """Форма для списка доступа с расширенными полями"""
    
    class Meta:
        model = AccessList
        fields = '__all__'
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


@admin.register(AccessList)
class AccessListAdmin(admin.ModelAdmin):
    """Админка для списков доступа"""
    form = AccessListForm
    
    list_display = [
        'contractor', 
        'contractor_organization',
        'date', 
        'is_allowed', 
        'valid_from', 
        'valid_until',
        'is_valid_display',
        'days_remaining',
        'on_territory_status',
        'ban_reason'
    ]
    list_filter = [
        'date', 
        'is_allowed',
        'valid_from',
        'valid_until'
    ]
    search_fields = [
        'contractor__phone_number', 
        'contractor__first_name', 
        'contractor__last_name',
        'contractor__organization'
    ]
    list_editable = ['is_allowed', 'valid_from', 'valid_until']
    list_per_page = 20
    
    fieldsets = (
        ('Информация о доступе', {
            'fields': ('contractor', 'date', 'is_allowed', 'ban_reason')
        }),
        ('Срок действия', {
            'fields': ('valid_from', 'valid_until'),
            'description': 'Установите период действия разрешения на доступ'
        }),
    )
    
    actions = ['extend_access_30_days', 'extend_access_90_days', 'revoke_access']
    
    def contractor_organization(self, obj):
        return obj.contractor.organization if obj.contractor.organization else '-'
    contractor_organization.short_description = "Организация"
    contractor_organization.admin_order_field = 'contractor__organization'
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            return '✅ Активен'
        elif not obj.is_allowed:
            return '❌ Заблокирован'
        else:
            return '⏰ Истек'
    is_valid_display.short_description = "Статус"
    is_valid_display.admin_order_field = 'valid_until'
    
    def days_remaining(self, obj):
        if not obj.is_allowed:
            return '—'
        today = timezone.now().date()
        if obj.valid_until < today:
            return '⏰ 0'
        days = (obj.valid_until - today).days
        if days <= 3:
            return f'🔴 {days} дн.'
        elif days <= 7:
            return f'🟡 {days} дн.'
        else:
            return f'🟢 {days} дн.'
    days_remaining.short_description = "Осталось дней"
    
    def on_territory_status(self, obj):
        if not obj.contractor:
            return '—'
        
        last_log = AccessLog.objects.filter(
            contractor=obj.contractor,
            is_successful=True
        ).order_by('-scanned_at').first()
        
        if not last_log:
            return '🚫 Не на территории'
        
        if last_log.access_type == 'entry':
            return '📍 На территории'
        else:
            return '🚫 Не на территории'
    on_territory_status.short_description = "На территории"
    
    def extend_access_30_days(self, request, queryset):
        count = 0
        for item in queryset:
            if item.is_allowed:
                item.valid_until = timezone.now().date() + timedelta(days=30)
                item.save()
                count += 1
        self.message_user(request, f'Доступ продлен на 30 дней для {count} записей')
    extend_access_30_days.short_description = "Продлить доступ на 30 дней"
    
    def extend_access_90_days(self, request, queryset):
        count = 0
        for item in queryset:
            if item.is_allowed:
                item.valid_until = timezone.now().date() + timedelta(days=90)
                item.save()
                count += 1
        self.message_user(request, f'Доступ продлен на 90 дней для {count} записей')
    extend_access_90_days.short_description = "Продлить доступ на 90 дней"
    
    def revoke_access(self, request, queryset):
        count = queryset.update(is_allowed=False, ban_reason='Доступ отозван администратором')
        self.message_user(request, f'Доступ отозван для {count} записей')
    revoke_access.short_description = "Отозвать доступ"
    
    def save_model(self, request, obj, form, change):
        if obj.valid_until < obj.valid_from:
            self.message_user(request, 'Дата окончания не может быть раньше даты начала', level='ERROR')
            return
        super().save_model(request, obj, form, change)


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
        'is_successful'
    ]
    list_filter = ['scanned_at', 'is_successful', 'access_method', 'access_type']
    search_fields = ['contractor__phone_number', 'contractor__first_name', 'contractor__last_name']
    readonly_fields = ['scanned_at', 'qr_code_scanned', 'access_code_entered', 'ip_address']
    list_per_page = 20
    
    def contractor_organization(self, obj):
        return obj.contractor.organization if obj.contractor.organization else '-'
    contractor_organization.short_description = "Организация"
    contractor_organization.admin_order_field = 'contractor__organization'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contractor')