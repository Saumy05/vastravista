"""
Color Analyzer Service
Delta-E calculations and color matching
"""

import logging
from typing import Dict, List, Tuple
from app.utils.color_utils import rgb_to_lab, calculate_delta_e_2000, rgb_to_hex
from app.utils.constants import FASHION_COLORS


class ColorAnalyzer:
    """
    Color analysis using Delta-E in Lab color space
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fashion_colors = self._build_color_database()
    
    def _build_color_database(self) -> Dict:
        """Build fashion color database with Lab values"""
        database = {}
        
        for name, rgb in FASHION_COLORS.items():
            lab = rgb_to_lab(rgb)
            hex_color = rgb_to_hex(rgb)
            
            database[name] = {
                'rgb': rgb,
                'lab': lab,
                'hex': hex_color,
                'family': self._determine_color_family(rgb),
                'undertone': self._determine_undertone(rgb)
            }
        
        return database
    
    def _determine_color_family(self, rgb: Tuple[int, int, int]) -> str:
        """Determine color family"""
        r, g, b = rgb
        
        if r > 200 and g > 200 and b > 200:
            return 'White/Light'
        elif r < 50 and g < 50 and b < 50:
            return 'Black/Dark'
        elif abs(r - g) < 30 and abs(g - b) < 30:
            return 'Neutral'
        elif r > max(g, b):
            return 'Red/Orange' if g > b else 'Red/Pink'
        elif g > max(r, b):
            return 'Green'
        elif b > max(r, g):
            return 'Purple/Violet' if r > g else 'Blue'
        else:
            return 'Mixed'
    
    def _determine_undertone(self, rgb: Tuple[int, int, int]) -> str:
        """Determine if color is warm, cool, or neutral"""
        r, g, b = rgb
        
        if r > b + 20:
            return 'Warm'
        elif b > r + 20:
            return 'Cool'
        else:
            return 'Neutral'
    
    def find_best_colors(self, skin_rgb: Tuple[int, int, int], 
                        top_n: int = 15) -> List[Dict]:
        """
        Find best FASHION colors for skin tone using CONTRAST and HARMONY theory
        NOT similarity - we want colors that COMPLEMENT, not match!
        
        Args:
            skin_rgb: Skin tone RGB values
            top_n: Number of top colors to return
            
        Returns:
            List of best complementary colors with details
        """
        try:
            # Calculate skin tone characteristics
            r, g, b = skin_rgb
            skin_brightness = (r + g + b) / 3
            skin_warmth = (r - b) / 255.0  # Positive = warm, negative = cool
            
            # Determine skin category for fashion rules
            if skin_brightness > 180:
                skin_category = 'very_light'
            elif skin_brightness > 140:
                skin_category = 'light'
            elif skin_brightness > 100:
                skin_category = 'medium'
            elif skin_brightness > 70:
                skin_category = 'tan'
            else:
                skin_category = 'dark'
            
            self.logger.info(f"🎨 Skin analysis: brightness={skin_brightness:.1f}, warmth={skin_warmth:.2f}, category={skin_category}")
            
            skin_lab = rgb_to_lab(skin_rgb)
            matches = []
            
            for color_name, color_data in self.fashion_colors.items():
                color_rgb = color_data['rgb']
                cr, cg, cb = color_rgb
                color_brightness = (cr + cg + cb) / 3
                
                # Calculate CONTRAST score (opposite of similarity for fashion!)
                brightness_contrast = abs(color_brightness - skin_brightness) / 255.0
                
                # Calculate COMPLEMENTARY score using color theory
                delta_e = calculate_delta_e_2000(skin_lab, color_data['lab'])
                
                # FASHION SCORING SYSTEM - Different rules for different skin tones
                base_score = 0
                
                if skin_category in ['very_light', 'light']:
                    # LIGHT SKIN: Looks best in BOLD, DARK, SATURATED colors
                    # AVOID: Pastels, pale colors, whites, beiges
                    if color_brightness < 100:  # Very dark colors - BEST
                        base_score += 50
                    elif color_brightness < 140:  # Dark colors - GREAT
                        base_score += 40
                    elif color_brightness < 170:  # Medium colors - OK
                        base_score += 15
                    else:  # Light colors - AVOID
                        base_score -= 30
                    
                    # Bonus for rich, saturated colors
                    color_saturation = (max(color_rgb) - min(color_rgb)) / (max(color_rgb) + 1)
                    if color_saturation > 0.6:  # Very vibrant
                        base_score += 35
                    elif color_saturation > 0.4:  # Vibrant
                        base_score += 20
                    
                    # Excellent: Navy, Emerald, Ruby, Deep Purple, Black
                    if color_name in ['Navy', 'Emerald', 'Ruby', 'Wine', 'Black', 'Forest Green', 
                                     'Royal Blue', 'Burgundy', 'Teal', 'Deep Purple', 'Charcoal']:
                        base_score += 45
                    
                    # Avoid: Pastels, pale colors, beiges
                    if color_name in ['Cream', 'Ivory', 'Beige', 'Pale Pink', 'Baby Blue', 'Lavender',
                                     'Camel', 'Tan', 'Khaki', 'Peach']:
                        base_score -= 60
                        
                elif skin_category in ['dark']:
                    # DARK SKIN: Looks stunning in BRIGHT, VIBRANT, JEWEL tones
                    # AVOID: Muddy browns, dark grays, blacks
                    if color_brightness > 140:  # Bright colors
                        base_score += 40
                    elif color_brightness > 100:  # Medium bright
                        base_score += 25
                    else:  # Dark colors - can work but not best
                        base_score += 5
                    
                    # Bonus for vibrant, saturated colors
                    color_saturation = (max(color_rgb) - min(color_rgb)) / (max(color_rgb) + 1)
                    if color_saturation > 0.6:  # Very vibrant
                        base_score += 35
                    
                    # Excellent: Bright jewel tones, metallics, bold colors
                    if color_name in ['Gold', 'Coral', 'Turquoise', 'Fuchsia', 'Bright Pink', 
                                     'Orange', 'Lemon Yellow', 'Cobalt Blue', 'Purple', 'White']:
                        base_score += 40
                    
                    # Avoid: Muddy, dark, muted colors
                    if color_name in ['Brown', 'Dark Gray', 'Black', 'Olive', 'Tan']:
                        base_score -= 40
                        
                else:  # medium, tan skin
                    # MEDIUM SKIN: Most versatile - earth tones, jewel tones, rich colors
                    # Best: Colors with STRONG contrast (not too similar to skin)
                    brightness_diff = abs(color_brightness - skin_brightness)
                    
                    if brightness_diff > 80:  # Very strong contrast - BEST
                        base_score += 45
                    elif brightness_diff > 50:  # Strong contrast - GREAT
                        base_score += 35
                    elif brightness_diff > 30:  # Medium contrast - GOOD
                        base_score += 20
                    else:  # Weak contrast - TOO SIMILAR
                        base_score -= 10
                    
                    color_saturation = (max(color_rgb) - min(color_rgb)) / (max(color_rgb) + 1)
                    if color_saturation > 0.5:  # Rich, saturated colors
                        base_score += 30
                    elif color_saturation > 0.35:
                        base_score += 18
                    
                    # EXCELLENT: Bold jewel tones and rich colors with high saturation
                    if color_name in ['Burgundy', 'Mustard', 'Teal', 'Forest Green', 
                                     'Royal Blue', 'Navy', 'Emerald', 'Deep Purple', 
                                     'Wine', 'Plum']:
                        base_score += 50
                    
                    # GOOD: Earth tones (but check brightness to avoid being too similar)
                    if color_name in ['Rust', 'Olive'] and brightness_diff > 40:
                        base_score += 40
                    
                    # CAREFUL: Terracotta can be too close to medium skin - only if good contrast
                    if color_name in ['Terracotta'] and brightness_diff > 35:
                        base_score += 30
                    elif color_name in ['Terracotta']:
                        base_score += 5  # Downgrade if too similar
                    
                    # Coral is bright - better for darker skin
                    if color_name in ['Coral', 'Salmon', 'Peach']:
                        base_score -= 10
                    
                    # AVOID: Colors too similar to medium skin (muddy/neutral tones)
                    if color_name in ['Camel', 'Tan', 'Beige', 'Khaki', 'Taupe', 'Desert Sand', 
                                     'Clay', 'Earth Brown']:
                        base_score -= 60
                
                # Add contrast bonus (colors different from skin = better)
                base_score += brightness_contrast * 20
                
                # Convert to confidence score (0-100)
                confidence_score = max(0, min(100, base_score))
                
                # Determine rating
                if confidence_score >= 75:
                    rating = 'Excellent'
                elif confidence_score >= 60:
                    rating = 'Good'
                elif confidence_score >= 40:
                    rating = 'Fair'
                else:
                    rating = 'Poor'
                
                matches.append({
                    'color_name': color_name,
                    'rgb': color_data['rgb'],
                    'hex': color_data['hex'],
                    'family': color_data['family'],
                    'undertone': color_data['undertone'],
                    'delta_e': round(delta_e, 2),
                    'confidence_score': confidence_score,
                    'rating': rating,
                    'skin_category': skin_category
                })
            
            # Sort by confidence score (highest = best for fashion)
            matches.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            self.logger.info(f"✨ Top 5 colors for {skin_category} skin: {[m['color_name'] for m in matches[:5]]}")
            
            return matches[:top_n]
            
        except Exception as e:
            self.logger.error(f"Color matching failed: {e}")
            return []
    
    def categorize_colors(self, colors: List[Dict]) -> Dict:
        """
        Categorize colors by rating
        
        Args:
            colors: List of color matches
            
        Returns:
            Dictionary with categorized colors
        """
        return {
            'excellent': [c for c in colors if c['rating'] == 'Excellent'],
            'good': [c for c in colors if c['rating'] == 'Good'],
            'fair': [c for c in colors if c['rating'] == 'Fair'],
            'poor': [c for c in colors if c['rating'] in ['Poor - Too Similar', 'Poor - Too Contrasting']]
        }
    
    def analyze_with_ai_reasoning(self, skin_rgb: Tuple[int, int, int], 
                                  monk_level: str,
                                  occasion: str = 'casual',
                                  style_preferences: List[str] = None) -> Dict:
        """
        Enhanced color analysis with AI-powered reasoning using DeepSeek R1
        
        Args:
            skin_rgb: Skin tone RGB values
            monk_level: Monk Skin Tone Scale level (MST-1 to MST-10)
            occasion: Event type (casual, formal, party, etc.)
            style_preferences: List of style preferences
            
        Returns:
            Color analysis with AI-generated fashion advice
        """
        try:
            # Get standard color matches using Delta-E
            best_colors = self.find_best_colors(skin_rgb, top_n=10)
            categorized = self.categorize_colors(best_colors)
            
            # Get AI-powered fashion advice using OpenRouter + DeepSeek R1
            from app.services.openrouter_service import get_openrouter_client
            openrouter = get_openrouter_client()
            
            skin_hex = rgb_to_hex(skin_rgb)
            style_prefs = style_preferences or ['modern', 'versatile']
            
            ai_advice = openrouter.generate_fashion_advice(
                user_skin_tone=skin_hex,
                monk_level=monk_level,
                occasion=occasion,
                style_preferences=style_prefs
            )
            
            return {
                'delta_e_analysis': {
                    'best_colors': best_colors,
                    'categorized_colors': categorized,
                    'scientific_method': 'Delta-E CIE2000'
                },
                'monk_scale': {
                    'level': monk_level,
                    'skin_rgb': skin_rgb,
                    'skin_hex': skin_hex
                },
                'ai_reasoning': ai_advice,
                'combined_recommendation': {
                    'top_colors': [c['color_name'] for c in best_colors[:5]],
                    'confidence': 'high',
                    'methodology': 'Delta-E CIE2000 + DeepSeek R1 AI'
                }
            }
            
        except Exception as e:
            self.logger.error(f"AI-enhanced color analysis failed: {e}")
            # Fallback to standard analysis
            best_colors = self.find_best_colors(skin_rgb, top_n=10)
            return {
                'delta_e_analysis': {
                    'best_colors': best_colors,
                    'categorized_colors': self.categorize_colors(best_colors)
                },
                'monk_scale': {'level': monk_level, 'skin_rgb': skin_rgb},
                'ai_reasoning': {'success': False, 'fallback': True},
                'error': str(e)
            }
