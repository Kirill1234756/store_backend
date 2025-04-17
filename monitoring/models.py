from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RequestLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in seconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['path']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.method} {self.path} ({self.status_code})"
