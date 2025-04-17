#!/bin/bash

# Проверяем статус сервисов
echo "Checking services status..."
systemctl status gunicorn
systemctl status nginx

# Проверяем SSL сертификаты
echo "Checking SSL certificates..."
curl -I https://cy16820.tw1.ru

# Проверяем API
echo "Checking API..."
curl -I https://cy16820.tw1.ru/api/products/products

# Проверяем статические файлы
echo "Checking static files..."
curl -I https://cy16820.tw1.ru/static/admin/css/base.css

# Проверяем CORS
echo "Checking CORS..."
curl -H "Origin: https://cy16820.tw1.ru" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     -I https://cy16820.tw1.ru/api/products/products 