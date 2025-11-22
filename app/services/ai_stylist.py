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
        """Parse AI's structured response"""
        result = {
            'gender': None,
            'age': None,
            'skin_tone': None,
            'colors': []
        }
        
        lines = ai_text.lower().split('\n')
        for line in lines:
            if 'gender:' in line:
                gender_text = line.split('gender:')[-1].strip()
                if 'male' in gender_text and 'female' not in gender_text:
                    result['gender'] = 'Male'
                elif 'female' in gender_text:
                    result['gender'] = 'Female'
            
            elif 'age:' in line:
                age_text = line.split('age:')[-1].strip()
                age_nums = ''.join(filter(str.isdigit, age_text[:5]))
                if age_nums:
                    result['age'] = int(age_nums)
            
            elif 'skin_tone:' in line or 'skin tone:' in line:
                skin_text = line.split(':')[-1].strip()
                result['skin_tone'] = skin_text.title()
            
            elif 'colors:' in line or 'colour' in line:
                colors_text = line.split(':')[-1].strip()
                colors = [c.strip().title() for c in colors_text.split(',')]
                result['colors'] = colors[:3]
        
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
        
        # Compare Gender
        tech_gender = technical_results.get('gender', {}).get('gender', 'Unknown')
        ai_gender = ai_results.get('gender', 'Unknown')
        if tech_gender and ai_gender:
            if tech_gender.lower() == ai_gender.lower():
                comparison['agreements'].append(f"✓ Gender: Both detected {tech_gender}")
                comparison['agreement_score'] += 25
            else:
                comparison['differences'].append(f"⚠ Gender: Technical={tech_gender}, AI={ai_gender}")
        
        # Compare Age
        tech_age = technical_results.get('age', {}).get('estimated_age', 0)
        ai_age = ai_results.get('age', 0)
        if tech_age and ai_age:
            age_diff = abs(tech_age - ai_age)
            if age_diff <= 5:
                comparison['agreements'].append(f"✓ Age: Both ~{tech_age} years (±{age_diff})")
                comparison['agreement_score'] += 25
            elif age_diff <= 10:
                comparison['agreements'].append(f"≈ Age: Technical={tech_age}, AI={ai_age} (±{age_diff} years)")
                comparison['agreement_score'] += 15
            else:
                comparison['differences'].append(f"⚠ Age: Technical={tech_age}, AI={ai_age} (diff: {age_diff} years)")
        
        # Compare Skin Tone (general category)
        tech_monk = technical_results.get('skin_tone', {}).get('monk_scale_level', '')
        ai_skin = ai_results.get('skin_tone', '')
        if tech_monk and ai_skin:
            # Map monk level to category
            monk_num = int(''.join(filter(str.isdigit, tech_monk))) if tech_monk else 5
            tech_category = 'Light' if monk_num <= 3 else 'Medium' if monk_num <= 7 else 'Deep'
            
            if tech_category.lower() in ai_skin.lower():
                comparison['agreements'].append(f"✓ Skin Tone: Both in {tech_category} range")
                comparison['agreement_score'] += 25
            else:
                comparison['differences'].append(f"⚠ Skin: Technical={tech_monk}, AI={ai_skin}")
                comparison['agreement_score'] += 10
        
        # Compare Colors (check if any overlap)
        tech_colors = technical_results.get('best_colors', {}).get('excellent', [])
        tech_color_names = [c.get('color_name', c.get('name', '')) for c in tech_colors[:5]]
        ai_colors = ai_results.get('colors', [])
        
        if tech_color_names and ai_colors:
            overlap = any(tc.lower() in [ac.lower() for ac in ai_colors] for tc in tech_color_names)
            if overlap:
                comparison['agreements'].append(f"✓ Colors: Some overlap detected")
                comparison['agreement_score'] += 25
            else:
                comparison['agreements'].append(f"≈ Colors: Different recommendations (both valid)")
                comparison['agreement_score'] += 10
        
        # Calculate final score
        comparison['agreement_score'] = min(comparison['agreement_score'], 100)
        
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


# Global instance
print("🚀 Initializing AI Stylist...")
ai_stylist = AIStyler()
print(f"{'🤖 AI MODE ACTIVE' if ai_stylist.use_ai else '🧠 Smart Template Mode'} - Using model: {ai_stylist.ollama_model if ai_stylist.use_ai else 'templates'}")
