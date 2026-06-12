from enum import Enum


class WorkflowStatus(str, Enum):

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"


class UserRole(str, Enum):

    OWNER = "OWNER"

    ADMIN = "ADMIN"

    MEMBER = "MEMBER"
