import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
import django
django.setup()
from django.contrib.auth.models import User
from django.test import Client

# Create a test user (if not exists)
username = 'ci_test'
password = 'secret123'
if not User.objects.filter(username=username).exists():
    User.objects.create_user(username=username, email='ci_test@example.com', password=password)
    print('created user', username)
else:
    print('user already exists', username)

c = Client()
r = c.post('/login/', {'username': username, 'password': password}, follow=True)
print('POST /login/ status:', r.status_code)
print('redirect_chain:', r.redirect_chain)
print('final_path:', r.request.get('PATH_INFO'))

# Access protected page to verify login
resp = c.get('/')
print('GET / status:', resp.status_code)

# Check if session indicates authenticated user
from django.contrib.auth import get_user
user = get_user(resp.wsgi_request)
print('client authenticated:', user.is_authenticated, 'username:', getattr(user, 'username', None))
