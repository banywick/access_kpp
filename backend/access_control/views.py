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

User = get_user_model()


# backend/access_control/views.py

# backend/access_control/views.py

class LoginView(APIView):
    """
    Вход в систему по номеру телефона
    POST /api/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone_number')
        password = request.data.get('password')  # Добавляем пароль
        
        if not phone:
            return Response({
                'success': False,
                'error': 'Телефон обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contractor = Contractor.objects.get(phone_number=phone)
            
            # Проверяем активен ли пользователь
            if not contractor.is_active:
                return Response({
                    'success': False,
                    'error': 'Доступ запрещен',
                    'reason': 'Аккаунт деактивирован'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Для охранников и администраторов - проверяем пароль
            if contractor.role in ['guard', 'admin']:
                # Проверяем наличие пароля
                if not contractor.has_usable_password():
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': 'Для входа требуется пароль. Обратитесь к администратору.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Проверяем пароль
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
                
                # Проверяем права доступа
                if contractor.role == 'admin' and not contractor.is_superuser:
                    return Response({
                        'success': False,
                        'error': 'Доступ запрещен',
                        'reason': 'Недостаточно прав для входа'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Для охранников проверяем is_staff
                if contractor.role == 'guard' and not contractor.is_staff:
                    contractor.is_staff = True
                    contractor.save()
                
                # Возвращаем данные без проверки верификации
                serializer = ContractorSerializer(contractor)
                return Response({
                    'success': True,
                    'user_data': serializer.data,
                    'role': contractor.role,
                    'message': 'Вход выполнен успешно',
                    'requires_verification': False
                })
            
            # Для подрядчиков - стандартная проверка без пароля
            else:
                # Проверяем доступ на сегодня
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


# ============ ViewSet для CRUD операций ============

class ContractorViewSet(viewsets.ModelViewSet):
    """CRUD для подрядчиков"""
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по номеру телефона
        phone = self.request.query_params.get('phone')
        if phone:
            queryset = queryset.filter(phone_number__icontains=phone)
        
        # Фильтр по верификации
        verified = self.request.query_params.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif verified == 'false':
            queryset = queryset.filter(is_verified=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def regenerate_qr(self, request, pk=None):
        """Перегенерировать QR код"""
        contractor = self.get_object()
        contractor.generate_qr_code()
        
        # Генерируем изображение QR
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


class AccessListViewSet(viewsets.ModelViewSet):
    """CRUD для списков доступа"""
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по дате
        date = self.request.query_params.get('date')
        if date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                pass
        
        # Фильтр по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter == 'allowed':
            queryset = queryset.filter(is_allowed=True)
        elif status_filter == 'banned':
            queryset = queryset.filter(is_allowed=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_access(self, request, pk=None):
        """Переключить доступ"""
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
        """Получить список доступа на сегодня"""
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
        
        # Фильтр по дате
        date = self.request.query_params.get('date')
        if date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                queryset = queryset.filter(scanned_at__date=date_obj)
            except ValueError:
                pass
        
        # Фильтр по подрядчику
        contractor_id = self.request.query_params.get('contractor')
        if contractor_id:
            queryset = queryset.filter(contractor_id=contractor_id)
        
        # Фильтр по успешности
        successful = self.request.query_params.get('successful')
        if successful == 'true':
            queryset = queryset.filter(is_successful=True)
        elif successful == 'false':
            queryset = queryset.filter(is_successful=False)
        
        return queryset


# ============ APIView для специфических операций ============

class ContractorRegisterView(APIView):
    """
    Шаг 1: Регистрация по телефону
    POST /api/register/☺
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone_number']
        
        try:
            contractor = Contractor.objects.get(phone_number=phone)
            
            # Проверяем доступ на сегодня
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


# backend/access_control/views.py (фрагмент с загрузкой фото)
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.base import ContentFile
import base64
import imghdr
from PIL import Image
import io
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


# backend/access_control/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import imghdr
from PIL import Image
import logging

logger = logging.getLogger(__name__)


# backend/access_control/views.py

# backend/access_control/views.py

class GetQRView(APIView):
    """
    Получение QR кода и кода доступа для верифицированного пользователя
    POST /api/get-qr/
    """
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
        
        # Генерируем изображение QR
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




