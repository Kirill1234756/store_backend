from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.cache import cache
from django.db.models import Count, Avg, Max, Min
from .models import RequestLog
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('security')


class LiveMetricsView(APIView):  # Добавлен отсутствующий класс
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Получаем метрики из кеша
        metrics = cache.get('performance_metrics', {})

        # Базовые метрики
        response_data = {
            'requests_per_second': metrics.get('rps', 0),
            'average_response_time': metrics.get('avg_response_time', 0),
            'active_users': len(metrics.get('active_users', set())),
            'endpoints': metrics.get('endpoints', {}),
            'status_codes': dict(metrics.get('status_codes', {})),
        }

        # Добавляем метрики из БД, если есть записи
        if RequestLog.objects.exists():
            db_metrics = RequestLog.objects.aggregate(
                total_requests=Count('id'),
                avg_response=Avg('response_time'),
                max_response=Max('response_time'),
                min_response=Min('response_time')
            )
            response_data['database'] = db_metrics

        return Response(response_data)


class SecurityMonitoringView(APIView):
    def get(self, request):
        try:
            # Get blocked IPs
            blocked_ips = cache.get('blocked_ips', [])

            # Get suspicious activity
            suspicious_activity = cache.get('suspicious_activity', [])

            # Get recent security events
            recent_events = []
            for handler in logger.handlers:
                if hasattr(handler, 'baseFilename'):
                    with open(handler.baseFilename, 'r') as f:
                        recent_events = f.readlines()[-100:]  # Last 100 events

            # Get attack statistics
            attack_stats = {
                'sql_injection': cache.get('sql_injection_count', 0),
                'xss': cache.get('xss_count', 0),
                'path_traversal': cache.get('path_traversal_count', 0),
                'suspicious_agents': cache.get('suspicious_agents_count', 0),
            }

            # Get request statistics
            request_stats = {
                'total_requests': cache.get('total_requests', 0),
                'blocked_requests': cache.get('blocked_requests', 0),
                'successful_requests': cache.get('successful_requests', 0),
            }

            return Response({
                'blocked_ips': blocked_ips,
                'suspicious_activity': suspicious_activity,
                'recent_events': recent_events,
                'attack_stats': attack_stats,
                'request_stats': request_stats,
            })
        except Exception as e:
            logger.error(f'Error in security monitoring: {str(e)}')
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SecurityMetricsView(APIView):
    def get(self, request):
        try:
            # Get metrics for the last 24 hours
            now = timezone.now()
            last_24h = now - timedelta(hours=24)

            metrics = {
                'requests_per_hour': self._get_requests_per_hour(last_24h),
                'blocked_ips_per_hour': self._get_blocked_ips_per_hour(last_24h),
                'attack_types': self._get_attack_types(last_24h),
                'top_blocked_ips': self._get_top_blocked_ips(last_24h),
            }

            return Response(metrics)
        except Exception as e:
            logger.error(f'Error in security metrics: {str(e)}')
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_requests_per_hour(self, since):
        # Implement request per hour counting
        return {}

    def _get_blocked_ips_per_hour(self, since):
        # Implement blocked IPs per hour counting
        return {}

    def _get_attack_types(self, since):
        # Implement attack type counting
        return {}

    def _get_top_blocked_ips(self, since):
        # Implement top blocked IPs counting
        return {}
