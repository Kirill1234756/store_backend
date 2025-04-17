#!/bin/bash

# Активируем виртуальное окружение
source /path/to/venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Применяем миграции
python manage.py migrate

# Собираем статику
python manage.py collectstatic --noinput

# Перезапускаем Gunicorn
sudo systemctl restart gunicorn

# Перезапускаем Nginx
sudo systemctl restart nginx 