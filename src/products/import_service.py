"""Service for importing products from JSON files."""
import json
from typing import Dict
from sqlalchemy.orm import Session
from .transformer import ProductTransformer
from .embedding_service import EmbeddingService
from .repository import ProductRepository
import logging

logger = logging.getLogger(__name__)


class ProductImportService:
    """Service for importing product data from JSON files."""
    
    def __init__(self, session: Session):
        """
        Initialize import service.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.transformer = ProductTransformer()
        self.embedding_service = EmbeddingService()
        self.repository = ProductRepository(session, self.embedding_service)
    
    def import_from_json(self, json_path: str) -> Dict[str, int]:
        """
        Import products from JSON file.
        
        Pipeline:
        1. Load raw JSON with variant-level data
        2. Transform variants → products
        3. Generate embeddings
        4. Upsert to database
        5. Return statistics
        
        Args:
            json_path: Path to JSON file with product variants
            
        Returns:
            Statistics dictionary with counts
        """
        logger.info(f"Starting import from: {json_path}")
        
        # 1. Load JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_variants = json.load(f)
        
        total_variants = len(raw_variants)
        logger.info(f"Loaded {total_variants} variant records")
        
        # 2. Transform variants to products
        products = self.transformer.transform_variants_to_products(raw_variants)
        unique_products = len(products)
        logger.info(f"Transformed into {unique_products} unique products")
        
        if not products:
            logger.warning("No products to import")
            return {
                "total_variants": total_variants,
                "unique_products": 0,
                "newly_saved": 0,
                "updated": 0
            }
        
        # 3. Generate embeddings in batch
        logger.info("Generating embeddings...")
        embeddings = self.embedding_service.embed_products_batch(products)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # 4. Upsert products to database
        newly_saved = 0
        updated = 0
        
        for product_data, embedding in zip(products, embeddings):
            try:
                # Check if exists before upserting to track stats
                existing = self.session.query(
                    self.repository.Product.__class__
                ).filter_by(
                    store_product_id=product_data["store_product_id"],
                    store_url=product_data["store_url"]
                ).first()
                
                # Upsert
                self.repository.upsert_product(product_data, embedding)
                
                if existing:
                    updated += 1
                else:
                    newly_saved += 1
                    
            except Exception as e:
                logger.error(f"Error saving product {product_data.get('name')}: {e}")
                continue
        
        # Commit transaction
        self.session.commit()
        
        stats = {
            "total_variants": total_variants,
            "unique_products": unique_products,
            "newly_saved": newly_saved,
            "updated": updated
        }
        
        logger.info(f"Import complete: {stats}")
        return stats
