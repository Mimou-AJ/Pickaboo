"""Embedding service using sentence transformers for semantic search."""
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate vector embeddings for products using sentence transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model.
        
        Args:
            model_name: Sentence transformer model name (default: all-MiniLM-L6-v2)
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")
    
    def build_product_text(self, product: Dict) -> str:
        """
        Build rich searchable text from product attributes.
        
        Concatenates:
        1. Product name (highest weight)
        2. Vendor/brand
        3. Product type
        4. Generated tags
        5. Available colors
        6. Target gender
        7. Price tier indicator
        8. Description (if available, truncated)
        
        Args:
            product: Product dictionary
            
        Returns:
            Concatenated text string for embedding
        """
        sections = []
        
        # 1. Product name (most important)
        name = product.get("name", "")
        if name:
            sections.append(name)
        
        # 2. Vendor/brand
        vendor = product.get("vendor", "")
        if vendor:
            sections.append(vendor)
        
        # 3. Product type
        product_type = product.get("product_type", "")
        if product_type:
            sections.append(product_type)
        
        # 4. Tags
        tags = product.get("tags", [])
        if tags:
            sections.append(" ".join(tags))
        
        # 5. Colors
        colors = product.get("colors", [])
        if colors:
            sections.append(f"Colors: {' '.join(colors)}")
        
        # 6. Gender
        gender = product.get("gender_target", "")
        if gender and gender != "unisex":
            sections.append(f"For: {gender}")
        
        # 7. Price tier
        price = product.get("price_eur")
        if price is not None:
            price_tier = self._get_price_tier(price)
            sections.append(price_tier)
        
        # 8. Description (truncated)
        description = product.get("description", "")
        if description:
            truncated_desc = description[:500]
            sections.append(truncated_desc)
        
        # Join with delimiter
        return " | ".join(sections)
    
    def _get_price_tier(self, price: float) -> str:
        """
        Get price tier label based on price value.
        
        Args:
            price: Price in EUR
            
        Returns:
            Price tier label
        """
        if price < 25:
            return "budget affordable"
        elif price < 50:
            return "mid-range moderate"
        elif price < 100:
            return "premium"
        else:
            return "luxury high-end"
    
    def embed_product(self, product: Dict) -> List[float]:
        """
        Generate embedding for a single product.
        
        Args:
            product: Product dictionary
            
        Returns:
            Embedding vector as list of floats
        """
        text = self.build_product_text(product)
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_products_batch(self, products: List[Dict], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple products in batch.
        
        Args:
            products: List of product dictionaries
            batch_size: Batch size for encoding
            
        Returns:
            List of embedding vectors
        """
        if not products:
            return []
        
        # Build text for all products
        texts = [self.build_product_text(p) for p in products]
        
        # Generate embeddings in batch
        logger.info(f"Generating embeddings for {len(texts)} products in batches of {batch_size}")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query string
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
