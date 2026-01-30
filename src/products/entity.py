"""SQLAlchemy entity model for Product."""
from sqlalchemy import Column, String, Float, Boolean, TIMESTAMP, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
from ..database.core import Base


class Product(Base):
    """Product entity with vector embeddings for semantic search."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_product_id = Column(String(100), nullable=False)
    store_url = Column(String(500), nullable=False)
    product_url = Column(String(1000))
    name = Column(String(500), nullable=False)
    vendor = Column(String(200))
    product_type = Column(String(200))
    price_eur = Column(Float)
    price_min = Column(Float)
    price_max = Column(Float)
    available = Column(Boolean, default=True)
    colors = Column(ARRAY(Text))
    sizes = Column(ARRAY(Text))
    gender_target = Column(String(50))
    tags = Column(ARRAY(Text))
    variants = Column(JSON)
    description = Column(Text)
    image_url = Column(String(1000))
    embedding = Column(Vector(384))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price_eur})>"
