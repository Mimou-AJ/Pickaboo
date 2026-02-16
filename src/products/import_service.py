"""Service for importing products from JSON files."""
import json
import ijson
from decimal import Decimal
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from .transformer import ProductTransformer
from .embedding_service import EmbeddingService
from .repository import ProductRepository
from .entity import Product
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
    
    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively convert Decimals to floats for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(i) for i in obj]
        return obj

    def import_from_json(self, json_path: str, batch_size: int = 1000, max_bytes: Optional[int] = None) -> Dict[str, int]:
        """
        Import products from JSON file using streaming to handle large files.
        
        Args:
            json_path: Path to JSON file with product variants
            batch_size: Number of variants to process in memory at once
            max_bytes: Approximate limit in bytes to read from file (stops import after limit)
            
        Returns:
            Statistics dictionary with counts
        """
        logger.info(f"Starting streaming import from: {json_path}")
        if max_bytes:
            logger.info(f"Import limited to approximately {max_bytes / (1024*1024):.2f} MB")
        
        stats = {
            "total_variants": 0,
            "unique_products": 0,
            "newly_saved": 0,
            "updated": 0,
            "errors": 0
        }
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                # Use ijson to stream items from the root array
                # 'item' assumes the file is a list of objects [{}, {}, ...]
                variant_stream = ijson.items(f, 'item')
                
                batch = []
                stop_import = False
                
                for variant in variant_stream:
                    batch.append(variant)
                    
                    # Check limit
                    if max_bytes and f.tell() > max_bytes:
                        logger.info(f"Reached byte limit of {max_bytes}. Stopping import.")
                        stop_import = True
                    
                    if len(batch) >= batch_size or stop_import:
                        self._process_batch(batch, stats)
                        batch = []
                        if stop_import:
                            break
                
                # Process remaining
                if batch and not stop_import:
                    self._process_batch(batch, stats)
                    
            logger.info(f"Import complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Fatal error during import: {e}")
            raise

    def _process_batch(self, batch: List[Dict[str, Any]], stats: Dict[str, int]):
        """
        Process a batch of variants.
        """
        if not batch:
            return

        current_variants_count = len(batch)
        stats["total_variants"] += current_variants_count
        logger.info(f"Processing batch of {current_variants_count} variants...")

        # Transform
        products = self.transformer.transform_variants_to_products(batch)
        unique_cnt = len(products)
        stats["unique_products"] += unique_cnt

        if not products:
            return

        # Sanitize products (convert Decimals to floats)
        products = [self._sanitize_for_json(p) for p in products]

        # Generate embeddings
        try:
            # Increased batch size for faster embedding generation (default was 32)
            embeddings = self.embedding_service.embed_products_batch(products, batch_size=128)
            
            # Upsert
            for product_data, embedding in zip(products, embeddings):
                try:
                    # Check existence (optional, can be skipped for speed if upsert handles it well)
                    # But we need it for stats
                    existing = self.session.query(Product).filter_by(
                        store_product_id=product_data["store_product_id"],
                        store_url=product_data["store_url"]
                    ).first()

                    self.repository.upsert_product(product_data, embedding)
                    
                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["newly_saved"] += 1
                
                except Exception as e:
                    logger.error(f"Error saving product {product_data.get('name')}: {e}")
                    stats["errors"] += 1
            
            # Commit AFTER EACH BATCH
            self.session.commit()
            logger.info(f"Committed batch. Total so far: {stats['unique_products']} products.")

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.session.rollback()
            stats["errors"] += len(products)
