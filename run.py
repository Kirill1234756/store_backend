import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    # Set environment variables
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["PYTHONUTF8"] = "1"
    
    # Run the server
    execute_from_command_line(["manage.py", "runserver", "--noreload"]) 