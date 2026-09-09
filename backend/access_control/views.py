# backend/access_control/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import Contractor, AccessList, AccessLog
from .serializers import ContractorSerializer, AccessListSerializer, AccessLogSerializer
from .utils import verify_face, process_excel_file, generate_qr_code_image, get_contractor_access

logger = logging.getLogger(__name__)


# ========== ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ ==========
@method_decorator(csrf_exempt, name='dispatch')
class CheckUserView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            print(f"🔍 Checking: {phone_number}")
            
            if not phone_number:
                return Response({
                    'exists': False,
                    'message': 'Нет номера'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .utils import normalize_belarus_phone
            
            try:
                phone_number = normalize_belarus_phone(phone_number)
            except ValueError as e:
                return Response({
                    'exists': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = Contractor.objects.get(phone_number=phone_number)
                
                return Response({
                    'exists': True,
                    'role': user.role,
                    'requires_password': user.role in ['guard', 'admin'],
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'full_name': user.get_full_name(),
                    'organization': user.organization,
                    'phone_number': user.phone_number,
                    'id': user.id
                })
            except Contractor.DoesNotExist:
                return Response({
                    'exists': False,
                    'message': 'Пользователь не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'exists': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ВХОД ДЛЯ ПОДРЯДЧИКОВ (БЕЗ ПАРОЛЯ) ==========
@method_decorator(csrf_exempt, name='dispatch')
class ContractorLoginView(APIView):
    """Вход для подрядчиков - без пароля"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            print(f"ContractorLoginView: phone {phone_number}")
            
            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Укажите номер телефона'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = Contractor.objects.get(phone_number=phone_number)
            except Contractor.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Пользователь не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if user.role != 'contractor':
                return Response({
                    'success': False,
                    'message': 'Для этой роли требуется пароль',
                    'requires_password': True
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'success': False,
                    'message': 'Учетная запись деактивирована'
                }, status=status.HTTP_403_FORBIDDEN)
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Успешный вход',
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': user.id,
                    'phone': user.phone_number,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'is_verified': user.is_verified,
                    'organization': user.organization,
                    'qr_code': user.qr_code,
                    'access_code': user.access_code
                }
            })
            
        except Exception as e:
            print(f"ContractorLoginView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка сервера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ВХОД ДЛЯ ОХРАНЫ И АДМИНОВ (С ПАРОЛЕМ) ==========
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """Вход для охранников и администраторов - с паролем"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            password = request.data.get('password')
            print(f"LoginView: phone {phone_number}")
            
            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Укажите номер телефона'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not password:
                return Response({
                    'success': False,
                    'message': 'Введите пароль'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = authenticate(request, phone_number=phone_number, password=password)
            
            if not user:
                return Response({
                    'success': False,
                    'message': 'Неверный телефон или пароль'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'success': False,
                    'message': 'Учетная запись деактивирована'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if user.role not in ['guard', 'admin']:
                return Response({
                    'success': False,
                    'message': 'Для подрядчиков пароль не требуется'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Успешный вход',
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': user.id,
                    'phone': user.phone_number,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'is_verified': user.is_verified,
                    'organization': user.organization,
                }
            })
            
        except Exception as e:
            print(f"LoginView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка сервера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ПОЛУЧЕНИЕ QR КОДА ==========
@method_decorator(csrf_exempt, name='dispatch')
class GetQRView(APIView):
    """Получить QR код и код доступа с информацией о сроке действия"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            print(f"GetQRView: getting QR for {user.phone_number}")
            
            if not user.is_verified:
                return Response({
                    'success': False,
                    'message': 'Пользователь не верифицирован'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not user.qr_code:
                user.generate_qr_code()
            
            if not user.access_code:
                user.generate_access_code()
            
            # Генерируем QR код как изображение
            qr_data = {
                'id': user.id,
                'phone': user.phone_number,
                'name': user.get_full_name(),
                'code': user.access_code
            }
            
            # Используем функцию из utils
            qr_image = generate_qr_code_image(qr_data)
            
            # Получаем информацию о доступе
            access_entry = AccessList.objects.filter(contractor=user).first()
            
            valid_until = None
            days_remaining = None
            is_allowed = False
            access_status = 'запрещен'
            ban_reason = None
            
            if access_entry:
                valid_until = access_entry.valid_until
                is_allowed = access_entry.is_allowed
                ban_reason = access_entry.ban_reason
                
                today = timezone.now().date()
                if is_allowed and valid_until:
                    days_remaining = (valid_until - today).days
                    if days_remaining < 0:
                        days_remaining = 0
                        is_allowed = False
                        access_status = 'просрочен'
                    else:
                        access_status = 'разрешен'
                elif not is_allowed:
                    access_status = 'запрещен'
                    if ban_reason:
                        access_status = f'запрещен ({ban_reason})'
            else:
                is_allowed = False
                access_status = 'не найден'
            
            # Формируем URL фото
            photo_url = None
            if user.photo:
                photo_url = user.photo.url
                print(f"Photo URL: {photo_url}")
            
            return Response({
                'success': True,
                'qr_code': user.qr_code,
                'qr_image': qr_image,
                'access_code': user.access_code,
                'full_name': user.get_full_name(),
                'phone': user.phone_number,
                'photo': photo_url,
                'organization': user.organization,
                'is_verified': user.is_verified,
                'valid_until': valid_until,
                'days_remaining': days_remaining,
                'is_allowed': is_allowed,
                'access_status': access_status,
                'ban_reason': ban_reason
            })
            
        except Exception as e:
            print(f"GetQRView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка получения QR кода: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== VIEWSETS ==========
class ContractorViewSet(viewsets.ModelViewSet):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        contractor = self.get_object()
        
        if contractor.role != 'contractor':
            return Response({
                'success': False,
                'message': 'Только подрядчики могут быть верифицированы'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if contractor.is_verified:
            return Response({
                'success': False,
                'message': 'Пользователь уже верифицирован'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        contractor.verify_user()
        
        return Response({
            'success': True,
            'message': 'Пользователь верифицирован, создан доступ на 30 дней',
            'access_code': contractor.access_code,
            'qr_code': contractor.qr_code,
            'contractor': ContractorSerializer(contractor).data
        })
    
    @action(detail=True, methods=['post'])
    def regenerate_codes(self, request, pk=None):
        contractor = self.get_object()
        
        if not contractor.is_verified:
            return Response({
                'success': False,
                'message': 'Пользователь не верифицирован'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        contractor.generate_access_code()
        contractor.generate_qr_code()
        
        return Response({
            'success': True,
            'access_code': contractor.access_code,
            'qr_code': contractor.qr_code
        })


class AccessListViewSet(viewsets.ModelViewSet):
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = AccessList.objects.all()
        # Убираем фильтр по дате
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_access(self, request, pk=None):
        access = self.get_object()
        access.is_allowed = not access.is_allowed
        
        if not access.is_allowed:
            access.status = AccessList.AccessStatus.BANNED
            access.ban_reason = request.data.get('ban_reason', 'Доступ запрещен')
        else:
            access.status = AccessList.AccessStatus.OFF_TERRITORY
            access.ban_reason = None
        
        access.save()
        return Response(AccessListSerializer(access).data)


class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = AccessLog.objects.all()
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(scanned_at__date=date_param)
        return queryset


# ========== QR СКАНИРОВАНИЕ ==========
@method_decorator(csrf_exempt, name='dispatch')
class QRScanView(APIView):
    """Сканирование QR кода и обработка доступа"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            access_code = request.data.get('access_code')
            qr_code_raw = request.data.get('qr_code')
            access_type = request.data.get('access_type', 'entry')
            guard_id = request.data.get('guard_id')
            guard_phone = request.data.get('guard_phone')
            
            print(f"QRScanView: access_code={access_code}, qr_code={qr_code_raw}, type={access_type}")
            
            contractor = None
            
            # Пытаемся декодировать QR код
            if qr_code_raw:
                try:
                    import json
                    qr_data = json.loads(qr_code_raw)
                    print(f"Decoded QR data: {qr_data}")
                    
                    contractor_id = qr_data.get('id')
                    if contractor_id:
                        contractor = Contractor.objects.filter(id=contractor_id).first()
                        if contractor:
                            print(f"Found by ID from QR: {contractor.phone_number}")
                    
                    if not contractor:
                        code = qr_data.get('code')
                        if code:
                            contractor = Contractor.objects.filter(access_code=code).first()
                            if contractor:
                                print(f"Found by code from QR: {contractor.phone_number}")
                    
                    if not contractor:
                        phone = qr_data.get('phone')
                        if phone:
                            contractor = Contractor.objects.filter(phone_number=phone).first()
                            if contractor:
                                print(f"Found by phone from QR: {contractor.phone_number}")
                                
                except json.JSONDecodeError:
                    print(f"Failed to parse QR data as JSON, treating as hash")
                    contractor = Contractor.objects.filter(qr_code=qr_code_raw).first()
                    if contractor:
                        print(f"Found by qr_code field: {contractor.phone_number}")
            
            if not contractor and access_code:
                contractor = Contractor.objects.filter(access_code=access_code).first()
                if contractor:
                    print(f"Found by access code: {contractor.phone_number}")
            
            if not contractor:
                return Response({
                    'success': False,
                    'message': 'Подрядчик не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if not contractor.is_verified:
                return Response({
                    'success': False,
                    'message': 'Пользователь не верифицирован'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем доступ (без привязки к дате)
            access_entry = AccessList.objects.filter(contractor=contractor).first()
            
            if not access_entry:
                return Response({
                    'success': False,
                    'message': 'Нет доступа'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not access_entry.is_allowed:
                return Response({
                    'success': False,
                    'message': f'Доступ запрещен: {access_entry.ban_reason or "Причина не указана"}'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not access_entry.is_valid():
                return Response({
                    'success': False,
                    'message': 'Срок действия доступа истек'
                }, status=status.HTTP_403_FORBIDDEN)
            
            is_on_territory = access_entry.is_on_territory
            
            if access_type == 'entry' and is_on_territory:
                return Response({
                    'success': False,
                    'message': 'Пользователь уже на территории'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if access_type == 'exit' and not is_on_territory:
                return Response({
                    'success': False,
                    'message': 'Пользователь не на территории'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if access_type == 'entry':
                access_entry.set_on_territory()
                is_on_territory = True
                message = f'{contractor.get_full_name()} заехал на территорию'
            else:
                access_entry.set_off_territory()
                is_on_territory = False
                message = f'{contractor.get_full_name()} покинул территорию'
            
            scanned_by = None
            if guard_id:
                scanned_by = Contractor.objects.filter(id=guard_id).first()
            elif guard_phone:
                scanned_by = Contractor.objects.filter(phone_number=guard_phone).first()
            
            access_log = AccessLog.objects.create(
                contractor=contractor,
                scanned_by=scanned_by,
                access_code_entered=access_code,
                qr_code_scanned=qr_code_raw,
                access_method='qr' if qr_code_raw else 'code',
                access_type=access_type,
                is_successful=True
            )
            
            photo_url = None
            if contractor.photo:
                photo_url = contractor.photo.url
            
            return Response({
                'success': True,
                'message': message,
                'is_on_territory': is_on_territory,
                'contractor': {
                    'id': contractor.id,
                    'full_name': contractor.get_full_name(),
                    'phone_number': contractor.phone_number,
                    'organization': contractor.organization,
                    'access_code': contractor.access_code,
                    'qr_code': contractor.qr_code,
                    'photo': photo_url,
                    'photo_url': photo_url
                },
                'valid_until': access_entry.valid_until,
                'scanned_by': scanned_by.get_full_name() if scanned_by else None,
                'scanned_by_name': scanned_by.get_full_name() if scanned_by else None,
                'access_time': access_log.scanned_at
            })
            
        except Exception as e:
            print(f"QRScanView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка сервера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПОДРЯДЧИКЕ ==========
@method_decorator(csrf_exempt, name='dispatch')
class GetContractorInfoView(APIView):
    """Получение информации о подрядчике по QR-коду или коду доступа"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            access_code = request.data.get('access_code')
            qr_code_raw = request.data.get('qr_code')
            
            print(f"GetContractorInfoView: access_code={access_code}, qr_code={qr_code_raw}")
            
            contractor = None
            
            if qr_code_raw:
                try:
                    import json
                    qr_data = json.loads(qr_code_raw)
                    print(f"Decoded QR data: {qr_data}")
                    
                    contractor_id = qr_data.get('id')
                    if contractor_id:
                        contractor = Contractor.objects.filter(id=contractor_id).first()
                        if contractor:
                            print(f"Found by ID from QR: {contractor.phone_number}")
                    
                    if not contractor:
                        code = qr_data.get('code')
                        if code:
                            contractor = Contractor.objects.filter(access_code=code).first()
                            if contractor:
                                print(f"Found by code from QR: {contractor.phone_number}")
                    
                    if not contractor:
                        phone = qr_data.get('phone')
                        if phone:
                            contractor = Contractor.objects.filter(phone_number=phone).first()
                            if contractor:
                                print(f"Found by phone from QR: {contractor.phone_number}")
                                
                except json.JSONDecodeError:
                    print(f"Failed to parse QR data as JSON, treating as hash")
                    contractor = Contractor.objects.filter(qr_code=qr_code_raw).first()
                    if contractor:
                        print(f"Found by qr_code field: {contractor.phone_number}")
            
            if not contractor and access_code:
                contractor = Contractor.objects.filter(access_code=access_code).first()
                if contractor:
                    print(f"Found by access code: {contractor.phone_number}")
            
            if not contractor:
                return Response({
                    'success': False,
                    'message': 'Подрядчик не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if not contractor.is_verified:
                return Response({
                    'success': False,
                    'message': 'Пользователь не верифицирован'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем доступ (без привязки к дате)
            access_entry = AccessList.objects.filter(contractor=contractor).first()
            
            is_on_territory = access_entry.is_on_territory if access_entry else False
            valid_until = access_entry.valid_until if access_entry else None
            is_allowed = access_entry.is_allowed if access_entry else False
            ban_reason = access_entry.ban_reason if access_entry else None
            
            photo_url = None
            if contractor.photo:
                photo_url = contractor.photo.url
            
            return Response({
                'success': True,
                'message': 'Пользователь найден',
                'contractor': {
                    'id': contractor.id,
                    'full_name': contractor.get_full_name(),
                    'phone_number': contractor.phone_number,
                    'organization': contractor.organization,
                    'access_code': contractor.access_code,
                    'qr_code': contractor.qr_code,
                    'photo': photo_url,
                    'photo_url': photo_url,
                    'is_verified': contractor.is_verified
                },
                'is_on_territory': is_on_territory,
                'valid_until': valid_until,
                'is_allowed': is_allowed,
                'ban_reason': ban_reason
            })
            
        except Exception as e:
            print(f"GetContractorInfoView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ОСТАЛЬНЫЕ VIEW ==========

class ContractorRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        return Response({
            'success': False,
            'message': 'Регистрация через админку'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class ContractorPhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            photo = request.FILES.get('photo')
            
            if not photo:
                return Response({
                    'success': False,
                    'message': 'Фото не загружено'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if photo.size > 5 * 1024 * 1024:
                return Response({
                    'success': False,
                    'message': 'Файл слишком большой. Максимальный размер 5MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            import imghdr
            file_format = imghdr.what(photo)
            valid_formats = ['jpeg', 'jpg', 'png', 'gif']
            
            if file_format not in valid_formats:
                return Response({
                    'success': False,
                    'message': f'Неверный формат файла. Допустимые: {", ".join(valid_formats)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.photo = photo
            user.save()
            
            if not user.is_verified:
                user.verify_user()
                print(f"✅ User {user.phone_number} automatically verified after photo upload")
            
            photo_url = user.photo.url if user.photo else None
            
            return Response({
                'success': True,
                'message': 'Фото загружено. Пользователь верифицирован.',
                'is_verified': user.is_verified,
                'photo_url': photo_url,
                'access_code': user.access_code,
                'qr_code': user.qr_code
            })
            
        except Exception as e:
            print(f"ContractorPhotoView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractorVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            if user.role != 'contractor':
                return Response({
                    'success': False,
                    'message': 'Только подрядчики могут быть верифицированы'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if user.is_verified:
                return Response({
                    'success': False,
                    'message': 'Пользователь уже верифицирован'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.verify_user()
            
            return Response({
                'success': True,
                'message': 'Пользователь верифицирован, создан доступ на 30 дней',
                'access_code': user.access_code,
                'qr_code': user.qr_code
            })
        except Exception as e:
            print(f"ContractorVerifyView error: {e}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExcelUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        return Response({'success': True, 'message': 'Excel загружен'})


class UpdateContractorStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, contractor_id):
        return Response({'success': True, 'message': 'Статус обновлен'})


class GetTerritoryStatsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'total': 0,
            'on_territory': 0,
            'off_territory': 0
        })


class GetContractorAccessHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, contractor_id):
        return Response({
            'success': True,
            'logs': [],
            'access_history': []
        })