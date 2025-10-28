"""Repository for managing message history persistence"""
from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from pydantic_ai import ModelMessage, ModelMessagesTypeAdapter
from .entity import MessageHistory


class MessageRepository:
    """Handles storage and retrieval of Pydantic AI message history"""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def store_messages(self, persona_id: UUID, messages_json: bytes) -> None:
        """Store new messages for a persona"""
        message_history = MessageHistory(
            persona_id=persona_id,
            messages_json=messages_json
        )
        self.session.add(message_history)
        self.session.commit()
    
    async def load_all_messages(self, persona_id: UUID) -> List[ModelMessage]:
        """Load all message history for a persona"""
        records = self.session.query(MessageHistory).filter(
            MessageHistory.persona_id == persona_id
        ).order_by(MessageHistory.created_at).all()
        
        messages: List[ModelMessage] = []
        for record in records:
            # Deserialize each batch of messages
            batch = ModelMessagesTypeAdapter.validate_json(record.messages_json)
            messages.extend(batch)
        
        return messages
    
    async def clear_history(self, persona_id: UUID) -> None:
        """Clear all message history for a persona"""
        self.session.query(MessageHistory).filter(
            MessageHistory.persona_id == persona_id
        ).delete()
        self.session.commit()


def get_message_repository(session: Session) -> MessageRepository:
    return MessageRepository(session)
