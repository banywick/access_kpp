# backend/access_control/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from datetime import timedelta
import logging
from .models import Contractor, AccessList, AccessLog
from .serializers import (
    ContractorSerializer, 
    AccessListSerializer, 
    AccessLogSerializer,
    ContractorRegisterSerializer,
    LoginSerializer
)

logger = logging.getLogger(__name__)


def get_today_access(contractor):
    """Получить запись доступа на сегодня"""
    today = timezone.now().date()
    return AccessList.objects.filter(
        contractor=contractor,
        date=today
    ).first()


class ContractorViewSet(viewsets.ModelViewSet):
    """ViewSet для управления подрядчиками"""
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по организации
        organization = self.request.query_params.get('organization')
        if organization:
            queryset = queryset.filter(organization__icontains=organization)
        
        # Фильтр по статусу верификации
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        # Поиск по имени или телефону
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(phone_number__icontains=search) |
                models.Q(organization__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def access_info(self, request, pk=None):
        """Получить информацию о доступе подрядчика"""
        contractor = self.get_object()
        today_access = get_today_access(contractor)
        
        if not today_access:
            return Response({
                'contractor': ContractorSerializer(contractor).data,
                'has_access': False,
                'message': 'Нет доступа на сегодня'
            })
        
        return Response({
            'contractor': ContractorSerializer(contractor).data,
            'has_access': today_access.is_allowed,
            'is_on_territory': today_access.is_on_territory,
            'status': today_access.get_status_display(),
            'valid_until': today_access.valid_until,
            'last_entry': today_access.last_entry_time,
            'last_exit': today_access.last_exit_time
        })
    
    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        """Установить статус доступа"""
        contractor = self.get_object()
        status_type = request.data.get('status_type')
        
        if status_type not in ['on_territory', 'off_territory', 'temporary', 'banned']:
            return Response({
                'error': 'Неверный тип статуса. Доступны: on_territory, off_territory, temporary, banned'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        today_access = get_today_access(contractor)
        
        if not today_access:
            return Response({
                'error': 'У подрядчика нет доступа на сегодня'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if status_type == 'on_territory':
            today_access.set_on_territory(updated_by=request.user)
        elif status_type == 'off_territory':
            today_access.set_off_territory(updated_by=request.user)
        elif status_type == 'temporary':
            days = int(request.data.get('days', 1))
            today_access.set_temporary(days=days, updated_by=request.user)
        elif status_type == 'banned':
            reason = request.data.get('reason', 'Блокировка')
            today_access.set_banned(reason=reason, updated_by=request.user)
        
        return Response({
            'success': True,
            'message': f'Статус изменен на {status_type}',
            'contractor': ContractorSerializer(contractor).data,
            'access': {
                'status': today_access.get_status_display(),
                'is_on_territory': today_access.is_on_territory,
                'valid_until': today_access.valid_until
            }
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Получить историю доступа подрядчика"""
        contractor = self.get_object()
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        logs = AccessLog.objects.filter(
            contractor=contractor,
            scanned_at__date__gte=start_date
        ).order_by('-scanned_at')
        
        access_history = AccessList.objects.filter(
            contractor=contractor,
            date__gte=start_date
        ).order_by('-date')
        
        return Response({
            'contractor': ContractorSerializer(contractor).data,
            'logs': [
                {
                    'time': log.scanned_at,
                    'type': log.get_access_type_display(),
                    'method': log.get_access_method_display(),
                    'success': log.is_successful
                }
                for log in logs[:100]
            ],
            'access_history': [
                {
                    'date': access.date,
                    'status': access.get_status_display(),
                    'is_on_territory': access.is_on_territory,
                    'entry_time': access.last_entry_time,
                    'exit_time': access.last_exit_time
                }
                for access in access_history
            ]
        })


class AccessListViewSet(viewsets.ModelViewSet):
    """ViewSet для управления списками доступа"""
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по дате
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Фильтр по подрядчику
        contractor_id = self.request.query_params.get('contractor_id')
        if contractor_id:
            queryset = queryset.filter(contractor_id=contractor_id)
        
        # Фильтр по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтр по нахождению на территории
        is_on_territory = self.request.query_params.get('is_on_territory')
        if is_on_territory is not None:
            queryset = queryset.filter(is_on_territory=is_on_territory.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_territory(self, request, pk=None):
        """Переключить статус нахождения на территории"""
        access = self.get_object()
        
        if access.is_on_territory:
            access.set_off_territory(updated_by=request.user)
            message = f"{access.contractor} - покинул территорию"
        else:
            access.set_on_territory(updated_by=request.user)
            message = f"{access.contractor} - на территории"
        
        return Response({
            'success': True,
            'message': message,
            'is_on_territory': access.is_on_territory,
            'status': access.get_status_display()
        })


class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра логов доступа (только чтение)"""
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по подрядчику
        contractor_id = self.request.query_params.get('contractor_id')
        if contractor_id:
            queryset = queryset.filter(contractor_id=contractor_id)
        
        # Фильтр по дате
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scanned_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scanned_at__date__lte=date_to)
        
        # Фильтр по успешности
        is_successful = self.request.query_params.get('is_successful')
        if is_successful is not None:
            queryset = queryset.filter(is_successful=is_successful.lower() == 'true')
        
        return queryset.order_by('-scanned_at')


class LoginView(APIView):
    """Вход в систему по номеру телефона"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone:
            return Response({
                'success': False,
                'error': 'Телефон обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contractor = Contractor.objects.get(phone_number=phone)
            
            if not contractor.is_active:
                return Response({
                    'success': False,
                    'error': 'Доступ запрещен',
                    'reason': 'Аккаунт деактивирован'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if contractor.role in ['guard', 'admin']:
                if not contractor.has_usable_password():
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': 'Для входа требуется пароль. Обратитесь к администратору.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if not password:
                    return Response({
                        'success': False,
                        'error': 'Требуется пароль',
                        'requires_password': True
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                if not contractor.check_password(password):
                    return Response({
                        'success': False,
                        'error': 'Неверный пароль',
                        'requires_password': True
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                if contractor.role == 'admin' and not contractor.is_superuser:
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': 'Недостаточно прав для входа'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if contractor.role == 'guard' and not contractor.is_staff:
                    contractor.is_staff = True
                    contractor.save()
                
                serializer = ContractorSerializer(contractor)
                return Response({
                    'success': True,
                    'user_data': serializer.data,
                    'role': contractor.role,
                    'message': 'Вход выполнен успешно',
                    'requires_verification': False
                })
            
            else:
                today_access = get_today_access(contractor)
                
                if not today_access:
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': 'Вы не найдены в списке доступа на сегодня'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if not today_access.is_allowed:
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': today_access.ban_reason or 'Доступ временно ограничен'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                serializer = ContractorSerializer(contractor)
                return Response({
                    'success': True,
                    'user_data': serializer.data,
                    'role': contractor.role,
                    'message': 'Вход выполнен успешно',
                    'requires_verification': not contractor.is_verified
                })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Пользователь с таким номером не найден'
            }, status=status.HTTP_404_NOT_FOUND)



class ContractorRegisterView(APIView):
    """Регистрация нового подрядчика"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ContractorRegisterSerializer(data=request.data)
        if serializer.is_valid():
            contractor = serializer.save()
            
            # Генерируем QR код и код доступа
            contractor.generate_access_code()
            contractor.generate_qr_code()
            
            return Response({
                'success': True,
                'message': 'Регистрация успешна',
                'contractor': ContractorSerializer(contractor).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractorPhotoView(APIView):
    """Загрузка фото подрядчика"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        contractor = request.user
        photo = request.FILES.get('photo')
        
        if not photo:
            return Response({
                'success': False,
                'message': 'Фото не загружено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        contractor.photo = photo
        contractor.save()
        
        return Response({
            'success': True,
            'message': 'Фото загружено',
            'photo_url': contractor.photo.url if contractor.photo else None
        })


class ContractorVerifyView(APIView):
    """Верификация подрядчика"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        contractor = request.user
        contractor.is_verified = True
        contractor.save()
        
        return Response({
            'success': True,
            'message': 'Пользователь верифицирован',
            'is_verified': contractor.is_verified
        })


class QRScanView(APIView):
    """Сканирование QR кода"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        qr_code = request.data.get('qr_code')
        access_type = request.data.get('access_type', 'entry')
        
        logger.info(f"QR Scan: qr_code={qr_code}, type={access_type}")
        
        if not qr_code:
            return Response({
                'success': False,
                'message': 'QR код не передан'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contractor = Contractor.objects.get(qr_code=qr_code)
            
            # Проверяем доступ
            today_access = get_today_access(contractor)
            
            if not today_access:
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Пользователь не найден в списке доступа на сегодня',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not today_access.is_allowed:
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': today_access.ban_reason or 'Доступ временно ограничен',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not today_access.is_valid():
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Срок действия доступа истек',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Обновляем статус
            with transaction.atomic():
                if access_type == 'entry':
                    today_access.is_on_territory = True
                    today_access.last_entry_time = timezone.now()
                    today_access.status = AccessList.AccessStatus.ON_TERRITORY
                    today_access.save()
                    message = f"✅ {contractor.get_full_name()} - въехал на территорию"
                else:
                    today_access.is_on_territory = False
                    today_access.last_exit_time = timezone.now()
                    today_access.status = AccessList.AccessStatus.OFF_TERRITORY
                    today_access.save()
                    message = f"🚫 {contractor.get_full_name()} - покинул территорию"
            
            # Логируем
            AccessLog.objects.create(
                contractor=contractor,
                qr_code_scanned=qr_code,
                access_method='qr',
                access_type=access_type,
                is_successful=True,
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'message': message,
                'contractor': {
                    'id': contractor.id,
                    'name': contractor.get_full_name(),
                    'phone': contractor.phone_number,
                    'organization': contractor.organization,
                },
                'is_on_territory': today_access.is_on_territory,
                'access_status': today_access.get_status_display(),
                'valid_until': today_access.valid_until
            })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'QR код не действителен',
                'reason': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in QRScanView: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ExcelUploadView(APIView):
    """Загрузка Excel файла с подрядчиками"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        # Здесь должна быть логика импорта Excel
        # Используем функционал из admin.py
        return Response({
            'success': True,
            'message': 'Импорт Excel выполнен'
        })


class GetQRView(APIView):
    """Получить QR код для текущего пользователя"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        contractor = request.user
        if not contractor.qr_code:
            contractor.generate_qr_code()
        
        return Response({
            'success': True,
            'qr_code': contractor.qr_code,
            'access_code': contractor.access_code
        })


# ========== Основные API Views ==========

class GetContractorInfoView(APIView):
    """Получение информации о подрядчике по QR-коду или коду доступа"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        qr_code = request.data.get('qr_code')
        access_code = request.data.get('access_code')
        access_type = request.data.get('access_type', 'entry')
        
        logger.info(f"Get contractor info: qr_code={qr_code}, access_code={access_code}, type={access_type}")
        
        if not qr_code and not access_code:
            return Response({
                'success': False,
                'message': 'Необходимо передать QR-код или код доступа'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if qr_code:
                contractor = Contractor.objects.get(qr_code=qr_code)
            else:
                contractor = Contractor.objects.get(access_code=access_code)
            
            if not contractor.is_verified:
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Пользователь не прошел верификацию',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            today_access = get_today_access(contractor)
            
            if not today_access:
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Пользователь не найден в списке доступа на сегодня',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not today_access.is_allowed:
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': today_access.ban_reason or 'Доступ временно ограничен',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not today_access.is_valid():
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Срок действия доступа истек',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Обновляем статус на территории
            with transaction.atomic():
                if access_type == 'entry':
                    today_access.is_on_territory = True
                    today_access.last_entry_time = timezone.now()
                    today_access.status = AccessList.AccessStatus.ON_TERRITORY
                    today_access.save()
                    logger.info(f"✅ {contractor.phone_number} ВЪЕЗД - теперь на территории")
                else:
                    today_access.is_on_territory = False
                    today_access.last_exit_time = timezone.now()
                    today_access.status = AccessList.AccessStatus.OFF_TERRITORY
                    today_access.save()
                    logger.info(f"🚫 {contractor.phone_number} ВЫЕЗД - покинул территорию")
            
            # Создаем запись в логе
            AccessLog.objects.create(
                contractor=contractor,
                scanned_by=request.user if request.user.is_authenticated else None,
                qr_code_scanned=qr_code,
                access_code_entered=access_code,
                access_method='qr' if qr_code else 'code',
                access_type=access_type,
                is_successful=True,
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'message': 'Пользователь найден',
                'contractor': ContractorSerializer(contractor).data,
                'is_on_territory': today_access.is_on_territory,
                'valid_until': today_access.valid_until,
                'access_status': today_access.get_status_display(),
                'last_entry_time': today_access.last_entry_time,
                'last_exit_time': today_access.last_exit_time,
            })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in GetContractorInfoView: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UpdateContractorStatusView(APIView):
    """Обновление статуса подрядчика (вручную)"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, contractor_id):
        try:
            contractor = get_object_or_404(Contractor, id=contractor_id)
            today_access = get_today_access(contractor)
            
            if not today_access:
                return Response({
                    'success': False,
                    'message': 'Пользователь не найден в списке доступа на сегодня'
                }, status=status.HTTP_404_NOT_FOUND)
            
            status_type = request.data.get('status_type')
            
            if status_type == 'on_territory':
                today_access.set_on_territory(updated_by=request.user)
                message = f'✅ {contractor} - установлен статус "На территории"'
            elif status_type == 'off_territory':
                today_access.set_off_territory(updated_by=request.user)
                message = f'🚫 {contractor} - установлен статус "Не на территории"'
            else:
                return Response({
                    'success': False,
                    'message': 'Неверный тип статуса. Используйте "on_territory" или "off_territory"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(message)
            
            return Response({
                'success': True,
                'message': message,
                'contractor': ContractorSerializer(contractor).data,
                'is_on_territory': today_access.is_on_territory,
                'status': today_access.get_status_display()
            })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in UpdateContractorStatusView: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetTerritoryStatsView(APIView):
    """Получить статистику по нахождению на территории"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        today = timezone.now().date()
        
        on_territory = AccessList.objects.filter(
            date=today,
            is_on_territory=True,
            is_allowed=True
        ).count()
        
        off_territory = AccessList.objects.filter(
            date=today,
            is_on_territory=False,
            is_allowed=True
        ).count()
        
        total = AccessList.objects.filter(date=today).count()
        
        on_territory_list = AccessList.objects.filter(
            date=today,
            is_on_territory=True,
            is_allowed=True
        ).select_related('contractor')
        
        data = {
            'total': total,
            'on_territory': on_territory,
            'off_territory': off_territory,
            'on_territory_percent': round(on_territory / total * 100, 1) if total > 0 else 0,
            'on_territory_list': [
                {
                    'id': item.contractor.id,
                    'name': item.contractor.get_full_name(),
                    'phone': item.contractor.phone_number,
                    'organization': item.contractor.organization,
                    'entry_time': item.last_entry_time,
                    'status': item.get_status_display()
                }
                for item in on_territory_list
            ]
        }
        
        return Response(data)


class GetContractorAccessHistoryView(APIView):
    """Получить историю доступа подрядчика"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, contractor_id):
        try:
            contractor = get_object_or_404(Contractor, id=contractor_id)
            
            days = request.query_params.get('days', 30)
            try:
                days = int(days)
            except ValueError:
                days = 30
            
            start_date = timezone.now().date() - timedelta(days=days)
            
            logs = AccessLog.objects.filter(
                contractor=contractor,
                scanned_at__date__gte=start_date
            ).order_by('-scanned_at')
            
            access_list = AccessList.objects.filter(
                contractor=contractor,
                date__gte=start_date
            ).order_by('-date')
            
            return Response({
                'success': True,
                'contractor': ContractorSerializer(contractor).data,
                'logs': [
                    {
                        'time': log.scanned_at,
                        'type': log.get_access_type_display(),
                        'method': log.get_access_method_display(),
                        'success': log.is_successful,
                        'ip': log.ip_address
                    }
                    for log in logs[:100]
                ],
                'access_history': [
                    {
                        'date': access.date,
                        'status': access.get_status_display(),
                        'is_on_territory': access.is_on_territory,
                        'entry_time': access.last_entry_time,
                        'exit_time': access.last_exit_time
                    }
                    for access in access_list
                ]
            })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in GetContractorAccessHistoryView: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)