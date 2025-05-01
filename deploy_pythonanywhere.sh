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
ENDSSH \Users\user\Desktop\store-main\backend> python manage.py test
Found 0 test(s).
System check identified no issues (0 silenced).

----------------------------------------------------------------------
Ran 0 tests in 0.000s

OK
(venv) PS C:\Users\user\Desktop\store-main\backend>