# backend/access_control/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContractorViewSet, 
    AccessListViewSet, 
    AccessLogViewSet,
    ContractorRegisterView,
    ContractorPhotoView,
    ContractorVerifyView,
    QRScanView,
    ExcelUploadView,
    GetQRView  # Добавляем
)

router = DefaultRouter()
router.register(r'contractors', ContractorViewSet, basename='contractor')
router.register(r'access-lists', AccessListViewSet, basename='access-list')
router.register(r'access-logs', AccessLogViewSet, basename='access-log')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', ContractorRegisterView.as_view(), name='register'),
    path('upload-photo/', ContractorPhotoView.as_view(), name='upload-photo'),
    path('verify-photo/', ContractorVerifyView.as_view(), name='verify-photo'),
    path('scan-qr/', QRScanView.as_view(), name='scan-qr'),
    path('upload-excel/', ExcelUploadView.as_view(), name='upload-excel'),
    path('get-qr/', GetQRView.as_view(), name='get-qr'),  # Добавляем
]