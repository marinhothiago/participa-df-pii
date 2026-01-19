"""Configuração do Celery para processamento assíncrono de lotes."""
from celery import Celery
import os
import sys

# Adiciona diretórios ao path para imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

# Config Celery/Redis
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('backend', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600

# Importa tasks para registrar (com fallback para HF Spaces)
try:
    import backend.api.tasks  # noqa: F401
except ModuleNotFoundError:
    import api.tasks  # noqa: F401
