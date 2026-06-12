import requests


from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def send_webhook(self, url, payload):

    try:

        response = requests.post(url, json=payload)

        return response.status_code

    except Exception as exc:

        raise self.retry(exc=exc, countdown=20)
