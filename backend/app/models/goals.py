import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.utils.goal import Status

if TYPE_CHECKING:
    pass  # Import only during type checking


class Goal(Base):
    __tablename__ = "goals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(80), index=True, nullable=False)
    description = Column(String, index=True)
    status = Column(Enum(Status), nullable=False)
    due_date = Column(Date, nullable=False)

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
