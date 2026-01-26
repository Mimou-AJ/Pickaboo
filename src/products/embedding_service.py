"""Generate vector embeddings using sentence transformers."""
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings for products and queries."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def build_product_text(self, product: Dict) -> str:
        """
        Build rich searchable text from product attributes.
        
        Concatenates multiple fields with delimiters to create comprehensive
        text representation for embedding generation.
        
        Args:
            product: Product dictionary with attributes
            
        Returns:
            Constructed text for embedding
        """
        parts = []
        
        # 1. Product name (highest weight)
        if product.get("name"):
            parts.append(product["name"])
        
        # 2. Vendor/brand
        if product.get("vendor"):
            parts.append(product["vendor"])
        
        # 3. Product type
        if product.get("product_type"):
            parts.append(product["product_type"])
        
        # 4. Tags
        if product.get("tags"):
            tags_str = " ".join(product["tags"])
            parts.append(tags_str)
        
        # 5. Colors
        if product.get("colors"):
            colors_str = f"Colors: {' '.join(product['colors'])}"
            parts.append(colors_str)
        
        # 6. Gender
        if product.get("gender_target"):
            parts.append(f"For: {product['gender_target']}")
        
        # 7. Price tier
        if product.get("price_eur"):
            price_tier = self._get_price_tier(product["price_eur"])
            parts.append(price_tier)
        
        # 8. Description (truncated)
        if product.get("description"):
            desc = product["description"][:500]  # Limit to 500 chars
            parts.append(desc)
        
        # Join with delimiter
        return " | ".join(parts)
    
    def _get_price_tier(self, price: float) -> str:
        """
        Categorize price into tier for embedding.
        
        Args:
            price: Price in EUR
            
        Returns:
            Price tier description
        """
        if price < 25:
            return "budget affordable"
        elif price < 50:
            return "moderate mid-range"
        elif price < 100:
            return "premium quality"
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
    
    def embed_products_batch(
        self, 
        products: List[Dict], 
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple products in batches.
        
        Args:
            products: List of product dictionaries
            batch_size: Number of products to process at once
            
        Returns:
            List of embedding vectors
        """
        if not products:
            return []
        
        # Build texts for all products
        texts = [self.build_product_text(p) for p in products]
        
        logger.info(f"Generating embeddings for {len(texts)} products (batch_size={batch_size})")
        
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        
        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
