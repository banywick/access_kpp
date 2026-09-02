# backend/access_control/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Contractor, AccessList, AccessLog
from .serializers import (
    ContractorSerializer, 
    AccessListSerializer, 
    AccessLogSerializer,
    PhoneVerificationSerializer,
    PhotoUploadSerializer,
    QRScanSerializer,
    ToggleAccessSerializer
)
from .utils import verify_face, process_excel_file, get_today_access, generate_qr_code_image
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ContractorViewSet(viewsets.ModelViewSet):
    """CRUD для подрядчиков"""
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        phone = self.request.query_params.get('phone')
        if phone:
            queryset = queryset.filter(phone_number__icontains=phone)
        verified = self.request.query_params.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif verified == 'false':
            queryset = queryset.filter(is_verified=False)
        return queryset
    
    @action(detail=True, methods=['post'])
    def regenerate_qr(self, request, pk=None):
        contractor = self.get_object()
        contractor.generate_qr_code()
        qr_data = {
            'id': contractor.id,
            'phone': contractor.phone_number,
            'name': contractor.get_full_name()
        }
        qr_image = generate_qr_code_image(qr_data)
        return Response({
            'qr_code': contractor.qr_code,
            'qr_image': qr_image
        })
    
    @action(detail=True, methods=['post'])
    def regenerate_code(self, request, pk=None):
        contractor = self.get_object()
        if not contractor.is_verified:
            return Response({
                'error': 'Пользователь не верифицирован'
            }, status=status.HTTP_400_BAD_REQUEST)
        new_code = contractor.generate_access_code()
        return Response({
            'success': True,
            'access_code': new_code,
            'message': 'Код доступа успешно обновлен'
        })


