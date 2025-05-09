# wakili_stamp/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

# Should match your project name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakili_stamp.settings')
application = get_wsgi_application()
