#!/bin/bash

# Остановка при ошибках
set -e

echo "Starting deployment..."

# Активация виртуального окружения
source venv/bin/activate

# Получение последних изменений
echo "Pulling latest changes..."
git pull origin main

# Установка зависимостей
echo "Installing dependencies..."
pip install -r requirements.txt

# Применение миграций
echo "Applying migrations..."
python manage.py migrate

# Сбор статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Перезапуск сервисов
echo "Restarting services..."
sudo systemctl restart store
sudo systemctl restart nginx

# Очистка кэша
echo "Clearing cache..."
python manage.py clearcache

echo "Deployment completed successfully!" 