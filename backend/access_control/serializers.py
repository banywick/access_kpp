# backend/access_control/serializers.py

from rest_framework import serializers
from .models import Contractor, AccessList, AccessLog


class ContractorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Contractor
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'patronymic',
            'organization', 'photo', 'role', 'is_verified', 'is_active',
            'qr_code', 'access_code', 'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['qr_code', 'access_code', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class AccessListSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(source='contractor', read_only=True)
    
    class Meta:
        model = AccessList
        fields = [
            'id', 'contractor', 'contractor_info', 'date', 'is_allowed',
            'status', 'is_on_territory', 'last_entry_time', 'last_exit_time',
            'ban_reason', 'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]


class AccessLogSerializer(serializers.ModelSerializer):
    contractor_info = ContractorSerializer(source='contractor', read_only=True)
    scanned_by_info = ContractorSerializer(source='scanned_by', read_only=True)
    
    class Meta:
        model = AccessLog
        fields = [
            'id', 'contractor', 'contractor_info', 'scanned_at', 'scanned_by',
            'scanned_by_info', 'qr_code_scanned', 'access_code_entered',
            'access_method', 'access_type', 'is_successful', 'ip_address'
        ]