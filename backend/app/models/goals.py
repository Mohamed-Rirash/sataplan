import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.goal import StatusEnum

from app.db import Base


if TYPE_CHECKING:
    pass  # Import only during type checking


class Goal(Base):
    __tablename__ = "goals"
    id = Column(UUID(), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(80), index=True, nullable=False)
    description = Column(String, index=True)
    status = Column(
        postgresql.ENUM(StatusEnum),
        default=StatusEnum.ACTIVE.value,
        nullable=False,
    )

    due_date = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Use a string for the relationship to avoid circular imports
    user = relationship("User", back_populates="goal", lazy="joined")
    motivation = relationship(
        "Motivation", back_populates="goal", cascade="all, delete-orphan"
    )
