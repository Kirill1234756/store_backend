import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    # Set environment variables
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["PYTHONUTF8"] = "1"
    
    # Disable HTTPS redirects
    os.environ["SECURE_SSL_REDIRECT"] = "False"
    os.environ["SESSION_COOKIE_SECURE"] = "False"
    os.environ["CSRF_COOKIE_SECURE"] = "False"
    
    # Run the server
    execute_from_command_line(["manage.py", "runserver", "--noreload"]) 