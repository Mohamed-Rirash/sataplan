import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import URLType

from app.db import Base

if TYPE_CHECKING:
    ...


class Motivation(Base):
    __tablename__ = "motivations"

    id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid
    )

    quote = Column(String(500), index=True, nullable=True, default=None)
    link = Column(URLType, index=True, nullable=True, default=None)

    goal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Use a string for the relationship to avoid circular imports
    goal = relationship("Goal", back_populates="motivation", lazy="joined")
