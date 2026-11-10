import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    athlete_profile = relationship("AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AgentAuditLog", back_populates="user", cascade="all, delete-orphan")
