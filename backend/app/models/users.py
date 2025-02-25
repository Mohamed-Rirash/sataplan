from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base

if TYPE_CHECKING:
    pass  # Import only during type checking


class User(Base):
    __tablename__ = "users"

    # id = Column(uuid.uuid4, primary_key=True)
    id = Column(Integer, primary_key=True)
    # profile_image = Column(String)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="user", cascade="all, delete-orphan",uselist=False,lazy="joined")
    goal = relationship("Goal", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    firstname = Column(String)
    lastname = Column(String)
    bio = Column(String)
    user = relationship("User", back_populates="profile", lazy="joined", uselist=False)
