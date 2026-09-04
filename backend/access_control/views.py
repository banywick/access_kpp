# backend/access_control/views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Contractor, AccessList, AccessLog
from .serializers import ContractorSerializer, AccessListSerializer, AccessLogSerializer

logger = logging.getLogger(__name__)


# ========== ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ ==========
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class CheckUserView(APIView):
    permission_classes = []
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            print(f"🔍 Checking: {phone_number}")
            
            if not phone_number:
                return Response({
                    'exists': False,
                    'message': 'Нет номера'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Нормализуем номер - используем статический метод из utils.py
            from .utils import normalize_belarus_phone
            
            try:
                phone_number = normalize_belarus_phone(phone_number)
            except ValueError as e:
                return Response({
                    'exists': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ищем пользователя в базе
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
    """Получить QR код и код доступа"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            print(f"GetQRView: getting QR for {user.phone_number}")
            
            if not user.qr_code:
                user.generate_qr_code()
            
            return Response({
                'success': True,
                'qr_code': user.qr_code,
                'access_code': user.access_code,
                'full_name': user.get_full_name(),
                'phone': user.phone_number,
                'organization': user.organization,
                'is_verified': user.is_verified
            })
            
        except Exception as e:
            print(f"GetQRView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка получения QR кода: {str(e)}'
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
            
            user.photo = photo
            user.save()
            
            return Response({
                'success': True,
                'message': 'Фото загружено'
            })
        except Exception as e:
            print(f"ContractorPhotoView error: {e}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractorVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            user.is_verified = True
            user.save()
            return Response({
                'success': True,
                'message': 'Пользователь верифицирован'
            })
        except Exception as e:
            print(f"ContractorVerifyView error: {e}")
            return Response({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== VIEWSETS ДЛЯ ADMIN ==========

class ContractorViewSet(viewsets.ModelViewSet):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.AllowAny]


class AccessListViewSet(viewsets.ModelViewSet):
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer  # Используем правильный сериализатор
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = AccessList.objects.all()
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        return queryset


class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer  # Используем правильный сериализатор
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = AccessLog.objects.all()
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(scanned_at__date=date_param)
        return queryset


# ========== ЗАГЛУШКИ ДЛЯ ДРУГИХ VIEW ==========

# backend/access_control/views.py

@method_decorator(csrf_exempt, name='dispatch')
class QRScanView(APIView):
    """Сканирование QR кода и обработка доступа"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            access_code = request.data.get('access_code')
            qr_code = request.data.get('qr_code')
            access_type = request.data.get('access_type', 'entry')
            guard_id = request.data.get('guard_id')
            guard_phone = request.data.get('guard_phone')
            guard_name = request.data.get('guard_name')
            
            # Ищем подрядчика по коду доступа или QR коду
            contractor = None
            if access_code:
                contractor = Contractor.objects.filter(access_code=access_code).first()
            elif qr_code:
                contractor = Contractor.objects.filter(qr_code=qr_code).first()
            
            if not contractor:
                return Response({
                    'success': False,
                    'message': 'Подрядчик не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем доступ
            today = timezone.now().date()
            access_entry = AccessList.objects.filter(
                contractor=contractor,
                date=today
            ).first()
            
            if access_entry and not access_entry.is_allowed:
                return Response({
                    'success': False,
                    'message': f'Доступ запрещен: {access_entry.ban_reason}'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем или создаем запись доступа
            if not access_entry:
                access_entry = AccessList.objects.create(
                    contractor=contractor,
                    date=today,
                    is_allowed=True
                )
            
            # Обновляем статус
            if access_type == 'entry':
                access_entry.set_on_territory()
                is_on_territory = True
                message = f'{contractor.get_full_name()} заехал на территорию'
            else:
                access_entry.set_off_territory()
                is_on_territory = False
                message = f'{contractor.get_full_name()} покинул территорию'
            
            # Записываем лог
            scanned_by = None
            if guard_id:
                scanned_by = Contractor.objects.filter(id=guard_id).first()
            
            AccessLog.objects.create(
                contractor=contractor,
                scanned_by=scanned_by,
                access_code_entered=access_code,
                qr_code_scanned=qr_code,
                access_method='qr' if qr_code else 'code',
                access_type=access_type,
                is_successful=True
            )
            
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
                    'photo': contractor.photo.url if contractor.photo else None
                },
                'valid_until': access_entry.valid_until
            })
            
        except Exception as e:
            print(f"QRScanView error: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Ошибка сервера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExcelUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        return Response({'success': True, 'message': 'Excel загружен'})


class GetContractorInfoView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        return Response({'success': True, 'message': 'Информация получена'})


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