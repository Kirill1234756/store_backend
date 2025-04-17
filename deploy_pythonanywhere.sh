#!/bin/bash

# Build and push Docker images
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml push

# SSH to PythonAnywhere and deploy
ssh yourusername@ssh.pythonanywhere.com << 'ENDSSH'
cd /home/yourusername/yourproject
git pull
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
ENDSSH 