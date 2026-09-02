# backend/access_control/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone
import re
import hashlib
import json
import random
import os


class ContractorManager(BaseUserManager):
    """Кастомный менеджер для модели Contractor"""
    
    def create_user(self, phone_number, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not phone_number:
            raise ValueError('Номер телефона обязателен')
        
        phone_number = self.normalize_phone_number(phone_number)
        
        user = self.model(
            phone_number=phone_number,
            first_name=extra_fields.get('first_name', ''),
            last_name=extra_fields.get('last_name', ''),
            patronymic=extra_fields.get('patronymic', ''),
            role=extra_fields.get('role', 'contractor'),
            is_active=extra_fields.get('is_active', True),
            is_staff=extra_fields.get('is_staff', False),
            is_superuser=extra_fields.get('is_superuser', False),
            is_verified=extra_fields.get('is_verified', False),
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        
        if not password:
            raise ValueError('Суперпользователь должен иметь пароль')
        
        return self.create_user(phone_number, password, **extra_fields)
    
    def normalize_phone_number(self, phone_number):
        """Нормализация белорусского номера телефона"""
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        if len(cleaned) < 9:
            raise ValueError('Слишком короткий номер телефона')
        
        if cleaned.startswith('8') and len(cleaned) == 11:
            cleaned = '375' + cleaned[1:]
        elif cleaned.startswith('375') and len(cleaned) == 12:
            pass
        elif cleaned.startswith(('29', '33', '44', '25')) and len(cleaned) == 9:
            cleaned = '375' + cleaned
        elif cleaned.startswith(('029', '033', '044', '025')) and len(cleaned) == 10:
            cleaned = '375' + cleaned[1:]
        else:
            raise ValueError(f'Неверный формат номера: {phone_number}')
        
        if len(cleaned) >= 12:
            operator_code = cleaned[3:5]
            valid_codes = ['29', '33', '44', '25']
            if operator_code not in valid_codes:
                raise ValueError(f'Неверный код оператора: {operator_code}. Допустимые: 29, 33, 44, 25')
        
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned


def upload_to_photo(instance, filename):
    """Генерация пути для сохранения фото"""
    date_path = timezone.now().strftime('%Y/%m/%d')
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    phone_clean = instance.phone_number.replace('+', '').replace(' ', '')
    new_filename = f"{phone_clean}_{int(timezone.now().timestamp())}.{ext}"
    return os.path.join('photos', date_path, new_filename)


class Contractor(AbstractUser):
    """Модель подрядчика - замена стандартному User"""
    
    class Role(models.TextChoices):
        CONTRACTOR = 'contractor', 'Подрядчик'
        GUARD = 'guard', 'Охранник'
        ADMIN = 'admin', 'Администратор'
    
    username = None
    
    phone_number = models.CharField(
        max_length=20, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+375(29|33|44|25)\d{7}$',
                message='Номер телефона должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        ],
        verbose_name="Номер телефона"
    )
    patronymic = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Отчество"
    )
    photo = models.ImageField(
        upload_to=upload_to_photo,
        blank=True, 
        null=True,
        verbose_name="Фото",
        max_length=500
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRACTOR,
        verbose_name="Роль"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Верифицирован"
    )
    qr_code = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        unique=True,
        verbose_name="QR код"
    )
    access_code = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Код доступа (4 цифры)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='contractor_set',
        related_query_name='contractor'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='contractor_set',
        related_query_name='contractor'
    )
    
    objects = ContractorManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic or ''}".strip()
    
    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic or ''}".strip()
    
    def get_short_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def generate_qr_code(self):
        """Генерация QR кода"""
        data = {
            'id': self.id,
            'phone': self.phone_number,
            'name': self.get_full_name(),
            'code': self.access_code
        }
        self.qr_code = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:32]
        self.save(update_fields=['qr_code'])
        return self.qr_code
    
    def generate_access_code(self):
        """Генерация уникального 4-значного кода"""
        while True:
            code = str(random.randint(1000, 9999))
            if not Contractor.objects.filter(access_code=code).exists():
                self.access_code = code
                self.save(update_fields=['access_code'])
                return code
    
    def has_usable_password(self):
        """Проверка наличия пароля"""
        return self.password is not None and self.password != ''


class AccessList(models.Model):
    """Список доступа на день"""
    contractor = models.ForeignKey(
        Contractor, 
        on_delete=models.CASCADE,
        related_name='access_entries',
        verbose_name="Подрядчик"
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Дата"
    )
    is_allowed = models.BooleanField(
        default=True,
        verbose_name="Доступ разрешен"
    )
    ban_reason = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Причина запрета"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Список доступа"
        verbose_name_plural = "Списки доступа"
        unique_together = ['date', 'contractor']
        ordering = ['-date', 'contractor']
    
    def __str__(self):
        status = "✅" if self.is_allowed else "❌"
        return f"{self.date} - {self.contractor} {status}"


class AccessLog(models.Model):
    """Лог сканирования QR кодов и ввода кодов"""
    contractor = models.ForeignKey(
        Contractor, 
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name="Подрядчик"
    )
    scanned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время сканирования"
    )
    scanned_by = models.ForeignKey(
        Contractor,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='scanned_logs',
        verbose_name="Кто сканировал"
    )
    qr_code_scanned = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="QR код"
    )
    access_code_entered = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        verbose_name="Введенный код"
    )
    access_method = models.CharField(
        max_length=20,
        choices=[
            ('qr', 'QR-код'),
            ('code', 'Ручной ввод кода'),
        ],
        default='qr',
        verbose_name="Способ доступа"
    )
    is_successful = models.BooleanField(
        default=True,
        verbose_name="Успешно"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="IP адрес"
    )
    
    class Meta:
        verbose_name = "Лог доступа"
        verbose_name_plural = "Логи доступа"
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"{self.scanned_at} - {self.contractor} ({self.get_access_method_display()})"