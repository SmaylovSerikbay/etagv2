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
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/profiles/static/css

# Копирование проекта
COPY . .

# Копирование статических файлов
RUN if [ -d "/app/static/css" ]; then cp -r /app/static/css/* /app/profiles/static/css/; fi

# Установка правильных прав
RUN chown -R www-data:www-data /app

# Команда для запуска
CMD ["gunicorn", "etag.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"] 