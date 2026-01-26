"""FastAPI controller for products endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from uuid import UUID
import tempfile
import os
import logging

from ..database.core import DbSession
from .models import (
    ProductResponse,
    ProductSearchRequest,
    ImportStatsResponse
)
from .repository import ProductRepository
from .import_service import ProductImportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/import", response_model=ImportStatsResponse)
async def import_products(
    file: UploadFile = File(...),
    session: DbSession = None
):
    """
    Import products from JSON file.
    
    Upload a JSON file with variant-level product data.
    The service will transform, aggregate, generate embeddings, and store products.
    
    Args:
        file: JSON file upload
        session: Database session
        
    Returns:
        Import statistics
    """
    logger.info(f"Received import request for file: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Import products
        import_service = ProductImportService(session)
        stats = import_service.import_from_json(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        message = f"Successfully imported {stats['newly_saved']} new products and updated {stats['updated']} existing products"
        
        return ImportStatsResponse(
            total_variants=stats["total_variants"],
            unique_products=stats["unique_products"],
            newly_saved=stats["newly_saved"],
            updated=stats["updated"],
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error importing products: {e}")
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error importing products: {str(e)}")


@router.get("/search", response_model=List[ProductResponse])
def search_products(
    query: str,
    top_k: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    gender: Optional[str] = None,
    session: DbSession = None
):
    """
    Semantic search for products.
    
    Search products using natural language queries with vector similarity.
    Supports filtering by price range and gender.
    
    Args:
        query: Search query string
        top_k: Number of results to return (default: 10)
        min_price: Minimum price filter
        max_price: Maximum price filter
        gender: Gender filter (women/men/unisex)
        session: Database session
        
    Returns:
        List of matching products
    """
    try:
        repository = ProductRepository(session)
        results = repository.semantic_search(
            query=query,
            top_k=top_k,
            min_price=min_price,
            max_price=max_price,
            gender_filter=gender
        )
        
        # Convert to response models
        products = [ProductResponse.model_validate(product) for product, _ in results]
        
        return products
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    session: DbSession = None
):
    """
    Get a single product by ID.
    
    Args:
        product_id: Product UUID
        session: Database session
        
    Returns:
        Product details
    """
    repository = ProductRepository(session)
    product = repository.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.model_validate(product)


@router.get("/stats/count")
def get_product_count(session: DbSession = None):
    """
    Get total product count.
    
    Args:
        session: Database session
        
    Returns:
        Total product count
    """
    repository = ProductRepository(session)
    count = repository.count_products()
    
    return {"total_products": count}
