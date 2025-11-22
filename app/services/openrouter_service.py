"""
VastraVista - OpenRouter + DeepSeek R1 Integration
Author: Saumya Tiwari
Purpose: Advanced AI reasoning for fashion recommendations using DeepSeek R1
Benefits: Free, unlimited, production-ready with strong reasoning capabilities

DeepSeek R1 through OpenRouter:
- Completely free and unlimited
- Drop-in replacement for OpenAI API
- Excellent for complex fashion logic
- No rate limits on free tier
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    OpenRouter API client for DeepSeek R1 model
    Free, unlimited AI reasoning for fashion intelligence
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (optional for free tier)
        """
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY', '')
        
        # DeepSeek R1 model (free, unlimited)
        self.model = "deepseek/deepseek-r1"
        
        # OpenRouter headers
        self.headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://vastravista.app",  # Optional, helps with analytics
            "X-Title": "VastraVista AI Fashion Assistant"  # Optional
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🤖 OpenRouter + DeepSeek R1 initialized")
    
    def chat_completion(self, messages: List[Dict], 
                       temperature: float = 0.7,
                       max_tokens: int = 1000) -> Dict:
        """
        Send chat completion request to DeepSeek R1 via OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity (0.0-1.0), default 0.7
            max_tokens: Maximum response length
            
        Returns:
            API response with generated text
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"✅ DeepSeek R1 responded successfully")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenRouter API error: {e}")
            return self._fallback_response()
        except Exception as e:
            self.logger.error(f"Unexpected error in chat_completion: {e}")
            return self._fallback_response()
    
    def generate_fashion_advice(self, 
                               user_skin_tone: str,
                               monk_level: str,
                               occasion: str,
                               style_preferences: List[str]) -> Dict:
        """
        Generate personalized fashion advice using DeepSeek R1 reasoning
        
        Args:
            user_skin_tone: User's skin tone (hex or description)
            monk_level: Monk Skin Tone Scale level (MST-1 to MST-10)
            occasion: Event type (casual, formal, party, etc.)
            style_preferences: List of style preferences
            
        Returns:
            AI-generated fashion recommendations with reasoning
        """
        prompt = f"""You are an expert fashion stylist and color consultant with deep knowledge of color theory, cultural fashion, and Indian styling.

User Profile:
- Skin Tone: {user_skin_tone}
- Monk Skin Tone Level: {monk_level} (10-level scientific scale)
- Occasion: {occasion}
- Style Preferences: {', '.join(style_preferences)}

Task: Provide comprehensive fashion advice including:
1. Best color palette (5-7 colors) with scientific reasoning using color theory
2. Specific outfit suggestions for the occasion
3. Cultural considerations for Indian fashion
4. Accessories and styling tips
5. Colors to avoid and why

Be specific, practical, and culturally aware. Focus on colors that complement the Monk scale level."""

        messages = [
            {"role": "system", "content": "You are VastraVista AI, an expert fashion consultant specializing in color analysis for diverse skin tones, with expertise in Indian fashion and color theory."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat_completion(messages, temperature=0.7, max_tokens=1500)
            
            if 'choices' in response and len(response['choices']) > 0:
                advice_text = response['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'advice': advice_text,
                    'monk_level': monk_level,
                    'occasion': occasion,
                    'generated_at': datetime.now().isoformat(),
                    'model': self.model,
                    'reasoning_quality': 'high'
                }
            else:
                return self._fallback_fashion_advice(monk_level, occasion)
                
        except Exception as e:
            self.logger.error(f"Fashion advice generation failed: {e}")
            return self._fallback_fashion_advice(monk_level, occasion)
    
    def explain_color_compatibility(self, 
                                   color1_rgb: tuple,
                                   color2_rgb: tuple,
                                   delta_e_score: float,
                                   skin_tone_rgb: tuple) -> Dict:
        """
        Explain why two colors work together using Delta-E science and AI reasoning
        
        Args:
            color1_rgb: First color RGB tuple
            color2_rgb: Second color RGB tuple
            delta_e_score: Delta-E CIE2000 distance
            skin_tone_rgb: User's skin tone RGB
            
        Returns:
            Detailed explanation of color compatibility
        """
        prompt = f"""You are a color science expert. Explain color compatibility using both scientific and practical terms.

Color Analysis:
- Color 1 (RGB): {color1_rgb}
- Color 2 (RGB): {color2_rgb}
- Delta-E CIE2000 Score: {delta_e_score:.2f}
- Skin Tone (RGB): {skin_tone_rgb}

