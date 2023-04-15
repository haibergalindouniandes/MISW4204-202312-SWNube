#!/bin/sh
gunicorn --bind 0.0.0.0:5000 manager:app
celery -A worker.celery worker --pool=solo -l info