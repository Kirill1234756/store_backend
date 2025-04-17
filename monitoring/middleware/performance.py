import time
import threading
from collections import defaultdict, deque
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


def default_endpoint_stats():
    return {'count': 0, 'total_time': 0.0}


class AdvancedPerformanceMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = {
            'total_requests': 0,
            'avg_response_time': 0.0,
            'endpoints': defaultdict(default_endpoint_stats),
            'status_codes': defaultdict(int),
            'active_users': set(),
            'throughput': deque(maxlen=60),
        }
        self.lock = threading.Lock()

    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        duration = time.time() - getattr(request, 'start_time', time.time())
        user = request.user if hasattr(request, 'user') else None

        with self.lock:
            # Update metrics
            self.metrics['total_requests'] += 1
            self.metrics['throughput'].append(time.time())

            if user and user.is_authenticated:
                self.metrics['active_users'].add(user.id)

            path = request.path
            self.metrics['endpoints'][path]['count'] += 1
            self.metrics['endpoints'][path]['total_time'] += duration
            self.metrics['status_codes'][response.status_code] += 1

            # Update EMA for response time
            alpha = 0.2
            self.metrics['avg_response_time'] = (
                alpha * duration +
                (1 - alpha) * self.metrics['avg_response_time']
            )

        # Store metrics in cache every 10 requests
        if self.metrics['total_requests'] % 10 == 0:
            # Convert sets to lists for caching
            metrics_to_cache = dict(self.metrics)
            metrics_to_cache['active_users'] = list(
                metrics_to_cache['active_users'])
            metrics_to_cache['throughput'] = list(
                metrics_to_cache['throughput'])
            cache.set('performance_metrics', metrics_to_cache, timeout=3600)

        # Add monitoring headers
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Cache-Status'] = 'HIT' if hasattr(
            request, 'from_cache') else 'MISS'

        return response
