from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class DevelopmentHttpsMiddleware(MiddlewareMixin):
    """
    Middleware to handle HTTPS requests in development mode.
    This is a workaround for the Django development server which doesn't support HTTPS.
    """

    def process_request(self, request):
        # In development, always treat requests as HTTP
        if settings.DEBUG:
            request._is_secure = False
            request.META['wsgi.url_scheme'] = 'http'
            request.META['HTTP_X_FORWARDED_PROTO'] = 'http'
            # Also update the request scheme
            request.scheme = 'http'
        return None
