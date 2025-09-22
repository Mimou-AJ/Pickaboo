from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
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

class Budget(str, enum.Enum):
    under_50 = "<50"
    between_50_100 = "50-100"
    between_100_200 = "100-200"
    over_200 = "200+"
    no_limit = "no_limit"

class AgeRange(str, enum.Enum):
    age_0_2 = "0-2"
    age_3_5 = "3-5"
    age_6_9 = "6-9"
    age_10_12 = "10-12"
    age_13_17 = "13-17"
    age_18_24 = "18-24"
    age_25_34 = "25-34"
    age_35_44 = "35-44"
    age_45_54 = "45-54"
    age_55_64 = "55-64"
    age_65_plus = "65+"

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
    budget = Column(Enum(Budget), nullable=False)
    age_range = Column(Enum(AgeRange), nullable=False)
    gender = Column(Enum(Gender), nullable=True)
    relationship = Column(Enum(Relationship), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Persona(id='{self.id}')>"
