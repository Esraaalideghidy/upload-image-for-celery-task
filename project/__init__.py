from .celery import app as celery_app

# Expose Celery app as a package-level variable
__all__ = ('celery_app',)
