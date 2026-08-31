# backend/access_control/utils.py
import cv2
import numpy as np
import pandas as pd
import hashlib
import json
import base64
from io import BytesIO
from PIL import Image
import qrcode
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime
from .models import Contractor, AccessList, AccessLog  # Добавляем импорт


def verify_face(image_path):
    """
    Проверка наличия лица на фото
    """
    if not image_path:
        return False
    
    try:
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        # Используем каскад Хаара
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(100, 100)
        )
        
        return len(faces) > 0
    except Exception as e:
        print(f"Error in face verification: {e}")
        return False


def generate_qr_code_image(data):
    """
    Генерация QR кода как изображение
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Конвертируем в base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def process_excel_file(file):
    """
    Обработка Excel файла с списком сотрудников
    Ожидаемые колонки: ФИО, Телефон
    """
    try:
        df = pd.read_excel(BytesIO(file.read()))
        
        # Проверяем наличие нужных колонок
        required_columns = ['ФИО', 'Телефон']
        if not all(col in df.columns for col in required_columns):
            return {
                'success': False, 
                'error': f'Файл должен содержать колонки: {", ".join(required_columns)}'
            }
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                full_name = str(row['ФИО']).strip().split()
                phone = str(row['Телефон']).strip()
                
                # Нормализуем телефон
                from .models import ContractorManager
                phone = ContractorManager.normalize_phone_number(phone)
                
                # Парсим ФИО
                last_name = full_name[0] if len(full_name) > 0 else ''
                first_name = full_name[1] if len(full_name) > 1 else ''
                patronymic = full_name[2] if len(full_name) > 2 else ''
                
                # Создаем или обновляем подрядчика
                contractor, created = Contractor.objects.get_or_create(
                    phone_number=phone,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'patronymic': patronymic,
                        'username': phone,  # Для совместимости
                    }
                )
                
                if not created:
                    # Обновляем данные если изменились
                    contractor.first_name = first_name
                    contractor.last_name = last_name
                    contractor.patronymic = patronymic
                    contractor.save()
                    updated_count += 1
                else:
                    created_count += 1
                
                # Добавляем в список доступа на сегодня
                AccessList.objects.get_or_create(
                    contractor=contractor,
                    date=timezone.now().date(),
                    defaults={'is_allowed': True}
                )
                
            except Exception as e:
                errors.append(f"Строка {idx+2}: {str(e)}")
        
        return {
            'success': True,
            'created': created_count,
            'updated': updated_count,
            'errors': errors
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_today_access(contractor):
    """
    Получить статус доступа на сегодня
    """
    today = timezone.now().date()
    try:
        access = AccessList.objects.get(
            contractor=contractor,
            date=today
        )
        return access
    except AccessList.DoesNotExist:
        return None


def normalize_belarus_phone(phone_number):
    """
    Нормализация белорусского номера телефона
    """
    # Убираем все пробелы, скобки, дефисы
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    if len(cleaned) < 9:
        raise ValueError('Слишком короткий номер телефона')
    
    # Если номер начинается с 8 (старый формат)
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '375' + cleaned[1:]
    
    # Если номер начинается с 375 и имеет 12 цифр
    elif cleaned.startswith('375') and len(cleaned) == 12:
        pass
    
    # Если номер начинается с 29, 33, 44, 25
    elif cleaned.startswith(('29', '33', '44', '25')) and len(cleaned) == 9:
        cleaned = '375' + cleaned
    
    # Если номер начинается с 0 (029, 033, 044)
    elif cleaned.startswith(('029', '033', '044', '025')) and len(cleaned) == 10:
        cleaned = '375' + cleaned[1:]
    
    else:
        raise ValueError(f'Неверный формат номера: {phone_number}')
    
    # Проверяем код оператора
    if len(cleaned) >= 12:
        operator_code = cleaned[3:5]
        valid_codes = ['29', '33', '44', '25']
        if operator_code not in valid_codes:
            raise ValueError(f'Неверный код оператора: {operator_code}')
    
    # Добавляем +
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned


def format_belarus_phone(phone_number):
    """
    Форматирование белорусского номера для отображения
    +375291234567 -> +375 29 123-45-67
    """
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    if cleaned.startswith('375'):
        cleaned = cleaned[3:]
    
    if len(cleaned) < 9:
        return phone_number
    
    operator = cleaned[:2]
    part1 = cleaned[2:5]
    part2 = cleaned[5:7]
    part3 = cleaned[7:9]
    
    return f"+375 {operator} {part1}-{part2}-{part3}"