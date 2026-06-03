"""
WSGI config for expense_tracker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import threading
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from expense_app.scheduler import run_scheduler


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_tracker.settings')

application = get_wsgi_application()


if getattr(settings, 'SCHEDULER_ENABLED', False):
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()