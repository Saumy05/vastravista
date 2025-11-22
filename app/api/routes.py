"""
VastraVista API Routes
Flask REST API endpoints
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import logging
import traceback

from app.models.model_loader import model_loader
from app.services.image_processor import ImageProcessor
from app.services.color_analyzer import ColorAnalyzer
from app.services.recommendation_engine import FashionRecommendationEngine
from app.services.ai_stylist import ai_stylist
from app.utils.validators import validate_image_file
import shutil

# Create blueprint
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Initialize services
image_processor = ImageProcessor()
color_analyzer = ColorAnalyzer()
recommendation_engine = FashionRecommendationEngine()


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'VastraVista API'
    })


@api_bp.route('/models/status', methods=['GET'])
def models_status():
    """Get status of loaded models"""
    try:
        age_detector = model_loader.get_age_detector()
        gender_detector = model_loader.get_gender_detector()
        skin_detector = model_loader.get_skin_tone_detector()
        
        return jsonify({
            'success': True,
            'models': {
                'age_detector': age_detector is not None,
                'gender_detector': gender_detector is not None,
                'skin_tone_detector': skin_detector is not None
            },
            'total_loaded': sum([
                age_detector is not None,
                gender_detector is not None,
                skin_detector is not None
            ])
        })
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Complete image analysis endpoint
    
    Accepts: multipart/form-data with 'image' file
    Returns: Complete analysis with recommendations
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Validate file
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        file.save(str(upload_path))

        # Ensure a persistent original copy is kept in an `originals/` folder
        try:
            originals_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'originals'
            originals_dir.mkdir(parents=True, exist_ok=True)
            persistent_path = originals_dir / filename
            # Copy the uploaded file to originals (preserve original upload)
            shutil.copyfile(str(upload_path), str(persistent_path))
            logger.info(f"Uploaded image saved to: {upload_path} (persistent copy: {persistent_path})")
        except Exception as e:
            logger.warning(f"Could not create persistent copy of upload: {e}")
        
        logger.info(f"Image uploaded: {filename}")
        
        # Process image
        preprocess_result = image_processor.preprocess_image(
            str(upload_path),
            enhance=request.form.get('enhance', 'true').lower() == 'true'
        )
        
        if not preprocess_result['success']:
            return jsonify({
                'success': False,
                'error': f"Image processing failed: {preprocess_result['error']}"
            }), 400
        
        image = preprocess_result['processed']
        
        # Run analysis (pass image path for AI analysis)
        analysis_result = run_complete_analysis(image, str(upload_path))
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc() if current_app.debug else None
        }), 500


def run_complete_analysis(image, image_path=None):
    """
    Run complete analysis pipeline
    
    Args:
        image: Preprocessed image (numpy array)
        image_path: Path to original uploaded image (for AI analysis)
        
    Returns:
        Complete analysis dictionary
    """
    import uuid
    import time
    
    # Generate unique analysis ID to prevent any caching/collision
    analysis_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    result = {
        'success': False,
        'analysis_id': analysis_id,  # Unique ID for this analysis
        'timestamp': datetime.now().isoformat(),
        'timestamp_ms': int(time.time() * 1000),  # Millisecond precision
        'data': {},
        'error': None
    }
    
    logger.info(f"🆔 Analysis ID: {analysis_id}")
    
    try:
        # Get models
        skin_detector = model_loader.get_skin_tone_detector()
        gender_detector = model_loader.get_gender_detector()
        age_detector = model_loader.get_age_detector()
        
        if not all([skin_detector, gender_detector, age_detector]):
            result['error'] = "One or more required models failed to load"
            return result
        
        # Step 1: Face and Skin Tone Detection
        logger.info("Step 1: Detecting faces and skin tones...")
        face_data = skin_detector.detect_face_and_skin(image)
        
        num_faces = face_data['faces_detected']
        if num_faces == 0:
            result['error'] = "No face detected in image"
            return result
        
        logger.info(f"👥 Detected {num_faces} face(s) - analyzing all...")
        
        # Analyze ALL detected faces
        result['data']['faces'] = []
        result['data']['num_faces'] = num_faces
        
        for face_idx in range(num_faces):
            logger.info(f"\n{'='*60}")
            logger.info(f"👤 ANALYZING PERSON {face_idx + 1}/{num_faces}")
            logger.info(f"{'='*60}")
            
            face_bbox = tuple(face_data['face_regions'][face_idx])
            skin_region = face_data['skin_regions'][face_idx] if face_idx < len(face_data['skin_regions']) else None
            
            if skin_region is None:
                logger.warning(f"⚠️ Could not extract skin region for person {face_idx + 1}, skipping...")
                continue
            
            x1, y1, x2, y2 = face_bbox
            face_image = image[y1:y2, x1:x2]
            skin_color = skin_detector.get_average_skin_color(face_image, skin_region)
            
            if 'error' in skin_color:
                logger.warning(f"⚠️ Skin color extraction failed for person {face_idx + 1}: {skin_color['error']}")
                continue
            
            skin_rgb = tuple(skin_color['rgb'])
            skin_hex = skin_color['hex']
            monk_level = skin_color.get('monk_level', 'N/A')
            monk_data = skin_color.get('monk_scale', {})
            
            # Analyze skin tone
            skin_analysis = analyze_skin_tone(skin_rgb)
            logger.info(f"✅ Skin Tone: {skin_analysis['brightness']} ({skin_analysis['undertone']}) - Monk Scale: {monk_level}")
            
            # Gender Detection with multi-model ensemble
            logger.info(f"🔬 Detecting gender for person {face_idx + 1}...")
            logger.info(f"   Face bbox: {face_bbox}")
            logger.info(f"   Face ROI shape: {face_image.shape}")
            gender_result = gender_detector.detect_gender(image, face_bbox)
            logger.info(f"✅ Gender: {gender_result['gender']} ({gender_result['confidence']*100:.1f}%)")
            if 'individual_predictions' in gender_result:
                logger.info(f"   Individual model predictions: {gender_result['individual_predictions']}")
            
            # Age Detection
            logger.info(f"🎂 Detecting age for person {face_idx + 1}...")
            age_result = age_detector.detect_age(image, face_bbox)
            logger.info(f"✅ Age: {age_result['age_group']} ({age_result['age_range']})")
            
            # Color Analysis
            logger.info(f"🎨 Analyzing best colors for person {face_idx + 1}...")
            best_colors = color_analyzer.find_best_colors(skin_rgb, top_n=15)
            categorized = color_analyzer.categorize_colors(best_colors)
            logger.info(f"✅ Found {len(categorized['excellent'])} excellent colors")
            
            # Generate Recommendations
            logger.info(f"👗 Generating recommendations for person {face_idx + 1}...")
            recommendations = recommendation_engine.generate_recommendations(
                gender=gender_result['gender'],
                age_group=age_result['age_group'],
                skin_rgb=skin_rgb,
                skin_undertone=skin_analysis['undertone']
            )
            
            # Store this person's complete analysis
            person_data = {
                'person_id': face_idx + 1,
                'face_bbox': list(face_bbox),
                'skin_tone': {
                    'rgb': list(skin_rgb),
                    'hex': skin_hex,
                    'undertone': skin_analysis['undertone'],
                    'brightness': skin_analysis['brightness'],
                    'monk_scale_level': monk_level,
                    'monk_scale_data': monk_data
                },
                'gender': {
                    'gender': gender_result['gender'],
                    'confidence': round(gender_result['confidence'] * 100, 2),
                    'method': gender_result['method'],
                    'models_used': gender_result.get('models_used', 1)
                },
                'age': {
                    'age_group': age_result['age_group'],
                    'age_range': age_result['age_range'],
                    'estimated_age': age_result['estimated_age'],
                    'confidence': round(age_result['confidence'] * 100, 2)
                },
                'best_colors': {
                    'all': best_colors[:10],
                    'excellent': categorized['excellent'][:5],
                    'good': categorized['good'][:5],
                    'fair': categorized['fair'][:5]
                },
                'recommendations': recommendations
            }
            
            result['data']['faces'].append(person_data)
            logger.info(f"✅ Person {face_idx + 1} analysis complete!")
        
        if not result['data']['faces']:
            result['error'] = "Could not analyze any of the detected faces"
            return result
        
        # For backward compatibility, copy first person's data to root level
        first_person = result['data']['faces'][0]
        result['data']['gender'] = first_person['gender']
        result['data']['age'] = first_person['age']
        result['data']['skin_tone'] = first_person['skin_tone']
        result['data']['best_colors'] = first_person['best_colors']
        result['data']['recommendations'] = first_person['recommendations']
        
        # Skip the old single-face analysis code
        logger.info(f"\n🎉 Multi-face analysis complete: {len(result['data']['faces'])} person(s) analyzed")
        
        # Calculate summary statistics for all faces
        all_excellent_colors = sum(len(p['best_colors']['excellent']) for p in result['data']['faces'])
        all_outfits = sum(len(p['recommendations'].get('outfit_recommendations', [])) for p in result['data']['faces'])
        
        result['data']['summary'] = {
            'face_detected': True,
            'num_faces': num_faces,
            'all_analyzed': True,
            'total_excellent_colors': all_excellent_colors,
            'total_outfits': all_outfits
        }
        
        # AI status tracking (diagnostics)
        ai_status = {
            'available_at_start': ai_stylist.use_ai,
            'verification': None,
            'independent_analysis': None,
            'comparison': None,
            'insights': None,
            'errors': []
        }

        # AI verification of analysis results
        logger.info("🔍 Verifying analysis with AI...")
        try:
            verification = ai_stylist.verify_analysis({
                'gender': first_person['gender'],
                'age': first_person['age'],
                'skin_tone': first_person['skin_tone'],
                'best_colors': first_person['best_colors']
            })
            result['data']['verification'] = verification
            ai_status['verification'] = {
                'attempted': True,
                'result_present': bool(verification),
                'confidence': verification.get('confidence') if verification else None
            }
            logger.info(f"✅ Verification complete: {verification.get('confidence', 'N/A')}% confidence")
        except Exception as e:
            ai_status['errors'].append(f"verification_error: {str(e)}")
            logger.error(f"AI verification error (caught in run_complete_analysis): {e}")
        
        # AI independent analysis and comparison
        if image_path:
            logger.info(f"🤖 Starting AI independent analysis... (image_path: {image_path})")
            try:
                ai_independent = ai_stylist.analyze_image_independently(image_path)
                ai_status['independent_analysis'] = {'attempted': True, 'result_present': bool(ai_independent)}

                if ai_independent:
                    result['data']['ai_analysis'] = ai_independent
                    logger.info("✅ AI independent analysis completed")
                    
                    # Compare technical vs AI analysis
                    logger.info("🔄 Comparing technical and AI analyses...")
                    try:
                        comparison = ai_stylist.compare_analyses(
                            {
                                'gender': first_person['gender'],
                                'age': first_person['age'],
                                'skin_tone': first_person['skin_tone'],
                                'best_colors': first_person['best_colors']
                            },
                            ai_independent
                        )
                        result['data']['comparison'] = comparison
                        ai_status['comparison'] = {'attempted': True, 'result_present': True, 'agreement_score': comparison.get('agreement_score')}
                        logger.info(f"✅ Comparison complete: {comparison.get('agreement_score', 'N/A')}% agreement")
                    except Exception as comp_err:
                        ai_status['comparison'] = {'attempted': True, 'result_present': False}
                        ai_status['errors'].append(f"comparison_error: {str(comp_err)}")
                        logger.error(f"AI comparison error: {comp_err}")
                else:
                    ai_status['independent_analysis']['result_present'] = False
                    logger.warning("⚠️ AI independent analysis returned None")
            except Exception as ai_err:
                ai_status['independent_analysis'] = {'attempted': True, 'result_present': False}
                ai_status['errors'].append(f"independent_error: {str(ai_err)}")
                logger.error(f"❌ AI independent analysis error: {ai_err}")
                logger.error(traceback.format_exc())

            # AI-powered insights (fashion commentary)
            logger.info("🤖 Generating AI fashion insights...")
            try:
                ai_insights = ai_stylist.analyze_image_with_ai(image_path, {
                    'monk_level': first_person['skin_tone']['monk_scale_level'],
                    'gender': first_person['gender']['gender'],
                    'age_group': first_person['age']['age_group'],
                    'best_colors': first_person['best_colors']
                })
                ai_status['insights'] = {'attempted': True, 'result_present': bool(ai_insights)}

                if ai_insights:
                    result['data']['ai_insights'] = ai_insights
                    logger.info("✅ AI fashion insights added to results")
                else:
                    logger.warning("⚠️ AI insights returned None")
            except Exception as ai_err:
                ai_status['insights'] = {'attempted': True, 'result_present': False}
                ai_status['errors'].append(f"insights_error: {str(ai_err)}")
                logger.error(f"❌ AI insights generation error: {ai_err}")
                logger.error(traceback.format_exc())

            # Attach ai_status diagnostics to response for visibility
            result['data']['ai_status'] = ai_status
        else:
            logger.warning("⚠️ No image_path provided, skipping AI analysis")
        
        result['success'] = True
        logger.info("✅ Complete analysis finished successfully")
        
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        logger.error(traceback.format_exc())
        result['error'] = str(e)
        result['trace'] = traceback.format_exc() if current_app.debug else None
    
    return result


def analyze_skin_tone(rgb):
    """Analyze skin tone from RGB values with improved accuracy"""
    r, g, b = rgb
    
    # Brightness analysis - improved thresholds for better categorization
    brightness = (r + g + b) / 3 / 255.0
    
    # More nuanced brightness categories for better accuracy
    if brightness > 0.75:
        brightness_cat = "Very Light"
    elif brightness > 0.62:
        brightness_cat = "Light"
    elif brightness > 0.48:
        brightness_cat = "Fair"
    elif brightness > 0.35:
        brightness_cat = "Medium"
    elif brightness > 0.22:
        brightness_cat = "Tan"
    elif brightness > 0.15:
        brightness_cat = "Dark"
    else:
        brightness_cat = "Very Dark"
    
    # Undertone analysis - more sensitive detection
    total = r + g + b + 1
    red_ratio = r / total
    blue_ratio = b / total
    green_ratio = g / total
    
    # Enhanced undertone detection
    if red_ratio > blue_ratio + 0.025 and red_ratio > green_ratio:
        undertone = "Warm"
    elif blue_ratio > red_ratio + 0.025 and blue_ratio > green_ratio:
        undertone = "Cool"
    elif green_ratio > max(red_ratio, blue_ratio) + 0.015:
        undertone = "Olive"
    elif abs(red_ratio - blue_ratio) < 0.015:
        undertone = "Neutral"
    elif r > b + 10:
        undertone = "Warm"
    elif b > r + 10:
        undertone = "Cool"
    else:
        undertone = "Neutral"
    
    return {
        'brightness': brightness_cat,
        'undertone': undertone,
        'brightness_value': round(brightness, 3)
    }


@api_bp.route('/v2/ai-fashion-advice', methods=['POST'])
def get_ai_fashion_advice():
    """Get AI-powered fashion advice based on skin tone and preferences"""
    try:
        data = request.get_json()
        
        skin_tone_hex = data.get('skin_tone_hex', '#B9966A')
        monk_level = data.get('monk_scale_level', 'MST-5')
        occasion = data.get('occasion', 'casual')
        style_prefs = data.get('style_preferences', [])
        gender = data.get('gender', 'both')
        age_group = data.get('age_group', 'Young Adult')
        brightness = data.get('brightness', 120)
        best_colors = data.get('best_colors', {})
        
        # Convert brightness to float if it's a string
        try:
            brightness = float(brightness) if brightness else 120
        except (ValueError, TypeError):
            brightness = 120
        
        # Generate personalized fashion advice
        advice_parts = []
        
        # Header with analysis info
        ai_badge = "🤖 AI-Powered" if ai_stylist.use_ai else "🧠 Smart Algorithm"
        advice_parts.append(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>")
        advice_parts.append(f"<h3 style='margin: 0 0 10px 0; color: white;'>👤 Personalized Fashion Advice</h3>")
        advice_parts.append(f"<p style='margin: 5px 0; opacity: 0.95;'>📊 Monk Scale: <strong>{monk_level}</strong> | {gender} | {age_group}</p>")
        advice_parts.append(f"<p style='margin: 5px 0; opacity: 0.95;'>🎨 Skin Brightness: <strong>{brightness:.0f}</strong></p>")
        advice_parts.append(f"<p style='margin: 5px 0; opacity: 0.8; font-size: 0.9em;'>{ai_badge} - Personalized to YOUR analyzed colors</p>")
        advice_parts.append(f"</div>")
        
        # Use actual color recommendations from analysis if available
        if best_colors and (best_colors.get('excellent') or best_colors.get('good')):
            excellent = best_colors.get('excellent', [])
            good = best_colors.get('good', [])
            
            advice_parts.append("<div style='background: #f8f9ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>")
            advice_parts.append("<h4 style='color: #667eea; margin-top: 0;'>🎨 YOUR PERSONALIZED COLOR PALETTE</h4>")
            
            if excellent:
                advice_parts.append("<div style='margin-bottom: 15px;'>")
                advice_parts.append("<p style='font-weight: 600; color: #4CAF50; margin-bottom: 10px;'>⭐ EXCELLENT MATCHES (Wear Often!):</p>")
                advice_parts.append("<div style='display: flex; flex-wrap: wrap; gap: 10px;'>")
                for color in excellent[:5]:
                    color_name = color.get('color_name') or color.get('name', 'Unknown')
                    color_hex = color.get('hex', '#cccccc')
                    # Get score - handle multiple possible keys
                    score = color.get('confidence_score') or color.get('score') or color.get('match_score', 0)
                    advice_parts.append(f"<div style='display: inline-flex; align-items: center; background: white; padding: 8px 15px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>")
                    advice_parts.append(f"<span style='display: inline-block; width: 25px; height: 25px; border-radius: 50%; background: {color_hex}; border: 2px solid #ddd; margin-right: 10px;'></span>")
                    advice_parts.append(f"<span style='font-weight: 600; color: #333;'>{color_name}</span>")
                    if score > 0:
                        advice_parts.append(f"<span style='margin-left: 8px; font-size: 0.85em; color: #4CAF50;'>✓ {score:.0f}%</span>")
                    advice_parts.append(f"</div>")
                advice_parts.append("</div></div>")
            
            if good:
                advice_parts.append("<div style='margin-bottom: 10px;'>")
                advice_parts.append("<p style='font-weight: 600; color: #2196F3; margin-bottom: 10px;'>👍 GOOD MATCHES (Mix & Match):</p>")
                advice_parts.append("<div style='display: flex; flex-wrap: wrap; gap: 10px;'>")
                for color in good[:5]:
                    color_name = color.get('color_name') or color.get('name', 'Unknown')
                    color_hex = color.get('hex', '#cccccc')
                    advice_parts.append(f"<div style='display: inline-flex; align-items: center; background: white; padding: 8px 15px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>")
                    advice_parts.append(f"<span style='display: inline-block; width: 25px; height: 25px; border-radius: 50%; background: {color_hex}; border: 2px solid #ddd; margin-right: 10px;'></span>")
                    advice_parts.append(f"<span style='font-weight: 600; color: #333;'>{color_name}</span>")
                    advice_parts.append(f"</div>")
                advice_parts.append("</div></div>")
            
            advice_parts.append("</div>")
        else:
            # Fallback to generic recommendations
            advice_parts.append("<div style='background: #f8f9ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>")
            advice_parts.append("<h4 style='color: #667eea; margin-top: 0;'>🎨 RECOMMENDED COLORS</h4>")
            
            if 'MST-1' in monk_level or 'MST-2' in monk_level or 'MST-3' in monk_level:
                advice_parts.append("<p><strong>Best for Light Skin Tones:</strong></p>")
                advice_parts.append("<ul><li>Bold, saturated colors create stunning contrast</li>")
                advice_parts.append("<li>Navy, Burgundy, Emerald Green, Ruby Red</li>")
                advice_parts.append("<li>Dark jewel tones: Sapphire Blue, Deep Purple</li>")
                advice_parts.append("<li>Avoid colors too similar to your skin tone</li></ul>")
            elif 'MST-4' in monk_level or 'MST-5' in monk_level or 'MST-6' in monk_level:
                advice_parts.append("<p><strong>Best for Medium Skin Tones:</strong></p>")
                advice_parts.append("<ul><li>High-contrast colors that pop against your skin</li>")
                advice_parts.append("<li>Royal Blue, Mustard, Teal, Burgundy</li>")
                advice_parts.append("<li>Earth tones with rich saturation</li>")
                advice_parts.append("<li>Jewel tones: Amethyst, Jade, Ruby</li></ul>")
            else:
                advice_parts.append("<p><strong>Best for Dark Skin Tones:</strong></p>")
                advice_parts.append("<ul><li>Bright, vibrant colors that enhance your complexion</li>")
                advice_parts.append("<li>Gold, Coral, Turquoise, Fuchsia, White</li>")
                advice_parts.append("<li>Jewel tones: Emerald, Sapphire, Ruby</li>")
                advice_parts.append("<li>Warm metallics and bright pastels</li></ul>")
            
            advice_parts.append("</div>")
        
        # Occasion-specific advice - AI GENERATED
        advice_parts.append("<div style='background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #667eea;'>")
        
        # Normalize occasion value
        occasion = occasion.lower() if occasion else 'casual'
        
        # Extract color names for AI
        color_names = []
        if best_colors:
            excellent = best_colors.get('excellent', [])
            good = best_colors.get('good', [])
            for color in (excellent + good)[:5]:
                name = color.get('color_name') or color.get('name')
                if name:
                    color_names.append(name)
        
        # Generate AI-powered tips
        ai_tips = ai_stylist.generate_occasion_tips(
            occasion=occasion,
            monk_level=monk_level,
            gender=gender,
            colors_list=color_names,
            brightness=brightness
        )
        
        # Occasion emoji map
        occasion_emoji = {
            'casual': '👕',
            'formal': '🎩',
            'party': '🎉',
            'business': '💼',
            'wedding': '💒',
            'date': '💝',
            'date night': '💝'
        }
        
        emoji = occasion_emoji.get(occasion, '👕')
        occasion_title = occasion.replace('_', ' ').title()
        
        advice_parts.append(f"<h4 style='color: #667eea; margin-top: 0;'>{emoji} {occasion_title} Style Tips</h4>")
        advice_parts.append("<ul style='line-height: 1.8;'>")
        
        for tip in ai_tips:
            advice_parts.append(f"<li>{tip}</li>")
        
        advice_parts.append("</ul>")
        advice_parts.append("</div>")
        
        # Style preferences
        if style_prefs and style_prefs[0]:
            advice_parts.append("<div style='background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #764ba2;'>")
            advice_parts.append(f"<h4 style='color: #764ba2; margin-top: 0;'>✨ Based on Your Style: {', '.join(style_prefs)}</h4>")
            advice_parts.append("<ul style='line-height: 1.8;'>")
            advice_parts.append("<li>Focus on pieces that align with your aesthetic</li>")
            advice_parts.append("<li>Build a cohesive wardrobe around these preferences</li>")
            advice_parts.append("<li>Mix classic pieces with trendy elements for balance</li>")
            advice_parts.append("</ul>")
            advice_parts.append("</div>")
        
        # General tips
        advice_parts.append("<div style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 20px; border-radius: 10px;'>")
        advice_parts.append("<h4 style='color: white; margin-top: 0;'>💡 Universal Fashion Wisdom</h4>")
        advice_parts.append("<ul style='line-height: 1.8; color: white;'>")
        advice_parts.append("<li><strong>Confidence</strong> is your best accessory - wear it always!</li>")
        advice_parts.append("<li><strong>Fit matters more than fashion</strong> - tailoring is worth it</li>")
        advice_parts.append("<li><strong>Invest in versatile pieces</strong> in your best colors</li>")
        advice_parts.append("<li><strong>Wear what makes YOU feel great</strong> - not just trends</li>")
        advice_parts.append("<li><strong>Your analyzed colors</strong> are scientifically matched to your skin tone!</li>")
        advice_parts.append("</ul>")
        advice_parts.append("</div>")
        
        advice_text = "".join(advice_parts)
        
        return jsonify({
            'success': True,
            'advice': advice_text,
            'skin_tone': skin_tone_hex,
            'monk_level': monk_level
        })
        
    except Exception as e:
        logger.error(f"AI advice error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Frontend routes
@api_bp.route('/', methods=['GET'])
def index():
    """Serve main page"""
    return render_template('index.html')


@api_bp.route('/results', methods=['GET'])
def results():
    """Serve results page"""
    return render_template('results.html')
