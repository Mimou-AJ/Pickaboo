from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
import enum
from ..database.core import Base


class Occasion(str, enum.Enum):
    birthday = "birthday"
    christmas = "christmas"
    valentine = "valentine"
    graduation = "graduation"
    wedding = "wedding"
    babyshower = "babyshower"
    other = "other"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non-binary"


class Relationship(str, enum.Enum):
    partner = "partner"
    parent = "parent"
    child = "child"
    sibling = "sibling"
    friend = "friend"
    colleague = "colleague"
    acquaintance = "acquaintance"
    other = "other"


class Persona(Base):
    __tablename__ = 'personas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    occasion = Column(Enum(Occasion), nullable=False)

    # Updated: removed budget, replaced age_range with integer age
    age = Column(Integer, nullable=False)

    gender = Column(Enum(Gender), nullable=True)
    relationship = Column(Enum(Relationship), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Persona(id='{self.id}')>"
