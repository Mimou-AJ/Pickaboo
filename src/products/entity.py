"""SQLAlchemy entity model for Product."""
from sqlalchemy import Column, String, Float, Boolean, TIMESTAMP, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
from uuid import uuid4
from ..database.core import Base


class Product(Base):
    """Product entity with vector embeddings for semantic search."""
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Store identification
    store_product_id = Column(String(100), nullable=False)
    store_url = Column(String(500), nullable=False)
    product_url = Column(String(1000))
    
    # Basic product information
    name = Column(String(500), nullable=False)
    vendor = Column(String(200))
    product_type = Column(String(200))
    
    # Pricing
    price_eur = Column(Float)
    price_min = Column(Float)
    price_max = Column(Float)
    
    # Availability
    available = Column(Boolean, default=True)
    
    # Extracted attributes
    colors = Column(ARRAY(Text))
    sizes = Column(ARRAY(Text))
    gender_target = Column(String(50))
    tags = Column(ARRAY(Text))
    
    # Raw data
    variants = Column(JSONB)
    description = Column(Text)
    image_url = Column(String(1000))
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384))
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', vendor='{self.vendor}')>"
