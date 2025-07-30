#!/bin/bash

# Скрипт для запуска Elasticsearch и связанных сервисов

echo "🚀 Запуск Elasticsearch и связанных сервисов..."

# Проверяем, установлен ли Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

# Проверяем, установлен ли Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f docker-compose.elasticsearch.yml down

# Запускаем Elasticsearch и Kibana
echo "🔧 Запускаем Elasticsearch и Kibana..."
docker-compose -f docker-compose.elasticsearch.yml up -d

# Ждем запуска Elasticsearch
echo "⏳ Ждем запуска Elasticsearch..."
sleep 30

# Проверяем статус Elasticsearch
echo "🔍 Проверяем статус Elasticsearch..."
curl -s http://localhost:9200/_cluster/health

if [ $? -eq 0 ]; then
    echo "✅ Elasticsearch успешно запущен!"
    echo "📊 Kibana доступен по адресу: http://localhost:5601"
    echo "🔍 Elasticsearch API: http://localhost:9200"
else
    echo "❌ Ошибка запуска Elasticsearch"
    exit 1
fi

echo "🎉 Все сервисы запущены успешно!" 