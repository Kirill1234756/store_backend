from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import re
import logging
import hashlib
import time
import json
from datetime import datetime, timedelta
import ipaddress
import socket
import dns.resolver

logger = logging.getLogger('security')


class AdvancedSecurityMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.blocked_ips = set()
        self.suspicious_ips = {}
        self.request_history = {}
        self.geo_cache = {}
        self.dns_cache = {}
        self.load_threat_intelligence()

    def load_threat_intelligence(self):
        """Load threat intelligence data"""
        self.malicious_ips = cache.get('malicious_ips', set())
        self.malicious_domains = cache.get('malicious_domains', set())
        self.tor_exit_nodes = cache.get('tor_exit_nodes', set())
        self.vpn_ips = cache.get('vpn_ips', set())

    def get_request_fingerprint(self, request):
        """Generate advanced request fingerprint"""
        components = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('REMOTE_ADDR', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', ''),
            request.META.get('HTTP_ACCEPT', ''),
            request.META.get('HTTP_CONNECTION', ''),
            request.META.get('HTTP_UPGRADE_INSECURE_REQUESTS', ''),
            request.META.get('HTTP_SEC_FETCH_SITE', ''),
            request.META.get('HTTP_SEC_FETCH_MODE', ''),
            request.META.get('HTTP_SEC_FETCH_USER', ''),
            request.META.get('HTTP_SEC_FETCH_DEST', ''),
        ]
        return hashlib.sha256(''.join(components).encode()).hexdigest()

    def check_ip_reputation(self, ip):
        """Check IP reputation"""
        if ip in self.malicious_ips:
            return 'malicious'
        if ip in self.tor_exit_nodes:
            return 'tor'
        if ip in self.vpn_ips:
            return 'vpn'
        return 'clean'

    def check_domain_reputation(self, domain):
        """Check domain reputation"""
        if domain in self.malicious_domains:
            return 'malicious'
        return 'clean'

    def analyze_request_patterns(self, request):
        """Analyze request patterns for anomalies"""
        ip = request.META.get('REMOTE_ADDR')
        fingerprint = self.get_request_fingerprint(request)

        # Initialize request history
        if ip not in self.request_history:
            self.request_history[ip] = {
                'requests': [],
                'fingerprints': set(),
                'last_seen': time.time(),
                'request_count': 0,
                'error_count': 0,
                'suspicious_count': 0
            }

        history = self.request_history[ip]

        # Check for rapid fingerprint changes
        if fingerprint not in history['fingerprints']:
            history['fingerprints'].add(fingerprint)
            if len(history['fingerprints']) > 3:
                logger.warning(f'Multiple fingerprints detected for IP {ip}')
                return True

        # Check for rapid requests
        current_time = time.time()
        if current_time - history['last_seen'] < 1:
            history['request_count'] += 1
            if history['request_count'] > 10:
                logger.warning(f'Rapid requests detected from IP {ip}')
                return True

        # Check for error patterns
        if request.path.endswith(('.php', '.asp', '.aspx', '.jsp')):
            history['error_count'] += 1
            if history['error_count'] > 5:
                logger.warning(f'Multiple error requests from IP {ip}')
                return True

        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'~/',
            r'%2e%2e%2f',
            r'%252e%252e%252f',
            r'<script',
            r'javascript:',
            r'eval\(',
            r'SELECT.*FROM',
            r'UNION SELECT',
            r'OR 1=1',
            r'--',
            r'/\*',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, str(request.GET) + str(request.POST), re.IGNORECASE):
                history['suspicious_count'] += 1
                if history['suspicious_count'] > 3:
                    logger.warning(
                        f'Multiple suspicious patterns from IP {ip}')
                    return True

        history['last_seen'] = current_time
        return False

    def check_geo_location(self, ip):
        """Check IP geolocation"""
        if ip in self.geo_cache:
            return self.geo_cache[ip]

        try:
            # Implement geolocation check
            # This is a placeholder - implement actual geolocation service
            self.geo_cache[ip] = 'unknown'
            return 'unknown'
        except Exception:
            return 'unknown'

    def check_dns_resolution(self, domain):
        """Check DNS resolution"""
        if domain in self.dns_cache:
            return self.dns_cache[domain]

        try:
            # Implement DNS resolution check
            # This is a placeholder - implement actual DNS check
            self.dns_cache[domain] = 'resolved'
            return 'resolved'
        except Exception:
            return 'unresolved'

    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR')

        # Check if IP is blocked
        if ip in self.blocked_ips:
            logger.warning(f'Blocked IP attempt: {ip}')
            return HttpResponseForbidden('Access denied')

        # Check IP reputation
        ip_reputation = self.check_ip_reputation(ip)
        if ip_reputation in ['malicious', 'tor']:
            logger.warning(f'Malicious IP detected: {ip}')
            self.blocked_ips.add(ip)
            return HttpResponseForbidden('Access denied')

        # Check for suspicious activity
        if self.analyze_request_patterns(request):
            self.blocked_ips.add(ip)
            return HttpResponseForbidden('Access denied')

        # Add security headers
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        response['X-Content-Security-Policy'] = "default-src 'self'"
        response['X-WebKit-CSP'] = "default-src 'self'"
        response['Feature-Policy'] = "geolocation 'none'; microphone 'none'; camera 'none'"

        return response
