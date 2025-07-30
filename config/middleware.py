"""
Middleware for database optimization and performance monitoring
"""

import time
import logging
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class DatabaseRouterMiddleware(MiddlewareMixin):
    """
    Middleware to handle database routing based on request type
    """
    
    def process_request(self, request):
        """
        Set database routing hints based on request method
        """
        # For GET requests, prefer replica
        if request.method == 'GET':
            request._database_hint = 'replica'
        else:
            request._database_hint = 'default'
        
        return None


class QueryOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to optimize database queries
    """
    
    def process_request(self, request):
        """
        Set query optimization hints
        """
        request._query_optimization = {
            'select_related': True,
            'prefetch_related': True,
            'only': True,
            'defer': True,
        }
        return None
    
    def process_response(self, request, response):
        """
        Log query statistics
        """
        if hasattr(connection, 'queries'):
            query_count = len(connection.queries)
            total_time = sum(float(q['time']) for q in connection.queries)
            
            if query_count > 10 or total_time > 1.0:  # Log slow or heavy queries
                logger.warning(
                    f"Slow request: {request.path} - {query_count} queries, "
                    f"{total_time:.3f}s total"
                )
        
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor request performance
    """
    
    def process_request(self, request):
        """
        Start timing the request
        """
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        Log request performance metrics
        """
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow request: {request.path} - {duration:.3f}s"
                )
            
            # Add performance headers
            response['X-Request-Time'] = f"{duration:.3f}"
            
            # Track performance metrics
            if hasattr(settings, 'MONITORING_CONFIG') and settings.MONITORING_CONFIG.get('enabled'):
                self._track_performance_metrics(request, duration)
        
        return response
    
    def _track_performance_metrics(self, request, duration):
        """
        Track performance metrics for monitoring
        """
        # This could send metrics to Prometheus, StatsD, etc.
        pass


class SlowQueryFilter:
    """
    Logging filter for slow queries
    """
    
    def __init__(self):
        self.threshold = getattr(settings, 'PERFORMANCE_MONITORING', {}).get('slow_query_threshold', 1000)
    
    def filter(self, record):
        """
        Filter slow queries for logging
        """
        if hasattr(record, 'duration'):
            return record.duration > self.threshold
        return True
