from celery import Celery

celery = Celery(broker='mongodb://localhost:27017/database_name')
