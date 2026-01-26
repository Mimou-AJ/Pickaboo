"""Repository for product database operations and vector search."""
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from .entity import Product
from .embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)


class ProductRepository:
    """Repository for product data access and vector search operations."""
    
    def __init__(self, session: Session, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy database session
            embedding_service: Optional embedding service for queries (created if not provided)
        """
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        gender_filter: Optional[str] = None
    ) -> List[Tuple[Product, float]]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_price: Minimum price filter (inclusive)
            max_price: Maximum price filter (inclusive)
            gender_filter: Filter by gender ("men", "women", "unisex")
            
        Returns:
            List of (Product, similarity_score) tuples, sorted by similarity
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build SQL query with filters
        filters = ["embedding IS NOT NULL"]
        params = {
            "embedding": query_embedding,
            "top_k": top_k
        }
        
        if min_price is not None:
            filters.append("price_eur >= :min_price")
            params["min_price"] = min_price
        
        if max_price is not None:
            filters.append("price_eur <= :max_price")
            params["max_price"] = max_price
        
        if gender_filter:
            filters.append("(gender_target = :gender_filter OR gender_target = 'unisex')")
            params["gender_filter"] = gender_filter.lower()
        
        where_clause = " AND ".join(filters)
        
        # Execute vector similarity search
        # Using cosine distance operator <=> (lower is better, 0 = identical)
        query_sql = text(f"""
            SELECT 
                id,
                1 - (embedding <=> :embedding) AS similarity
            FROM products
            WHERE {where_clause}
            ORDER BY embedding <=> :embedding
            LIMIT :top_k
        """)
        
        logger.debug(f"Executing semantic search: query='{query[:50]}...', top_k={top_k}, filters={filters}")
        
        result = self.session.execute(query_sql, params)
        rows = result.fetchall()
        
        # Fetch full Product objects and pair with similarity scores
        results = []
        for row in rows:
            product_id, similarity = row
            product = self.session.query(Product).filter(Product.id == product_id).first()
            if product:
                results.append((product, float(similarity)))
        
        logger.info(f"Found {len(results)} products for query: '{query[:50]}...'")
        return results
    
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get a product by its ID.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Product or None if not found
        """
        return self.session.query(Product).filter(Product.id == product_id).first()
    
    def count_products(self) -> int:
        """
        Count total products in database.
        
        Returns:
            Total number of products
        """
        return self.session.query(Product).count()
    
    def upsert_product(self, product_data: dict, embedding: List[float]) -> Product:
        """
        Insert or update a product.
        
        Args:
            product_data: Product attributes dictionary
            embedding: Product embedding vector
            
        Returns:
            Saved Product instance
        """
        # Check if product exists
        existing = self.session.query(Product).filter(
            Product.store_product_id == product_data["store_product_id"],
            Product.store_url == product_data["store_url"]
        ).first()
        
        if existing:
            # Update existing product
            for key, value in product_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.embedding = embedding
            logger.debug(f"Updated product: {existing.name}")
            return existing
        else:
            # Create new product
            product = Product(**product_data, embedding=embedding)
            self.session.add(product)
            logger.debug(f"Created new product: {product.name}")
            return product
