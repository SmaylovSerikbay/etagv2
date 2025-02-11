FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание необходимых директорий
RUN mkdir -p /app/staticfiles \
    && mkdir -p /app/media \
    && mkdir -p /app/logs \
    && mkdir -p /app/static/css \
    && mkdir -p /app/profiles/static/css

# Копирование проекта
COPY . .

# Установка правильных прав
RUN chown -R www-data:www-data /app \
    && chmod -R 755 /app/staticfiles \
    && chmod -R 755 /app/static \
    && chmod -R 755 /app/profiles

# Команда для запуска
CMD ["gunicorn", "etag.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"] 