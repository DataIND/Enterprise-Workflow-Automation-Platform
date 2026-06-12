from app.workers.celery_app import celery_app


from app.workers.tasks.email_tasks import send_email


@celery_app.task(bind=True, max_retries=3)
def execute_workflow(self, workflow_id, actions, payload):

    try:

        for action in actions:

            if action["type"] == "EMAIL":

                send_email.delay(payload["email"], "Workflow", "Executed")

        return "SUCCESS"

    except Exception as exc:

        raise self.retry(exc=exc, countdown=30)
