from sqlalchemy.orm import relationship

actions = relationship(
    "WorkflowAction", back_populates="workflow", cascade="all, delete"
)


conditions = relationship(
    "WorkflowCondition", back_populates="workflow", cascade="all, delete"
)
