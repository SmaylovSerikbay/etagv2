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
RUN mkdir -p /app/static /app/media /app/logs

# Копирование проекта
COPY . .

# Создание символической ссылки для статических файлов
RUN mkdir -p /app/static/css && \
    cp -r /app/profiles/static/css/* /app/static/css/ && \
    mkdir -p /app/static/images && \
    cp -r /app/profiles/static/images/* /app/static/images/

# Установка правильных прав
RUN chown -R www-data:www-data /app

# Сбор статических файлов
RUN python manage.py collectstatic --noinput

# Команда для запуска
CMD ["gunicorn", "etag.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"] 