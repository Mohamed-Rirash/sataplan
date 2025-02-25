from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

if TYPE_CHECKING:
    pass  # Import only during type checking


class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(80), index=True, nullable=False)
    description = Column(String, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Use a string for the relationship to avoid circular imports
    user = relationship("User", back_populates="goal", lazy="joined")
    motivation = relationship(
        "Motivation", back_populates="goal", cascade="all, delete-orphan"
    )
