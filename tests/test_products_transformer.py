"""Tests for ProductTransformer."""
import pytest
from src.products.transformer import ProductTransformer


class TestProductTransformer:
    """Test cases for product transformation logic."""
    
    def test_parse_variant_title_slash_format(self):
        """Test parsing variant title with slash delimiter."""
        color, size = ProductTransformer._parse_variant_title("Khaki / M")
        assert color == "Khaki"
        assert size == "M"
    
    def test_parse_variant_title_dash_format(self):
        """Test parsing variant title with dash delimiter."""
        color, size = ProductTransformer._parse_variant_title("Blue - Large")
        assert color == "Blue"
        assert size == "Large"
    
    def test_parse_variant_title_color_only(self):
        """Test parsing variant title with color only."""
        color, size = ProductTransformer._parse_variant_title("Black")
        assert color == "Black"
        assert size is None
    
    def test_parse_variant_title_size_only(self):
        """Test parsing variant title with size only."""
        color, size = ProductTransformer._parse_variant_title("XL")
        assert color is None
        assert size == "XL"
    
    def test_parse_variant_title_default(self):
        """Test parsing default variant title."""
        color, size = ProductTransformer._parse_variant_title("Default Title")
        assert color is None
        assert size is None
    
    def test_parse_variant_title_empty(self):
        """Test parsing empty variant title."""
        color, size = ProductTransformer._parse_variant_title("")
        assert color is None
        assert size is None
    
    def test_detect_gender_women(self):
        """Test gender detection for women's products."""
        assert ProductTransformer._detect_gender("Women's Classic Sweatpants") == "women"
        assert ProductTransformer._detect_gender("Ladies Fashion Jacket") == "women"
        assert ProductTransformer._detect_gender("Female Athletic Wear") == "women"
    
    def test_detect_gender_men(self):
        """Test gender detection for men's products."""
        assert ProductTransformer._detect_gender("Men's Essential Hoodie") == "men"
        assert ProductTransformer._detect_gender("Gentleman's Suit") == "men"
        assert ProductTransformer._detect_gender("Male Casual Shirt") == "men"
    
    def test_detect_gender_unisex(self):
        """Test gender detection for unisex products."""
        assert ProductTransformer._detect_gender("Unisex Canvas Tote") == "unisex"
        assert ProductTransformer._detect_gender("Classic T-Shirt") == "unisex"
        assert ProductTransformer._detect_gender("Gender Neutral Backpack") == "unisex"
    
    def test_sort_sizes_standard(self):
        """Test sorting standard letter sizes."""
        sizes = ["XL", "M", "S", "L", "XS"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["XS", "S", "M", "L", "XL"]
    
    def test_sort_sizes_with_xxl(self):
        """Test sorting sizes including XXL."""
        sizes = ["XXL", "M", "L", "XL", "S"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["S", "M", "L", "XL", "XXL"]
    
    def test_sort_sizes_numeric(self):
        """Test sorting numeric sizes."""
        sizes = ["42", "38", "40", "36"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["36", "38", "40", "42"]
    
    def test_sort_sizes_mixed(self):
        """Test sorting mixed size formats."""
        sizes = ["2XL", "M", "L", "3XL"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        # 2XL and 3XL should be sorted correctly
        assert "M" in sorted_sizes
        assert "L" in sorted_sizes
    
    def test_generate_tags(self):
        """Test tag generation from product attributes."""
        tags = ProductTransformer._generate_tags(
            product_title="Women's Comfortable Sweatpants",
            product_type="Fleece Pants",
            vendor="Teddy Fresh",
            colors={"Khaki", "Navy"},
            gender="women"
        )
        
        assert "fleece pants" in tags
        assert "teddy fresh" in tags
        assert "women" in tags
        assert "khaki" in tags
        assert "navy" in tags
    
    def test_generate_tags_filters_stop_words(self):
        """Test that common stop words are filtered from tags."""
        tags = ProductTransformer._generate_tags(
            product_title="The Best Product With Amazing Quality",
            product_type="",
            vendor="",
            colors=set(),
            gender="unisex"
        )
        
        # Stop words should be filtered
        assert "the" not in tags
        assert "with" not in tags
        # But meaningful words should be included
        assert "best" in tags or "product" in tags
    
    def test_transform_variants_to_products_aggregation(self):
        """Test full transformation of variants into products."""
        variants = [
            {
                "store_url": "https://www.example.com",
                "product_id": 123,
                "product_title": "Women's Classic Sweatpants",
                "vendor": "TestBrand",
                "product_type": "Pants",
                "variant_id": 1,
                "variant_title": "Khaki / M",
                "price_eur": 55.0,
                "available": True,
                "product_url": "https://www.example.com/product/123"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 123,
                "product_title": "Women's Classic Sweatpants",
                "vendor": "TestBrand",
                "product_type": "Pants",
                "variant_id": 2,
                "variant_title": "Navy / L",
                "price_eur": 55.0,
                "available": False,
                "product_url": "https://www.example.com/product/123"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 123,
                "product_title": "Women's Classic Sweatpants",
                "vendor": "TestBrand",
                "product_type": "Pants",
                "variant_id": 3,
                "variant_title": "Black / S",
                "price_eur": 50.0,
                "available": True,
                "product_url": "https://www.example.com/product/123"
            }
        ]
        
        products = ProductTransformer.transform_variants_to_products(variants)
        
        assert len(products) == 1
        product = products[0]
        
        # Check basic fields
        assert product["store_product_id"] == "123"
        assert product["name"] == "Women's Classic Sweatpants"
        assert product["vendor"] == "TestBrand"
        
        # Check aggregated colors and sizes
        assert "Khaki" in product["colors"]
        assert "Navy" in product["colors"]
        assert "Black" in product["colors"]
        assert "M" in product["sizes"]
        assert "L" in product["sizes"]
        assert "S" in product["sizes"]
        
        # Check availability (true if ANY variant is available)
        assert product["available"] is True
        
        # Check price range
        assert product["price_min"] == 50.0
        assert product["price_max"] == 55.0
        
        # Check gender detection
        assert product["gender_target"] == "women"
        
        # Check variants are stored
        assert len(product["variants"]) == 3
    
    def test_transform_variants_to_products_multiple_products(self):
        """Test transformation of variants from different products."""
        variants = [
            {
                "store_url": "https://www.example.com",
                "product_id": 123,
                "product_title": "Product A",
                "vendor": "Brand A",
                "product_type": "Type A",
                "variant_id": 1,
                "variant_title": "Red / M",
                "price_eur": 30.0,
                "available": True,
                "product_url": "https://www.example.com/a"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 456,
                "product_title": "Product B",
                "vendor": "Brand B",
                "product_type": "Type B",
                "variant_id": 2,
                "variant_title": "Blue / L",
                "price_eur": 40.0,
                "available": True,
                "product_url": "https://www.example.com/b"
            }
        ]
        
        products = ProductTransformer.transform_variants_to_products(variants)
        
        assert len(products) == 2
        
        # Verify both products are distinct
        product_ids = [p["store_product_id"] for p in products]
        assert "123" in product_ids
        assert "456" in product_ids
    
    def test_transform_variants_empty_list(self):
        """Test transformation with empty variant list."""
        products = ProductTransformer.transform_variants_to_products([])
        assert products == []
