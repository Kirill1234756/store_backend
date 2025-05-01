import time
from django.core.cache import cache
from django.conf import settings

def test_cache_performance():
    # Тест записи
    write_times = []
    for i in range(1000):
        key = f'test_key_{i}'
        value = f'test_value_{i}'
        start = time.time()
        cache.set(key, value, timeout=60)
        write_times.append(time.time() - start)
    
    # Тест чтения
    read_times = []
    for i in range(1000):
        key = f'test_key_{i}'
        start = time.time()
        cache.get(key)
        read_times.append(time.time() - start)
    
    # Тест удаления
    delete_times = []
    for i in range(1000):
        key = f'test_key_{i}'
        start = time.time()
        cache.delete(key)
        delete_times.append(time.time() - start)
    
    # Вывод результатов
    print(f"Среднее время записи: {sum(write_times)/len(write_times)*1000:.2f}ms")
    print(f"Среднее время чтения: {sum(read_times)/len(read_times)*1000:.2f}ms")
    print(f"Среднее время удаления: {sum(delete_times)/len(delete_times)*1000:.2f}ms")
    
    # Тест массовых операций
    data = {f'bulk_key_{i}': f'bulk_value_{i}' for i in range(100)}
    
    start = time.time()
    cache.set_many(data, timeout=60)
    bulk_write_time = time.time() - start
    
    start = time.time()
    cache.get_many(data.keys())
    bulk_read_time = time.time() - start
    
    print(f"\nВремя массовой записи (100 ключей): {bulk_write_time*1000:.2f}ms")
    print(f"Время массового чтения (100 ключей): {bulk_read_time*1000:.2f}ms")

if __name__ == '__main__':
    test_cache_performance() 