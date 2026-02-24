"""Pydantic models for product API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


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
    variants: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MatchedProductResponse(BaseModel):
    """Product with matching metadata from RAG pipeline."""
    
    id: UUID
    name: str
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    price_eur: Optional[float] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    # Matching metadata
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    match_reasoning: str = Field(..., description="LLM explanation of why this product matches")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the match")
    
    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    """Request parameters for product search."""
    
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    gender_filter: Optional[str] = Field(None, description="Filter by gender (men/women/unisex)")


class ImportStatsResponse(BaseModel):
    """Statistics from product import operation."""
    
    total_variants: int = Field(..., description="Total variant records processed")
    unique_products: int = Field(..., description="Unique products after aggregation")
    newly_saved: int = Field(..., description="New products saved to database")
    updated: int = Field(..., description="Existing products updated")
