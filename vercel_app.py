"""
Alternative entry point for Vercel deployment
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trucking_project.settings')

app = get_wsgi_application()
