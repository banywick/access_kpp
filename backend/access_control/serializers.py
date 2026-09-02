# backend/access_control/serializers.py
from rest_framework import serializers
from .models import Contractor, AccessList, AccessLog
import re
import imghdr
import logging

logger = logging.getLogger(__name__)


class ContractorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Contractor
        fields = [
            'id', 'first_name', 'last_name', 'patronymic', 'organization',
            'phone_number', 'photo', 'is_verified', 'qr_code', 
            'access_code', 'role', 'role_display', 'is_active',
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'qr_code', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_role_display(self, obj):
        role_map = {
            'contractor': 'Подрядчик',
            'guard': 'Охранник',
            'admin': 'Администратор'
        }
        return role_map.get(obj.role, obj.role)
    
    def validate_phone_number(self, value):
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        return value
    
    def validate_organization(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Организация обязательна для заполнения')
        return value.strip()


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
            'date', 'is_allowed', 'ban_reason', 
            'valid_from', 'valid_until',  # Добавляем поля
            'created_at'
        ]
        read_only_fields = ['created_at']


# backend/access_control/serializers.py (фрагмент)

class AccessLogSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(
        source='contractor', 
        read_only=True
    )
    scanned_by_info = ContractorSerializer(
        source='scanned_by', 
        read_only=True
    )
    scanned_by_name = serializers.SerializerMethodField()
    access_type_display = serializers.CharField(
        source='get_access_type_display',
        read_only=True
    )
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'contractor', 'contractor_info', 'scanned_at',
            'scanned_by', 'scanned_by_info', 'scanned_by_name',
            'qr_code_scanned', 'access_code_entered', 
            'access_method', 'access_type', 'access_type_display',
            'is_successful', 'ip_address'
        ]
        read_only_fields = ['scanned_at']
    
    def get_scanned_by_name(self, obj):
        """Получение имени охранника, который сканировал"""
        if obj.scanned_by:
            return obj.scanned_by.get_full_name()
        return None


class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    
    def validate_phone_number(self, value):
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        return value


class PhotoUploadSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    photo = serializers.ImageField()
    
    def validate_phone_number(self, value):
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        
        try:
            contractor = Contractor.objects.get(phone_number=value)
            logger.info(f"Contractor found: {contractor.id}")
        except Contractor.DoesNotExist:
            raise serializers.ValidationError('Пользователь с таким номером не найден')
        
        return value
    
    def validate_photo(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Файл слишком большой. Максимальный размер 5MB')
        
        file_format = imghdr.what(value)
        valid_formats = ['jpeg', 'jpg', 'png', 'gif']
        
        if file_format not in valid_formats:
            raise serializers.ValidationError(
                f'Неверный формат файла: {file_format}. Допустимые: {", ".join(valid_formats)}'
            )
        
        return value


class QRScanSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=255, required=False, allow_blank=True)
    access_code = serializers.CharField(max_length=4, required=False, allow_blank=True)
    access_type = serializers.ChoiceField(
        choices=['entry', 'exit'],
        required=True,
        help_text="Тип доступа: entry - въезд, exit - выезд"
    )


class ToggleAccessSerializer(serializers.Serializer):
    ban_reason = serializers.CharField(max_length=255, required=False, allow_blank=True)

