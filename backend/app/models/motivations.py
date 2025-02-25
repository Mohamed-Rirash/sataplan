from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from app.db import Base
from typing import TYPE_CHECKING
from sqlalchemy_utils import URLType

if TYPE_CHECKING:
    from app.models.goals import Goal  # Import only during type checking


class Motivation(Base):
    __tablename__ = "motivations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quote = Column(String(500), index=True, nullable=True, default=None)
    link = Column(URLType, index=True, nullable=True, default=None)

    goal_id = Column(
        Integer,
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Use a string for the relationship to avoid circular imports
    goal = relationship("Goal", back_populates="motivation", lazy="joined")
