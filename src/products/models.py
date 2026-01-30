"""Pydantic models for products API."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID


class ProductResponse(BaseModel):
    """API response model for a product."""
    id: UUID
    store_product_id: str
    store_url: str
    product_url: Optional[str] = None
    name: str
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    price_eur: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    available: bool = True
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    gender_target: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class MatchedProductResponse(BaseModel):
    """Product with matching metadata from RAG pipeline."""
    # Product details
    id: UUID
    name: str
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    price_eur: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    available: bool = True
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    gender_target: Optional[str] = None
    tags: Optional[List[str]] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    
    # Matching metadata
    similarity_score: float
    match_reasoning: str
    confidence: float
    
    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    """Search request parameters."""
    query: str
    top_k: int = 10
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    gender_filter: Optional[str] = None


class ImportStatsResponse(BaseModel):
    """Statistics from product import operation."""
    total_variants: int
    unique_products: int
    newly_saved: int
    updated: int
    message: str
