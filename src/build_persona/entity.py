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


class BudgetRange(str, enum.Enum):
    under_25 = "under_25"      # Less than 25€
    range_25_50 = "25-50"      # 25-50€
    range_50_100 = "50-100"    # 50-100€
    over_100 = "over_100"      # More than 100€


class Persona(Base):
    __tablename__ = 'personas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    occasion = Column(Enum(Occasion), nullable=False)

    # Updated: removed age_range, added budget back as enum
    age = Column(Integer, nullable=False)
    budget = Column(Enum(BudgetRange), nullable=True)  # e.g., "under_25", "25-50", "50-100", "over_100"

    gender = Column(Enum(Gender), nullable=True)
    relationship = Column(Enum(Relationship), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Persona(id='{self.id}')>"
