# backend/access_control/serializers.py
from rest_framework import serializers
from .models import Contractor, AccessList, AccessLog
import re
import imghdr
import logging

logger = logging.getLogger(__name__)


class ContractorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Contractor
        fields = [
            'id', 'first_name', 'last_name', 'patronymic',
            'phone_number', 'photo', 'is_verified', 'qr_code', 
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'qr_code', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def validate_phone_number(self, value):
        """Валидация белорусского номера телефона"""
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        return value


class AccessListSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(
        source='contractor', 
        read_only=True
    )
    contractor_id = serializers.PrimaryKeyRelatedField(
        source='contractor',
        queryset=Contractor.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = AccessList
        fields = [
            'id', 'contractor', 'contractor_id', 'contractor_info',
            'date', 'is_allowed', 'ban_reason', 'created_at'
        ]
        read_only_fields = ['created_at']


class AccessLogSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(
        source='contractor', 
        read_only=True
    )
    scanned_by_username = serializers.CharField(
        source='scanned_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'contractor', 'contractor_info', 'scanned_at',
            'scanned_by', 'scanned_by_username', 
            'qr_code_scanned', 'is_successful'
        ]
        read_only_fields = ['scanned_at']


class PhoneVerificationSerializer(serializers.Serializer):
    """Сериализатор для проверки телефона"""
    phone_number = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Номер телефона в формате +375291234567"
    )
    
    def validate_phone_number(self, value):
        """Валидация номера телефона"""
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        
        # Проверяем код оператора
        operator_code = value[4:6]  # +37529...
        valid_codes = ['29', '33', '44', '25']
        if operator_code not in valid_codes:
            raise serializers.ValidationError(
                f'Неверный код оператора: +375{operator_code}. Допустимые: 29, 33, 44, 25'
            )
        
        return value


class PhotoUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки фото"""
    phone_number = serializers.CharField(max_length=20)
    photo = serializers.ImageField(
        required=True,
        error_messages={
            'required': 'Фото обязательно для загрузки',
            'invalid': 'Неверный формат файла. Загрузите изображение',
            'empty': 'Файл пуст'
        }
    )
    
    def validate_phone_number(self, value):
        """Валидация номера телефона"""
        logger.info(f"Validating phone: {value}")
        
        # Проверяем формат +375XXXXXXXXX
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        
        # Проверяем существует ли пользователь
        try:
            contractor = Contractor.objects.get(phone_number=value)
            logger.info(f"Contractor found: {contractor.id} - {contractor.get_full_name()}")
        except Contractor.DoesNotExist:
            logger.error(f"Contractor with phone {value} not found")
            raise serializers.ValidationError('Пользователь с таким номером не найден')
        
        return value
    
    def validate_photo(self, value):
        """Валидация фото"""
        logger.info(f"Validating photo: {value.name}, size: {value.size} bytes")
        
        # Проверяем размер (максимум 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Файл слишком большой. Максимальный размер 5MB')
        
        # Проверяем формат
        try:
            file_format = imghdr.what(value)
            logger.info(f"File format detected: {file_format}")
        except Exception as e:
            logger.error(f"Error detecting file format: {e}")
            raise serializers.ValidationError('Не удалось определить формат файла')
        
        valid_formats = ['jpeg', 'jpg', 'png', 'gif']
        
        if file_format not in valid_formats:
            raise serializers.ValidationError(
                f'Неверный формат файла: {file_format}. Допустимые: {", ".join(valid_formats)}'
            )
        
        return value


class QRScanSerializer(serializers.Serializer):
    """Сериализатор для сканирования QR"""
    qr_code = serializers.CharField(
        max_length=255,
        required=True,
        help_text="QR код пользователя"
    )


class ToggleAccessSerializer(serializers.Serializer):
    """Сериализатор для переключения доступа"""
    ban_reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Причина запрета"
    )