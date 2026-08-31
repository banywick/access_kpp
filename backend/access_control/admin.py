# backend/access_control/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Contractor, AccessList, AccessLog


class ContractorCreationForm(UserCreationForm):
    """Форма создания подрядчика без пароля"""
    
    class Meta:
        model = Contractor
        fields = ('phone_number', 'first_name', 'last_name', 'patronymic')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем обязательность пароля
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].help_text = 'Оставьте пустым, если не хотите устанавливать пароль'
        self.fields['password2'].help_text = 'Оставьте пустым, если не хотите устанавливать пароль'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Если пароль не указан, устанавливаем случайный
        if not self.cleaned_data.get('password1'):
            user.set_password(None)  # Пользователь не сможет войти по паролю
        if commit:
            user.save()
        return user


class ContractorChangeForm(UserChangeForm):
    """Форма изменения подрядчика"""
    
    class Meta:
        model = Contractor
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем пароль необязательным
        self.fields['password'].required = False
        self.fields['password'].help_text = 'Оставьте пустым, чтобы не менять пароль'


@admin.register(Contractor)
class ContractorAdmin(UserAdmin):
    """Админка для подрядчиков без пароля"""
    
    # Используем кастомные формы
    add_form = ContractorCreationForm
    form = ContractorChangeForm
    
    list_display = [
        'phone_number', 
        'get_full_name', 
        'is_verified', 
        'has_photo', 
        'has_qr',
        'created_at'
    ]
    list_filter = ['is_verified', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['phone_number', 'first_name', 'last_name', 'patronymic']
    list_editable = ['is_verified']
    list_per_page = 20
    
    # Поля для отображения
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'patronymic', 'photo')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'qr_code'),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Поля для формы создания
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'patronymic'),
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
    
    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.boolean = True
    has_photo.short_description = "Фото"
    
    def has_qr(self, obj):
        return bool(obj.qr_code)
    has_qr.boolean = True
    has_qr.short_description = "QR код"
    
    def save_model(self, request, obj, form, change):
        """При сохранении проверяем пароль"""
        if not change:  # Создание нового
            # Если пароль не указан, устанавливаем пустой
            if not form.cleaned_data.get('password1'):
                obj.set_password(None)
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Поля только для чтения"""
        if obj:  # Редактирование существующего
            return ['created_at', 'updated_at']
        return []


@admin.register(AccessList)
class AccessListAdmin(admin.ModelAdmin):
    """Админка для списков доступа"""
    list_display = ['contractor', 'date', 'is_allowed', 'ban_reason', 'created_at']
    list_filter = ['date', 'is_allowed']
    search_fields = ['contractor__phone_number', 'contractor__first_name', 'contractor__last_name']
    list_editable = ['is_allowed']
    list_per_page = 20
    
    actions = ['ban_selected', 'unban_selected']
    
    def ban_selected(self, request, queryset):
        count = queryset.update(is_allowed=False, ban_reason='Запрещено администратором')
        self.message_user(request, f'{count} записей запрещено')
    ban_selected.short_description = "Запретить доступ"
    
    def unban_selected(self, request, queryset):
        count = queryset.update(is_allowed=True, ban_reason='')
        self.message_user(request, f'{count} записей разрешено')
    unban_selected.short_description = "Разрешить доступ"


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Админка для логов доступа"""
    list_display = ['contractor', 'scanned_at', 'scanned_by', 'is_successful']
    list_filter = ['scanned_at', 'is_successful']
    search_fields = ['contractor__phone_number', 'contractor__first_name', 'contractor__last_name']
    readonly_fields = ['scanned_at', 'qr_code_scanned', 'ip_address']
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contractor')