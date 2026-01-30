"""Repository for product database operations and vector search."""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
import logging

from .entity import Product
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ProductRepository:
    """Handle database operations and vector search for products."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.embedding_service = EmbeddingService()
    
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
            query: Search query string
            top_k: Number of results to return
            min_price: Minimum price filter
            max_price: Maximum price filter
            gender_filter: Gender filter (women/men/unisex)
            
        Returns:
            List of (Product, similarity_score) tuples, ordered by similarity
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build SQL query with filters
        sql = """
            SELECT 
                id, store_product_id, store_url, product_url, name, vendor, 
                product_type, price_eur, price_min, price_max, available, 
                colors, sizes, gender_target, tags, variants, description, 
                image_url, embedding, created_at, updated_at,
                1 - (embedding <=> :query_embedding) as similarity
            FROM products
            WHERE embedding IS NOT NULL
        """
        
        params = {"query_embedding": str(query_embedding), "top_k": top_k}
        
        # Add price filters
        if min_price is not None:
            sql += " AND price_eur >= :min_price"
            params["min_price"] = min_price
        
        if max_price is not None:
            sql += " AND price_eur <= :max_price"
            params["max_price"] = max_price
        
        # Add gender filter
        if gender_filter:
            sql += " AND (gender_target = :gender_filter OR gender_target = 'unisex')"
            params["gender_filter"] = gender_filter
        
        # Order by similarity and limit
        sql += " ORDER BY embedding <=> :query_embedding LIMIT :top_k"
        
        # Execute query
        result = self.session.execute(text(sql), params)
        rows = result.fetchall()
        
        # Convert to Product objects with similarity scores
        products_with_scores = []
        for row in rows:
            product = Product(
                id=row.id,
                store_product_id=row.store_product_id,
                store_url=row.store_url,
                product_url=row.product_url,
                name=row.name,
                vendor=row.vendor,
                product_type=row.product_type,
                price_eur=row.price_eur,
                price_min=row.price_min,
                price_max=row.price_max,
                available=row.available,
                colors=row.colors,
                sizes=row.sizes,
                gender_target=row.gender_target,
                tags=row.tags,
                variants=row.variants,
                description=row.description,
                image_url=row.image_url,
                embedding=row.embedding,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            similarity = float(row.similarity)
            products_with_scores.append((product, similarity))
        
        logger.info(f"Semantic search for '{query}' returned {len(products_with_scores)} results")
        return products_with_scores
    
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get product by ID.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Product or None if not found
        """
        return self.session.query(Product).filter(Product.id == product_id).first()
    
    def count_products(self) -> int:
        """
        Count total number of products.
        
        Returns:
            Total product count
        """
        return self.session.query(Product).count()
    
    def save(self, product: Product) -> Product:
        """
        Save or update a product.
        
        Args:
            product: Product entity
            
        Returns:
            Saved product
        """
        self.session.add(product)
        self.session.flush()
        return product
    
    def get_by_store_id(self, store_product_id: str, store_url: str) -> Optional[Product]:
        """
        Get product by store product ID and store URL.
        
        Args:
            store_product_id: Store's product ID
            store_url: Store URL
            
        Returns:
            Product or None if not found
        """
        return self.session.query(Product).filter(
            Product.store_product_id == store_product_id,
            Product.store_url == store_url
        ).first()
