from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import RequestLog


@receiver(post_save, sender=RequestLog)
def clear_request_log_cache(sender, instance, **kwargs):
    cache.delete(f'request_log_{instance.id}')
    cache.delete('request_log_list')


@receiver(post_delete, sender=RequestLog)
def clear_request_log_cache_on_delete(sender, instance, **kwargs):
    cache.delete(f'request_log_{instance.id}')
    cache.delete('request_log_list')
