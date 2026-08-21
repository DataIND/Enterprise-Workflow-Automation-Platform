from enum import Enum


class WorkflowStatus(str, Enum):

    PENDING = "PENDING"

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"


class UserRole(str, Enum):

    OWNER = "OWNER"

    ADMIN = "ADMIN"

    MEMBER = "MEMBER"


class ActionType(str, Enum):

    EMAIL = "EMAIL"

    WEBHOOK = "WEBHOOK"

    SLACK = "SLACK"

    NOTIFICATION = "NOTIFICATION"


class ConditionOperator(str, Enum):

    EQ = "eq"

    NE = "ne"

    GT = "gt"

    GTE = "gte"

    LT = "lt"

    LTE = "lte"

    CONTAINS = "contains"

    IN = "in"
