"""
Auth Routes
Implements signup, login, OTP verification, resend, dashboard, and logout.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, current_app, send_from_directory
from datetime import datetime
import logging

from app.models.database import db, User
from flask_login import login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from pathlib import Path
from app.services.image_processor import ImageProcessor
from app.services.color_analyzer import ColorAnalyzer
from app.models.model_loader import model_loader
from app.services.ai_stylist import ai_stylist
from app.services.ar_styling_service import ARColorDraping
from app.utils.color_utils import calculate_color_distance, rgb_to_hex
from app.utils.validators import validate_image_file
from app.services.recommendation_engine import FashionRecommendationEngine
from app.models.monk_skin_tone import MonkSkinToneScale
import cv2
import numpy as np
import time

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

image_processor = ImageProcessor()
color_analyzer = ColorAnalyzer()
recommendation_engine = FashionRecommendationEngine()

@auth_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'service': 'Auth'})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('Invalid email or password', 'danger')
        return render_template('login.html'), 401
    user.last_login = datetime.utcnow()
    db.session.commit()
    login_user(user)
    return redirect(url_for('auth.dashboard'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    email = request.form.get('email', '').strip().lower()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not email or not username or not password:
        flash('All fields are required', 'danger')
        return render_template('signup.html'), 400
    existing = User.query.filter((User.email == email) | (User.username == username)).first()
    if existing:
        flash('Email or username already exists', 'danger')
        return render_template('signup.html'), 400
    user = User(email=email, username=username)
    user.set_password(password)
    user.is_verified = True
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('auth.dashboard'))


# Backward compatibility: redirect old /api/ to login
@auth_bp.route('/api/', methods=['GET'])
def api_root_redirect():
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    file = request.files.get('image')
    is_valid, err = validate_image_file(file) if file else (False, 'No image')
    if not is_valid:
        return jsonify({'success': False, 'error': err}), 400

    ts = int(time.time() * 1000)
    base_name = secure_filename(file.filename or 'upload.jpg')
    name_parts = base_name.rsplit('.', 1)
    ext = name_parts[1].lower() if len(name_parts) > 1 else 'jpg'
    filename = f"{ts}_{name_parts[0]}.{ext}"

    upload_dir = Path(str(current_app.config.get('UPLOAD_FOLDER')))
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / filename
    file.save(saved_path)

    try:
        preprocess = image_processor.preprocess_image(str(saved_path))
        if not preprocess.get('success'):
            return jsonify({'success': False, 'error': preprocess.get('error', 'Preprocess failed')}), 500
        image_np = preprocess['processed']

        skin_detector = model_loader.get_skin_tone_detector()
        gender_detector = model_loader.get_gender_detector()
        age_detector = model_loader.get_age_detector()

        face_data = skin_detector.detect_face_and_skin(image_np) if skin_detector else {'faces_detected': 0, 'face_regions': [], 'skin_regions': []}

        num_faces = face_data.get('faces_detected', 0)
        face_bbox = None
        skin_mask = None
        faces_payload = []
        if num_faces > 1 and face_data.get('face_regions'):
            ar = ARColorDraping()
            try:
                for i, fb in enumerate(face_data.get('face_regions') or []):
                    try:
                        x1, y1, x2, y2 = tuple(fb)
                    except Exception:
                        continue
                    roi = image_np[y1:y2, x1:x2]
                    sm = None
                    try:
                        sm = (face_data.get('skin_regions') or [None])[i]
                    except Exception:
                        sm = None
                    if skin_detector and sm is not None and roi.size > 0:
                        si = skin_detector.get_average_skin_color(roi, sm)
                        rgb_p = si.get('rgb', [128, 128, 128])
                        hex_p = si.get('hex', '#808080')
                        monk_p = si.get('monk_level', 'MST-5')
                        undertone_p = None
                        ms = si.get('monk_scale') or {}
                        uts = ms.get('undertones') or []
                        if uts:
                            undertone_p = uts[0]
                    else:
                        from PIL import Image
                        img_p = Image.open(saved_path).convert('RGB')
                        r_p, g_p, b_p = np.mean(np.array(img_p), axis=(0, 1)).astype(int).tolist()
                        rgb_p = [r_p, g_p, b_p]
                        hex_p = '#%02x%02x%02x' % (r_p, g_p, b_p)
                        try:
                            monk_result_p = MonkSkinToneScale().classify_skin_tone(tuple(rgb_p), use_delta_e=True)
                            monk_p = monk_result_p.get('monk_level', 'MST-5')
                            uts = monk_result_p.get('undertones') or []
                            undertone_p = uts[0] if uts else color_analyzer._determine_undertone(tuple(rgb_p))
                        except Exception:
                            monk_p = 'MST-5'
                            undertone_p = color_analyzer._determine_undertone(tuple(rgb_p))

                    brightness_p = float(sum(rgb_p) / 3)
                    gender_p = gender_detector.detect_gender(image_np, tuple((x1, y1, x2, y2))) if gender_detector else {'gender': 'Unknown', 'confidence': 0}
                    age_p = age_detector.detect_age(image_np, tuple((x1, y1, x2, y2))) if age_detector else {'age_group': 'Unknown', 'confidence': 0}

                    best_list_p = color_analyzer.find_best_colors(tuple(rgb_p), top_n=10)
                    categorized_p = color_analyzer.categorize_colors(best_list_p)

                    clothing_p = ar.extract_clothing_color_for_bbox(str(saved_path), (x1, y1, x2, y2), 'all')
                    feedback_p = None
                    if clothing_p and clothing_p.get('rgb'):
                        detected_rgb_p = tuple(clothing_p['rgb'])
                        ex_p = categorized_p.get('excellent', [])
                        gd_p = categorized_p.get('good', [])
                        pool_p = ex_p + gd_p
                        closest_p = None
                        best_d_p = 1e9
                        for c in pool_p:
                            crgb = tuple(c.get('rgb') or (0, 0, 0))
                            d = calculate_color_distance(detected_rgb_p, crgb)
                            if d < best_d_p:
                                best_d_p = d
                                closest_p = c
                        msg_p = ''
                        qual_p = ''
                        if closest_p and closest_p in ex_p and best_d_p < 12:
                            qual_p = 'excellent'
                            msg_p = f"Great choice. {closest_p.get('color_name')} complements you."
                        elif closest_p and closest_p in gd_p and best_d_p < 18:
                            qual_p = 'good'
                            msg_p = f"Good match. {closest_p.get('color_name')} works for you."
                        else:
                            qual_p = 'not_ideal'
                            names = [c.get('color_name') for c in ex_p[:3]]
                            suggestion = ", ".join([n for n in names if n])
                            msg_p = f"This color is less enhancing. Try {suggestion}."
                        feedback_p = {
                            'message': msg_p,
                            'quality': qual_p,
                            'closest_recommendation': closest_p,
                            'delta_e': float(best_d_p)
                        }

                    faces_payload.append({
                        'skin_tone': {
                            'hex': hex_p,
                            'rgb': rgb_p,
                            'monk_scale_level': monk_p,
                            'brightness': brightness_p,
                            'undertone': undertone_p
                        },
                        'gender': {
                            'gender': gender_p.get('gender', 'Unknown'),
                            'confidence': gender_p.get('confidence', 0)
                        },
                        'age': {
                            'age_group': age_p.get('age_group', 'Unknown'),
                            'confidence': age_p.get('confidence', 0),
                            'estimated_age': age_p.get('estimated_age', None)
                        },
                        'best_colors': {
                            'excellent': categorized_p.get('excellent', []),
                            'good': categorized_p.get('good', [])
                        },
                        'clothing_color': clothing_p or None,
                        'clothing_feedback': feedback_p or None
                    })
            except Exception as e:
                logger.warning(f"Multi-face processing error: {e}")
        else:
            if num_faces > 0 and face_data['face_regions']:
                face_bbox = tuple(face_data['face_regions'][0])
                x1, y1, x2, y2 = face_bbox
                face_roi = image_np[y1:y2, x1:x2]
                if face_data['skin_regions']:
                    skin_mask = face_data['skin_regions'][0]
            else:
                face_roi = image_np

        if skin_detector and skin_mask is not None and face_roi.size > 0:
            skin_info = skin_detector.get_average_skin_color(face_roi, skin_mask)
            rgb = skin_info.get('rgb', [128, 128, 128])
            hex_color = skin_info.get('hex', '#808080')
            monk = skin_info.get('monk_level', 'MST-5')
            undertone = None
            ms = skin_info.get('monk_scale') or {}
            uts = ms.get('undertones') or []
            if uts:
                undertone = uts[0]
        else:
            from PIL import Image
            img = Image.open(saved_path).convert('RGB')
            r, g, b = np.mean(np.array(img), axis=(0, 1)).astype(int).tolist()
            rgb = [r, g, b]
            hex_color = '#%02x%02x%02x' % (r, g, b)
            try:
                monk_result = MonkSkinToneScale().classify_skin_tone(tuple(rgb), use_delta_e=True)
                monk = monk_result.get('monk_level', 'MST-5')
                uts = monk_result.get('undertones') or []
                undertone = uts[0] if uts else color_analyzer._determine_undertone(tuple(rgb))
            except Exception:
                monk = 'MST-5'
                undertone = color_analyzer._determine_undertone(tuple(rgb))

        brightness_val = float(sum(rgb) / 3)

        gender_result = gender_detector.detect_gender(image_np, face_bbox) if gender_detector else {'gender': 'Unknown', 'confidence': 0}
        age_result = age_detector.detect_age(image_np, face_bbox) if age_detector else {'age_group': 'Unknown', 'confidence': 0}

        best_list = color_analyzer.find_best_colors(tuple(rgb), top_n=10)
        categorized = color_analyzer.categorize_colors(best_list)

        data = {
            'num_faces': num_faces or 1,
            'skin_tone': {
                'hex': hex_color,
                'rgb': rgb,
                'monk_scale_level': monk,
                'brightness': brightness_val,
                'undertone': undertone
            },
            'gender': {
                'gender': gender_result.get('gender', 'Unknown'),
                'confidence': gender_result.get('confidence', 0)
            },
            'age': {
                'age_group': age_result.get('age_group', 'Unknown'),
                'confidence': age_result.get('confidence', 0),
                'estimated_age': age_result.get('estimated_age', None)
            },
            'best_colors': {
                'excellent': categorized.get('excellent', []),
                'good': categorized.get('good', [])
            },
            'image_path': str(saved_path)
        }

        try:
            ar = ARColorDraping()
            clothing = ar.extract_dominant_clothing_color(str(saved_path), 'all')
            if faces_payload:
                data['faces'] = faces_payload
                data['num_faces'] = len(faces_payload)
            if clothing and clothing.get('rgb'):
                detected_rgb = tuple(clothing['rgb'])
                detected_hex = rgb_to_hex(detected_rgb)
                ex = categorized.get('excellent', [])
                gd = categorized.get('good', [])
                pool = ex + gd
                closest = None
                best_d = 1e9
                for c in pool:
                    crgb = tuple(c.get('rgb') or (0, 0, 0))
                    d = calculate_color_distance(detected_rgb, crgb)
                    if d < best_d:
                        best_d = d
                        closest = c
                feedback_msg = ''
                quality = ''
                if closest and closest in ex and best_d < 12:
                    quality = 'excellent'
                    feedback_msg = f"Great choice. {closest.get('color_name')} complements you."
                elif closest and closest in gd and best_d < 18:
                    quality = 'good'
                    feedback_msg = f"Good match. {closest.get('color_name')} works for you."
                else:
                    quality = 'not_ideal'
                    names = [c.get('color_name') for c in ex[:3]]
                    suggestion = ", ".join([n for n in names if n])
                    feedback_msg = f"This color is less enhancing. Try {suggestion}."
                data['clothing_color'] = {
                    'rgb': list(detected_rgb),
                    'hex': detected_hex,
                    'nearest': clothing.get('nearest_fashion_color'),
                    'region': clothing.get('region')
                }
                data['clothing_feedback'] = {
                    'message': feedback_msg,
                    'quality': quality,
                    'closest_recommendation': closest,
                    'delta_e': float(best_d)
                }
        except Exception as e:
            logger.warning(f"Clothing color feedback error: {e}")

        try:
            ai_independent = ai_stylist.analyze_image_independently(str(saved_path))
            if ai_independent:
                data['ai_independent'] = ai_independent
                comparison = ai_stylist.compare_analyses(data, ai_independent)
                if comparison:
                    data['comparison'] = comparison
            verification = ai_stylist.verify_analysis(data)
            if verification:
                data['verification'] = verification

            # Decide final displayed gender/age using AI when technical confidence is low
            tech_gender = data['gender'].get('gender', 'Unknown')
            tech_gender_conf = float(data['gender'].get('confidence', 0) or 0)
            tech_age_num = data['age'].get('estimated_age')
            tech_age_conf = float(data['age'].get('confidence', 0) or 0)
            final_gender = tech_gender
            final_age = tech_age_num
            if ai_independent:
                ai_gender = ai_independent.get('gender')
                ai_age = ai_independent.get('age')
                if (tech_gender_conf < 50 or not tech_gender or tech_gender == 'Unknown') and ai_gender:
                    final_gender = ai_gender
                if (tech_age_conf < 25 or final_age is None) and isinstance(ai_age, int):
                    final_age = ai_age
            data['final'] = {
                'gender': final_gender,
                'estimated_age': final_age,
                'gender_source': 'ai' if final_gender != tech_gender else 'technical',
                'age_source': 'ai' if (final_age != tech_age_num and final_age is not None) else 'technical'
            }
        except Exception as e:
            logger.warning(f"AI comparison/verification error: {e}")

        try:
            ai_insights = ai_stylist.analyze_image_with_ai(str(saved_path), {
                'monk_level': data['skin_tone']['monk_scale_level'],
                'gender': data['gender']['gender'],
                'age_group': data['age']['age_group'],
                'best_colors': data['best_colors']
            })
            if ai_insights:
                data['ai_insights'] = ai_insights
        except Exception as e:
            logger.warning(f"AI insights error: {e}")

        try:
            recs = recommendation_engine.generate_recommendations(
                data['gender']['gender'] or 'Male',
                data['age']['age_group'] or 'Young Adult',
                tuple(rgb),
                data['skin_tone'].get('undertone')
            )
            data['fashion_advice'] = recs
        except Exception as e:
            logger.warning(f"Recommendation engine error: {e}")

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/v2/ai-fashion-advice', methods=['POST'])
def get_ai_fashion_advice():
    try:
        payload = request.get_json(force=True)
        skin_hex = payload.get('skin_tone_hex', '#B9966A')
        monk_level = payload.get('monk_scale_level', 'MST-5')
        occasion = payload.get('occasion', 'casual')
        style_prefs = payload.get('style_preferences') or []
        gender = payload.get('gender', 'both')
        age_group = payload.get('age_group', 'Young Adult')
        brightness = float(payload.get('brightness', 120))
        best_colors = payload.get('best_colors') or {}

        excellent = best_colors.get('excellent', [])
        color_names = [c.get('color_name') or c.get('name', '') for c in excellent[:4] if c]

        tips = ai_stylist.generate_occasion_tips(occasion, monk_level, gender, color_names, brightness)

        advice_parts = []
        advice_parts.append(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 10px; margin-bottom: 16px;'>")
        advice_parts.append(f"<h3 style='margin: 0 0 6px 0;'>👤 Personalized Fashion Advice</h3>")
        advice_parts.append(f"<p style='margin: 4px 0; opacity: 0.95;'>Monk Scale: <strong>{monk_level}</strong> | {gender} | {age_group}</p>")
        advice_parts.append(f"<p style='margin: 4px 0; opacity: 0.9;'>Skin Tone: <span style='display:inline-block;width:14px;height:14px;border-radius:50%;background:{skin_hex};border:1px solid rgba(255,255,255,0.7);vertical-align:middle;margin-right:6px;'></span> {skin_hex}</p>")
        advice_parts.append("</div>")

        if excellent:
            advice_parts.append("<div style='background:#f8f9ff;padding:14px;border-radius:10px;margin-bottom:16px;'>")
            advice_parts.append("<h4 style='color:#667eea;margin:0 0 10px 0;'>🎨 Your Top Colors</h4>")
            advice_parts.append("<div style='display:flex;flex-wrap:wrap;gap:8px;'>")
            for c in excellent[:6]:
                advice_parts.append(
                    f"<div title='{c.get('color_name')}' style='width:28px;height:28px;border-radius:6px;background:{c.get('hex','#ccc')};border:1px solid #ddd'></div>"
                )
            advice_parts.append("</div>")
            advice_parts.append("</div>")

        if tips:
            advice_parts.append("<div style='background:#fff;padding:14px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);'>")
            advice_parts.append("<h4 style='margin:0 0 8px 0;color:#333;'>💡 Occasion Tips</h4>")
            advice_parts.append("<ul style='margin:0;padding-left:18px;color:#444;'>")
            for t in tips:
                advice_parts.append(f"<li>{t}</li>")
            advice_parts.append("</ul>")
            advice_parts.append("</div>")

        # Add seasonal palette and outfits via recommendation engine
        try:
            # Convert skin_hex to rgb
            r = int(skin_hex[1:3], 16)
            g = int(skin_hex[3:5], 16)
            b = int(skin_hex[5:7], 16)
            recs = recommendation_engine.generate_recommendations(
                'Male' if gender.lower() == 'male' else ('Female' if gender.lower() == 'female' else 'Male'),
                age_group,
                (r, g, b),
                None
            )
            seasonal = recs.get('seasonal_palette', {})
            outfits = recs.get('outfit_recommendations', [])

            # Seasonal palette
            advice_parts.append("<div style='background:#f9fafb;padding:14px;border-radius:10px;margin-top:12px;'>")
            advice_parts.append("<h4 style='margin:0 0 8px 0;color:#333;'>🍂 Seasonal Palette</h4>")
            for season in ['spring','summer','fall','winter']:
                colors = seasonal.get(season, [])
                if colors:
                    advice_parts.append(f"<div style='margin:6px 0'><strong>{season.title()}:</strong> ")
                    for sc in colors[:6]:
                        advice_parts.append(
                            f"<span title='{sc.get('name')}' style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{sc.get('hex','#ccc')};border:1px solid #ddd;margin-right:6px'></span>"
                        )
                    advice_parts.append("</div>")
            advice_parts.append("</div>")

            # Top outfit suggestion
            if outfits:
                top = outfits[0]
                advice_parts.append("<div style='background:#fff;padding:14px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-top:12px;'>")
                advice_parts.append(f"<h4 style='margin:0 0 8px 0;color:#333;'>👗 Top Outfit – {top.get('occasion')}</h4>")
                advice_parts.append(f"<p style='margin:0 0 6px 0;color:#555;'>Primary: <strong>{top['primary_color']['name']}</strong> ({top['primary_color']['hex']})</p>")
                advice_parts.append("<ul style='margin:0;padding-left:18px;color:#444;'>")
                for item in top.get('items', [])[:3]:
                    advice_parts.append(f"<li>{item['type']} in {item['color']}</li>")
                advice_parts.append("</ul>")
                advice_parts.append(f"<p style='margin:8px 0 0 0;color:#666;'>💬 {top.get('styling_note','')}</p>")
                advice_parts.append("</div>")
        except Exception as e:
            logger.warning(f"Advice extras error: {e}")

        return jsonify({
            'success': True,
            'advice': ''.join(advice_parts)
        })
    except Exception as e:
        logger.error(f"AI fashion advice error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/results', methods=['GET'])
def api_results():
    return render_template('results.html')


@auth_bp.route('/api/v2/monk-scale-info', methods=['GET'])
def monk_scale_info():
    scale = MonkSkinToneScale()
    levels = scale.get_all_monk_levels()
    payload = {}
    for level_id, data in levels.items():
        rec = scale.get_color_recommendations_by_monk_level(level_id)
        best = (rec.get('excellent') or []) + (rec.get('good') or [])
        payload[level_id] = {
            'reference_rgb': data.get('rgb'),
            'description': data.get('description'),
            'best_colors': best
        }
    return jsonify({'monk_scale_levels': payload})
@auth_bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    upload_dir = str(current_app.config.get('UPLOAD_FOLDER'))
    return send_from_directory(upload_dir, filename)
