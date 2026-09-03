# backend/access_control/admin_actions.py

import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.template.response import TemplateResponse
from .models import Contractor
import logging

logger = logging.getLogger(__name__)


# backend/access_control/admin.py (исправленная функция)

def normalize_phone_number(phone):
    """Нормализация номера телефона"""
    if not phone:
        return None
    
    # Убираем все не цифры
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    
    # Проверяем длину
    if len(cleaned) < 9:
        return None
    
    # Если номер начинается с 8 и длина 11 (например 80291234510)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '375' + cleaned[1:]  # 80291234510 -> 3750291234510
    
    # Если номер начинается с 375 и длина 12 (например 375291234510)
    elif cleaned.startswith('375') and len(cleaned) == 12:
        pass  # Уже правильный формат
    
    # Если номер начинается с 0 (например 0291234510)
    elif cleaned.startswith('0') and len(cleaned) == 10:
        cleaned = '375' + cleaned[1:]  # 0291234510 -> 375291234510
    
    # Если номер состоит из 9 цифр и начинается с кода оператора (29, 33, 44, 25)
    elif len(cleaned) == 9 and cleaned[:2] in ['29', '33', '44', '25']:
        cleaned = '375' + cleaned  # 291234510 -> 375291234510
    
    # Если номер состоит из 10 цифр и начинается с 0 и кода оператора (029, 033, 044, 025)
    elif len(cleaned) == 10 and cleaned.startswith('0') and cleaned[1:3] in ['29', '33', '44', '25']:
        cleaned = '375' + cleaned[1:]  # 0291234510 -> 375291234510
    
    else:
        return None
    
    # Проверяем код оператора для белорусских номеров
    if len(cleaned) >= 12:
        operator_code = cleaned[3:5]
        valid_codes = ['29', '33', '44', '25']
        if operator_code not in valid_codes:
            return None
    
    # Добавляем + если нет
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # Финальная проверка формата +375XXXXXXXXX
    if not cleaned.startswith('+375') or len(cleaned) != 13:
        return None
    
    return cleaned


class ExcelImportMixin:
    """Mixin для импорта данных из Excel в админке"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel_view, name='import_excel'),
            path('process-excel/', self.process_excel_view, name='process_excel'),
        ]
        return custom_urls + urls
    
    def import_excel_view(self, request):
        """Страница загрузки Excel файла"""
        context = {
            'title': 'Загрузка подрядчиков из Excel',
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }
        return TemplateResponse(request, 'admin/access_control/import_excel.html', context)
    
    def process_excel_view(self, request):
        """Обработка загруженного Excel файла"""
        if request.method != 'POST':
            return redirect('admin:access_control_contractor_changelist')
        
        if 'excel_file' not in request.FILES:
            messages.error(request, 'Файл не выбран')
            return redirect('admin:access_control_contractor_changelist')
        
        excel_file = request.FILES['excel_file']
        
        # Проверка расширения файла
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Поддерживаются только файлы .xlsx и .xls')
            return redirect('admin:access_control_contractor_changelist')
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(excel_file)
            
            # Проверка наличия необходимых колонок
            required_columns = ['Телефон', 'Имя', 'Фамилия', 'Организация']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(
                    request, 
                    f'В файле отсутствуют необходимые колонки: {", ".join(missing_columns)}. '
                    f'Доступные колонки: {", ".join(df.columns)}'
                )
                return redirect('admin:access_control_contractor_changelist')
            
            # Обработка данных
            created_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            success_items = []
            
            for index, row in df.iterrows():
                try:
                    # Нормализация номера телефона
                    phone_raw = str(row['Телефон']).strip()
                    phone_normalized = normalize_phone_number(phone_raw)
                    
                    if not phone_normalized:
                        errors.append(f'Строка {index + 2}: Неверный формат номера телефона "{phone_raw}"')
                        error_count += 1
                        continue
                    
                    # Проверка существования пользователя
                    if Contractor.objects.filter(phone_number=phone_normalized).exists():
                        skipped_count += 1
                        continue
                    
                    # Создание пользователя
                    first_name = str(row.get('Имя', '')).strip()
                    last_name = str(row.get('Фамилия', '')).strip()
                    patronymic = str(row.get('Отчество', '')).strip() if 'Отчество' in row else ''
                    organization = str(row.get('Организация', '')).strip()
                    
                    if not first_name or not last_name or not organization:
                        errors.append(
                            f'Строка {index + 2}: Не заполнены обязательные поля '
                            f'(Имя: "{first_name}", Фамилия: "{last_name}", Организация: "{organization}")'
                        )
                        error_count += 1
                        continue
                    
                    # Создаем пользователя
                    contractor = Contractor.objects.create_user(
                        phone_number=phone_normalized,
                        password=None,
                        first_name=first_name,
                        last_name=last_name,
                        patronymic=patronymic if patronymic else None,
                        organization=organization,
                        is_active=True,
                        is_verified=False,
                        role='contractor'
                    )
                    
                    # Генерируем QR код и код доступа
                    contractor.generate_access_code()
                    contractor.generate_qr_code()
                    
                    created_count += 1
                    success_items.append(f"{last_name} {first_name} ({phone_normalized})")
                    
                except Exception as e:
                    errors.append(f'Строка {index + 2}: {str(e)}')
                    error_count += 1
            
            # Формируем сообщение
            if created_count > 0:
                messages.success(
                    request, 
                    f'✅ Создано подрядчиков: {created_count}'
                )
                if success_items:
                    messages.info(
                        request, 
                        f'Созданы: {", ".join(success_items[:5])}{"..." if len(success_items) > 5 else ""}'
                    )
            
            if skipped_count > 0:
                messages.info(request, f'⏭️ Пропущено (уже существуют): {skipped_count}')
            
            if error_count > 0:
                messages.warning(
                    request, 
                    f'❌ Ошибок: {error_count}'
                )
                if errors:
                    messages.error(
                        request, 
                        f'Детали ошибок:\n' + '\n'.join(errors[:10])
                    )
                    if len(errors) > 10:
                        messages.info(request, f'... и еще {len(errors) - 10} ошибок')
            
            if created_count == 0 and skipped_count == 0 and error_count == 0:
                messages.warning(request, 'Нет данных для импорта')
            
        except Exception as e:
            logger.error(f'Error importing Excel: {str(e)}')
            messages.error(request, f'Ошибка при обработке файла: {str(e)}')
        
        return redirect('admin:access_control_contractor_changelist')