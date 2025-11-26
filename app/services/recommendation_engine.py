"""
VastraVista - Fashion Recommendation Engine
Author: Saumya Tiwari
Purpose: Comprehensive outfit recommendations based on gender, age, and skin tone
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import sys

from app.services.color_analyzer import ColorAnalyzer
from app.utils.constants import CLOTHING_CATEGORIES

class FashionRecommendationEngine:
    """
    Comprehensive fashion recommendation system
    Combines gender, age group, and skin tone analysis
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize color analyzer
        self.color_analyzer = ColorAnalyzer()
        
        # Clothing categories database
        self.clothing_categories = CLOTHING_CATEGORIES
        
        self.logger.info("👗 RecommendationEngine initialized")
    
    def _DEPRECATED_build_clothing_database(self) -> Dict:
        """
        Build clothing category database based on gender and age
        
        Returns:
            Dictionary of clothing recommendations
        """
        return {
            'Male': {
                'Teen': {
                    'casual': ['T-shirts', 'Hoodies', 'Jeans', 'Sneakers', 'Caps', 'Bomber Jackets'],
                    'formal': ['Dress Shirts', 'Chinos', 'Blazers', 'Loafers'],
                    'sports': ['Athletic Shorts', 'Sports Jersey', 'Running Shoes', 'Track Pants'],
                    'party': ['Polo Shirts', 'Denim Jackets', 'Casual Blazers', 'Smart Sneakers']
                },
                'Young Adult': {
                    'casual': ['Casual Shirts', 'Slim Jeans', 'Sneakers', 'T-shirts', 'Hoodies', 'Chinos'],
                    'formal': ['Suits', 'Dress Shirts', 'Ties', 'Dress Shoes', 'Blazers', 'Formal Trousers'],
                    'business': ['Business Suits', 'Oxford Shirts', 'Leather Shoes', 'Dress Pants'],
                    'party': ['Fitted Shirts', 'Designer Jeans', 'Leather Jackets', 'Dress Boots'],
                    'sports': ['Gym Wear', 'Athletic Shoes', 'Sports Jackets', 'Performance Wear']
                },
                'Middle-aged': {
                    'casual': ['Polo Shirts', 'Khakis', 'Loafers', 'Casual Blazers', 'Dark Jeans'],
                    'formal': ['Business Suits', 'Dress Shirts', 'Ties', 'Formal Shoes', 'Waistcoats'],
                    'business': ['Executive Suits', 'Premium Shirts', 'Leather Briefcase', 'Cufflinks'],
                    'smart_casual': ['Blazer + Jeans', 'Button-down Shirts', 'Chelsea Boots'],
                    'weekend': ['Casual Jackets', 'Comfortable Pants', 'Casual Shoes']
                },
                'Senior': {
                    'casual': ['Comfortable Shirts', 'Easy-fit Pants', 'Comfortable Shoes', 'Cardigans'],
                    'formal': ['Classic Suits', 'Dress Shirts', 'Comfortable Formal Shoes', 'Ties'],
                    'smart_casual': ['Sport Coats', 'Dress Pants', 'Comfortable Loafers'],
                    'relaxed': ['Polo Shirts', 'Khakis', 'Slip-on Shoes', 'Vests']
                }
            },
            'Female': {
                'Teen': {
                    'casual': ['T-shirts', 'Jeans', 'Sneakers', 'Hoodies', 'Crop Tops', 'Denim Jackets'],
                    'formal': ['Dresses', 'Skirts', 'Blouses', 'Flats', 'Formal Pants'],
                    'party': ['Party Dresses', 'Heels', 'Stylish Tops', 'Accessories'],
                    'sports': ['Athletic Wear', 'Leggings', 'Sports Bras', 'Running Shoes']
                },
                'Young Adult': {
                    'casual': ['Tops', 'Jeans', 'Dresses', 'Sneakers', 'Casual Jackets'],
                    'formal': ['Business Suits', 'Blazers', 'Dress Pants', 'Pumps', 'Formal Dresses'],
                    'business': ['Pantsuits', 'Pencil Skirts', 'Blouses', 'Professional Heels'],
                    'party': ['Cocktail Dresses', 'Evening Wear', 'High Heels', 'Clutches'],
                    'ethnic': ['Sarees', 'Kurtas', 'Salwar Kameez', 'Ethnic Jewelry'],
                    'western': ['Dresses', 'Jumpsuits', 'Rompers', 'Midi Skirts']
                },
                'Middle-aged': {
                    'casual': ['Comfortable Tops', 'Classic Jeans', 'Flats', 'Cardigans'],
                    'formal': ['Business Dresses', 'Blazers', 'Dress Pants', 'Classic Pumps'],
                    'business': ['Professional Suits', 'Silk Blouses', 'Elegant Shoes'],
                    'elegant': ['A-line Dresses', 'Wrap Dresses', 'Classic Jewelry'],
                    'ethnic': ['Designer Sarees', 'Elegant Kurtas', 'Traditional Jewelry']
                },
                'Senior': {
                    'casual': ['Comfortable Tops', 'Easy-fit Pants', 'Comfortable Shoes', 'Light Jackets'],
                    'formal': ['Classic Dresses', 'Comfortable Suits', 'Low Heels', 'Elegant Accessories'],
                    'ethnic': ['Comfortable Sarees', 'Cotton Kurtas', 'Traditional Wear'],
                    'elegant': ['Timeless Pieces', 'Classic Cuts', 'Comfortable Footwear']
                }
            }
        }
    
    def generate_recommendations(self, gender: str, age_group: str, 
                                skin_rgb: Tuple[int, int, int],
                                skin_undertone: str = None) -> Dict:
        """
        Generate comprehensive fashion recommendations
        
        Args:
            gender: 'Male' or 'Female'
            age_group: 'Teen', 'Young Adult', 'Middle-aged', or 'Senior'
            skin_rgb: Skin tone RGB values
            skin_undertone: Optional undertone ('Warm', 'Cool', 'Neutral')
            
        Returns:
            Complete recommendation dictionary
        """
        try:
            # Validate inputs
            if gender not in ['Male', 'Female']:
                gender = 'Male'  # Default
            
            if age_group not in ['Teen', 'Young Adult', 'Middle-aged', 'Senior']:
                age_group = 'Young Adult'  # Default
            
            # Get clothing categories for this demographic
            clothing_cats = self.clothing_categories.get(gender, {}).get(age_group, {})
            
            # Find best matching colors
            best_colors = self.color_analyzer.find_best_colors(skin_rgb, top_n=15)
            
            # Categorize colors by rating
            excellent_colors = [c for c in best_colors if c['rating'] == 'Excellent']
            good_colors = [c for c in best_colors if c['rating'] == 'Good']
            fair_colors = [c for c in best_colors if c['rating'] == 'Fair']
            
            # Generate outfit recommendations with confidence scores
            outfit_recommendations = self._generate_outfit_list(
                clothing_cats, best_colors, gender, age_group)
            
            # Generate style tips
            style_tips = self._generate_style_tips(gender, age_group, skin_undertone, best_colors)
            
            # Create color palette
            color_palette = self._create_color_palette(best_colors[:10])
            
            # Generate seasonal palette
            seasonal_palette = self._generate_seasonal_palette(best_colors, skin_undertone)
            
            # Convert RGB to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(skin_rgb[0], skin_rgb[1], skin_rgb[2])
            
            return {
                'detected_gender': gender,
                'detected_age_group': age_group,
                'detected_skin_tone': {
                    'rgb': skin_rgb,
                    'hex': hex_color,
                    'undertone': skin_undertone or 'Not specified'
                },
                'recommended_clothing_categories': clothing_cats,
                'best_color_palette': color_palette,
                'seasonal_palette': seasonal_palette,
                'outfit_recommendations': outfit_recommendations,
                'color_analysis': {
                    'excellent_colors': [{'name': c['color_name'], 
                                         'hex': c['hex'], 
                                         'confidence': c['confidence_score']} 
                                        for c in excellent_colors],
                    'good_colors': [{'name': c['color_name'], 
                                    'hex': c['hex'], 
                                    'confidence': c['confidence_score']} 
                                   for c in good_colors],
                    'fair_colors': [{'name': c['color_name'], 
                                    'hex': c['hex'], 
                                    'confidence': c['confidence_score']} 
                                   for c in fair_colors]
                },
                'style_tips': style_tips,
                'summary': self._generate_summary(gender, age_group, skin_undertone, 
                                                 excellent_colors, outfit_recommendations)
            }
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_outfit_list(self, clothing_categories: Dict, best_colors: List[Dict],
                             gender: str, age_group: str) -> List[Dict]:
        """
        Generate specific outfit recommendations with color confidence scores
        
        Args:
            clothing_categories: Available clothing categories
            best_colors: Best matching colors with confidence scores
            gender: User gender
            age_group: User age group
            
        Returns:
            List of outfit recommendations
        """
        outfits = []
        
        # Get top 5 colors for outfit recommendations
        top_colors = best_colors[:5]
        
        # Generate outfits for each occasion
        for occasion, items in clothing_categories.items():
            # Create 2-3 outfit combinations per occasion
            for i, color_data in enumerate(top_colors[:3]):
                outfit = {
                    'occasion': occasion.replace('_', ' ').title(),
                    'outfit_number': i + 1,
                    'primary_color': {
                        'name': color_data['color_name'],
                        'hex': color_data['hex'],
                        'rgb': color_data['rgb']
                    },
                    'color_confidence_score': color_data['confidence_score'],
                    'delta_e': color_data['delta_e'],
                    'rating': color_data['rating'],
                    'items': []
                }
                
                # Select complementary items
                if len(items) >= 3:
                    # Primary item in main color
                    outfit['items'].append({
                        'type': items[0],
                        'color': color_data['color_name'],
                        'confidence': color_data['confidence_score']
                    })
                    
                    # Secondary item in neutral or complementary
                    secondary_color = self._get_complementary_color(
                        color_data, best_colors)
                    outfit['items'].append({
                        'type': items[1],
                        'color': secondary_color['color_name'],
                        'confidence': secondary_color['confidence_score']
                    })
                    
                    # Accent/accessory
                    if len(items) > 2:
                        outfit['items'].append({
                            'type': items[2],
                            'color': 'Neutral or matching',
                            'confidence': 85.0
                        })
                
                # Add styling note
                outfit['styling_note'] = self._get_styling_note(
                    outfit, gender, age_group, occasion)
                
                outfits.append(outfit)
        
        # Sort by confidence score
        outfits.sort(key=lambda x: x['color_confidence_score'], reverse=True)
        
        return outfits[:12]  # Return top 12 outfits
    
    def _get_complementary_color(self, primary_color: Dict, 
                                 available_colors: List[Dict]) -> Dict:
        brightness = lambda rgb: (rgb[0] + rgb[1] + rgb[2]) / 3.0
        if not available_colors:
            return primary_color
        candidates = [c for c in available_colors if c != primary_color]
        if not candidates:
            return primary_color
        pb = brightness(primary_color['rgb'])
        candidates.sort(key=lambda c: (abs(brightness(c['rgb']) - pb), c['family'] != primary_color['family']), reverse=True)
        return candidates[0]
    
    def _get_styling_note(self, outfit: Dict, gender: str, 
                         age_group: str, occasion: str) -> str:
        """Generate styling note for outfit"""
        notes = {
            'Male': {
                'Teen': {
                    'casual': "Perfect for everyday wear - comfortable and trendy",
                    'formal': "Great for school events and presentations",
                    'sports': "Ideal for active lifestyle and sports activities",
                    'party': "Stand out at social gatherings"
                },
                'Young Adult': {
                    'casual': "Versatile for work-from-home or weekend outings",
                    'formal': "Professional look for office and meetings",
                    'business': "Executive presence for important meetings",
                    'party': "Make a statement at social events"
                },
                'Middle-aged': {
                    'casual': "Sophisticated comfort for daily activities",
                    'formal': "Command respect in professional settings",
                    'smart_casual': "Perfect balance of style and comfort"
                },
                'Senior': {
                    'casual': "Comfortable elegance for daily wear",
                    'formal': "Timeless sophistication for special occasions"
                }
            },
            'Female': {
                'Teen': {
                    'casual': "Trendy and comfortable for school and hangouts",
                    'formal': "Elegant for special occasions and events",
                    'party': "Turn heads at parties and celebrations"
                },
                'Young Adult': {
                    'casual': "Chic and versatile for everyday style",
                    'formal': "Professional confidence for workplace",
                    'party': "Glamorous for evening events",
                    'ethnic': "Celebrate your cultural heritage with style"
                },
                'Middle-aged': {
                    'casual': "Effortless elegance for daily activities",
                    'formal': "Sophisticated presence in professional settings",
                    'elegant': "Timeless grace for any occasion"
                },
                'Senior': {
                    'casual': "Comfortable style that doesn't compromise on elegance",
                    'elegant': "Age-defying grace and sophistication"
                }
            }
        }
        
        try:
            return notes[gender][age_group].get(
                occasion, "A great choice that complements your style")
        except:
            return "This outfit will enhance your natural features"
    
    def _generate_style_tips(self, gender: str, age_group: str, 
                            undertone: Optional[str], 
                            best_colors: List[Dict]) -> List[str]:
        """Generate personalized style tips"""
        tips = []
        
        # Undertone-based tips
        if undertone:
            if undertone == 'Warm':
                tips.append("✨ Your warm undertone pairs beautifully with gold jewelry")
                tips.append("🌅 Earth tones and warm colors enhance your natural glow")
                tips.append("🎨 Avoid icy blues and pure whites - opt for cream instead")
            elif undertone == 'Cool':
                tips.append("✨ Silver jewelry complements your cool undertone perfectly")
                tips.append("❄️ Cool blues, purples, and pinks bring out your natural radiance")
                tips.append("🎨 Avoid orange and yellow-based colors")
            else:  # Neutral
                tips.append("✨ You're lucky - both gold and silver jewelry work for you!")
                tips.append("🎨 You have flexibility with most color palettes")
                tips.append("⚖️ Balance warm and cool tones in your outfits")
        
        # Gender and age specific tips
        if gender == 'Male':
            if age_group == 'Teen':
                tips.append("👕 Experiment with layers - hoodies, jackets, and vests")
                tips.append("👟 Sneakers in your best colors make a statement")
            elif age_group == 'Young Adult':
                tips.append("👔 Invest in a well-fitted suit in your best color")
                tips.append("⌚ Accessories matter - watch, belt, and shoes should coordinate")
            elif age_group == 'Middle-aged':
                tips.append("🎩 Quality over quantity - invest in timeless pieces")
                tips.append("👞 Classic leather shoes in brown or black are essentials")
            else:  # Senior
                tips.append("🧥 Comfort and style go hand in hand - choose both")
                tips.append("👔 Classic patterns like stripes and checks remain timeless")
        
        else:  # Female
            if age_group == 'Teen':
                tips.append("👗 Mix and match separates for versatile looks")
                tips.append("💄 Your best colors work great for makeup too!")
            elif age_group == 'Young Adult':
                tips.append("👠 Build a capsule wardrobe in your best colors")
                tips.append("💼 Professional doesn't mean boring - add your best colors")
            elif age_group == 'Middle-aged':
                tips.append("👗 A-line and wrap dresses are universally flattering")
                tips.append("🎀 Statement accessories in your best colors elevate any outfit")
            else:  # Senior
                tips.append("👗 Comfort fabrics in your best colors are key")
                tips.append("🧣 Scarves and shawls add elegance and warmth")
        
        # Color-specific tips
        if best_colors:
            top_color = best_colors[0]['color_name']
            tips.append(f"🎨 {top_color} is your best color with {best_colors[0]['confidence_score']:.1f}% confidence!")
            
            if len(best_colors) > 1:
                second_color = best_colors[1]['color_name']
                tips.append(f"💫 Combine {top_color} and {second_color} for stunning outfits")
        
        return tips
    
    def _generate_seasonal_palette(self, best_colors: List[Dict], undertone: Optional[str]) -> Dict:
        """
        Generate PERSONALIZED seasonal color palettes based on YOUR skin tone
        Only shows colors from your best_colors that match each season's characteristics
        
        Args:
            best_colors: List of colors that suit YOUR specific skin tone
            undertone: Your skin undertone
            
        Returns:
            Dictionary with personalized seasonal color recommendations
        """
        result = {}
        
        # Categorize YOUR best colors into seasons based on color characteristics
        for season in ['spring', 'summer', 'fall', 'winter']:
            season_matches = []
            
            for color in best_colors[:20]:  # Check more colors for better seasonal distribution
                rgb = color['rgb']
                r, g, b = rgb
                
                # Calculate color characteristics
                brightness = (r + g + b) / 3
                saturation = (max(rgb) - min(rgb)) / (max(rgb) + 1) if max(rgb) > 0 else 0
                warmth = (r - b) / 255.0  # Positive = warm, negative = cool
                
                # Determine if this color fits the season
                is_match = False
                
                if season == 'spring':
                    # Spring: Warm, bright, clear (fresh, vibrant warm tones)
                    # High brightness + warm + moderate to high saturation
                    if brightness > 140 and warmth > -0.1 and saturation > 0.25:
                        is_match = True
                        
                elif season == 'summer':
                    # Summer: Cool, soft, muted (gentle, pastel cool tones)
                    # Medium to high brightness + cool + low to medium saturation
                    if brightness > 120 and warmth < 0.15 and saturation < 0.55:
                        is_match = True
                        
                elif season == 'fall':
                    # Fall: Warm, rich, earthy (deep, golden warm tones)
                    # Medium brightness + warm + medium saturation
                    if 70 < brightness < 170 and warmth > 0 and 0.2 < saturation < 0.75:
                        is_match = True
                        
                elif season == 'winter':
                    # Winter: Cool, vivid, intense (bold, dramatic cool tones)
                    # Any brightness + cool + high saturation OR very dark/light
                    if (saturation > 0.45 and warmth < 0.1) or brightness < 80 or brightness > 200:
                        is_match = True
                
                if is_match and color['color_name'] != 'undefined':
                    season_matches.append({
                        'name': color['color_name'],
                        'hex': color['hex'],
                        'confidence': color['confidence_score']
                    })
            
            # Sort by confidence and take top 6
            season_matches.sort(key=lambda x: x['confidence'], reverse=True)
            result[season] = season_matches[:6] if season_matches else []
        
        # If any season has no matches, redistribute colors
        all_seasons = ['spring', 'summer', 'fall', 'winter']
        empty_seasons = [s for s in all_seasons if not result[s]]
        
        if empty_seasons:
            # Use remaining best colors
            remaining_colors = [c for c in best_colors[6:15] if c['color_name'] != 'undefined']
            for i, season in enumerate(empty_seasons):
                if remaining_colors:
                    # Distribute remaining colors
                    colors_per_season = max(1, len(remaining_colors) // len(empty_seasons))
                    start_idx = i * colors_per_season
                    end_idx = start_idx + colors_per_season
                    result[season] = [
                        {'name': c['color_name'], 'hex': c['hex'], 'confidence': c['confidence_score']}
                        for c in remaining_colors[start_idx:end_idx]
                    ]
        
        return result
    
    def _create_color_palette(self, colors: List[Dict]) -> Dict:
        """Create organized color palette"""
        return {
            'primary_colors': [
                {
                    'name': c['color_name'],
                    'hex': c['hex'],
                    'rgb': c['rgb'],
                    'confidence': c['confidence_score'],
                    'family': c['family'],
                    'undertone': c['undertone']
                }
                for c in colors[:5]
            ],
            'accent_colors': [
                {
                    'name': c['color_name'],
                    'hex': c['hex'],
                    'rgb': c['rgb'],
                    'confidence': c['confidence_score'],
                    'family': c['family']
                }
                for c in colors[5:10] if len(colors) > 5
            ]
        }
    
    def _generate_summary(self, gender: str, age_group: str, undertone: Optional[str],
                         excellent_colors: List[Dict], 
                         outfits: List[Dict]) -> Dict:
        """Generate recommendation summary"""
        return {
            'profile': f"{age_group} {gender}",
            'skin_undertone': undertone or 'Not specified',
            'total_excellent_colors': len(excellent_colors),
            'total_outfits_recommended': len(outfits),
            'avg_confidence_score': round(
                sum(o['color_confidence_score'] for o in outfits) / len(outfits), 2
            ) if outfits else 0,
            'top_recommendation': outfits[0] if outfits else None,
            'personalization_level': 'High' if undertone else 'Medium'
        }
    
    def print_recommendations(self, recommendations: Dict):
        """
        Pretty print recommendations to console
        
        Args:
            recommendations: Recommendation dictionary
        """
        print("\n" + "="*80)
        print("🎨 VASTRAVISTA - PERSONALIZED FASHION RECOMMENDATIONS")
        print("="*80)
        
        # Profile
        print(f"\n📋 YOUR PROFILE")
        print(f"   Gender: {recommendations['detected_gender']}")
        print(f"   Age Group: {recommendations['detected_age_group']}")
        print(f"   Skin Tone: {recommendations['detected_skin_tone']['hex']}")
        print(f"   Undertone: {recommendations['detected_skin_tone']['undertone']}")
        
        # Best Colors
        print(f"\n🎨 YOUR BEST COLOR PALETTE")
        print(f"   Excellent Colors ({len(recommendations['color_analysis']['excellent_colors'])}):")
        for color in recommendations['color_analysis']['excellent_colors'][:5]:
            print(f"      • {color['name']} - {color['hex']} (Confidence: {color['confidence']:.1f}%)")
        
        # Outfit Recommendations
        print(f"\n👗 TOP OUTFIT RECOMMENDATIONS")
        for i, outfit in enumerate(recommendations['outfit_recommendations'][:5], 1):
            print(f"\n   Outfit #{i}: {outfit['occasion']}")
            print(f"   Primary Color: {outfit['primary_color']['name']} ({outfit['primary_color']['hex']})")
            print(f"   Color Confidence Score: {outfit['color_confidence_score']:.1f}%")
            print(f"   Rating: {outfit['rating']}")
            print(f"   Items:")
            for item in outfit['items']:
                print(f"      • {item['type']} in {item['color']}")
            print(f"   💡 {outfit['styling_note']}")
        
        # Style Tips
        print(f"\n💡 PERSONALIZED STYLE TIPS")
        for tip in recommendations['style_tips']:
            print(f"   {tip}")
        
        # Summary
        summary = recommendations['summary']
        print(f"\n📊 SUMMARY")
        print(f"   Total Excellent Colors: {summary['total_excellent_colors']}")
        print(f"   Total Outfits Recommended: {summary['total_outfits_recommended']}")
        print(f"   Average Confidence Score: {summary['avg_confidence_score']:.1f}%")
        print(f"   Personalization Level: {summary['personalization_level']}")
        
        print("\n" + "="*80)