class ContractorPhotoView(APIView):
    """
    Шаг 2: Загрузка фото
    POST /api/upload-photo/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        logger.info(f"Photo upload request received")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request FILES: {request.FILES}")
        
        serializer = PhotoUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone_number']
        photo = serializer.validated_data['photo']
        
        logger.info(f"Processing photo for phone: {phone}")
        logger.info(f"Photo: {photo.name}, size: {photo.size}, type: {photo.content_type}")
        
        contractor = get_object_or_404(Contractor, phone_number=phone)
        
        try:
            # Проверяем, что это действительно изображение
            from PIL import Image
            img = Image.open(photo)
            img.verify()
            
            # Сохраняем фото
            contractor.photo = photo
            contractor.save()
            
            logger.info(f"Photo saved successfully for {phone}")
            
            return Response({
                'success': True,
                'message': 'Фото загружено',
                'needs_verification': not contractor.is_verified,
                'photo_url': contractor.photo.url if contractor.photo else None
            })
            
        except Exception as e:
            logger.error(f"Error saving photo: {str(e)}")
            return Response({
                'success': False,
                'error': f'Ошибка сохранения фото: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class ContractorVerifyView(APIView):
    """
    Шаг 3: Проверка фото и генерация QR и кода доступа
    POST /api/verify-photo/
    """
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
            
            # Генерируем QR код
            contractor.generate_qr_code()
            
            # Генерируем уникальный 4-значный код
            contractor.generate_access_code()
            
            contractor.save()
            
            # Генерируем изображение QR кода
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


# backend/access_control/views.py

class QRScanView(APIView):
    """
    Сканирование QR кода или ввод кода доступа
    POST /api/scan-qr/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Проверяем что передано: qr_code или access_code
        qr_code = request.data.get('qr_code')
        access_code = request.data.get('access_code')
        
        logger.info(f"Scan request: qr_code={qr_code}, access_code={access_code}")
        
        if not qr_code and not access_code:
            return Response({
                'success': False,
                'message': 'Необходимо передать QR-код или код доступа'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Ищем по QR коду или по access_code
            if qr_code:
                contractor = Contractor.objects.get(qr_code=qr_code)
                access_method = 'qr'
                logger.info(f"Found by QR: {contractor.phone_number}")
            else:
                # Ищем по коду доступа
                contractor = Contractor.objects.get(access_code=access_code)
                access_method = 'code'
                logger.info(f"Found by access code: {contractor.phone_number}")
            
            # Проверяем верификацию
            if not contractor.is_verified:
                logger.warning(f"Contractor not verified: {contractor.phone_number}")
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Пользователь не прошел верификацию',
                    'contractor': ContractorSerializer(contractor).data
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Проверяем доступ на сегодня
            today_access = get_today_access(contractor)
            
            # Логируем сканирование
            access_log = AccessLog.objects.create(
                contractor=contractor,
                qr_code_scanned=qr_code if qr_code else None,
                access_code_entered=access_code if access_code else None,
                access_method=access_method,
                ip_address=self.get_client_ip(request)
            )
            
            if not today_access:
                access_log.is_successful = False
                access_log.save()
                logger.warning(f"No access list for today: {contractor.phone_number}")
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': 'Пользователь не найден в списке доступа на сегодня',
                    'contractor': ContractorSerializer(contractor).data
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not today_access.is_allowed:
                access_log.is_successful = False
                access_log.save()
                logger.warning(f"Access denied by admin: {contractor.phone_number}")
                return Response({
                    'success': False,
                    'message': 'Доступ запрещен',
                    'reason': today_access.ban_reason or 'Доступ временно ограничен',
                    'contractor': ContractorSerializer(contractor).data
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Успешный проход
            access_log.is_successful = True
            access_log.save()
            
            logger.info(f"Access granted: {contractor.phone_number}")
            
            return Response({
                'success': True,
                'message': 'Проезд разрешен ✅',
                'contractor': ContractorSerializer(contractor).data,
                'access_time': access_log.scanned_at,
                'access_method': access_method
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
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ExcelUploadView(APIView):
    """
    Загрузка Excel файла
    POST /api/upload-excel/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Файл не загружен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем расширение
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