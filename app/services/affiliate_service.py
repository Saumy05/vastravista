"""
VastraVista - Affiliate API Integration Service
Author: Saumya Tiwari
Purpose: Integrate Amazon, Flipkart, and other e-commerce APIs for product recommendations
"""

import os
import logging
from typing import List, Dict, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AffiliateAPIManager:
    """
    Manage affiliate API integrations for product recommendations
    Supports: Amazon India, Flipkart, Myntra (via Cuelinks/EarnKaro)
    """
    
    def __init__(self):
        """Initialize affiliate API manager"""
        self.logger = logging.getLogger(__name__)
        
        # API credentials (from environment variables)
        self.amazon_affiliate_id = os.getenv('AMAZON_AFFILIATE_ID', '')
        self.amazon_access_key = os.getenv('AMAZON_ACCESS_KEY', '')
        self.amazon_secret_key = os.getenv('AMAZON_SECRET_KEY', '')
        
        self.flipkart_affiliate_id = os.getenv('FLIPKART_AFFILIATE_ID', '')
        self.flipkart_affiliate_token = os.getenv('FLIPKART_AFFILIATE_TOKEN', '')
        
        # Cuelinks/EarnKaro for simplified affiliate tracking
        self.cuelinks_api_key = os.getenv('CUELINKS_API_KEY', '')
        
        # Cache for API responses (to avoid rate limits)
        self.cache = {}
        self.cache_duration = timedelta(hours=6)
        
        self.logger.info("🛒 Affiliate API Manager initialized")
    
    def search_products(self, 
                       keywords: List[str], 
                       colors: List[str],
                       category: str,
                       gender: str,
                       max_results: int = 20,
                       platform: str = 'amazon') -> List[Dict]:
        """
        Search for products matching keywords and colors
        
        Args:
            keywords: Search keywords (e.g., ['shirt', 'formal'])
            colors: Target colors (e.g., ['coral', 'navy'])
            category: Product category (e.g., 'shirt', 'pants')
            gender: User gender for filtering
            max_results: Maximum number of results
            platform: 'amazon', 'flipkart', or 'all'
            
        Returns:
            List of product dictionaries with affiliate links
        """
        try:
            products = []
            
            if platform in ['amazon', 'all']:
                amazon_products = self._search_amazon(keywords, colors, category, gender, max_results)
                products.extend(amazon_products)
            
            if platform in ['flipkart', 'all']:
                flipkart_products = self._search_flipkart(keywords, colors, category, gender, max_results)
                products.extend(flipkart_products)
            
            # Sort by relevance and price
            products = self._rank_products(products, colors)
            
            return products[:max_results]
            
        except Exception as e:
            self.logger.error(f"Product search failed: {e}")
            return []
    
    def _search_amazon(self, keywords: List[str], colors: List[str], 
                      category: str, gender: str, max_results: int) -> List[Dict]:
        """
        Search Amazon India using Product Advertising API
        
        Returns:
            List of Amazon products with affiliate links
        """
        try:
            # Check if API credentials are configured
            if not self.amazon_affiliate_id or not self.amazon_access_key:
                self.logger.warning("Amazon API credentials not configured - using mock data")
                return self._get_mock_amazon_products(keywords, colors, category, gender)
            
            # Use Amazon PA-API 5.0
            from paapi5_python_sdk.api.default_api import DefaultApi
            from paapi5_python_sdk.search_items_request import SearchItemsRequest
            from paapi5_python_sdk.search_items_resource import SearchItemsResource
            from paapi5_python_sdk.partner_type import PartnerType
            
            # Build search query
            search_query = ' '.join(keywords + colors + [category, gender])
            
            # Check cache
            cache_key = f"amazon_{search_query}"
            if cache_key in self.cache:
                cached_data, cache_time = self.cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    self.logger.info(f"✅ Using cached Amazon results for: {search_query}")
                    return cached_data
            
            # Make API request
            api_client = DefaultApi(
                access_key=self.amazon_access_key,
                secret_key=self.amazon_secret_key,
                host='webservices.amazon.in',
                region='eu-west-1'
            )
            
            search_request = SearchItemsRequest(
                partner_tag=self.amazon_affiliate_id,
                partner_type=PartnerType.ASSOCIATES,
                keywords=search_query,
                search_index='Fashion',
                item_count=max_results,
                resources=[
                    SearchItemsResource.ITEMINFO_TITLE,
                    SearchItemsResource.OFFERS_LISTINGS_PRICE,
                    SearchItemsResource.IMAGES_PRIMARY_LARGE
                ]
            )
            
            response = api_client.search_items(search_request)
            
            # Parse response
            products = []
            if response and response.search_result and response.search_result.items:
                for item in response.search_result.items:
                    product = {
                        'platform': 'Amazon',
                        'name': item.item_info.title.display_value,
                        'url': item.detail_page_url,
                        'affiliate_url': item.detail_page_url,  # Already has affiliate tag
                        'image_url': item.images.primary.large.url if item.images else '',
                        'price': self._extract_amazon_price(item),
                        'currency': 'INR',
                        'category': category,
                        'color': self._detect_product_color(item.item_info.title.display_value, colors),
                        'asin': item.asin
                    }
                    products.append(product)
            
            # Cache results
            self.cache[cache_key] = (products, datetime.now())
            
            self.logger.info(f"✅ Found {len(products)} Amazon products")
            return products
            
        except ImportError:
            self.logger.warning("Amazon PA-API SDK not installed - using mock data")
            return self._get_mock_amazon_products(keywords, colors, category, gender)
        except Exception as e:
            self.logger.error(f"Amazon search failed: {e}")
            return self._get_mock_amazon_products(keywords, colors, category, gender)
    
    def _search_flipkart(self, keywords: List[str], colors: List[str],
                        category: str, gender: str, max_results: int) -> List[Dict]:
        """
        Search Flipkart using Affiliate API
        
        Returns:
            List of Flipkart products with affiliate links
        """
        try:
            if not self.flipkart_affiliate_id or not self.flipkart_affiliate_token:
                self.logger.warning("Flipkart API credentials not configured - using mock data")
                return self._get_mock_flipkart_products(keywords, colors, category, gender)
            
            # Build search query
            search_query = ' '.join(keywords + colors + [category])
            
            # Flipkart Affiliate API endpoint
            api_url = "https://affiliate-api.flipkart.net/affiliate/api/{}.json".format(
                self.flipkart_affiliate_id
            )
            
            headers = {
                'Fk-Affiliate-Id': self.flipkart_affiliate_id,
                'Fk-Affiliate-Token': self.flipkart_affiliate_token
            }
            
            params = {
                'query': search_query,
                'resultCount': max_results
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                products = []
                
                for item in data.get('products', []):
                    product = {
                        'platform': 'Flipkart',
                        'name': item.get('productBaseInfoV1', {}).get('title', ''),
                        'url': item.get('productBaseInfoV1', {}).get('productUrl', ''),
                        'affiliate_url': self._generate_flipkart_affiliate_link(
                            item.get('productBaseInfoV1', {}).get('productUrl', '')
                        ),
                        'image_url': item.get('productBaseInfoV1', {}).get('imageUrls', {}).get('400x400', ''),
                        'price': item.get('productBaseInfoV1', {}).get('flipkartSellingPrice', {}).get('amount', 0),
                        'currency': 'INR',
                        'category': category,
                        'color': self._detect_product_color(item.get('productBaseInfoV1', {}).get('title', ''), colors)
                    }
                    products.append(product)
                
                self.logger.info(f"✅ Found {len(products)} Flipkart products")
                return products
            else:
                self.logger.warning(f"Flipkart API returned status {response.status_code}")
                return self._get_mock_flipkart_products(keywords, colors, category, gender)
                
        except Exception as e:
            self.logger.error(f"Flipkart search failed: {e}")
            return self._get_mock_flipkart_products(keywords, colors, category, gender)
    
    def _generate_flipkart_affiliate_link(self, product_url: str) -> str:
        """Generate Flipkart affiliate link"""
        if self.flipkart_affiliate_id and product_url:
            return f"{product_url}?affid={self.flipkart_affiliate_id}"
        return product_url
    
    def _extract_amazon_price(self, item) -> float:
        """Extract price from Amazon item"""
        try:
            if item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if listing.price:
                    return listing.price.amount
        except:
            pass
        return 0.0
    
    def _detect_product_color(self, product_title: str, target_colors: List[str]) -> str:
        """Detect which target color is mentioned in product title"""
        product_title_lower = product_title.lower()
        for color in target_colors:
            if color.lower() in product_title_lower:
                return color
        return 'Unknown'
    
    def _rank_products(self, products: List[Dict], target_colors: List[str]) -> List[Dict]:
        """
        Rank products by relevance to target colors
        
        Args:
            products: List of product dictionaries
            target_colors: User's best colors
            
        Returns:
            Sorted list of products
        """
        def color_match_score(product):
            """Calculate color match score"""
            product_color = product.get('color', '').lower()
            if product_color in [c.lower() for c in target_colors]:
                return 10  # High score for exact match
            return 1  # Low score for no match
        
        # Sort by color match, then by price
        products.sort(key=lambda p: (color_match_score(p), -p.get('price', 0)), reverse=True)
        return products
    
    def _get_mock_amazon_products(self, keywords: List[str], colors: List[str],
                                 category: str, gender: str) -> List[Dict]:
        """Generate mock Amazon products for development/testing"""
        mock_products = []
        base_prices = {'shirt': 999, 'pants': 1499, 'dress': 1999, 'shoes': 2499}
        base_price = base_prices.get(category, 1299)
        
        for i, color in enumerate(colors[:5]):
            product = {
                'platform': 'Amazon',
                'name': f"{color.title()} {category.title()} for {gender}",
                'url': f"https://www.amazon.in/dp/MOCK{i}?tag={self.amazon_affiliate_id}",
                'affiliate_url': f"https://www.amazon.in/dp/MOCK{i}?tag={self.amazon_affiliate_id}",
                'image_url': 'https://via.placeholder.com/400x400?text=' + color.replace(' ', '+'),
                'price': base_price + (i * 200),
                'currency': 'INR',
                'category': category,
                'color': color,
                'asin': f'MOCK{i:03d}',
                'mock': True
            }
            mock_products.append(product)
        
        return mock_products
    
    def _get_mock_flipkart_products(self, keywords: List[str], colors: List[str],
                                   category: str, gender: str) -> List[Dict]:
        """Generate mock Flipkart products for development/testing"""
        mock_products = []
        base_prices = {'shirt': 899, 'pants': 1399, 'dress': 1899, 'shoes': 2299}
        base_price = base_prices.get(category, 1199)
        
        for i, color in enumerate(colors[:5]):
            product = {
                'platform': 'Flipkart',
                'name': f"{color.title()} {category.title()} - {gender}",
                'url': f"https://www.flipkart.com/mock-product-{i}",
                'affiliate_url': f"https://www.flipkart.com/mock-product-{i}?affid={self.flipkart_affiliate_id}",
                'image_url': 'https://via.placeholder.com/400x400?text=' + color.replace(' ', '+'),
                'price': base_price + (i * 150),
                'currency': 'INR',
                'category': category,
                'color': color,
                'mock': True
            }
            mock_products.append(product)
        
        return mock_products
    
    def convert_to_affiliate_link(self, original_url: str, platform: str) -> str:
        """
        Convert a regular product URL to affiliate link using Cuelinks/EarnKaro
        
        Args:
            original_url: Original product URL
            platform: Platform name
            
        Returns:
            Affiliate tracking URL
        """
        try:
            if self.cuelinks_api_key:
                # Use Cuelinks universal affiliate link converter
                cuelinks_url = f"https://linksredirect.com/?pub_id={self.cuelinks_api_key}&url={original_url}"
                return cuelinks_url
            else:
                return original_url
        except Exception as e:
            self.logger.error(f"Affiliate link conversion failed: {e}")
            return original_url
