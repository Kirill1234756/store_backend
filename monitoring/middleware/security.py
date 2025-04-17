from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if settings.DEBUG:
            # Skip security headers in development mode
            return response
        else:
            # Strict headers for production
            headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Content-Security-Policy': "default-src 'self'",
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'geolocation=(), microphone=()'
            }

            # Add headers to response
            for header, value in headers.items():
                if header not in response:
                    response[header] = value

            return response
