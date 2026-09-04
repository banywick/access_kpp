# backend/access_control/urls.py

from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from .views import (
    ContractorViewSet,
    AccessListViewSet,
    AccessLogViewSet,
    CheckUserView,
    ContractorLoginView,
    LoginView,  # <-- Используем LoginView вместо CustomLoginView
    GetQRView,
    ContractorRegisterView,
    ContractorPhotoView,
    ContractorVerifyView,
    QRScanView,
    ExcelUploadView,
    GetContractorInfoView,
    UpdateContractorStatusView,
    GetTerritoryStatsView,
    GetContractorAccessHistoryView
)

router = DefaultRouter()
router.register(r'contractors', ContractorViewSet, basename='contractor')
router.register(r'access-lists', AccessListViewSet, basename='access-list')
router.register(r'access-logs', AccessLogViewSet, basename='access-log')

# backend/access_control/urls.py

urlpatterns = [
    path('', include(router.urls)),
    
    # ========== АУТЕНТИФИКАЦИЯ ==========
    path('check-user/', csrf_exempt(CheckUserView.as_view()), name='check-user'),
    path('contractor-login/', csrf_exempt(ContractorLoginView.as_view()), name='contractor-login'),
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    
    # ========== ПОДРЯДЧИКИ ==========
    path('get-qr/', GetQRView.as_view(), name='get-qr'),
    path('upload-photo/', ContractorPhotoView.as_view(), name='upload-photo'),
    path('verify-photo/', ContractorVerifyView.as_view(), name='verify-photo'),
    path('register/', ContractorRegisterView.as_view(), name='register'),
    
    # ========== ОСТАЛЬНЫЕ ==========
    path('scan-qr/', csrf_exempt(QRScanView.as_view()), name='scan-qr'),
    path('upload-excel/', ExcelUploadView.as_view(), name='upload-excel'),
    path('get-contractor-info/', csrf_exempt(GetContractorInfoView.as_view()), name='get-contractor-info'),
    path('update-contractor-status/<int:contractor_id>/', UpdateContractorStatusView.as_view(), name='update_status'),
    path('territory-stats/', GetTerritoryStatsView.as_view(), name='territory_stats'),
    path('contractor-history/<int:contractor_id>/', GetContractorAccessHistoryView.as_view(), name='contractor_history'),
]
