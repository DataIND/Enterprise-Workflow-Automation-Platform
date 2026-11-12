"""Publishes execution state changes for WebSocket clients."""

from app.engine.matcher import organization_member_ids
from app.websocket import redis_bridge
from app.websocket.connection_manager import EXECUTIONS_TOPIC


def emit_execution_event(session, execution, organization_id: int) -> None:
    redis_bridge.publish_event(
        {
            "topic": EXECUTIONS_TOPIC,
            "type": "execution.status",
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "organization_id": organization_id,
            "status": execution.status,
            "error": execution.error_message,
            "retry_count": execution.retry_count,
            "user_ids": organization_member_ids(session, organization_id),
        }
    )
