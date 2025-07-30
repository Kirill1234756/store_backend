# 🚀 Быстрый старт Elasticsearch

## Шаг 1: Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Или установка только Elasticsearch зависимостей
pip install django-elasticsearch-dsl==8.0.0 elasticsearch-dsl==8.11.0 elasticsearch==8.11.0
```

## Шаг 2: Запуск Elasticsearch

```bash
# Запуск Elasticsearch и Kibana через Docker
chmod +x start_elasticsearch.sh
./start_elasticsearch.sh

# Или вручную
docker-compose -f docker-compose.elasticsearch.yml up -d
```

## Шаг 3: Настройка индексов

```bash
# Создание и индексация данных
python setup_elasticsearch.py

# Или пошагово:
python manage.py elasticsearch_manage create
python manage.py elasticsearch_manage update
```

## Шаг 4: Проверка работы

```bash
# Проверка статуса
python manage.py elasticsearch_manage status

# Тестовый запрос
curl http://localhost:9200/products/_search?q=iPhone
```

## Шаг 5: Включение Elasticsearch

Добавьте в `.env` файл:

```env
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOST=localhost:9200
```

## 🎯 Проверка работы

### API эндпоинты:

- **Поиск**: `GET /api/products/?search=iPhone`
- **Подсказки**: `GET /api/products/suggest/?q=iph`
- **Фасеты**: `GET /api/products/facets/`
- **Аналитика**: `GET /api/products/search_analytics/?q=iPhone`

### Kibana Dashboard:

- **URL**: http://localhost:5601
- **Индекс**: `products`

## 🔧 Управление индексами

```bash
# Создание индексов
python manage.py elasticsearch_manage create

# Индексация данных
python manage.py elasticsearch_manage update --batch-size 1000

# Пересоздание индексов
python manage.py elasticsearch_manage rebuild

# Статус индексов
python manage.py elasticsearch_manage status

# Удаление индексов
python manage.py elasticsearch_manage delete --force
```

## 📊 Мониторинг

### Elasticsearch API:

```bash
# Статус кластера
curl http://localhost:9200/_cluster/health

# Статистика индекса
curl http://localhost:9200/products/_stats

# Поиск документов
curl http://localhost:9200/products/_search
```

### Kibana:

- **Discover**: Просмотр документов
- **Visualize**: Создание графиков
- **Dashboard**: Сводные дашборды

## 🚨 Устранение проблем

### Elasticsearch не запускается:

```bash
# Проверка логов
docker-compose -f docker-compose.elasticsearch.yml logs elasticsearch

# Перезапуск
docker-compose -f docker-compose.elasticsearch.yml restart elasticsearch
```

### Ошибки индексации:

```bash
# Проверка подключения
python -c "from elasticsearch import Elasticsearch; es = Elasticsearch(['localhost:9200']); print(es.ping())"

# Пересоздание индексов
python manage.py elasticsearch_manage rebuild
```

### Медленная работа:

```bash
# Увеличение памяти для Elasticsearch
# В docker-compose.elasticsearch.yml:
# mem_limit: 2g
# "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

## 🎉 Готово!

Теперь ваш проект использует Elasticsearch для быстрого поиска и фильтрации!

**Ожидаемые улучшения:**

- ⚡ **10x быстрее** поиск
- 🔍 **Автодополнение** и подсказки
- 📊 **Фасетный поиск** и агрегации
- 📈 **Аналитика** поиска
