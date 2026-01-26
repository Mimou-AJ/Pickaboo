"""Tests for EmbeddingService."""
import pytest
from src.products.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for embedding service."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create an embedding service instance for testing."""
        return EmbeddingService()
    
    def test_build_product_text_complete(self, embedding_service):
        """Test building product text with all fields."""
        product = {
            "name": "Women's Classic Sweatpants",
            "vendor": "Teddy Fresh",
            "product_type": "Fleece Pants",
            "tags": ["comfortable", "casual", "women"],
            "colors": ["Khaki", "Navy", "Black"],
            "gender_target": "women",
            "price_eur": 55.0,
            "description": "Comfortable sweatpants for everyday wear"
        }
        
        text = embedding_service.build_product_text(product)
        
        # Check that all components are present
        assert "Women's Classic Sweatpants" in text
        assert "Teddy Fresh" in text
        assert "Fleece Pants" in text
        assert "comfortable" in text
        assert "Colors:" in text
        assert "Khaki" in text
        assert "For: women" in text
        assert "mid-range moderate" in text  # Price tier for 55.0
        assert "Comfortable sweatpants" in text
    
    def test_build_product_text_minimal(self, embedding_service):
        """Test building product text with minimal fields."""
        product = {
            "name": "Basic T-Shirt"
        }
        
        text = embedding_service.build_product_text(product)
        
        assert "Basic T-Shirt" in text
        # Should still work with missing fields
        assert text != ""
    
    def test_get_price_tier_budget(self, embedding_service):
        """Test price tier classification for budget items."""
        assert embedding_service._get_price_tier(20.0) == "budget affordable"
        assert embedding_service._get_price_tier(24.99) == "budget affordable"
    
    def test_get_price_tier_mid_range(self, embedding_service):
        """Test price tier classification for mid-range items."""
        assert embedding_service._get_price_tier(30.0) == "mid-range moderate"
        assert embedding_service._get_price_tier(49.99) == "mid-range moderate"
    
    def test_get_price_tier_premium(self, embedding_service):
        """Test price tier classification for premium items."""
        assert embedding_service._get_price_tier(55.0) == "premium"
        assert embedding_service._get_price_tier(99.99) == "premium"
    
    def test_get_price_tier_luxury(self, embedding_service):
        """Test price tier classification for luxury items."""
        assert embedding_service._get_price_tier(100.0) == "luxury high-end"
        assert embedding_service._get_price_tier(500.0) == "luxury high-end"
    
    def test_embed_product_returns_vector(self, embedding_service):
        """Test that embed_product returns a vector of correct dimensions."""
        product = {
            "name": "Test Product",
            "vendor": "Test Brand",
            "product_type": "Test Type",
            "price_eur": 50.0
        }
        
        embedding = embedding_service.embed_product(product)
        
        # Check that it's a list
        assert isinstance(embedding, list)
        
        # Check dimensions (all-MiniLM-L6-v2 produces 384-dimensional vectors)
        assert len(embedding) == 384
        
        # Check that all values are floats
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_query_returns_vector(self, embedding_service):
        """Test that embed_query returns a vector of correct dimensions."""
        query = "comfortable women's clothing for casual wear"
        
        embedding = embedding_service.embed_query(query)
        
        # Check that it's a list
        assert isinstance(embedding, list)
        
        # Check dimensions
        assert len(embedding) == 384
        
        # Check that all values are floats
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_products_batch(self, embedding_service):
        """Test batch embedding of multiple products."""
        products = [
            {
                "name": "Product 1",
                "vendor": "Brand A",
                "price_eur": 30.0
            },
            {
                "name": "Product 2",
                "vendor": "Brand B",
                "price_eur": 40.0
            },
            {
                "name": "Product 3",
                "vendor": "Brand C",
                "price_eur": 50.0
            }
        ]
        
        embeddings = embedding_service.embed_products_batch(products, batch_size=2)
        
        # Check that we got embeddings for all products
        assert len(embeddings) == 3
        
        # Check that each embedding has correct dimensions
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == 384
    
    def test_embed_products_batch_empty(self, embedding_service):
        """Test batch embedding with empty list."""
        embeddings = embedding_service.embed_products_batch([])
        assert embeddings == []
    
    def test_semantic_similarity(self, embedding_service):
        """Test that semantically similar products have similar embeddings."""
        product1 = {
            "name": "Women's Cozy Sweatpants",
            "vendor": "Comfort Brand",
            "product_type": "Pants",
            "tags": ["comfortable", "casual"],
            "price_eur": 50.0
        }
        
        product2 = {
            "name": "Women's Comfortable Lounge Pants",
            "vendor": "Cozy Brand",
            "product_type": "Loungewear",
            "tags": ["cozy", "casual"],
            "price_eur": 55.0
        }
        
        product3 = {
            "name": "Men's Athletic Running Shoes",
            "vendor": "Sport Brand",
            "product_type": "Footwear",
            "tags": ["sport", "running"],
            "price_eur": 90.0
        }
        
        emb1 = embedding_service.embed_product(product1)
        emb2 = embedding_service.embed_product(product2)
        emb3 = embedding_service.embed_product(product3)
        
        # Calculate cosine similarity (simplified)
        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(y * y for y in b) ** 0.5
            return dot / (norm_a * norm_b)
        
        # Similar products should have higher similarity
        sim_12 = cosine_similarity(emb1, emb2)
        sim_13 = cosine_similarity(emb1, emb3)
        
        # Sweatpants and lounge pants should be more similar than sweatpants and running shoes
        assert sim_12 > sim_13
