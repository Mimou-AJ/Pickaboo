"""Transform raw scraped variant-level JSON into aggregated product records."""
from typing import List, Dict, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class ProductTransformer:
    """Transform and aggregate variant-level scraped data into product records."""
    
    # Keywords for gender detection
    WOMEN_KEYWORDS = ["women's", "womens", "woman", "female", "ladies", "lady"]
    MEN_KEYWORDS = ["men's", "mens", "man", "male", "guys", "gentleman"]
    UNISEX_KEYWORDS = ["unisex", "gender neutral"]
    
    # Size ordering for logical sorting
    SIZE_ORDER = {
        "xxs": 0, "xs": 1, "s": 2, "m": 3, "l": 4, "xl": 5, "xxl": 6, "xxxl": 7,
        "2xs": 0, "2xl": 6, "3xl": 7, "4xl": 8, "5xl": 9,
        "small": 2, "medium": 3, "large": 4, "x-large": 5, "xx-large": 6,
    }
    
    @staticmethod
    def transform_variants_to_products(raw_variants: List[Dict]) -> List[Dict]:
        """
        Transform list of variant records into aggregated product records.
        
        Args:
            raw_variants: List of variant-level records from scraping
            
        Returns:
            List of aggregated product dictionaries ready for database insertion
        """
        if not raw_variants:
            return []
        
        # Group variants by (store_url, product_id)
        grouped = {}
        for variant in raw_variants:
            key = (variant.get("store_url"), variant.get("product_id"))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(variant)
        
        # Aggregate each group into a product
        products = []
        for (store_url, product_id), variants in grouped.items():
            try:
                product = ProductTransformer._aggregate_variants(store_url, product_id, variants)
                products.append(product)
            except Exception as e:
                logger.error(f"Error aggregating product {product_id} from {store_url}: {e}")
                continue
        
        logger.info(f"Transformed {len(raw_variants)} variants into {len(products)} products")
        return products
    
    @staticmethod
    def _aggregate_variants(store_url: str, product_id: int, variants: List[Dict]) -> Dict:
        """
        Aggregate multiple variants into a single product record.
        
        Args:
            store_url: Store URL
            product_id: Product ID
            variants: List of variant records for this product
            
        Returns:
            Aggregated product dictionary
        """
        # Take common fields from first variant
        first = variants[0]
        
        # Parse all variant titles to extract colors and sizes
        colors = set()
        sizes = set()
        for variant in variants:
            color, size = ProductTransformer._parse_variant_title(
                variant.get("variant_title", "")
            )
            if color:
                colors.add(color)
            if size:
                sizes.add(size)
        
        # Determine pricing
        prices = [v.get("price_eur") for v in variants if v.get("price_eur") is not None]
        price_eur = prices[0] if prices else None
        price_min = min(prices) if len(prices) > 1 else None
        price_max = max(prices) if len(prices) > 1 else None
        
        # Availability: true if ANY variant is available
        available = any(v.get("available", False) for v in variants)
        
        # Detect gender
        product_title = first.get("product_title", "")
        gender_target = ProductTransformer._detect_gender(product_title)
        
        # Generate tags
        tags = ProductTransformer._generate_tags(
            product_title,
            first.get("product_type", ""),
            first.get("vendor", ""),
            colors,
            gender_target
        )
        
        # Sort sizes logically
        sorted_sizes = ProductTransformer._sort_sizes(list(sizes))
        
        # Build aggregated product
        product = {
            "store_product_id": str(product_id),
            "store_url": store_url,
            "product_url": first.get("product_url"),
            "name": product_title,
            "vendor": first.get("vendor"),
            "product_type": first.get("product_type"),
            "price_eur": price_eur,
            "price_min": price_min,
            "price_max": price_max,
            "available": available,
            "colors": sorted(list(colors)) if colors else None,
            "sizes": sorted_sizes if sorted_sizes else None,
            "gender_target": gender_target,
            "tags": tags,
            "variants": variants,  # Store all variants as JSONB
            "description": first.get("description"),
            "image_url": first.get("image_url"),
        }
        
        return product
    
    @staticmethod
    def _parse_variant_title(variant_title: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse variant title to extract color and size.
        
        Handles formats like:
        - "Khaki / L"
        - "Navy - Medium"
        - "Black"
        - "XL"
        
        Args:
            variant_title: Variant title string
            
        Returns:
            Tuple of (color, size)
        """
        if not variant_title or variant_title.lower() == "default title":
            return None, None
        
        # Split by common delimiters
        parts = re.split(r'[/\-]', variant_title)
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            return None, None
        
        color = None
        size = None
        
        # Common size patterns
        size_pattern = re.compile(r'^(xxs|xs|s|m|l|xl|xxl|xxxl|2xl|3xl|4xl|5xl|\d+)$', re.IGNORECASE)
        
        for part in parts:
            part_lower = part.lower()
            
            # Check if it's a size
            if size_pattern.match(part_lower) or part_lower in ["small", "medium", "large", "x-large", "xx-large"]:
                size = part
            else:
                # Assume it's a color if not a size
                color = part
        
        return color, size
    
    @staticmethod
    def _detect_gender(title: str) -> str:
        """
        Detect target gender from product title.
        
        Args:
            title: Product title
            
        Returns:
            "women", "men", or "unisex"
        """
        title_lower = title.lower()
        
        # Check for explicit keywords
        if any(kw in title_lower for kw in ProductTransformer.WOMEN_KEYWORDS):
            return "women"
        if any(kw in title_lower for kw in ProductTransformer.MEN_KEYWORDS):
            return "men"
        if any(kw in title_lower for kw in ProductTransformer.UNISEX_KEYWORDS):
            return "unisex"
        
        # Default to unisex if no clear indicator
        return "unisex"
    
    @staticmethod
    def _generate_tags(
        product_title: str,
        product_type: str,
        vendor: str,
        colors: set,
        gender: str
    ) -> List[str]:
        """
        Generate searchable tags from product attributes.
        
        Args:
            product_title: Product title
            product_type: Product type/category
            vendor: Brand/vendor name
            colors: Set of available colors
            gender: Target gender
            
        Returns:
            List of tags
        """
        tags = set()
        
        # Add product type
        if product_type:
            tags.add(product_type.lower())
        
        # Add vendor
        if vendor:
            tags.add(vendor.lower())
        
        # Add gender
        if gender and gender != "unisex":
            tags.add(gender)
        
        # Extract keywords from title (simple tokenization)
        title_words = re.findall(r'\b[a-z]{3,}\b', product_title.lower())
        # Filter out common words
        stop_words = {"the", "and", "for", "with", "from", "this", "that"}
        meaningful_words = [w for w in title_words if w not in stop_words]
        tags.update(meaningful_words[:5])  # Limit to first 5 meaningful words
        
        # Add color-related tags
        for color in colors:
            if color:
                tags.add(color.lower())
        
        return sorted(list(tags))
    
    @staticmethod
    def _sort_sizes(sizes: List[str]) -> List[str]:
        """
        Sort sizes in logical order (XS, S, M, L, XL, etc.).
        
        Args:
            sizes: List of size strings
            
        Returns:
            Sorted list of sizes
        """
        if not sizes:
            return []
        
        def size_key(size: str) -> int:
            """Generate sort key for a size."""
            size_lower = size.lower().strip()
            
            # Check if in predefined order
            if size_lower in ProductTransformer.SIZE_ORDER:
                return ProductTransformer.SIZE_ORDER[size_lower]
            
            # Try to extract numeric size
            numeric_match = re.match(r'^(\d+)', size_lower)
            if numeric_match:
                return int(numeric_match.group(1)) + 100  # Offset to sort after letter sizes
            
            # Default: sort alphabetically (return high value)
            return 1000
        
        try:
            return sorted(sizes, key=size_key)
        except Exception:
            # Fallback to simple sorting
            return sorted(sizes)
