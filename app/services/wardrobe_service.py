"""
VastraVista - Digital Wardrobe Management Service
Author: Saumya Tiwari
Purpose: Manage user's digital wardrobe with AI-powered analysis and recommendations
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import json

from app.services.color_analyzer import ColorAnalyzer
from app.utils.color_utils import rgb_to_hex, calculate_color_distance

logger = logging.getLogger(__name__)


class WardrobeManager:
    """
    Digital wardrobe management with AI-powered analysis
    Features: Item categorization, color analysis, skin tone compatibility, outfit generation
    """
    
    def __init__(self):
        """Initialize wardrobe manager"""
        self.logger = logging.getLogger(__name__)
        self.color_analyzer = ColorAnalyzer()
        
        # Clothing categories
        self.categories = {
            'tops': ['t-shirt', 'shirt', 'blouse', 'sweater', 'hoodie', 'tank-top', 'polo'],
            'bottoms': ['jeans', 'pants', 'trousers', 'shorts', 'skirt', 'leggings'],
            'dresses': ['casual-dress', 'formal-dress', 'maxi-dress', 'midi-dress'],
            'outerwear': ['jacket', 'coat', 'blazer', 'cardigan', 'vest'],
            'shoes': ['sneakers', 'formal-shoes', 'sandals', 'boots', 'heels', 'flats'],
            'accessories': ['scarf', 'hat', 'belt', 'bag', 'jewelry']
        }
        
        self.logger.info("👔 Wardrobe Manager initialized")
    
    def analyze_wardrobe_item(self, image_path: str, user_skin_tone: Dict,
                              item_name: Optional[str] = None,
                              category: Optional[str] = None) -> Dict:
        """
        Analyze a wardrobe item for color, category, and skin tone compatibility
        
        Args:
            image_path: Path to item image
            user_skin_tone: User's skin tone analysis results
            item_name: Optional item name
            category: Optional category (auto-detected if not provided)
            
        Returns:
            Complete item analysis including compatibility scores
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Auto-detect category if not provided
            if not category:
                category = self._detect_clothing_category(image, item_name)
            
            # Extract dominant colors
            color_analysis = self._extract_item_colors(image)
            
            # Calculate skin tone compatibility using Delta-E
            compatibility = self._calculate_skin_tone_compatibility(
                color_analysis['dominant_colors'],
                user_skin_tone
            )
            
            # Detect fabric texture (for advanced recommendations)
            fabric_info = self._analyze_fabric_texture(image)
            
            # Generate item metadata
            result = {
                'name': item_name or f"{color_analysis['primary_color_name']} {category}",
                'category': category,
                'sub_category': self._determine_sub_category(category, image),
                'primary_color': color_analysis['primary_color'],
                'primary_color_name': color_analysis['primary_color_name'],
                'secondary_color': color_analysis['secondary_color'],
                'secondary_color_name': color_analysis['secondary_color_name'],
                'color_palette': color_analysis['all_colors'],
                'skin_tone_compatibility': compatibility['score'],
                'compatibility_rating': compatibility['rating'],
                'delta_e_score': compatibility['delta_e'],
                'fabric_texture': fabric_info['texture_type'],
                'fabric_formality': fabric_info['formality_score'],
                'recommended_occasions': self._suggest_occasions(category, color_analysis, fabric_info),
                'recommended_seasons': self._suggest_seasons(category, color_analysis, fabric_info),
                'styling_tips': self._generate_styling_tips(category, color_analysis, compatibility)
            }
            
            self.logger.info(f"✅ Analyzed item: {result['name']} - {result['compatibility_rating']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Item analysis failed: {e}")
            return {'error': str(e)}
    
    def _extract_item_colors(self, image: np.ndarray) -> Dict:
        """
        Extract dominant colors from clothing item
        
        Args:
            image: Item image
            
        Returns:
            Dictionary with color information
        """
        try:
            # Resize for faster processing
            height, width = image.shape[:2]
            if height > 800:
                scale = 800 / height
                image = cv2.resize(image, (int(width * scale), 800))
            
            # Remove background (focus on clothing item)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract colors using k-means clustering
            pixels = image_rgb.reshape(-1, 3)
            pixels = np.float32(pixels)
            
            # K-means clustering to find dominant colors
            n_colors = 5
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
            _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            
            # Count pixels in each cluster
            unique, counts = np.unique(labels, return_counts=True)
            sorted_indices = np.argsort(-counts)
            
            # Get dominant colors
            dominant_colors = []
            for idx in sorted_indices:
                rgb = centers[idx].astype(int)
                hex_color = rgb_to_hex(tuple(rgb))
                color_name = self._get_color_name(tuple(rgb))
                percentage = (counts[idx] / len(labels)) * 100
                
                dominant_colors.append({
                    'rgb': tuple(rgb),
                    'hex': hex_color,
                    'name': color_name,
                    'percentage': float(percentage)
                })
            
            return {
                'primary_color': dominant_colors[0]['rgb'],
                'primary_color_name': dominant_colors[0]['name'],
                'secondary_color': dominant_colors[1]['rgb'] if len(dominant_colors) > 1 else dominant_colors[0]['rgb'],
                'secondary_color_name': dominant_colors[1]['name'] if len(dominant_colors) > 1 else dominant_colors[0]['name'],
                'all_colors': dominant_colors
            }
            
        except Exception as e:
            self.logger.error(f"Color extraction failed: {e}")
            return {
                'primary_color': (128, 128, 128),
                'primary_color_name': 'Gray',
                'secondary_color': (128, 128, 128),
                'secondary_color_name': 'Gray',
                'all_colors': []
            }
    
    def _calculate_skin_tone_compatibility(self, item_colors: List[Dict],
                                          user_skin_tone: Dict) -> Dict:
        """
        Calculate how well item colors match user's skin tone using Delta-E
        
        Args:
            item_colors: List of dominant colors from item
            user_skin_tone: User's skin tone analysis
            
        Returns:
            Compatibility score and rating
        """
        try:
            # Get user's skin tone RGB
            skin_tone_rgb = user_skin_tone.get('rgb', (180, 140, 110))
            
            # Calculate Delta-E for primary color
            primary_rgb = item_colors[0]['rgb']
            delta_e = calculate_color_distance(primary_rgb, skin_tone_rgb)
            
            # Convert Delta-E to compatibility score (0-100)
            # Lower Delta-E = better compatibility
            # Delta-E < 15: Excellent, 15-30: Good, 30-50: Fair, >50: Poor
            if delta_e < 15:
                score = 100
                rating = 'Excellent Match'
            elif delta_e < 30:
                score = 85 - (delta_e - 15) * 2
                rating = 'Good Match'
            elif delta_e < 50:
                score = 55 - (delta_e - 30)
                rating = 'Fair Match'
            else:
                score = max(30 - (delta_e - 50) * 0.5, 0)
                rating = 'Poor Match'
            
            return {
                'score': float(score),
                'rating': rating,
                'delta_e': float(delta_e)
            }
            
        except Exception as e:
            self.logger.error(f"Compatibility calculation failed: {e}")
            return {'score': 50.0, 'rating': 'Unknown', 'delta_e': 0.0}
    
    def _detect_clothing_category(self, image: np.ndarray, item_name: Optional[str]) -> str:
        """
        Auto-detect clothing category using image analysis and ML
        
        Args:
            image: Item image
            item_name: Optional item name for hints
            
        Returns:
            Detected category
        """
        try:
            # Simple heuristic-based detection
            # In production, use a trained CNN classifier
            
            height, width = image.shape[:2]
            aspect_ratio = height / width
            
            # Analyze item name if provided
            if item_name:
                item_name_lower = item_name.lower()
                for main_cat, sub_cats in self.categories.items():
                    for sub_cat in sub_cats:
                        if sub_cat.replace('-', ' ') in item_name_lower:
                            return main_cat
                    if main_cat in item_name_lower:
                        return main_cat
            
            # Basic shape-based detection
            if aspect_ratio > 1.3:
                return 'tops'  # Tall and narrow
            elif aspect_ratio < 0.8:
                return 'shoes'  # Wide and short
            elif aspect_ratio > 2.0:
                return 'dresses'  # Very tall
            else:
                return 'bottoms'  # Medium aspect ratio
                
        except Exception as e:
            self.logger.error(f"Category detection failed: {e}")
            return 'unknown'
    
    def _determine_sub_category(self, category: str, image: np.ndarray) -> str:
        """Determine specific sub-category within main category"""
        # Simplified - in production, use ML classifier
        sub_cats = self.categories.get(category, [])
        return sub_cats[0] if sub_cats else category
    
    def _analyze_fabric_texture(self, image: np.ndarray) -> Dict:
        """
        Analyze fabric texture to determine formality and material type
        
        Args:
            image: Item image
            
        Returns:
            Fabric analysis results
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Texture analysis using variance and edges
            texture_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # High variance = textured (casual, denim, knit)
            # Low variance = smooth (formal, silk, cotton)
            if texture_variance > 100:
                texture_type = 'textured'
                formality = 30  # More casual
            elif texture_variance > 50:
                texture_type = 'medium'
                formality = 60  # Business casual
            else:
                texture_type = 'smooth'
                formality = 90  # Formal
            
            return {
                'texture_type': texture_type,
                'texture_variance': float(texture_variance),
                'formality_score': formality
            }
            
        except Exception as e:
            self.logger.error(f"Fabric analysis failed: {e}")
            return {'texture_type': 'unknown', 'texture_variance': 0, 'formality_score': 50}
    
    def _suggest_occasions(self, category: str, color_analysis: Dict, fabric_info: Dict) -> List[str]:
        """Suggest appropriate occasions for the item"""
        occasions = []
        formality = fabric_info.get('formality_score', 50)
        
        if formality > 70:
            occasions.extend(['formal', 'business', 'wedding', 'interview'])
        elif formality > 40:
            occasions.extend(['business-casual', 'date-night', 'dinner'])
        else:
            occasions.extend(['casual', 'weekend', 'sports', 'everyday'])
        
        return occasions
    
    def _suggest_seasons(self, category: str, color_analysis: Dict, fabric_info: Dict) -> List[str]:
        """Suggest appropriate seasons based on color and fabric"""
        seasons = []
        
        # Analyze primary color brightness
        primary_rgb = color_analysis['primary_color']
        brightness = sum(primary_rgb) / 3
        
        if brightness > 180:
            seasons.extend(['summer', 'spring'])
        elif brightness < 100:
            seasons.extend(['winter', 'fall'])
        else:
            seasons.append('all-season')
        
        return seasons
    
    def _generate_styling_tips(self, category: str, color_analysis: Dict, compatibility: Dict) -> List[str]:
        """Generate personalized styling tips"""
        tips = []
        
        if compatibility['rating'] == 'Excellent Match':
            tips.append(f"This {color_analysis['primary_color_name']} color perfectly complements your skin tone!")
            tips.append("Wear this for important occasions where you want to look your best.")
        elif compatibility['rating'] == 'Good Match':
            tips.append(f"This {color_analysis['primary_color_name']} works well with your coloring.")
        elif compatibility['rating'] == 'Poor Match':
            tips.append("Try wearing this with accessories in your best colors to balance the look.")
            tips.append("Consider keeping this for layering under better-matching outer pieces.")
        
        return tips
    
    def _get_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to approximate color name"""
        # Simplified color naming
        r, g, b = rgb
        
        if r > 200 and g < 100 and b < 100:
            return 'Red'
        elif r < 100 and g > 200 and b < 100:
            return 'Green'
        elif r < 100 and g < 100 and b > 200:
            return 'Blue'
        elif r > 200 and g > 200 and b < 100:
            return 'Yellow'
        elif r > 150 and g < 100 and b > 150:
            return 'Purple'
        elif r > 200 and g > 150 and b < 100:
            return 'Orange'
        elif r > 200 and g > 200 and b > 200:
            return 'White'
        elif r < 50 and g < 50 and b < 50:
            return 'Black'
        elif abs(r - g) < 30 and abs(g - b) < 30:
            return 'Gray'
        else:
            return 'Multi-color'
    
    def generate_outfit_combinations(self, wardrobe_items: List[Dict],
                                   occasion: str = 'casual',
                                   season: str = 'all-season',
                                   max_outfits: int = 10) -> List[Dict]:
        """
        Generate complete outfit combinations from wardrobe items
        
        Args:
            wardrobe_items: List of user's wardrobe items
            occasion: Target occasion
            season: Target season
            max_outfits: Maximum number of outfits to generate
            
        Returns:
            List of outfit combinations with scores
        """
        try:
            # Separate items by category
            categorized = {}
            for item in wardrobe_items:
                cat = item.get('category', 'unknown')
                if cat not in categorized:
                    categorized[cat] = []
                categorized[cat].append(item)
            
            outfits = []
            
            # Generate combinations: Top + Bottom + Shoes
            tops = categorized.get('tops', [])
            bottoms = categorized.get('bottoms', [])
            shoes = categorized.get('shoes', [])
            
            for top in tops:
                for bottom in bottoms:
                    for shoe in shoes:
                        # Check occasion and season compatibility
                        if self._items_match_occasion([top, bottom, shoe], occasion):
                            outfit = self._create_outfit(top, bottom, shoe, occasion, season)
                            outfits.append(outfit)
            
            # Sort by compatibility score
            outfits.sort(key=lambda x: x['overall_score'], reverse=True)
            
            return outfits[:max_outfits]
            
        except Exception as e:
            self.logger.error(f"Outfit generation failed: {e}")
            return []
    
    def _items_match_occasion(self, items: List[Dict], occasion: str) -> bool:
        """Check if items are appropriate for occasion"""
        for item in items:
            occasions = item.get('recommended_occasions', [])
            if occasion in occasions:
                return True
        return False
    
    def _create_outfit(self, top: Dict, bottom: Dict, shoe: Dict,
                      occasion: str, season: str) -> Dict:
        """Create outfit combination with scoring"""
        # Calculate color harmony
        color_harmony = self._calculate_color_harmony(
            top['primary_color'],
            bottom['primary_color'],
            shoe['primary_color']
        )
        
        # Calculate average skin tone compatibility
        avg_compatibility = (
            top['skin_tone_compatibility'] +
            bottom['skin_tone_compatibility'] +
            shoe['skin_tone_compatibility']
        ) / 3
        
        # Overall score
        overall_score = (color_harmony * 0.4 + avg_compatibility * 0.6)
        
        return {
            'items': {
                'top': top,
                'bottom': bottom,
                'shoes': shoe
            },
            'occasion': occasion,
            'season': season,
            'color_harmony_score': color_harmony,
            'skin_tone_match_score': avg_compatibility,
            'overall_score': overall_score,
            'recommendation_reason': self._generate_outfit_reason(overall_score, color_harmony)
        }
    
    def _calculate_color_harmony(self, color1: Tuple, color2: Tuple, color3: Tuple) -> float:
        """Calculate color harmony score (0-100)"""
        # Simplified color harmony based on color theory
        # Check complementary, analogous, or triadic relationships
        
        # For now, use Delta-E distances
        d12 = calculate_color_distance(color1, color2)
        d23 = calculate_color_distance(color2, color3)
        d13 = calculate_color_distance(color1, color3)
        
        avg_distance = (d12 + d23 + d13) / 3
        
        # Good harmony: not too similar, not too different
        if 20 < avg_distance < 40:
            return 90.0
        elif 15 < avg_distance < 50:
            return 75.0
        else:
            return 50.0
    
    def _generate_outfit_reason(self, overall_score: float, color_harmony: float) -> str:
        """Generate explanation for outfit recommendation"""
        if overall_score > 85:
            return "Excellent combination! Colors work beautifully together and complement your skin tone."
        elif overall_score > 70:
            return "Great outfit choice with good color coordination."
        elif overall_score > 50:
            return "Decent combination, suitable for casual occasions."
        else:
            return "Consider trying other combinations for better color harmony."
