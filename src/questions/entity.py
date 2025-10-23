from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from ..database.core import Base
from ..build_persona.entity import Persona

class Question(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey('personas.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    choices = Column(JSONB, nullable=False)  # Store the available choices as JSONB array
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Question(id='{self.id}', question_text='{self.question_text}')>"

class Answer(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'), nullable=False)
    selected_choice_text = Column(Text, nullable=False)  # Store the actual choice text selected
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Answer(id='{self.id}', selected_choice='{self.selected_choice_text}')>"
