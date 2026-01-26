"""Tests for ProductTransformer."""
import pytest
from src.products.transformer import ProductTransformer


class TestProductTransformer:
    """Test cases for product transformation logic."""
    
    def test_parse_variant_title_slash_delimiter(self):
        """Test parsing variant title with slash delimiter."""
        color, size = ProductTransformer._parse_variant_title("Khaki / M")
        assert color == "Khaki"
        assert size == "M"
    
    def test_parse_variant_title_dash_delimiter(self):
        """Test parsing variant title with dash delimiter."""
        color, size = ProductTransformer._parse_variant_title("Blue - Large")
        assert color == "Blue"
        assert size == "LARGE"
    
    def test_parse_variant_title_color_only(self):
        """Test parsing variant title with only color."""
        color, size = ProductTransformer._parse_variant_title("Red")
        assert color == "Red"
        assert size is None
    
    def test_parse_variant_title_size_only(self):
        """Test parsing variant title with only size."""
        color, size = ProductTransformer._parse_variant_title("XL")
        assert color is None
        assert size == "XL"
    
    def test_parse_variant_title_empty(self):
        """Test parsing empty variant title."""
        color, size = ProductTransformer._parse_variant_title("")
        assert color is None
        assert size is None
    
    def test_detect_gender_women(self):
        """Test gender detection for women's products."""
        assert ProductTransformer._detect_gender("Women's Classic Sweatpants") == "women"
        assert ProductTransformer._detect_gender("Womens Jacket") == "women"
        assert ProductTransformer._detect_gender("Ladies Sweater") == "women"
    
    def test_detect_gender_men(self):
        """Test gender detection for men's products."""
        assert ProductTransformer._detect_gender("Men's Classic Hoodie") == "men"
        assert ProductTransformer._detect_gender("Mens Shorts") == "men"
        assert ProductTransformer._detect_gender("Guys T-Shirt") == "men"
    
    def test_detect_gender_unisex(self):
        """Test gender detection for unisex products."""
        assert ProductTransformer._detect_gender("Classic T-Shirt") == "unisex"
        assert ProductTransformer._detect_gender("Unisex Logo Hoodie") == "unisex"
        assert ProductTransformer._detect_gender("") == "unisex"
    
    def test_sort_sizes_standard(self):
        """Test sorting standard sizes."""
        sizes = ["XL", "S", "M", "L", "XS"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["XS", "S", "M", "L", "XL"]
    
    def test_sort_sizes_with_extra(self):
        """Test sorting sizes with XXL and XXXL."""
        sizes = ["XXXL", "M", "XXL", "L"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["M", "L", "XXL", "XXXL"]
    
    def test_sort_sizes_numeric(self):
        """Test sorting numeric sizes."""
        sizes = ["10", "8", "12", "6"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        assert sorted_sizes == ["6", "8", "10", "12"]
    
    def test_sort_sizes_mixed(self):
        """Test sorting mixed sizes."""
        sizes = ["10", "M", "L", "8"]
        sorted_sizes = ProductTransformer._sort_sizes(sizes)
        # Standard sizes come first, then numeric
        assert sorted_sizes[0] == "M"
        assert sorted_sizes[1] == "L"
        assert sorted_sizes[2] == "8"
        assert sorted_sizes[3] == "10"
    
    def test_generate_tags(self):
        """Test tag generation from product attributes."""
        product = {
            "product_title": "Women's Classic Sweatpants",
            "vendor": "Teddy Fresh",
            "product_type": "Fleece Pants"
        }
        colors = ["Khaki", "Navy", "Black"]
        gender = "women"
        
        tags = ProductTransformer._generate_tags(product, colors, gender)
        
        # Check that key tags are present
        assert "fleece pants" in tags
        assert "teddy fresh" in tags
        assert "women" in tags
        assert "khaki" in tags
    
    def test_transform_variants_to_products_single_product(self):
        """Test transforming multiple variants into a single product."""
        raw_variants = [
            {
                "store_url": "https://www.example.com",
                "product_id": 12345,
                "product_title": "Women's Classic Sweatpants",
                "vendor": "Test Brand",
                "product_type": "Pants",
                "variant_id": 1,
                "variant_title": "Khaki / M",
                "price_eur": 55.0,
                "available": True,
                "product_url": "https://www.example.com/product/12345"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 12345,
                "product_title": "Women's Classic Sweatpants",
                "vendor": "Test Brand",
                "product_type": "Pants",
                "variant_id": 2,
                "variant_title": "Black / L",
                "price_eur": 55.0,
                "available": False,
                "product_url": "https://www.example.com/product/12345"
            }
        ]
        
        products = ProductTransformer.transform_variants_to_products(raw_variants)
        
        assert len(products) == 1
        product = products[0]
        
        assert product["name"] == "Women's Classic Sweatpants"
        assert product["vendor"] == "Test Brand"
        assert product["price_eur"] == 55.0
        assert set(product["colors"]) == {"Khaki", "Black"}
        assert set(product["sizes"]) == {"M", "L"}
        assert product["gender_target"] == "women"
        assert product["available"] is True  # True because at least one variant is available
        assert len(product["variants"]) == 2
    
    def test_transform_variants_to_products_multiple_products(self):
        """Test transforming variants into multiple products."""
        raw_variants = [
            {
                "store_url": "https://www.example.com",
                "product_id": 111,
                "product_title": "Product A",
                "vendor": "Brand A",
                "product_type": "Type A",
                "variant_id": 1,
                "variant_title": "Red / S",
                "price_eur": 30.0,
                "available": True,
                "product_url": "https://www.example.com/a"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 222,
                "product_title": "Product B",
                "vendor": "Brand B",
                "product_type": "Type B",
                "variant_id": 2,
                "variant_title": "Blue / M",
                "price_eur": 40.0,
                "available": True,
                "product_url": "https://www.example.com/b"
            }
        ]
        
        products = ProductTransformer.transform_variants_to_products(raw_variants)
        
        assert len(products) == 2
        assert products[0]["name"] == "Product A"
        assert products[1]["name"] == "Product B"
    
    def test_transform_variants_empty_list(self):
        """Test transforming empty variant list."""
        products = ProductTransformer.transform_variants_to_products([])
        assert products == []
    
    def test_transform_variants_with_price_range(self):
        """Test transforming variants with different prices."""
        raw_variants = [
            {
                "store_url": "https://www.example.com",
                "product_id": 12345,
                "product_title": "Test Product",
                "vendor": "Brand",
                "product_type": "Type",
                "variant_id": 1,
                "variant_title": "Color1 / M",
                "price_eur": 30.0,
                "available": True,
                "product_url": "https://www.example.com/test"
            },
            {
                "store_url": "https://www.example.com",
                "product_id": 12345,
                "product_title": "Test Product",
                "vendor": "Brand",
                "product_type": "Type",
                "variant_id": 2,
                "variant_title": "Color2 / L",
                "price_eur": 35.0,
                "available": True,
                "product_url": "https://www.example.com/test"
            }
        ]
        
        products = ProductTransformer.transform_variants_to_products(raw_variants)
        
        assert len(products) == 1
        product = products[0]
        
        assert product["price_min"] == 30.0
        assert product["price_max"] == 35.0
        assert product["price_eur"] == 30.0  # First variant price