class AccessListViewSet(viewsets.ModelViewSet):
    """CRUD для списков доступа"""
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                pass
        status_filter = self.request.query_params.get('status')
        if status_filter == 'allowed':
            queryset = queryset.filter(is_allowed=True)
        elif status_filter == 'banned':
            queryset = queryset.filter(is_allowed=False)
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_access(self, request, pk=None):
        access_entry = self.get_object()
        serializer = ToggleAccessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        access_entry.is_allowed = not access_entry.is_allowed
        if not access_entry.is_allowed:
            ban_reason = serializer.validated_data.get('ban_reason', 'Доступ запрещен администратором')
            access_entry.ban_reason = ban_reason
        else:
            access_entry.ban_reason = None
        access_entry.save()
        return Response(self.get_serializer(access_entry).data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        queryset = self.get_queryset().filter(date=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AccessLogViewSet(viewsets.ModelViewSet):
    """CRUD для логов доступа"""
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                queryset = queryset.filter(scanned_at__date=date_obj)
            except ValueError:
                pass
        contractor_id = self.request.query_params.get('contractor')
        if contractor_id:
            queryset = queryset.filter(contractor_id=contractor_id)
        successful = self.request.query_params.get('successful')
        if successful == 'true':
            queryset = queryset.filter(is_successful=True)
        elif successful == 'false':
            queryset = queryset.filter(is_successful=False)
        return queryset


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


class GetContractorInfoView(APIView):
    """Получение информации о подрядчике по QR-коду или коду доступа"""
    permission_classes = [permissions.AllowAny]  # Разрешаем без аутентификации
    
    def post(self, request):
        qr_code = request.data.get('qr_code')
        access_code = request.data.get('access_code')
        
        logger.info(f"Get contractor info: qr_code={qr_code}, access_code={access_code}")
        
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
            
            is_on_territory = self.check_if_on_territory(contractor)
            logger.info(f"Status for {contractor.phone_number}: on_territory={is_on_territory}")
            
            return Response({
                'success': True,
                'message': 'Пользователь найден',
                'contractor': ContractorSerializer(contractor).data,
                'is_on_territory': is_on_territory,
                'valid_until': today_access.valid_until
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
    
    def check_if_on_territory(self, contractor):
        last_log = AccessLog.objects.filter(
            contractor=contractor,
            is_successful=True
        ).order_by('-scanned_at').first()
        if not last_log:
            return False
        return last_log.access_type == 'entry'

# backend/access_control/views.py (фрагмент QRScanView)

# backend/access_control/views.py (фрагмент QRScanView)

class QRScanView(APIView):
    """
    Сканирование QR кода или ввод кода доступа
    POST /api/scan-qr/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        qr_code = request.data.get('qr_code')
        access_code = request.data.get('access_code')
        access_type = request.data.get('access_type', 'entry')
        guard_phone = request.data.get('guard_phone')  # Телефон охранника
        guard_name = request.data.get('guard_name')    # Имя охранника
        
        logger.info(f"Scan request: qr_code={qr_code}, access_code={access_code}, type={access_type}")
        logger.info(f"Guard info: phone={guard_phone}, name={guard_name}")
        
        if not qr_code and not access_code:
            return Response({
                'success': False,
                'message': 'Необходимо передать QR-код или код доступа'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if access_type not in ['entry', 'exit']:
            return Response({
                'success': False,
                'message': 'Неверный тип доступа. Допустимые: entry, exit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if qr_code:
                contractor = Contractor.objects.get(qr_code=qr_code)
                access_method = 'qr'
                logger.info(f"Found by QR: {contractor.phone_number}")
            else:
                contractor = Contractor.objects.get(access_code=access_code)
                access_method = 'code'
                logger.info(f"Found by access code: {contractor.phone_number}")
            
            if not contractor.is_verified:
                logger.warning(f"Contractor not verified: {contractor.phone_number}")
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
            
            is_on_territory = self.check_if_on_territory(contractor)
            logger.info(f"Current status for {contractor.phone_number}: on_territory={is_on_territory}")
            
            if access_type == 'entry' and is_on_territory:
                return Response({
                    'success': False,
                    'message': 'Ошибка: пользователь уже на территории',
                    'reason': 'Пользователь уже находится на территории',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if access_type == 'exit' and not is_on_territory:
                return Response({
                    'success': False,
                    'message': 'Ошибка: пользователь не на территории',
                    'reason': 'Пользователь не находится на территории',
                    'contractor': ContractorSerializer(contractor).data,
                    'is_on_territory': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ищем охранника по телефону
            scanned_by = None
            if guard_phone:
                try:
                    scanned_by = Contractor.objects.get(phone_number=guard_phone)
                    logger.info(f"Guard found: {scanned_by.phone_number} - {scanned_by.get_full_name()}")
                except Contractor.DoesNotExist:
                    logger.warning(f"Guard not found: {guard_phone}")
            
            access_log = AccessLog.objects.create(
                contractor=contractor,
                qr_code_scanned=qr_code if qr_code else None,
                access_code_entered=access_code if access_code else None,
                access_method=access_method,
                access_type=access_type,
                ip_address=self.get_client_ip(request),
                scanned_by=scanned_by,
                is_successful=True
            )
            
            logger.info(f"Access granted: {contractor.phone_number}, type: {access_type}, scanned_by: {scanned_by}")
            
            new_status = (access_type == 'entry')
            
            scanned_by_data = None
            scanned_by_name = None
            if scanned_by:
                scanned_by_data = ContractorSerializer(scanned_by).data
                scanned_by_name = scanned_by.get_full_name()
            
            return Response({
                'success': True,
                'message': f'{"✅ Въезд" if access_type == "entry" else "✅ Выезд"} разрешен',
                'contractor': ContractorSerializer(contractor).data,
                'access_time': access_log.scanned_at,
                'access_method': access_method,
                'access_type': access_type,
                'is_on_territory': new_status,
                'scanned_by': scanned_by_data,
                'scanned_by_name': scanned_by_name,
                'valid_until': today_access.valid_until
            })
            
        except Contractor.DoesNotExist:
            logger.warning(f"Contractor not found for: {qr_code or access_code}")
            return Response({
                'success': False,
                'message': 'Недействительный QR-код или код доступа'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in QRScanView: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def check_if_on_territory(self, contractor):
        last_log = AccessLog.objects.filter(
            contractor=contractor,
            is_successful=True
        ).order_by('-scanned_at').first()
        if not last_log:
            return False
        return last_log.access_type == 'entry'
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContractorRegisterView(APIView):
    """Шаг 1: Регистрация по телефону"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone_number']
        
        try:
            contractor = Contractor.objects.get(phone_number=phone)
            today_access = get_today_access(contractor)
            
            if not today_access:
                return Response({
                    'success': False,
                    'error': 'Доступ запрещен',
                    'reason': 'Пользователь не найден в списке доступа на сегодня'
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
                'needs_photo': not contractor.photo,
                'is_verified': contractor.is_verified,
                'has_qr': bool(contractor.qr_code)
            })
            
        except Contractor.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Пользователь с таким номером не найден'
            }, status=status.HTTP_404_NOT_FOUND)


class ContractorPhotoView(APIView):
    """Шаг 2: Загрузка фото"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone_number']
        photo = serializer.validated_data['photo']
        contractor = get_object_or_404(Contractor, phone_number=phone)
        
        contractor.photo = photo
        contractor.save()
        
        return Response({
            'success': True,
            'message': 'Фото загружено',
            'needs_verification': not contractor.is_verified,
            'photo_url': contractor.photo.url if contractor.photo else None
        })


class ContractorVerifyView(APIView):
    """Шаг 3: Проверка фото и генерация QR"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone:
            return Response(
                {'error': 'Телефон обязателен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contractor = get_object_or_404(Contractor, phone_number=phone)
        
        if not contractor.photo:
            return Response({
                'success': False,
                'error': 'Фото не загружено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            is_face_detected = verify_face(contractor.photo.path)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Ошибка проверки фото: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if is_face_detected:
            contractor.is_verified = True
            contractor.generate_qr_code()
            contractor.generate_access_code()
            contractor.save()
            
            qr_data = {
                'id': contractor.id,
                'phone': contractor.phone_number,
                'name': contractor.get_full_name(),
                'code': contractor.access_code
            }
            qr_image = generate_qr_code_image(qr_data)
            
            return Response({
                'success': True,
                'message': 'Регистрация успешно завершена!',
                'qr_code': contractor.qr_code,
                'qr_image': qr_image,
                'access_code': contractor.access_code,
                'contractor': ContractorSerializer(contractor).data
            })
        else:
            return Response({
                'success': False,
                'error': 'На фото не найдено лицо. Пожалуйста, сделайте другое фото'
            }, status=status.HTTP_400_BAD_REQUEST)


class ExcelUploadView(APIView):
    """Загрузка Excel файла"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Файл не загружен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'Поддерживаются только файлы .xlsx и .xls'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = process_excel_file(file)
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Файл успешно обработан',
                'created': result.get('created', 0),
                'updated': result.get('updated', 0),
                'errors': result.get('errors', [])
            })
        else:
            return Response(
                {'success': False, 'error': result.get('error', 'Ошибка обработки файла')},
                status=status.HTTP_400_BAD_REQUEST
            )


class GetQRView(APIView):
    """Получение QR кода и кода доступа"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone:
            return Response({
                'error': 'Телефон обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        contractor = get_object_or_404(Contractor, phone_number=phone)
        
        if not contractor.is_verified:
            return Response({
                'error': 'Пользователь не верифицирован'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not contractor.qr_code:
            contractor.generate_qr_code()
        
        if not contractor.access_code:
            contractor.generate_access_code()
        
        qr_data = {
            'id': contractor.id,
            'phone': contractor.phone_number,
            'name': contractor.get_full_name(),
            'code': contractor.access_code
        }
        qr_image = generate_qr_code_image(qr_data)
        
        return Response({
            'success': True,
            'qr_code': contractor.qr_code,
            'qr_image': qr_image,
            'access_code': contractor.access_code,
            'contractor': ContractorSerializer(contractor).data
        })