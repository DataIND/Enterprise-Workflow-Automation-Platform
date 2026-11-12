"""Handlers for every action type the workflow API accepts.

Handlers raise on failure so the calling Celery task can retry with backoff.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable

from app.db.models.notification import Notification
from app.db.models.workflow_action import WorkflowAction
from app.engine.matcher import organization_member_ids
from app.integrations.email.smtp_client import SMTPClient
from app.integrations.slack.slack_client import SlackClient
from app.integrations.webhook.webhook_client import WebhookClient
from app.utils.enums import ActionType

logger = logging.getLogger(__name__)


@dataclass
class ActionContext:
    session: Any
    organization_id: int
    workflow_id: int
    execution_id: int
    payload: dict


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def render(template: Any, payload: dict) -> Any:
    """Substitute {placeholders} from the event payload, leaving unknown keys."""

    if not isinstance(template, str):
        return template

    try:
        return template.format_map(_SafeDict(payload))
    except (IndexError, ValueError):
        return template


def _handle_email(action: WorkflowAction, context: ActionContext) -> dict:
    config = action.config or {}

    recipient = render(config.get("to"), context.payload) or context.payload.get("email")

    if not recipient:
        raise ValueError("EMAIL action requires a 'to' config value or payload.email")

    subject = render(config.get("subject", "Workflow notification"), context.payload)
    body = render(config.get("body", ""), context.payload)

    sent = SMTPClient.send(recipient, subject, body)

    return {"type": ActionType.EMAIL.value, "to": recipient, "sent": sent}


def _handle_webhook(action: WorkflowAction, context: ActionContext) -> dict:
    config = action.config or {}

    url = render(config.get("url"), context.payload)

    if not url:
        raise ValueError("WEBHOOK action requires a 'url' config value")

    body = config.get("body") or {
        "workflow_id": context.workflow_id,
        "execution_id": context.execution_id,
        "payload": context.payload,
    }

    response = WebhookClient.post(url, body)
    response.raise_for_status()

    return {"type": ActionType.WEBHOOK.value, "url": url, "status": response.status_code}


def _handle_slack(action: WorkflowAction, context: ActionContext) -> dict:
    config = action.config or {}

    webhook_url = render(config.get("webhook_url"), context.payload)

    if not webhook_url:
        raise ValueError("SLACK action requires a 'webhook_url' config value")

    message = render(config.get("message", "Workflow executed"), context.payload)

    response = SlackClient.send_message(webhook_url, message)
    response.raise_for_status()

    return {"type": ActionType.SLACK.value, "status": response.status_code}


def _handle_notification(action: WorkflowAction, context: ActionContext) -> dict:
    config = action.config or {}

    title = render(config.get("title", "Workflow notification"), context.payload)
    message = render(config.get("message", ""), context.payload)

    target = config.get("user_id")
    user_ids = (
        [int(target)]
        if target is not None
        else organization_member_ids(context.session, context.organization_id)
    )

    for user_id in user_ids:
        context.session.add(
            Notification(user_id=user_id, title=title, message=message)
        )

    context.session.commit()

    return {"type": ActionType.NOTIFICATION.value, "recipients": len(user_ids)}


ACTION_HANDLERS: dict[str, Callable[[WorkflowAction, ActionContext], dict]] = {
    ActionType.EMAIL.value: _handle_email,
    ActionType.WEBHOOK.value: _handle_webhook,
    ActionType.SLACK.value: _handle_slack,
    ActionType.NOTIFICATION.value: _handle_notification,
}


def run_action(action: WorkflowAction, context: ActionContext) -> dict:
    handler = ACTION_HANDLERS.get(action.action_type)

    if handler is None:
        raise ValueError(f"Unsupported action type: {action.action_type}")

    return handler(action, context)


def load_ordered_actions(session, workflow_id: int) -> list[WorkflowAction]:
    from sqlalchemy import select

    return list(
        session.execute(
            select(WorkflowAction)
            .where(WorkflowAction.workflow_id == workflow_id)
            .order_by(WorkflowAction.execution_order, WorkflowAction.id)
        )
        .scalars()
        .all()
    )


def queue_for(action_type: str) -> str:
    from app.core.config import settings

    if action_type == ActionType.EMAIL.value:
        return settings.EMAIL_QUEUE

    if action_type in (ActionType.WEBHOOK.value, ActionType.SLACK.value):
        return settings.WEBHOOK_QUEUE

    return "celery"
