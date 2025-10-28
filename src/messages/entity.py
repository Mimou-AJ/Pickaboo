from sqlalchemy import Column, DateTime, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from ..database.core import Base


class MessageHistory(Base):
    """Store raw Pydantic AI message history for each persona"""
    __tablename__ = 'message_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey('personas.id'), nullable=False)
    messages_json = Column(LargeBinary, nullable=False)  # Stores serialized messages
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<MessageHistory(persona_id='{self.persona_id}')>"
