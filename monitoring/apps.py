from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Monitoring'

    def ready(self):
        try:
            import monitoring.signals  # noqa
        except ImportError:
            pass