Context:
- Delta-E < 15: Excellent match (perceptually very similar)
- Delta-E 15-30: Good match (noticeable but harmonious)
- Delta-E 30-50: Fair match (distinct but may work)
- Delta-E > 50: Poor match (very different, may clash)

Provide:
1. Scientific explanation of the Delta-E score
2. Color theory perspective (complementary, analogous, triadic, etc.)
3. How these colors interact with the given skin tone
4. Practical styling advice for wearing these colors together
5. Overall recommendation (Yes/No/Maybe)

Be concise but informative (200-300 words)."""

        messages = [
            {"role": "system", "content": "You are a color science expert specializing in Delta-E CIE2000 analysis and fashion color theory."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat_completion(messages, temperature=0.6, max_tokens=800)
            
            if 'choices' in response and len(response['choices']) > 0:
                explanation = response['choices'][0]['message']['content']
                
                # Determine compatibility level
                if delta_e_score < 15:
                    compatibility = 'Excellent'
                elif delta_e_score < 30:
                    compatibility = 'Good'
                elif delta_e_score < 50:
                    compatibility = 'Fair'
                else:
                    compatibility = 'Poor'
                
                return {
                    'success': True,
                    'explanation': explanation,
                    'delta_e_score': delta_e_score,
                    'compatibility_level': compatibility,
                    'scientific_method': 'Delta-E CIE2000',
                    'ai_reasoning': True
                }
            else:
                return self._fallback_color_explanation(delta_e_score)
                
        except Exception as e:
            self.logger.error(f"Color explanation failed: {e}")
            return self._fallback_color_explanation(delta_e_score)
    
    def suggest_outfit_improvements(self, 
                                   current_outfit: Dict,
                                   wardrobe_items: List[Dict],
                                   style_goals: List[str]) -> Dict:
        """
        Analyze current outfit and suggest improvements using AI reasoning
        
        Args:
            current_outfit: Current outfit details
            wardrobe_items: Available items in wardrobe
            style_goals: User's styling goals
            
        Returns:
            Improvement suggestions with reasoning
        """
        prompt = f"""You are a personal stylist. Analyze this outfit and suggest improvements.

Current Outfit:
{json.dumps(current_outfit, indent=2)}

Available Wardrobe Items: {len(wardrobe_items)} items
Style Goals: {', '.join(style_goals)}

Provide:
1. What's working well in the current outfit
2. 3-5 specific improvement suggestions
3. Alternative items from wardrobe (reference by item ID if available)
4. Color harmony analysis
5. Occasion appropriateness

Be constructive, specific, and actionable."""

        messages = [
            {"role": "system", "content": "You are an expert personal stylist with knowledge of color theory, fashion trends, and cultural styling."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat_completion(messages, temperature=0.7, max_tokens=1200)
            
            if 'choices' in response and len(response['choices']) > 0:
                suggestions = response['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'suggestions': suggestions,
                    'current_outfit': current_outfit,
                    'improvement_areas': self._extract_improvement_areas(suggestions),
                    'confidence': 'high'
                }
            else:
                return self._fallback_outfit_suggestions()
                
        except Exception as e:
            self.logger.error(f"Outfit improvement failed: {e}")
            return self._fallback_outfit_suggestions()
    
    def generate_seasonal_palette(self, monk_level: str, season: str) -> Dict:
        """
        Generate season-specific color palette optimized for Monk skin tone level
        
        Args:
            monk_level: Monk Skin Tone Scale level (MST-1 to MST-10)
            season: Season (Spring, Summer, Autumn, Winter)
            
        Returns:
            Seasonal color palette with reasoning
        """
        prompt = f"""You are a color consultant specializing in seasonal color analysis.

Create a {season} color palette for Monk Skin Tone Level {monk_level}.

Provide:
1. 10-12 specific colors (with hex codes if possible)
2. Color temperature guidance (warm/cool)
3. Patterns and textures for the season
4. Styling tips specific to this skin tone in {season}
5. Cultural considerations for Indian fashion

