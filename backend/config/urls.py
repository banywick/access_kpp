from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,      # Для получения токена
    TokenRefreshView,         # Для обновления токена
    TokenVerifyView,          # Для проверки токена
)

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # ========== JWT эндпоинты ==========
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API для контроля доступа (подключаем наше приложение)
    path('api/', include('access_control.urls')),
    
    # API аутентификации (если нужна)
    path('api/auth/', include('rest_framework.urls')),
    
    # Главная страница (для проверки)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Раздача медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)