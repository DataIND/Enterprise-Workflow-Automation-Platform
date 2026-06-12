from datetime import datetime, timedelta


from app.workers.celery_app import celery_app


@celery_app.task
def cleanup_old_logs():

    print("Cleaning old logs", datetime.utcnow())
