"""Tests for EmbeddingService."""
import pytest
from src.products.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for embedding service."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()
    
    @pytest.fixture
    def sample_product(self):
        """Create sample product dictionary."""
        return {
            "name": "Women's Classic Sweatpants",
            "vendor": "Teddy Fresh",
            "product_type": "Fleece Pants",
            "tags": ["fleece", "pants", "comfortable"],
            "colors": ["Khaki", "Navy"],
            "gender_target": "women",
            "price_eur": 55.0,
            "description": "Comfortable fleece sweatpants perfect for lounging."
        }
    
    def test_embedding_dimension(self, embedding_service):
        """Test that embedding service loads with correct dimensions."""
        assert embedding_service.embedding_dim == 384
    
    def test_build_product_text(self, embedding_service, sample_product):
        """Test building searchable text from product."""
        text = embedding_service.build_product_text(sample_product)
        
        # Check that key fields are included
        assert "Women's Classic Sweatpants" in text
        assert "Teddy Fresh" in text
        assert "Fleece Pants" in text
        assert "women" in text
        assert "Khaki" in text or "Navy" in text
        
        # Check delimiter is used
        assert "|" in text
    
    def test_build_product_text_with_missing_fields(self, embedding_service):
        """Test building text with minimal product data."""
        minimal_product = {
            "name": "Simple Product"
        }
        
        text = embedding_service.build_product_text(minimal_product)
        assert "Simple Product" in text
        # Should not crash with missing fields
        assert isinstance(text, str)
    
    def test_get_price_tier_budget(self, embedding_service):
        """Test price tier categorization for budget items."""
        tier = embedding_service._get_price_tier(20.0)
        assert "budget" in tier or "affordable" in tier
    
    def test_get_price_tier_moderate(self, embedding_service):
        """Test price tier categorization for moderate items."""
        tier = embedding_service._get_price_tier(35.0)
        assert "moderate" in tier or "mid-range" in tier
    
    def test_get_price_tier_premium(self, embedding_service):
        """Test price tier categorization for premium items."""
        tier = embedding_service._get_price_tier(75.0)
        assert "premium" in tier or "quality" in tier
    
    def test_get_price_tier_luxury(self, embedding_service):
        """Test price tier categorization for luxury items."""
        tier = embedding_service._get_price_tier(150.0)
        assert "luxury" in tier or "high-end" in tier
    
    def test_embed_product(self, embedding_service, sample_product):
        """Test generating embedding for a single product."""
        embedding = embedding_service.embed_product(sample_product)
        
        # Check embedding properties
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_products_batch(self, embedding_service):
        """Test batch embedding generation."""
        products = [
            {"name": "Product 1", "vendor": "Brand A"},
            {"name": "Product 2", "vendor": "Brand B"},
            {"name": "Product 3", "vendor": "Brand C"}
        ]
        
        embeddings = embedding_service.embed_products_batch(products, batch_size=2)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)
    
    def test_embed_products_batch_empty(self, embedding_service):
        """Test batch embedding with empty list."""
        embeddings = embedding_service.embed_products_batch([])
        assert embeddings == []
    
    def test_embed_query(self, embedding_service):
        """Test query embedding generation."""
        query = "comfortable women's loungewear"
        embedding = embedding_service.embed_query(query)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embedding_similarity(self, embedding_service):
        """Test that similar products have similar embeddings."""
        product1 = {
            "name": "Women's Sweatpants",
            "product_type": "Pants",
            "gender_target": "women"
        }
        product2 = {
            "name": "Women's Joggers",
            "product_type": "Pants",
            "gender_target": "women"
        }
        product3 = {
            "name": "Men's Leather Wallet",
            "product_type": "Accessories",
            "gender_target": "men"
        }
        
        emb1 = embedding_service.embed_product(product1)
        emb2 = embedding_service.embed_product(product2)
        emb3 = embedding_service.embed_product(product3)
        
        # Calculate cosine similarity (simple dot product for normalized vectors)
        import numpy as np
        
        # Normalize embeddings
        emb1_norm = np.array(emb1) / np.linalg.norm(emb1)
        emb2_norm = np.array(emb2) / np.linalg.norm(emb2)
        emb3_norm = np.array(emb3) / np.linalg.norm(emb3)
        
        # Similar products should have higher similarity
        sim_1_2 = np.dot(emb1_norm, emb2_norm)
        sim_1_3 = np.dot(emb1_norm, emb3_norm)
        
        # Sweatpants and joggers should be more similar than sweatpants and wallet
        assert sim_1_2 > sim_1_3
