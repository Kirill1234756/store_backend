from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import os
import zipfile
import shutil
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Backup database and media files'

    def handle(self, *args, **options):
        self.stdout.write('Starting backup...')

        # Create backup directory if it doesn't exist
        os.makedirs(settings.BACKUP_ROOT, exist_ok=True)

        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(settings.BACKUP_ROOT, backup_filename)

        # Create zip file
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup database
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                zipf.write(db_path, os.path.basename(db_path))

            # Backup media files
            media_root = settings.MEDIA_ROOT
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, media_root)
                        zipf.write(file_path, arcname)

        # Clean up old backups
        self.cleanup_old_backups()

        self.stdout.write(f'Backup completed: {backup_path}')

    def cleanup_old_backups(self):
        now = timezone.now()

        # Get all backup files
        backup_files = []
        for filename in os.listdir(settings.BACKUP_ROOT):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                file_path = os.path.join(settings.BACKUP_ROOT, filename)
                backup_files.append((file_path, os.path.getmtime(file_path)))

        # Sort by modification time
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Remove old backups based on retention policy
        for file_path, mtime in backup_files:
            file_date = datetime.fromtimestamp(mtime)
            age = now - file_date

            if age > timedelta(days=settings.BACKUP_RETENTION['daily']):
                os.remove(file_path)
                self.stdout.write(f'Removed old backup: {file_path}')
