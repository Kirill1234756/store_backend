from rest_framework.throttling import UserRateThrottle

class ProductRateThrottle(UserRateThrottle):
    rate = '100/day'  # Allow 100 requests per day per user 