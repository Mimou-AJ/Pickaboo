"""Service for importing products from JSON files."""
from typing import Dict
import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from .entity import Product
from .transformer import ProductTransformer
from .embedding_service import EmbeddingService
from .repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductImportService:
    """Pipeline for importing product data from JSON files."""
    
    def __init__(self, session: Session):
        """
        Initialize import service.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.repository = ProductRepository(session)
        self.transformer = ProductTransformer()
        self.embedding_service = EmbeddingService()
    
    def import_from_json(self, json_path: str) -> Dict[str, int]:
        """
        Import products from JSON file.
        
        Pipeline steps:
        1. Load raw JSON with variant-level data
        2. Transform variants to products
        3. Generate embeddings
        4. Check for existing products
        5. Update or create records
        6. Commit to database
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Dictionary with statistics:
            - total_variants: Number of variants in file
            - unique_products: Number of unique products
            - newly_saved: Number of new products created
            - updated: Number of existing products updated
        """
        logger.info(f"Starting import from {json_path}")
        
        # 1. Load raw JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_variants = json.load(f)
        
        total_variants = len(raw_variants)
        logger.info(f"Loaded {total_variants} variants from JSON")
        
        if not raw_variants:
            return {
                "total_variants": 0,
                "unique_products": 0,
                "newly_saved": 0,
                "updated": 0
            }
        
        # 2. Transform variants to products
        products = self.transformer.transform_variants_to_products(raw_variants)
        unique_products = len(products)
        logger.info(f"Transformed into {unique_products} unique products")
        
        # 3. Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.embedding_service.embed_products_batch(products)
        
        # Add embeddings to products
        for product, embedding in zip(products, embeddings):
            product["embedding"] = embedding
        
        # 4-5. Check for existing and save/update
        newly_saved = 0
        updated = 0
        
        for product_data in products:
            try:
                # Check if product exists
                existing = self.repository.get_by_store_id(
                    product_data["store_product_id"],
                    product_data["store_url"]
                )
                
                if existing:
                    # Update existing product
                    existing.name = product_data["name"]
                    existing.vendor = product_data.get("vendor")
                    existing.product_type = product_data.get("product_type")
                    existing.price_eur = product_data.get("price_eur")
                    existing.price_min = product_data.get("price_min")
                    existing.price_max = product_data.get("price_max")
                    existing.available = product_data.get("available", True)
                    existing.colors = product_data.get("colors")
                    existing.sizes = product_data.get("sizes")
                    existing.gender_target = product_data.get("gender_target")
                    existing.tags = product_data.get("tags")
                    existing.variants = product_data.get("variants")
                    existing.description = product_data.get("description")
                    existing.image_url = product_data.get("image_url")
                    existing.product_url = product_data.get("product_url")
                    existing.embedding = product_data.get("embedding")
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    # Create new product
                    product = Product(
                        store_product_id=product_data["store_product_id"],
                        store_url=product_data["store_url"],
                        product_url=product_data.get("product_url"),
                        name=product_data["name"],
                        vendor=product_data.get("vendor"),
                        product_type=product_data.get("product_type"),
                        price_eur=product_data.get("price_eur"),
                        price_min=product_data.get("price_min"),
                        price_max=product_data.get("price_max"),
                        available=product_data.get("available", True),
                        colors=product_data.get("colors"),
                        sizes=product_data.get("sizes"),
                        gender_target=product_data.get("gender_target"),
                        tags=product_data.get("tags"),
                        variants=product_data.get("variants"),
                        description=product_data.get("description"),
                        image_url=product_data.get("image_url"),
                        embedding=product_data.get("embedding")
                    )
                    self.repository.save(product)
                    newly_saved += 1
                    
            except Exception as e:
                logger.error(f"Error saving product {product_data.get('name')}: {e}")
                continue
        
        # 6. Commit transaction
        self.session.commit()
        logger.info(f"Import complete: {newly_saved} new, {updated} updated")
        
        return {
            "total_variants": total_variants,
            "unique_products": unique_products,
            "newly_saved": newly_saved,
            "updated": updated
        }
