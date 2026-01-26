"""FastAPI controller for product endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional
from uuid import UUID
from ..database.core import DbSession
from .models import ProductResponse, ProductSearchRequest, ImportStatsResponse
from .repository import ProductRepository
from .import_service import ProductImportService
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/import", response_model=ImportStatsResponse)
async def import_products(
    file: UploadFile = File(...),
    session: DbSession = None
):
    """
    Import products from uploaded JSON file.
    
    Args:
        file: Uploaded JSON file with product variants
        session: Database session
        
    Returns:
        Import statistics
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Import products
        import_service = ProductImportService(session)
        stats = import_service.import_from_json(tmp_path)
        
        return ImportStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error importing products: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/search", response_model=List[ProductResponse])
def search_products(
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    gender: Optional[str] = Query(None, description="Gender filter (men/women/unisex)"),
    session: DbSession = None
):
    """
    Semantic search for products.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        min_price: Minimum price filter
        max_price: Maximum price filter
        gender: Gender filter
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
        
        # Convert to response models (without similarity scores for this endpoint)
        products = [ProductResponse.model_validate(product) for product, _ in results]
        return products
    
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


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
