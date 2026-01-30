"""Transform raw scraped variant-level JSON into aggregated product records."""
from typing import List, Dict, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class ProductTransformer:
    """Transform and aggregate product variants into unified product records."""
    
    # Gender detection keywords
    WOMEN_KEYWORDS = ["women's", "womens", "woman", "female", "ladies", "lady"]
    MEN_KEYWORDS = ["men's", "mens", "man", "male", "guys", "gentleman"]
    UNISEX_KEYWORDS = ["unisex", "everyone", "all"]
    
    # Size ordering for logical sorting
    SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "ONE SIZE"]
    
    @classmethod
    def transform_variants_to_products(cls, raw_variants: List[Dict]) -> List[Dict]:
        """
        Transform raw variant-level data into aggregated product records.
        
        Args:
            raw_variants: List of variant dictionaries from scraping
            
        Returns:
            List of aggregated product dictionaries
        """
        if not raw_variants:
            return []
        
        # Group variants by (store_url, product_id)
        grouped_variants = {}
        for variant in raw_variants:
            key = (variant.get("store_url"), variant.get("product_id"))
            if key not in grouped_variants:
                grouped_variants[key] = []
            grouped_variants[key].append(variant)
        
        # Aggregate each group into a product
        products = []
        for (store_url, product_id), variants in grouped_variants.items():
            try:
                product = cls._aggregate_variants(store_url, product_id, variants)
                products.append(product)
            except Exception as e:
                logger.error(f"Error aggregating product {product_id}: {e}")
                continue
        
        logger.info(f"Transformed {len(raw_variants)} variants into {len(products)} products")
        return products
    
    @classmethod
    def _aggregate_variants(cls, store_url: str, product_id: int, variants: List[Dict]) -> Dict:
        """
        Aggregate multiple variants into a single product record.
        
        Args:
            store_url: Store URL
            product_id: Product ID
            variants: List of variant dictionaries
            
        Returns:
            Aggregated product dictionary
        """
        if not variants:
            raise ValueError("Cannot aggregate empty variants list")
        
        # Use first variant as base
        first = variants[0]
        
        # Extract and aggregate variant attributes
        colors = set()
        sizes = set()
        prices = []
        available_any = False
        
        for variant in variants:
            # Parse variant title to extract color and size
            color, size = cls._parse_variant_title(variant.get("variant_title", ""))
            if color:
                colors.add(color)
            if size:
                sizes.add(size)
            
            # Track prices
            price = variant.get("price_eur")
            if price is not None:
                prices.append(float(price))
            
            # Availability: true if ANY variant is available
            if variant.get("available", False):
                available_any = True
        
        # Calculate price range
        price_eur = prices[0] if prices else None
        price_min = min(prices) if len(prices) > 1 else None
        price_max = max(prices) if len(prices) > 1 else None
        
        # Detect gender from product title
        product_title = first.get("product_title", "")
        gender = cls._detect_gender(product_title)
        
        # Sort sizes logically
        sorted_sizes = cls._sort_sizes(list(sizes))
        colors_list = sorted(list(colors))
        
        # Generate tags
        tags = cls._generate_tags(first, colors_list, gender)
        
        # Build product record
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
            "available": available_any,
            "colors": colors_list,
            "sizes": sorted_sizes,
            "gender_target": gender,
            "tags": tags,
            "variants": variants,  # Store raw variants as JSONB
            "description": None,  # Can be added later if available
            "image_url": None,  # Can be added later if available
        }
        
        return product
    
    @classmethod
    def _parse_variant_title(cls, variant_title: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse variant title to extract color and size.
        
        Examples:
            "Khaki / M" -> ("Khaki", "M")
            "Blue - Large" -> ("Blue", "Large")
            "Red" -> ("Red", None)
            "XL" -> (None, "XL")
            
        Args:
            variant_title: Variant title string
            
        Returns:
            Tuple of (color, size), either can be None
        """
        if not variant_title:
            return None, None
        
        # Split by common delimiters
        parts = re.split(r'[/\-|]', variant_title)
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            return None, None
        
        color = None
        size = None
        
        # Common size patterns
        size_patterns = [
            r'^(XXS|XS|S|M|L|XL|XXL|XXXL)$',
            r'^(SMALL|MEDIUM|LARGE|X-LARGE|XX-LARGE)$',
            r'^(ONE SIZE|OS)$',
            r'^\d+$',  # Numeric sizes
        ]
        
        for part in parts:
            part_upper = part.upper()
            
            # Check if it's a size
            is_size = any(re.match(pattern, part_upper) for pattern in size_patterns)
            
            if is_size:
                size = part_upper
            else:
                # Assume it's a color
                color = part
        
        return color, size
    
    @classmethod
    def _detect_gender(cls, title: str) -> str:
        """
        Detect gender target from product title.
        
        Args:
            title: Product title
            
        Returns:
            "women", "men", or "unisex"
        """
        if not title:
            return "unisex"
        
        title_lower = title.lower()
        
        # Check for women keywords
        if any(keyword in title_lower for keyword in cls.WOMEN_KEYWORDS):
            return "women"
        
        # Check for men keywords
        if any(keyword in title_lower for keyword in cls.MEN_KEYWORDS):
            return "men"
        
        # Check for unisex keywords
        if any(keyword in title_lower for keyword in cls.UNISEX_KEYWORDS):
            return "unisex"
        
        # Default to unisex
        return "unisex"
    
    @classmethod
    def _generate_tags(cls, product: Dict, colors: List[str], gender: str) -> List[str]:
        """
        Generate searchable tags from product attributes.
        
        Args:
            product: Product dictionary
            colors: List of color names
            gender: Gender target
            
        Returns:
            List of tag strings
        """
        tags = []
        
        # Add product type as tag
        product_type = product.get("product_type", "")
        if product_type:
            tags.append(product_type.lower())
        
        # Add vendor as tag
        vendor = product.get("vendor", "")
        if vendor:
            tags.append(vendor.lower())
        
        # Add gender as tag
        if gender != "unisex":
            tags.append(gender)
        
        # Extract keywords from product title
        title = product.get("product_title", "")
        if title:
            # Remove gender keywords and split
            title_lower = title.lower()
            for keyword in cls.WOMEN_KEYWORDS + cls.MEN_KEYWORDS + cls.UNISEX_KEYWORDS:
                title_lower = title_lower.replace(keyword, "")
            
            # Extract meaningful words (longer than 2 chars)
            words = re.findall(r'\b\w{3,}\b', title_lower)
            tags.extend(words[:5])  # Limit to 5 keywords
        
        # Add main colors as tags
        for color in colors[:3]:  # Limit to 3 colors
            if color:
                tags.append(color.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    @classmethod
    def _sort_sizes(cls, sizes: List[str]) -> List[str]:
        """
        Sort sizes in logical order (XS, S, M, L, XL, etc.).
        
        Args:
            sizes: List of size strings
            
        Returns:
            Sorted list of sizes
        """
        if not sizes:
            return []
        
        # Create a mapping for known sizes
        size_priority = {size: i for i, size in enumerate(cls.SIZE_ORDER)}
        
        # Sort sizes: known sizes first (by priority), then unknown (alphabetically)
        def sort_key(size):
            size_upper = size.upper()
            if size_upper in size_priority:
                return (0, size_priority[size_upper])
            else:
                # Try to parse as number
                try:
                    return (1, float(size))
                except ValueError:
                    return (2, size_upper)
        
        return sorted(sizes, key=sort_key)
