"""Tests for ProductRepository.

Note: These tests use SQLite which doesn't support pgvector.
Full vector search tests would require PostgreSQL with pgvector extension.
These tests validate the basic repository structure and non-vector operations.
"""
import pytest
from uuid import uuid4
from src.products.repository import ProductRepository
from src.products.entity import Product
from src.products.embedding_service import EmbeddingService


class TestProductRepository:
    """Test cases for product repository."""
    
    @pytest.fixture
    def repository(self, db_session):
        """Create repository instance with test database."""
        # Skip embedding service initialization for basic tests
        return ProductRepository(db_session, embedding_service=None)
    
    @pytest.fixture
    def sample_product_data(self):
        """Create sample product data."""
        return {
            "store_product_id": "12345",
            "store_url": "https://www.example.com",
            "product_url": "https://www.example.com/product/12345",
            "name": "Test Product",
            "vendor": "Test Vendor",
            "product_type": "Test Type",
            "price_eur": 50.0,
            "price_min": 45.0,
            "price_max": 55.0,
            "available": True,
            "colors": ["Red", "Blue"],
            "sizes": ["M", "L"],
            "gender_target": "unisex",
            "tags": ["test", "product"],
            "variants": [{"id": 1, "title": "Red / M"}],
            "description": "Test product description",
            "image_url": "https://www.example.com/image.jpg"
        }
    
    def test_get_by_id_not_found(self, repository):
        """Test getting product by ID when it doesn't exist."""
        product_id = uuid4()
        product = repository.get_by_id(product_id)
        assert product is None
    
    def test_count_products_empty(self, repository):
        """Test counting products in empty database."""
        count = repository.count_products()
        assert count == 0
    
    def test_upsert_product_insert(self, repository, sample_product_data):
        """Test inserting a new product."""
        # Create a dummy embedding
        embedding = [0.1] * 384
        
        product = repository.upsert_product(sample_product_data, embedding)
        repository.session.commit()
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.vendor == "Test Vendor"
        assert product.price_eur == 50.0
        assert product.available is True
        
        # Verify count increased
        assert repository.count_products() == 1
    
    def test_upsert_product_update(self, repository, sample_product_data):
        """Test updating an existing product."""
        embedding1 = [0.1] * 384
        
        # Insert first
        product1 = repository.upsert_product(sample_product_data, embedding1)
        repository.session.commit()
        original_id = product1.id
        
        # Update with new data
        updated_data = sample_product_data.copy()
        updated_data["price_eur"] = 60.0
        updated_data["available"] = False
        
        embedding2 = [0.2] * 384
        product2 = repository.upsert_product(updated_data, embedding2)
        repository.session.commit()
        
        # Should be same product (same ID)
        assert product2.id == original_id
        assert product2.price_eur == 60.0
        assert product2.available is False
        
        # Count should still be 1
        assert repository.count_products() == 1
    
    def test_get_by_id_found(self, repository, sample_product_data):
        """Test getting product by ID when it exists."""
        embedding = [0.1] * 384
        
        # Insert product
        product = repository.upsert_product(sample_product_data, embedding)
        repository.session.commit()
        product_id = product.id
        
        # Retrieve by ID
        retrieved = repository.get_by_id(product_id)
        
        assert retrieved is not None
        assert retrieved.id == product_id
        assert retrieved.name == "Test Product"
    
    def test_count_products_multiple(self, repository, sample_product_data):
        """Test counting multiple products."""
        embedding = [0.1] * 384
        
        # Insert first product
        repository.upsert_product(sample_product_data, embedding)
        
        # Insert second product with different ID
        data2 = sample_product_data.copy()
        data2["store_product_id"] = "67890"
        data2["name"] = "Second Product"
        repository.upsert_product(data2, embedding)
        
        repository.session.commit()
        
        assert repository.count_products() == 2
    
    def test_upsert_product_unique_constraint(self, repository, sample_product_data):
        """Test that same store_product_id + store_url updates instead of duplicating."""
        embedding = [0.1] * 384
        
        # Insert first
        product1 = repository.upsert_product(sample_product_data, embedding)
        repository.session.commit()
        
        # Insert same product again
        product2 = repository.upsert_product(sample_product_data, embedding)
        repository.session.commit()
        
        # Should have same ID (update, not insert)
        assert product1.id == product2.id
        
        # Count should be 1, not 2
        assert repository.count_products() == 1


class TestProductRepositoryVectorSearch:
    """
    Tests for vector search functionality.
    
    Note: These tests are marked to skip on SQLite since vector operations
    require PostgreSQL with pgvector extension.
    """
    
    @pytest.mark.skip(reason="Vector search requires PostgreSQL with pgvector")
    def test_semantic_search_basic(self):
        """Test basic semantic search."""
        pass
    
    @pytest.mark.skip(reason="Vector search requires PostgreSQL with pgvector")
    def test_semantic_search_with_price_filter(self):
        """Test semantic search with price filters."""
        pass
    
    @pytest.mark.skip(reason="Vector search requires PostgreSQL with pgvector")
    def test_semantic_search_with_gender_filter(self):
        """Test semantic search with gender filter."""
        pass
