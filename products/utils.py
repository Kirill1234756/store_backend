from django.db.models import Avg, Count, F, Q
from .models import Product
import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

def get_product_stats():
    stats = Product.objects.aggregate(
        total_products=Count('id'),
        avg_price=Avg('price'),
        total_active=Count('id', filter=Q(is_active=True))
    )
    return stats 

def save_image(image_file, path_prefix='products/', max_size=(1200, 1200), quality=85):
    """
    Save an image file with compression and optimization
    
    Args:
        image_file: The uploaded image file
        path_prefix: Directory prefix for saving the image
        max_size: Maximum dimensions (width, height)
        quality: JPEG/WebP quality (1-100)
    
    Returns:
        str: Path to the saved image
    """
    # Open and process image
    image = Image.open(image_file)
    
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Resize if too large
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Generate filename
    ext = '.webp'  # Use WebP for better compression
    filename = f"{os.path.splitext(image_file.name)[0]}{ext}"
    filepath = os.path.join(path_prefix, filename)
    
    # Save as WebP
    output = BytesIO()
    image.save(output, format='WEBP', quality=quality, optimize=True)
    output.seek(0)
    
    # Save to storage
    saved_path = default_storage.save(filepath, ContentFile(output.read()))
    return saved_path

def delete_image(image_path):
    """
    Delete an image file from storage
    
    Args:
        image_path: Path to the image file
    """
    if image_path and default_storage.exists(image_path):
        default_storage.delete(image_path) 

def get_city_by_ip(ip_address: str) -> Optional[str]:
    """
    Определяет город по IP адресу используя бесплатные API
    """
    if not ip_address or ip_address == '127.0.0.1':
        return None
    
    try:
        # Используем ipapi.co для определения города
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city')
                if city:
                    return city
        
        # Fallback: используем ipapi.co
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city')
            if city:
                return city
                
    except Exception as e:
        logger.error(f"Error getting city by IP {ip_address}: {e}")
    
    return None

def get_client_ip(request) -> str:
    """
    Получает реальный IP адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detect_user_city(request) -> Optional[str]:
    """
    Определяет город пользователя по IP адресу
    """
    ip = get_client_ip(request)
    return get_city_by_ip(ip)

def validate_city_name(city_name: str) -> bool:
    """
    Проверяет корректность названия города
    """
    if not city_name or len(city_name.strip()) < 2:
        return False
    
    # Проверяем, что название содержит только буквы, цифры, пробелы и дефисы
    import re
    pattern = r'^[а-яА-Яa-zA-Z0-9\s\-\.]+$'
    return bool(re.match(pattern, city_name.strip()))

def normalize_city_name(city_name: str) -> str:
    """
    Нормализует название города (убирает лишние пробелы, приводит к правильному регистру)
    """
    if not city_name:
        return ""
    
    # Убираем лишние пробелы и приводим к правильному регистру
    normalized = city_name.strip()
    
    # Приводим к правильному регистру (первая буква заглавная, остальные строчные)
    words = normalized.split()
    normalized_words = []
    
    for word in words:
        if word:
            # Обрабатываем специальные случаи (Москва, Санкт-Петербург и т.д.)
            if word.lower() in ['москва', 'moscow']:
                normalized_words.append('Москва')
            elif word.lower() in ['санкт-петербург', 'spb', 'st-petersburg']:
                normalized_words.append('Санкт-Петербург')
            elif word.lower() in ['новосибирск', 'novosibirsk']:
                normalized_words.append('Новосибирск')
            elif word.lower() in ['екатеринбург', 'ekaterinburg']:
                normalized_words.append('Екатеринбург')
            elif word.lower() in ['казань', 'kazan']:
                normalized_words.append('Казань')
            elif word.lower() in ['нижний новгород', 'nizhny novgorod']:
                normalized_words.append('Нижний Новгород')
            elif word.lower() in ['челябинск', 'chelyabinsk']:
                normalized_words.append('Челябинск')
            elif word.lower() in ['самара', 'samara']:
                normalized_words.append('Самара')
            elif word.lower() in ['уфа', 'ufa']:
                normalized_words.append('Уфа')
            elif word.lower() in ['ростов-на-дону', 'rostov-on-don']:
                normalized_words.append('Ростов-на-Дону')
            elif word.lower() in ['краснодар', 'krasnodar']:
                normalized_words.append('Краснодар')
            elif word.lower() in ['воронеж', 'voronezh']:
                normalized_words.append('Воронеж')
            elif word.lower() in ['пермь', 'perm']:
                normalized_words.append('Пермь')
            elif word.lower() in ['волгоград', 'volgograd']:
                normalized_words.append('Волгоград')
            elif word.lower() in ['красноярск', 'krasnoyarsk']:
                normalized_words.append('Красноярск')
            else:
                # Обычное слово - первая буква заглавная
                normalized_words.append(word.capitalize())
    
    return ' '.join(normalized_words)

def get_popular_cities() -> list:
    """
    Возвращает список популярных городов России
    """
    return [
        'Москва',
        'Санкт-Петербург',
        'Новосибирск',
        'Екатеринбург',
        'Казань',
        'Нижний Новгород',
        'Челябинск',
        'Самара',
        'Уфа',
        'Ростов-на-Дону',
        'Краснодар',
        'Воронеж',
        'Пермь',
        'Волгоград',
        'Красноярск',
        'Саратов',
        'Тюмень',
        'Тольятти',
        'Ижевск',
        'Барнаул',
        'Ульяновск',
        'Иркутск',
        'Хабаровск',
        'Ярославль',
        'Владивосток',
        'Махачкала',
        'Томск',
        'Оренбург',
        'Кемерово',
        'Новокузнецк'
    ]

def search_cities(query: str, limit: int = 10) -> list:
    """
    Ищет города по запросу
    """
    if not query or len(query.strip()) < 2:
        return []
    
    query = query.strip().lower()
    popular_cities = get_popular_cities()
    
    # Сначала ищем среди популярных городов
    results = [city for city in popular_cities if query in city.lower()]
    
    # Если результатов мало, можно добавить поиск через внешние API
    if len(results) < limit:
        try:
            # Используем Nominatim API для поиска городов
            import requests
            response = requests.get(
                f'https://nominatim.openstreetmap.org/search',
                params={
                    'q': f'{query}, Россия',
                    'format': 'json',
                    'limit': limit - len(results),
                    'countrycodes': 'ru',
                    'addressdetails': 1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get('type') in ['city', 'town']:
                        city_name = item.get('name')
                        if city_name and city_name not in results:
                            results.append(city_name)
                            if len(results) >= limit:
                                break
        except Exception as e:
            logger.error(f"Error searching cities: {e}")
    
    return results[:limit] 