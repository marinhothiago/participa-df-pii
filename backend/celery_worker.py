from celery import Celery
import os

# Config Celery/Redis
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('backend', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600

# Importa tasks para registrar
import celery_worker_tasks  # noqa: F401
