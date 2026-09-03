# backend/access_control/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Contractor, AccessList, AccessLog


class ContractorSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Contractor"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Contractor
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'patronymic',
            'organization', 'photo', 'role', 'role_display', 'is_verified',
            'is_active', 'qr_code', 'access_code', 'full_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['qr_code', 'access_code', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_role_display(self, obj):
        return obj.get_role_display()


class ContractorRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового подрядчика"""
    password = serializers.CharField(write_only=True, min_length=6, required=False, allow_blank=True)
    
    class Meta:
        model = Contractor
        fields = [
            'phone_number', 'first_name', 'last_name', 'patronymic',
            'organization', 'password'
        ]
    
    def validate_phone_number(self, value):
        """Проверка уникальности номера телефона"""
        if Contractor.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Пользователь с таким номером телефона уже существует')
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        contractor = Contractor.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            patronymic=validated_data.get('patronymic', ''),
            organization=validated_data.get('organization', ''),
            is_active=True,
            is_verified=False,
            role='contractor'
        )
        return contractor


class LoginSerializer(serializers.Serializer):
    """Сериализатор для авторизации"""
    phone_number = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        if phone_number and password:
            user = authenticate(phone_number=phone_number, password=password)
            if not user:
                raise serializers.ValidationError('Неверный номер телефона или пароль')
            if not user.is_active:
                raise serializers.ValidationError('Учетная запись деактивирована')
        else:
            raise serializers.ValidationError('Необходимо указать номер телефона и пароль')
        
        data['user'] = user
        return data


class AccessListSerializer(serializers.ModelSerializer):
    """Сериализатор для модели AccessList"""
    contractor_name = serializers.SerializerMethodField()
    contractor_phone = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessList
        fields = [
            'id', 'contractor', 'contractor_name', 'contractor_phone',
            'date', 'is_allowed', 'status', 'status_display',
            'is_on_territory', 'ban_reason', 'valid_from', 'valid_until',
            'last_entry_time', 'last_exit_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_entry_time', 'last_exit_time']
    
    def get_contractor_name(self, obj):
        return obj.contractor.get_full_name()
    
    def get_contractor_phone(self, obj):
        return obj.contractor.phone_number
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class AccessLogSerializer(serializers.ModelSerializer):
    """Сериализатор для модели AccessLog"""
    contractor_name = serializers.SerializerMethodField()
    contractor_phone = serializers.SerializerMethodField()
    access_type_display = serializers.SerializerMethodField()
    access_method_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'contractor', 'contractor_name', 'contractor_phone',
            'scanned_at', 'scanned_by', 'qr_code_scanned',
            'access_code_entered', 'access_method', 'access_method_display',
            'access_type', 'access_type_display', 'is_successful',
            'ip_address'
        ]
        read_only_fields = '__all__'
    
    def get_contractor_name(self, obj):
        return obj.contractor.get_full_name()
    
    def get_contractor_phone(self, obj):
        return obj.contractor.phone_number
    
    def get_access_type_display(self, obj):
        return obj.get_access_type_display()
    
    def get_access_method_display(self, obj):
        return obj.get_access_method_display()


class AccessListCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания записи в списке доступа"""
    
    class Meta:
        model = AccessList
        fields = [
            'contractor', 'date', 'is_allowed', 'status',
            'ban_reason', 'valid_from', 'valid_until'
        ]
    
    def validate(self, data):
        """Проверка что дата не в прошлом"""
        if data.get('date') and data['date'] < timezone.now().date():
            raise serializers.ValidationError('Дата не может быть в прошлом')
        return data


class AccessListUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления записи в списке доступа"""
    
    class Meta:
        model = AccessList
        fields = [
            'is_allowed', 'status', 'ban_reason',
            'valid_from', 'valid_until', 'is_on_territory'
        ]
    
    def validate(self, data):
        """Проверка что valid_from не позже valid_until"""
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        
        if valid_from and valid_until and valid_from > valid_until:
            raise serializers.ValidationError('Дата начала не может быть позже даты окончания')
        return data


class ContractorAccessInfoSerializer(serializers.Serializer):
    """Сериализатор для информации о доступе подрядчика"""
    contractor = ContractorSerializer()
    has_access = serializers.BooleanField()
    is_on_territory = serializers.BooleanField()
    status = serializers.CharField()
    valid_until = serializers.DateField()
    last_entry = serializers.DateTimeField(allow_null=True)
    last_exit = serializers.DateTimeField(allow_null=True)


class TerritoryStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики по территории"""
    total = serializers.IntegerField()
    on_territory = serializers.IntegerField()
    off_territory = serializers.IntegerField()
    on_territory_percent = serializers.FloatField()
    on_territory_list = serializers.ListField(
        child=serializers.DictField()
    )


class QRScanSerializer(serializers.Serializer):
    """Сериализатор для сканирования QR кода"""
    qr_code = serializers.CharField()
    access_type = serializers.ChoiceField(choices=['entry', 'exit'], default='entry')


class ContractorPhotoSerializer(serializers.Serializer):
    """Сериализатор для загрузки фото"""
    photo = serializers.ImageField()