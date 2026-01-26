"""Integration tests for ProductRepository."""
import pytest
from uuid import uuid4
from src.products.repository import ProductRepository
from src.products.entity import Product


class TestProductRepository:
    """Integration tests for product repository."""
    
    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance with test database."""
        return ProductRepository(db_session)
    
    def test_save_product(self, repository, db_session):
        """Test saving a product to the database."""
        product = Product(
            store_product_id="TEST123",
            store_url="https://test.com",
            name="Test Product",
            vendor="Test Vendor",
            product_type="Test Type",
            price_eur=50.0,
            available=True,
            colors=["Red", "Blue"],
            sizes=["M", "L"],
            gender_target="unisex",
            tags=["test", "product"],
            embedding=[0.1] * 384  # Mock embedding
        )
        
        saved = repository.save(product)
        db_session.commit()
        
        assert saved.id is not None
        assert saved.name == "Test Product"
        assert saved.price_eur == 50.0
    
    def test_get_by_id(self, repository, db_session):
        """Test retrieving a product by ID."""
        product = Product(
            store_product_id="TEST456",
            store_url="https://test.com",
            name="Test Product 2",
            price_eur=60.0,
            embedding=[0.2] * 384
        )
        
        saved = repository.save(product)
        db_session.commit()
        
        retrieved = repository.get_by_id(saved.id)
        
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.name == "Test Product 2"
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent product."""
        result = repository.get_by_id(uuid4())
        assert result is None
    
    def test_count_products(self, repository, db_session):
        """Test counting products."""
        # Initially should be 0
        assert repository.count_products() == 0
        
        # Add a product
        product = Product(
            store_product_id="TEST789",
            store_url="https://test.com",
            name="Test Product 3",
            price_eur=70.0,
            embedding=[0.3] * 384
        )
        repository.save(product)
        db_session.commit()
        
        # Should now be 1
        assert repository.count_products() == 1
    
    def test_get_by_store_id(self, repository, db_session):
        """Test retrieving product by store ID and URL."""
        product = Product(
            store_product_id="STORE123",
            store_url="https://store.com",
            name="Store Product",
            price_eur=80.0,
            embedding=[0.4] * 384
        )
        
        repository.save(product)
        db_session.commit()
        
        retrieved = repository.get_by_store_id("STORE123", "https://store.com")
        
        assert retrieved is not None
        assert retrieved.store_product_id == "STORE123"
        assert retrieved.store_url == "https://store.com"
    
    def test_get_by_store_id_not_found(self, repository):
        """Test retrieving non-existent product by store ID."""
        result = repository.get_by_store_id("NONEXISTENT", "https://test.com")
        assert result is None


# Note: Vector search tests would require a PostgreSQL database with pgvector extension
# These are skipped in SQLite-based testing but would work with actual PostgreSQL
@pytest.mark.skip(reason="Requires PostgreSQL with pgvector extension")
class TestProductRepositoryVectorSearch:
    """Vector search tests (requires PostgreSQL with pgvector)."""
    
    def test_semantic_search_basic(self, repository, db_session):
        """Test basic semantic search."""
        # Create test products with embeddings
        products = [
            Product(
                store_product_id="P1",
                store_url="https://test.com",
                name="Women's Comfortable Sweatpants",
                vendor="Comfort Brand",
                product_type="Pants",
                price_eur=55.0,
                gender_target="women",
                embedding=[0.5] * 384
            ),
            Product(
                store_product_id="P2",
                store_url="https://test.com",
                name="Men's Running Shoes",
                vendor="Sport Brand",
                product_type="Footwear",
                price_eur=90.0,
                gender_target="men",
                embedding=[0.3] * 384
            )
        ]
        
        for product in products:
            repository.save(product)
        db_session.commit()
        
        # Search for women's clothing
        results = repository.semantic_search(
            query="comfortable women's clothing",
            top_k=5
        )
        
        assert len(results) > 0
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
    
    def test_semantic_search_with_price_filter(self, repository, db_session):
        """Test semantic search with price filtering."""
        # Create products with different prices
        products = [
            Product(
                store_product_id="P3",
                store_url="https://test.com",
                name="Budget T-Shirt",
                price_eur=20.0,
                embedding=[0.6] * 384
            ),
            Product(
                store_product_id="P4",
                store_url="https://test.com",
                name="Premium Sweater",
                price_eur=100.0,
                embedding=[0.7] * 384
            )
        ]
        
        for product in products:
            repository.save(product)
        db_session.commit()
        
        # Search with price filter
        results = repository.semantic_search(
            query="clothing",
            top_k=5,
            min_price=50.0,
            max_price=150.0
        )
        
        # Should only return products in price range
        assert all(50.0 <= product.price_eur <= 150.0 for product, _ in results)
    
    def test_semantic_search_with_gender_filter(self, repository, db_session):
        """Test semantic search with gender filtering."""
        # Create products with different genders
        products = [
            Product(
                store_product_id="P5",
                store_url="https://test.com",
                name="Women's Dress",
                price_eur=60.0,
                gender_target="women",
                embedding=[0.8] * 384
            ),
            Product(
                store_product_id="P6",
                store_url="https://test.com",
                name="Men's Jacket",
                price_eur=80.0,
                gender_target="men",
                embedding=[0.9] * 384
            )
        ]
        
        for product in products:
            repository.save(product)
        db_session.commit()
        
        # Search with gender filter
        results = repository.semantic_search(
            query="clothing",
            top_k=5,
            gender_filter="women"
        )
        
        # Should only return women's or unisex products
        assert all(
            product.gender_target in ["women", "unisex"]
            for product, _ in results
        )