Focus on colors that enhance natural beauty and are seasonally appropriate."""

        messages = [
            {"role": "system", "content": "You are an expert in seasonal color analysis and diverse skin tone representation."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat_completion(messages, temperature=0.7, max_tokens=1000)
            
            if 'choices' in response and len(response['choices']) > 0:
                palette_info = response['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'monk_level': monk_level,
                    'season': season,
                    'palette': palette_info,
                    'generated_at': datetime.now().isoformat()
                }
            else:
                return self._fallback_seasonal_palette(season)
                
        except Exception as e:
            self.logger.error(f"Seasonal palette generation failed: {e}")
            return self._fallback_seasonal_palette(season)
    
    def _extract_improvement_areas(self, suggestions_text: str) -> List[str]:
        """Extract key improvement areas from AI response"""
        # Simple keyword extraction
        keywords = ['color', 'fit', 'style', 'accessories', 'proportion', 'harmony']
        areas = []
        
        lower_text = suggestions_text.lower()
        for keyword in keywords:
            if keyword in lower_text:
                areas.append(keyword.capitalize())
        
        return areas if areas else ['General styling']
    
    def _fallback_response(self) -> Dict:
        """Fallback response when API fails"""
        return {
            'choices': [{
                'message': {
                    'content': 'AI service temporarily unavailable. Using default recommendations.'
                }
            }],
            'error': 'API call failed',
            'fallback': True
        }
    
    def _fallback_fashion_advice(self, monk_level: str, occasion: str) -> Dict:
        """Fallback fashion advice"""
        basic_advice = f"""Fashion Advice for {monk_level} - {occasion}:

**Color Palette:**
- Rich jewel tones work beautifully with medium-tan skin
- Try emerald green, sapphire blue, ruby red
- Warm earth tones like terracotta, mustard, olive

**Outfit Suggestions:**
- Formal: Navy suit with burgundy shirt
- Casual: Olive chinos with cream linen shirt
- Party: Deep purple kurta or emerald dress

**Styling Tips:**
- Gold accessories complement warm undertones
- Experiment with bold colors - they look stunning
- Consider traditional Indian silhouettes for special occasions

This is a general recommendation. For personalized AI-powered advice, please check your API configuration."""

        return {
            'success': True,
            'advice': basic_advice,
            'monk_level': monk_level,
            'occasion': occasion,
            'fallback': True,
            'note': 'Using default recommendations'
        }
    
    def _fallback_color_explanation(self, delta_e_score: float) -> Dict:
        """Fallback color compatibility explanation"""
        if delta_e_score < 15:
            explanation = "Excellent match! These colors are perceptually very similar and will create a harmonious, cohesive look."
        elif delta_e_score < 30:
            explanation = "Good match! The colors are distinct but work well together, creating visual interest while maintaining harmony."
        elif delta_e_score < 50:
            explanation = "Fair match. The colors are quite different - they may work for bold, contrasting looks but require careful styling."
        else:
            explanation = "These colors are very different and may clash. Consider using one as an accent rather than combining equally."
        
        return {
            'success': True,
            'explanation': explanation,
            'delta_e_score': delta_e_score,
            'fallback': True
        }
    
    def _fallback_outfit_suggestions(self) -> Dict:
        """Fallback outfit improvement suggestions"""
        return {
            'success': True,
            'suggestions': """Outfit Improvement Tips:
            
1. **Color Balance**: Ensure your outfit has a cohesive color story (60-30-10 rule)
2. **Proportion**: Balance fitted and loose pieces for flattering silhouette
3. **Accessories**: Add one statement piece to elevate the look
4. **Texture Mix**: Combine different textures for visual interest
5. **Occasion Match**: Ensure formality level matches the event

For detailed AI-powered analysis, please configure your OpenRouter API key.""",
            'fallback': True
        }
    
    def _fallback_seasonal_palette(self, season: str) -> Dict:
        """Fallback seasonal palette"""
        seasonal_colors = {
            'Spring': ['Coral', 'Peach', 'Mint Green', 'Sky Blue', 'Butter Yellow'],
            'Summer': ['Soft Pink', 'Lavender', 'Powder Blue', 'Sage Green', 'Rose'],
            'Autumn': ['Rust', 'Olive', 'Burgundy', 'Mustard', 'Terracotta'],
            'Winter': ['Ruby Red', 'Emerald', 'Sapphire', 'Pure White', 'Charcoal']
        }
        
        colors = seasonal_colors.get(season, seasonal_colors['Spring'])
        
        return {
            'success': True,
            'season': season,
            'palette': f"{season} Color Palette: {', '.join(colors)}",
            'fallback': True
        }


# Singleton instance for app-wide use
_openrouter_client = None

def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client singleton"""
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient()
    return _openrouter_client
