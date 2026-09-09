# backend/access_control/serializers.py
from rest_framework import serializers
from .models import Contractor, AccessList, AccessLog


class ContractorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Contractor
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'patronymic',
            'organization', 'photo', 'photo_url', 'role', 'is_verified', 'is_active',
            'qr_code', 'access_code', 'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['qr_code', 'access_code', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None


class AccessListSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(source='contractor', read_only=True)
    
    class Meta:
        model = AccessList
        fields = [
            'id', 'contractor', 'contractor_info', 'is_allowed',
            'status', 'is_on_territory', 'last_entry_time', 'last_exit_time',
            'ban_reason', 'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]


class AccessLogSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(source='contractor', read_only=True)
    scanned_by_info = ContractorSerializer(source='scanned_by', read_only=True)
    scanned_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'contractor', 'contractor_info', 'scanned_at', 'scanned_by',
            'scanned_by_info', 'scanned_by_name', 'qr_code_scanned', 'access_code_entered',
            'access_method', 'access_type', 'is_successful', 'ip_address'
        ]
    
    def get_scanned_by_name(self, obj):
        if obj.scanned_by:
            return obj.scanned_by.get_full_name()
        return None


class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    
    def validate_phone_number(self, value):
        import re
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
        import re
        pattern = r'^\+375(29|33|44|25)\d{7}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Номер должен быть в формате +375291234567 (коды: 29, 33, 44, 25)'
            )
        
        try:
            contractor = Contractor.objects.get(phone_number=value)
        except Contractor.DoesNotExist:
            raise serializers.ValidationError('Пользователь с таким номером не найден')
        
        return value
    
    def validate_photo(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Файл слишком большой. Максимальный размер 5MB')
        
        import imghdr
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