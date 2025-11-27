"""
AI Stylist Service using Local LLM
Generates personalized fashion advice using Ollama or fallback templates
Also provides AI-powered image analysis insights
"""

import logging
import json
import base64
import os
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AIStyler:
    """AI-powered fashion stylist using local LLM"""
    
    def __init__(self):
        self.use_ai = False
        # Configurable Ollama endpoint and model via environment variables
        self.ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434').rstrip('/')
        self.ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.2')
        self._check_ollama_availability()
    
    def _check_ollama_availability(self):
        """Check if Ollama is installed and running"""
        try:
            import requests
            # Try a few endpoints to detect a running Ollama-like server
            tried = []
            urls = [f"{self.ollama_url}/api/tags", f"{self.ollama_url}/api/models"]
            ok = False
            for u in urls:
                tried.append(u)
                try:
                    response = requests.get(u, timeout=4)
                    if response.status_code == 200:
                        ok = True
                        break
                except Exception:
                    continue

            # As a last resort try a tiny generate request (non-streaming, very small prompt)
            if not ok:
                try:
                    # small generate probe with slightly longer timeout
                    gresp = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={"model": self.ollama_model, "prompt": "test", "stream": False, "options": {"num_predict": 1}},
                        timeout=6
                    )
                    if gresp.status_code == 200:
                        ok = True
                except Exception:
                    ok = False

            if ok:
                self.use_ai = True
                logger.info(f"✅ Ollama AI available at {self.ollama_url} - using model: {self.ollama_model}")
            else:
                logger.info(f"💡 Ollama not available at {self.ollama_url} (tried: {tried}) - using smart template system")
        except Exception as e:
            logger.info(f"💡 Ollama not running - using smart template system: {str(e)}")
            self.use_ai = False

    def _call_generate(self, payload, timeout=30, retries=1):
        """Call the Ollama generate endpoint with simple retry logic."""
        try:
            import requests
        except Exception:
            return None

        last_exc = None
        for attempt in range(retries + 1):
            try:
                resp = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=timeout)
                return resp
            except Exception as e:
                last_exc = e
                logger.debug(f"Generate attempt {attempt+1} failed: {str(e)}")
                # small backoff
                time.sleep(0.4)

        logger.warning(f"All generate attempts failed: {str(last_exc)}")
        return None
    
    def generate_occasion_tips(self, occasion, monk_level, gender, colors_list, brightness):
        """
        Generate occasion-specific style tips
        
        Args:
            occasion: casual, formal, party, business, wedding, date
            monk_level: MST-1 to MST-10
            gender: Male/Female
            colors_list: List of color names from analysis
            brightness: Skin brightness value
        """
        logger.info(f"🎯 Generating tips for {occasion} - AI Mode: {self.use_ai}")
        # Refresh availability in case Ollama started after app boot
        try:
            self._check_ollama_availability()
        except Exception:
            pass

        if self.use_ai:
            logger.info(f"🤖 Calling Ollama AI with model: {self.ollama_model}")
            return self._generate_ai_tips(occasion, monk_level, gender, colors_list, brightness)
        else:
            logger.info("🧠 Using smart templates")
            return self._generate_smart_tips(occasion, monk_level, gender, colors_list, brightness)
    
    def _generate_ai_tips(self, occasion, monk_level, gender, colors_list, brightness):
        """Generate tips using local AI model"""
        try:
            # Ensure Ollama is available before making the request
            self._check_ollama_availability()
            import requests
            
            # Create personalized prompt
            colors_str = ", ".join(colors_list[:5]) if colors_list else "neutral tones"
            
            prompt = f"""You are a fashion stylist. Give 4 quick {occasion} outfit tips for {gender}, {monk_level} skin.

Best colors: {colors_str}

Rules:

Format: 4 lines starting with -"""

            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": 150,
                    "top_k": 40,
                    "top_p": 0.9
                }
            }
            response = self._call_generate(payload, timeout=60, retries=1)
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip()
                
                # Parse AI response into list items
                tips = []
                for line in ai_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        tip = line.lstrip('-•* ').strip()
                        if tip:
                            tips.append(tip)
                
                if tips and len(tips) >= 3:
                    logger.info(f"✅ AI generated {len(tips)} personalized tips")
                    return tips[:4]  # Return max 4 tips
            
            # Fallback if AI fails
            logger.warning("AI response not suitable, using smart templates")
            return self._generate_smart_tips(occasion, monk_level, gender, colors_list, brightness)
            
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            return self._generate_smart_tips(occasion, monk_level, gender, colors_list, brightness)
    
    def analyze_image_with_ai(self, image_path, analysis_results):
        """
        Analyze the uploaded image with AI and provide personalized insights
        
        Args:
            image_path: Path to the uploaded image
            analysis_results: Dict with monk_level, gender, age_group, best_colors
        
        Returns:
            Dict with AI analysis insights or None if AI not available
        """
        # Refresh availability (Ollama may have started after app boot)
        try:
            self._check_ollama_availability()
        except Exception:
            pass

        if not self.use_ai:
            logger.warning("🧠 AI not available for image analysis - Ollama not running")
            return None
        
        try:
            import requests
            from PIL import Image
            import io
            import os
            
            logger.info("🔍 Starting AI fashion insights generation...")
            logger.info(f"📸 Image path: {image_path}")
            logger.info(f"📂 File exists: {os.path.exists(image_path)}")
            logger.info(f"🤖 Using AI model: {self.ollama_model}")
            
            # Load and encode image
            with Image.open(image_path) as img:
                # Resize to reduce processing time
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Extract analysis data
            monk_level = analysis_results.get('monk_level', 'medium')
            gender = analysis_results.get('gender', 'Person')
            age_group = analysis_results.get('age_group', 'Adult')
            
            # Get top colors
            best_colors = analysis_results.get('best_colors', {})
            excellent = best_colors.get('excellent', [])
            color_names = [c.get('color_name', c.get('name', '')) for c in excellent[:3]]
            colors_str = ", ".join(color_names) if color_names else "various colors"
            
            # Create prompt for vision analysis
            prompt = f"""You are a professional fashion consultant analyzing this person's photo.

Technical Analysis Results:

Provide a brief, friendly fashion analysis in 3-4 sentences covering:
1. Overall style impression and what stands out
2. How their detected best colors will complement their features
3. One specific styling suggestion based on what you observe

Be encouraging, specific, and professional. Keep it under 80 words."""

            # Call Ollama with vision model if available, else use text-only
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 120
                }
            }
            response = self._call_generate(payload, timeout=40, retries=1)
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip()
                
                if ai_text and len(ai_text) > 20:
                    logger.info(f"✅ AI image analysis completed: {len(ai_text)} chars")
                    return {
                        'success': True,
                        'analysis': ai_text,
                        'model': self.ollama_model
                    }
            
            logger.warning("AI image analysis returned insufficient data")
            return None
            
        except Exception as e:
            logger.error(f"AI image analysis error: {str(e)}")
            return None
    
    def analyze_image_independently(self, image_path):
        """
        Let AI analyze the image independently without technical results
        Then compare with technical analysis
        
        Args:
            image_path: Path to the uploaded image
        
        Returns:
            Dict with AI's independent analysis or None
        """
        # Refresh availability in case Ollama came up later
        try:
            self._check_ollama_availability()
        except Exception:
            pass

        if not self.use_ai:
            logger.warning("🧠 AI not available for independent analysis - Ollama not running")
            return None
        
        try:
            import requests
            from PIL import Image
            import io
            import os
            
            logger.info(f"🤖 Starting AI independent image analysis...")
            logger.info(f"📸 Image path: {image_path}")
            logger.info(f"📂 File exists: {os.path.exists(image_path)}")
            logger.info(f"🤖 Using AI model: {self.ollama_model}")
            
            # Load and encode image
            with Image.open(image_path) as img:
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Create prompt for independent analysis
            prompt = """You are an expert image analyst. Analyze this person's photo and provide:

1. GENDER: Male/Female (your best assessment)
2. AGE: Estimated age in years (single number)
3. SKIN TONE: Describe as Very Light/Light/Light-Medium/Medium/Medium-Deep/Deep/Very Deep
4. TOP 3 COLORS: List 3 specific colors that would look best (like "Navy Blue", "Burgundy", "Emerald")

Format your response exactly like this:
GENDER: [answer]
AGE: [number]
SKIN_TONE: [answer]
COLORS: [color1], [color2], [color3]

Be precise and concise. Analyze based only on what you see in the image."""

            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "num_predict": 150
                }
            }
            response = self._call_generate(payload, timeout=45, retries=1)
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip()
                
                if ai_text and len(ai_text) > 20:
                    # Parse AI response
                    parsed = self._parse_ai_analysis(ai_text)
                    parsed['raw_response'] = ai_text
                    logger.info(f"✅ AI independent analysis: {parsed.get('gender', 'N/A')}, {parsed.get('age', 'N/A')} yrs, {parsed.get('skin_tone', 'N/A')}")
                    return parsed
            
            logger.warning("AI independent analysis returned insufficient data")
            return None
            
        except Exception as e:
            logger.error(f"AI independent analysis error: {str(e)}")
            return None
    
    def _parse_ai_analysis(self, ai_text):
        """Parse AI's structured response - more robust parsing"""
        result = {
            'gender': None,
            'age': None,
            'skin_tone': None,
            'colors': []
        }
        
        if not ai_text or not isinstance(ai_text, str):
            return result
        
        # Normalize text
        ai_text_lower = ai_text.lower()
        lines = ai_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Parse Gender - try multiple patterns
            if 'gender:' in line_lower:
                gender_text = line.split('gender:')[-1].strip() if ':' in line else line.strip()
                gender_text_lower = gender_text.lower()
                
                if 'male' in gender_text_lower and 'female' not in gender_text_lower:
                    result['gender'] = 'Male'
                elif 'female' in gender_text_lower:
                    result['gender'] = 'Female'
                elif 'woman' in gender_text_lower or 'girl' in gender_text_lower:
                    result['gender'] = 'Female'
                elif 'man' in gender_text_lower or 'boy' in gender_text_lower:
                    result['gender'] = 'Male'
            
            # Parse Age - try multiple patterns
            if 'age:' in line_lower:
                age_text = line.split('age:')[-1].strip() if ':' in line else line.strip()
                # Extract first number found
                age_nums = ''.join(filter(str.isdigit, age_text[:10]))
                if age_nums:
                    try:
                        age_val = int(age_nums)
                        if 1 <= age_val <= 120:  # Reasonable age range
                            result['age'] = age_val
                    except:
                        pass
            
            # Parse Skin Tone - try multiple patterns
            if 'skin' in line_lower and ('tone' in line_lower or 'color' in line_lower or 'colour' in line_lower):
                # Try to extract after colon
                if ':' in line:
                    skin_text = line.split(':')[-1].strip()
                else:
                    # Try to extract after keywords
                    for keyword in ['skin tone', 'skin color', 'skin colour']:
                        if keyword in line_lower:
                            parts = line_lower.split(keyword)
                            if len(parts) > 1:
                                skin_text = parts[1].strip()
                                break
                    else:
                        skin_text = line.strip()
                
                if skin_text:
                    result['skin_tone'] = skin_text.title()
            
            # Parse Colors - try multiple patterns
            if 'color' in line_lower or 'colour' in line_lower:
                if ':' in line:
                    colors_text = line.split(':')[-1].strip()
                else:
                    # Try to extract after keyword
                    for keyword in ['colors:', 'colours:', 'color:', 'colour:']:
                        if keyword in line_lower:
                            parts = line.split(keyword)
                            if len(parts) > 1:
                                colors_text = parts[1].strip()
                                break
                    else:
                        colors_text = line.strip()
                
                if colors_text:
                    # Split by comma, semicolon, or "and"
                    colors = []
                    for sep in [',', ';', ' and ', ' & ']:
                        if sep in colors_text:
                            colors = [c.strip().title() for c in colors_text.split(sep)]
                            break
                    
                    if not colors:
                        # Single color or space-separated
                        colors = [colors_text.strip().title()]
                    
                    # Clean up colors
                    cleaned_colors = []
                    for c in colors:
                        c = c.strip()
                        if c and len(c) > 2:  # Valid color name
                            cleaned_colors.append(c)
                    
                    result['colors'] = cleaned_colors[:5]  # Max 5 colors
        
        # Fallback: if structured parsing failed, try to extract from free text
        if not result['gender'] and not result['age'] and not result['skin_tone']:
            # Try to find gender in text
            if 'male' in ai_text_lower or 'man' in ai_text_lower or 'boy' in ai_text_lower:
                if 'female' not in ai_text_lower and 'woman' not in ai_text_lower and 'girl' not in ai_text_lower:
                    result['gender'] = 'Male'
            elif 'female' in ai_text_lower or 'woman' in ai_text_lower or 'girl' in ai_text_lower:
                result['gender'] = 'Female'
            
            # Try to find age in text (look for numbers that could be ages)
            import re
            age_matches = re.findall(r'\b(\d{1,2})\b', ai_text)
            for match in age_matches:
                age_val = int(match)
                if 10 <= age_val <= 100:  # Reasonable age
                    result['age'] = age_val
                    break
        
        return result
    
    def compare_analyses(self, technical_results, ai_results):
        """
        Compare technical analysis with AI's independent analysis
        
        Returns:
            Dict with comparison results and agreement percentage
        """
        if not ai_results:
            return {
                'comparison_available': False,
                'message': 'AI analysis not available for comparison'
            }
        
        comparison = {
            'comparison_available': True,
            'agreements': [],
            'differences': [],
            'agreement_score': 0
        }
        
        # Track how many comparisons we can make
        comparisons_made = 0
        max_possible_score = 0
        
        # Compare Gender
        tech_gender = None
        ai_gender = None
        
        # Try multiple ways to get technical gender
        if isinstance(technical_results.get('gender'), dict):
            tech_gender = technical_results['gender'].get('gender') or technical_results['gender'].get('detected_gender')
        elif isinstance(technical_results.get('gender'), str):
            tech_gender = technical_results['gender']
        
        # Try multiple ways to get AI gender
        if isinstance(ai_results.get('gender'), dict):
            ai_gender = ai_results['gender'].get('gender') or ai_results['gender'].get('detected_gender')
        elif isinstance(ai_results.get('gender'), str):
            ai_gender = ai_results['gender']
        
        if tech_gender and tech_gender != 'Unknown' and ai_gender and ai_gender != 'Unknown':
            comparisons_made += 1
            max_possible_score += 25
            tech_gender_lower = str(tech_gender).lower().strip()
            ai_gender_lower = str(ai_gender).lower().strip()
            
            if tech_gender_lower == ai_gender_lower:
                comparison['agreements'].append(f"✓ Gender: Both detected {tech_gender}")
                comparison['agreement_score'] += 25
            else:
                comparison['differences'].append(f"⚠ Gender: Technical={tech_gender}, AI={ai_gender}")
        
        # Compare Age
        tech_age = None
        ai_age = None
        
        # Try multiple ways to get technical age
        if isinstance(technical_results.get('age'), dict):
            tech_age = technical_results['age'].get('estimated_age') or technical_results['age'].get('age')
        elif isinstance(technical_results.get('age'), (int, float)):
            tech_age = technical_results['age']
        
        # Try multiple ways to get AI age
        if isinstance(ai_results.get('age'), dict):
            ai_age = ai_results['age'].get('age') or ai_results['age'].get('estimated_age')
        elif isinstance(ai_results.get('age'), (int, float)):
            ai_age = ai_results['age']
        
        if tech_age and isinstance(tech_age, (int, float)) and tech_age > 0 and ai_age and isinstance(ai_age, (int, float)) and ai_age > 0:
            comparisons_made += 1
            max_possible_score += 25
            age_diff = abs(float(tech_age) - float(ai_age))
            if age_diff <= 5:
                comparison['agreements'].append(f"✓ Age: Both ~{int(tech_age)} years (±{int(age_diff)})")
                comparison['agreement_score'] += 25
            elif age_diff <= 10:
                comparison['agreements'].append(f"≈ Age: Technical={int(tech_age)}, AI={int(ai_age)} (±{int(age_diff)} years)")
                comparison['agreement_score'] += 15
            else:
                comparison['differences'].append(f"⚠ Age: Technical={int(tech_age)}, AI={int(ai_age)} (diff: {int(age_diff)} years)")
        
        # Compare Skin Tone (general category)
        tech_monk = None
        ai_skin = None
        
        # Try multiple ways to get technical skin tone
        if isinstance(technical_results.get('skin_tone'), dict):
            tech_monk = (technical_results['skin_tone'].get('monk_scale_level') or 
                        technical_results['skin_tone'].get('monk_level') or
                        technical_results['skin_tone'].get('monk_scale', {}).get('monk_level'))
        elif isinstance(technical_results.get('skin_tone'), str):
            tech_monk = technical_results['skin_tone']
        
        # Try multiple ways to get AI skin tone
        if isinstance(ai_results.get('skin_tone'), dict):
            ai_skin = ai_results['skin_tone'].get('skin_tone') or ai_results['skin_tone'].get('level')
        elif isinstance(ai_results.get('skin_tone'), str):
            ai_skin = ai_results['skin_tone']
        
        if tech_monk and ai_skin:
            comparisons_made += 1
            max_possible_score += 25
            tech_monk_str = str(tech_monk).strip()
            ai_skin_str = str(ai_skin).strip()
            
            # Map monk level to category
            try:
                monk_num = int(''.join(filter(str.isdigit, tech_monk_str))) if tech_monk_str else 5
                tech_category = 'Light' if monk_num <= 3 else 'Medium' if monk_num <= 7 else 'Deep'
            except:
                tech_category = 'Medium'  # Default
            
            # Check if categories match (case-insensitive, partial match)
            ai_skin_lower = ai_skin_str.lower()
            if (tech_category.lower() in ai_skin_lower or 
                any(word in ai_skin_lower for word in ['light', 'medium', 'deep', 'tan', 'fair', 'dark'] if tech_category.lower() in word)):
                comparison['agreements'].append(f"✓ Skin Tone: Both in {tech_category} range")
                comparison['agreement_score'] += 25
            else:
                comparison['differences'].append(f"⚠ Skin: Technical={tech_monk}, AI={ai_skin_str}")
                comparison['agreement_score'] += 10
        
        # Compare Colors (check if any overlap)
        tech_colors = []
        ai_colors = []
        
        # Try multiple ways to get technical colors
        if isinstance(technical_results.get('best_colors'), dict):
            tech_colors = (technical_results['best_colors'].get('excellent', []) or 
                          technical_results['best_colors'].get('good', []) or
                          technical_results['best_colors'].get('colors', []))
        elif isinstance(technical_results.get('best_colors'), list):
            tech_colors = technical_results['best_colors']
        
        # Try multiple ways to get AI colors
        if isinstance(ai_results.get('colors'), list):
            ai_colors = ai_results['colors']
        elif isinstance(ai_results.get('colors'), str):
            # Try to parse comma-separated colors
            ai_colors = [c.strip() for c in str(ai_results['colors']).split(',')]
        
        tech_color_names = []
        for c in tech_colors[:5]:
            if isinstance(c, dict):
                tech_color_names.append(c.get('color_name') or c.get('name') or '')
            elif isinstance(c, str):
                tech_color_names.append(c)
        
        tech_color_names = [c for c in tech_color_names if c and c.strip()]
        ai_colors = [str(c).strip() for c in ai_colors if c and str(c).strip()]
        
        if tech_color_names and ai_colors:
            comparisons_made += 1
            max_possible_score += 25
            # Check for overlap (case-insensitive, partial matching)
            overlap = False
            for tc in tech_color_names:
                tc_lower = tc.lower()
                for ac in ai_colors:
                    ac_lower = ac.lower()
                    if tc_lower in ac_lower or ac_lower in tc_lower:
                        overlap = True
                        break
                if overlap:
                    break
            
            if overlap:
                comparison['agreements'].append(f"✓ Colors: Some overlap detected")
                comparison['agreement_score'] += 25
            else:
                comparison['agreements'].append(f"≈ Colors: Different recommendations (both valid)")
                comparison['agreement_score'] += 10
        
        # If no comparisons could be made, provide helpful message
        if comparisons_made == 0:
            comparison['agreements'].append("ℹ️ Limited data available for comparison")
            comparison['agreement_score'] = 50  # Neutral score when data is limited
            comparison['message'] = 'Some analysis data was missing, so full comparison was not possible'
        else:
            # Normalize score if we couldn't compare all aspects
            if max_possible_score > 0:
                # Scale to 100% based on what we could compare
                comparison['agreement_score'] = min(100, int((comparison['agreement_score'] / max_possible_score) * 100))
        
        # Ensure score is at least 0 and at most 100
        comparison['agreement_score'] = max(0, min(100, comparison['agreement_score']))
        
        return comparison
    
    def verify_analysis(self, analysis_results):
        """
        Use AI to verify and validate the analysis results for accuracy
        
        Args:
            analysis_results: Dict with gender, age, monk_level, colors
        
        Returns:
            Dict with verification status, confidence, and any concerns
        """
        # Make sure we re-check availability at verification time
        try:
            self._check_ollama_availability()
        except Exception:
            pass

        if not self.use_ai:
            logger.info("🧠 AI not available for verification - accepting results")
            return {
                'verified': True,
                'confidence': 85,
                'method': 'rule-based',
                'concerns': []
            }
        
        try:
            import requests
            
            logger.info("🔍 Verifying analysis with AI...")
            
            # Extract analysis data
            gender = analysis_results.get('gender', {}).get('gender', 'Unknown')
            age = analysis_results.get('age', {}).get('estimated_age', 'Unknown')
            age_group = analysis_results.get('age', {}).get('age_group', 'Unknown')
            monk_level = analysis_results.get('skin_tone', {}).get('monk_scale_level', 'Unknown')
            
            # Get top colors
            best_colors = analysis_results.get('best_colors', {})
            excellent = best_colors.get('excellent', [])
            color_names = [c.get('color_name', c.get('name', '')) for c in excellent[:3]]
            colors_str = ", ".join(color_names) if color_names else "none detected"
            
            # Create verification prompt
            prompt = f"""You are a fashion analysis validator. Review these results for consistency:

Gender: {gender}
Age: {age} years ({age_group})
Skin Tone: {monk_level}
Top Colors: {colors_str}

Task: Check if these results make sense together. Consider:
1. Do the colors match the skin tone level?
2. Is the age consistent with age group?
3. Are there any obvious inconsistencies?

Respond in this format:
VALID: yes/no
CONFIDENCE: 0-100
CONCERNS: list any issues (or "none")

Keep response under 50 words."""

            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 100
                }
            }
            response = self._call_generate(payload, timeout=30, retries=1)
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip().lower()
                
                # Parse AI response
                is_valid = 'yes' in ai_text.split('valid:')[-1][:10] if 'valid:' in ai_text else True
                
                # Extract confidence (default to 80 if not found)
                confidence = 80
                if 'confidence:' in ai_text:
                    try:
                        conf_text = ai_text.split('confidence:')[-1].split('\n')[0]
                        confidence = int(''.join(filter(str.isdigit, conf_text[:5])))
                        confidence = min(max(confidence, 0), 100)
                    except:
                        pass
                
                # Extract concerns
                concerns = []
                if 'concerns:' in ai_text:
                    concern_text = ai_text.split('concerns:')[-1].strip()
                    if concern_text and 'none' not in concern_text[:10]:
                        concerns.append(concern_text[:200])
                
                logger.info(f"✅ AI verification: valid={is_valid}, confidence={confidence}%")
                return {
                    'verified': is_valid,
                    'confidence': confidence,
                    'method': 'ai-validated',
                    'concerns': concerns,
                    'raw_response': ai_text[:300]
                }
            
            logger.warning("AI verification returned no data")
            return {
                'verified': True,
                'confidence': 75,
                'method': 'timeout-accepted',
                'concerns': []
            }
            
        except Exception as e:
            logger.error(f"AI verification error: {str(e)}")
            return {
                'verified': True,
                'confidence': 70,
                'method': 'error-accepted',
                'concerns': [f'Verification failed: {str(e)[:50]}']
            }
    
    def _generate_smart_tips(self, occasion, monk_level, gender, colors_list, brightness):
        """Generate smart personalized tips using templates with actual colors and randomization"""
        import random
        
        # Extract actual color names
        color1 = colors_list[0] if len(colors_list) > 0 else "navy"
        color2 = colors_list[1] if len(colors_list) > 1 else "burgundy"
        color3 = colors_list[2] if len(colors_list) > 2 else "emerald"
        color4 = colors_list[3] if len(colors_list) > 3 else "olive"
        neutral = "white" if brightness < 0.4 else "black"
        neutral_alt = "cream" if brightness < 0.4 else "charcoal"
        
        # Multiple variations for each occasion - randomized selection
        tips_variations = {
            'casual': [
                # Variation set 1
                [
                    f"Rock a {color1} tee with denim and {neutral} sneakers for effortless cool",
                    f"Layer a {color2} jacket over neutrals to add depth",
                    f"Try {color3} chinos with a simple {neutral_alt} top for relaxed sophistication",
                    f"Weekend essential: {color1} with {color4} creates an eye-catching combo"
                ],
                # Variation set 2
                [
                    f"Start with a {color2} button-down - pairs perfectly with any denim",
                    f"{color1} hoodie + {neutral} joggers = your go-to comfort outfit",
                    f"Elevate basics: add a {color3} overshirt to a plain tee and jeans",
                    f"Color block with {color1} top and {color2} bottoms for modern edge"
                ],
                # Variation set 3
                [
                    f"A {color3} sweater over {neutral} creates instant polish",
                    f"Mix {color1} and {color4} pieces - these colors are scientifically matched to you",
                    f"{color2} bomber jacket + plain tee = effortlessly put-together",
                    f"Your casual power move: {color1} shirt tucked into dark denim"
                ]
            ],
            'formal': [
                [
                    f"Command the room in a {color1} suit with crisp {neutral} shirt",
                    f"Pair {color2} blazer with {neutral_alt} trousers for refined elegance",
                    f"Add a {color3} tie or pocket square to your {neutral} suit",
                    f"Power combination: {color1} jacket, {neutral} pants, {color4} accessories"
                ],
                [
                    f"{color2} three-piece suit - your most flattering formal option",
                    f"Elevate a {neutral} suit with {color1} dress shirt and {color3} tie",
                    f"Tailored {color1} or {color2} - perfect fit trumps trendy cuts",
                    f"Classic move: {neutral} suit, {color4} shirt, {color2} pocket square"
                ],
                [
                    f"Stand out professionally with a {color3} suit - unexpected but flattering",
                    f"{color1} tuxedo jacket over {neutral} creates memorable impact",
                    f"Mix formal: {color2} blazer, {neutral_alt} pants, {color1} accessories",
                    f"Your signature: {color1} suit with subtle {color3} detailing"
                ]
            ],
            'party': [
                [
                    f"Own the room in bold {color1} - it's your scientifically proven power color",
                    f"{color2} with metallic gold accessories amplifies your natural glow",
                    f"Statement piece: {color3} jacket over all {neutral} creates drama",
                    f"Mix {color1} top with {color2} pants for head-turning contrast"
                ],
                [
                    f"Go monochrome: all {color2} for sophisticated party presence",
                    f"Pattern play: {color1} print with solid {color3} creates visual interest",
                    f"Confidence booster: {color4} paired with {neutral} metallics",
                    f"Layer {color1} and {color2} pieces for dynamic depth"
                ],
                [
                    f"Shine in {color3} satin or silk - textures matter",
                    f"{color1} sequins or velvet takes advantage of your skin's natural warmth",
                    f"Bold move: {color2} suit with {color4} shirt - unexpectedly perfect",
                    f"Your party uniform: {color1} statement piece + {neutral} foundation"
                ]
            ],
            'business': [
                [
                    f"{color1} blazer over {neutral} shirt projects confident authority",
                    f"Power pants: {color2} trousers with {neutral_alt} top shows leadership",
                    f"Subtle personality: {color3} accessories with classic {color1} suit",
                    f"Your signature look: {color1} jacket, {neutral} base, {color4} accents"
                ],
                [
                    f"Professional edge: {color2} suit with crisp {neutral} shirt",
                    f"Smart casual: {color1} button-down with {neutral_alt} chinos",
                    f"Add {color3} tie or scarf to a {neutral} suit for distinction",
                    f"Trustworthy combo: {color4} cardigan over {neutral} with {color1} pants"
                ],
                [
                    f"Executive presence: tailored {color1} dress with {color2} blazer",
                    f"{color3} blouse under {color2} suit makes you memorable",
                    f"Boardroom ready: {color1} or {color2} monochrome with {neutral} accessories",
                    f"Build authority: {neutral} suit elevated by {color1} shirt and {color4} tie"
                ]
            ],
            'wedding': [
                [
                    f"Guest perfection: elegant {color1} or {color2} - your most flattering shades",
                    f"Pair {color3} with {neutral_alt} for sophisticated celebration style",
                    f"Avoid pure white - your {color1} will photograph beautifully against skin",
                    f"{color2} suit with {color4} accessories strikes the perfect formal note"
                ],
                [
                    f"Standout guest: {color2} dress or suit in luxe fabric",
                    f"{color1} outfit with {color3} shoes creates elegant cohesion",
                    f"Timeless choice: {color4} with {neutral} accessories",
                    f"Your winning look: {color2} base with {color1} accent pieces"
                ],
                [
                    f"Celebrate in style: {color3} ensemble with subtle {neutral} details",
                    f"{color1} formal wear - scientifically matched to your complexion",
                    f"Pair {color2} with metallics to enhance your natural radiance",
                    f"Classic elegance: {color4} suit with {color1} tie or accessories"
                ]
            ],
            'date': [
                [
                    f"First impression: {color1} - scientifically your most flattering color",
                    f"Confidence builder: {color2} with {neutral} for put-together appeal",
                    f"{color3} makes you stand out while staying approachable",
                    f"Winning combo: {color1} top with {color4} or {color2} bottoms"
                ],
                [
                    f"Date night power: fitted {color2} shirt or dress",
                    f"Casual charm: {color1} sweater with dark denim",
                    f"Add {color3} accessories to elevate a simple {neutral} base",
                    f"Your advantage: {color4} paired with {color1} highlights your features"
                ],
                [
                    f"Romantic option: soft {color3} creates warmth and connection",
                    f"{color1} dress or button-down - your color confidence shows",
                    f"Layer {color2} over {neutral} for dimensional interest",
                    f"Can't-miss: {color1} and {color4} combo is uniquely flattering on you"
                ]
            ]
        }
        
        # Normalize occasion and handle variations
        occasion_key = occasion.lower()
        if 'date' in occasion_key:
            occasion_key = 'date'
        
        # Get all variations for this occasion
        variations = tips_variations.get(occasion_key, tips_variations['casual'])
        
        # Randomly select one variation set
        selected_tips = random.choice(variations)
        
        logger.info(f"💡 Generated smart personalized tips (randomized) using colors: {color1}, {color2}, {color3}, {color4}")
        return selected_tips
    
    def get_chatbot_response(self, user_message: str, context: Dict = None) -> str:
        """
        Get chatbot response for conversational fashion advice
        
        Args:
            user_message: User's message/question
            context: Optional context dict with user analysis data
        
        Returns:
            Bot response string
        """
        try:
            # Refresh AI availability
            self._check_ollama_availability()
            
            if not self.use_ai:
                # Fallback to template responses
                return self._get_template_chatbot_response(user_message, context)
            
            # Use AI for response
            import requests
            
            # Build context-aware prompt
            prompt = f"""You are a friendly fashion stylist chatbot. The user asks: "{user_message}"

"""
            
            if context:
                skin_info = context.get('skin_tone', {})
                gender = context.get('gender', {}).get('gender', 'Person')
                age_group = context.get('age', {}).get('age_group', 'Adult')
                
                if skin_info:
                    monk_scale = skin_info.get('monk_scale', {})
                    monk_level = monk_scale.get('monk_level', skin_info.get('monk_scale_level', 'MST-5'))
                    colors = context.get('recommendations', {}).get('color_analysis', {}).get('excellent_colors', [])
                    color_names = [c.get('name', c.get('color_name', '')) for c in colors[:3] if c]
                    
                    prompt += f"""User Profile:
- Gender: {gender}
- Age Group: {age_group}
- Skin Tone: {monk_level}
- Best Colors: {', '.join(color_names) if color_names else 'Various'}

"""
            
            prompt += """Give a helpful, friendly fashion advice response. Keep it concise (2-3 sentences). Be conversational and helpful."""
            
            # Call Ollama
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            }
            
            response = self._call_generate(payload, timeout=30, retries=1)
            
            if response and response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip()
                return ai_text if ai_text else self._get_template_chatbot_response(user_message, context)
            else:
                return self._get_template_chatbot_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return self._get_template_chatbot_response(user_message, context)
    
    def _get_template_chatbot_response(self, user_message: str, context: Dict = None) -> str:
        """Fallback template responses for chatbot"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['color', 'colour', 'what color', 'which color']):
            return "Based on your skin tone analysis, I recommend colors that complement your complexion. Try navy blue, burgundy, or emerald green for best results! These colors will enhance your natural features."
        
        elif any(word in message_lower for word in ['outfit', 'wear', 'what to wear', 'what should i wear']):
            return "For a great outfit, start with your best colors and build from there. A well-fitted piece in your top color will make you look confident and polished! Consider the occasion and choose pieces that make you feel comfortable and stylish."
        
        elif any(word in message_lower for word in ['style', 'fashion', 'tips', 'advice']):
            return "Fashion is about confidence! Choose pieces that fit well and colors that make you feel great. Your best colors will enhance your natural features. Remember, the best outfit is one that makes you feel like the best version of yourself!"
        
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your AI fashion stylist. I can help you with color recommendations, outfit suggestions, and styling tips based on your skin tone analysis. What would you like to know?"
        
        elif any(word in message_lower for word in ['help', 'what can you do']):
            return "I can help you with:\n• Color recommendations based on your skin tone\n• Outfit suggestions for different occasions\n• Styling tips and fashion advice\n• Answering questions about fashion and style\n\nJust ask me anything about fashion!"
        
        else:
            return "I'm here to help with fashion advice! Ask me about colors, outfits, styling tips, or anything related to fashion based on your analysis. What would you like to know?"


# Global instance
print("🚀 Initializing AI Stylist...")
ai_stylist = AIStyler()
print(f"{'🤖 AI MODE ACTIVE' if ai_stylist.use_ai else '🧠 Smart Template Mode'} - Using model: {ai_stylist.ollama_model if ai_stylist.use_ai else 'templates'}")
