#!/bin/bash

# Переходим в директорию проекта
cd ~/projects/etag/

# Создаем необходимые директории если их нет
sudo mkdir -p /var/www/my-business-card.kz/{static,media,logs}
sudo chown -R $USER:$USER /var/www/my-business-card.kz

# Получаем последние изменения из git
git pull

# Останавливаем и удаляем старые контейнеры
docker-compose down

# Собираем и запускаем новые контейнеры
docker-compose up --build -d

# Применяем миграции
docker-compose exec web python manage.py migrate

# Собираем статику
docker-compose exec web python manage.py collectstatic --noinput

# Перезагружаем gunicorn
docker-compose restart web

echo "Деплой завершен успешно!" 