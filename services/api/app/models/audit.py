import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class AgentAuditLog(Base, TimestampMixin):
    __tablename__ = "agent_audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    input_snapshot = Column(JSON, nullable=False)
    output_snapshot = Column(JSON, nullable=False)
    validation_passed = Column(Boolean, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    error_info = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
