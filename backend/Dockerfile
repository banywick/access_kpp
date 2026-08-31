# backend/Dockerfile
FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем директорию для медиа-файлов
RUN mkdir -p /app/media /app/static

# Открываем порт
EXPOSE 8000

# Команда для разработки с горячей перезагрузкой
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]