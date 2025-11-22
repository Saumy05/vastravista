"""
VastraVista Extended API Routes - New Features
Wardrobe Management, AR, Style Profiling, Affiliate Integration, PDF Reports
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import logging
import json

# Create extended routes blueprint
extended_bp = Blueprint('extended', __name__)
logger = logging.getLogger(__name__)


# ==================== WARDROBE MANAGEMENT ====================

@extended_bp.route('/wardrobe/items', methods=['GET'])
def get_wardrobe_items():
    """Get all wardrobe items for a user"""
    try:
        # In production, get user_id from session/auth
        user_id = request.args.get('user_id', 1)
        
        from app.models.database import WardrobeItem, db
        items = WardrobeItem.query.filter_by(user_id=user_id).all()
        
        items_data = [{
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'primary_color': item.primary_color,
            'compatibility_rating': item.compatibility_rating,
            'skin_tone_compatibility': item.skin_tone_compatibility,
            'times_worn': item.times_worn,
            'favorite': item.favorite,
            'image_path': item.image_path,
            'occasions': item.occasion
        } for item in items]
        
        return jsonify({'success': True, 'items': items_data, 'total': len(items_data)})
        
    except ImportError:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    except Exception as e:
        logger.error(f"Get wardrobe items failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/wardrobe/add', methods=['POST'])
def add_wardrobe_item():
    """Add new item to digital wardrobe with analysis"""
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        item_name = request.form.get('name', 'New Item')
        category = request.form.get('category')
        user_id = request.form.get('user_id', 1)
        
        # Get user's skin tone analysis
        user_skin_tone = json.loads(request.form.get('user_skin_tone', '{}'))
        
        # Save image
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wardrobe_{timestamp}_{filename}"
        
        wardrobe_path = Path(current_app.config['WARDROBE_FOLDER']) / str(user_id)
        wardrobe_path.mkdir(parents=True, exist_ok=True)
        
        filepath = wardrobe_path / filename
        file.save(str(filepath))
        
        # Analyze wardrobe item
        from app.services.wardrobe_service import WardrobeManager
        wardrobe_manager = WardrobeManager()
        
        analysis = wardrobe_manager.analyze_wardrobe_item(
            str(filepath),
            user_skin_tone,
            item_name,
            category
        )
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']}), 400
        
        # Save to database
        from app.models.database import WardrobeItem, db
        
        new_item = WardrobeItem(
            user_id=user_id,
            name=analysis['name'],
            category=analysis['category'],
            sub_category=analysis.get('sub_category'),
            image_path=str(filepath),
            primary_color=str(analysis['primary_color']),
            secondary_color=str(analysis.get('secondary_color')),
            color_palette=json.dumps(analysis.get('color_palette', [])),
            skin_tone_compatibility=analysis['skin_tone_compatibility'],
            compatibility_rating=analysis['compatibility_rating'],
            delta_e_score=analysis.get('delta_e_score'),
            occasion=','.join(analysis.get('recommended_occasions', []))
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'item_id': new_item.id,
            'analysis': analysis,
            'message': 'Item added to wardrobe successfully'
        })
        
    except ImportError:
        # Fallback without database
        return jsonify({
            'success': True,
            'message': 'Item analyzed (database not configured)',
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Add wardrobe item failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/wardrobe/analyze', methods=['GET'])
def analyze_wardrobe():
    """Analyze entire wardrobe for color harmony"""
    try:
        user_id = request.args.get('user_id', 1)
        
        from app.models.database import WardrobeItem
        items = WardrobeItem.query.filter_by(user_id=user_id).all()
        
        # Calculate statistics
        total_items = len(items)
        color_distribution = {}
        compatibility_stats = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for item in items:
            # Count colors
            if item.primary_color:
                color = item.primary_color
                color_distribution[color] = color_distribution.get(color, 0) + 1
            
            # Count compatibility ratings
            rating = (item.compatibility_rating or 'fair').lower()
            if rating in compatibility_stats:
                compatibility_stats[rating] += 1
        
        return jsonify({
            'success': True,
            'total_items': total_items,
            'color_distribution': color_distribution,
            'compatibility_stats': compatibility_stats,
            'recommendations': [
                'Your wardrobe has good color variety!',
                f'{compatibility_stats.get("excellent", 0)} items are excellent matches for your skin tone',
                'Consider adding more versatile basics'
            ]
        })
        
    except ImportError:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    except Exception as e:
        logger.error(f"Wardrobe analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/wardrobe/outfits/generate', methods=['POST'])
def generate_outfits():
    """Generate outfit combinations from wardrobe"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        occasion = data.get('occasion', 'casual')
        season = data.get('season', 'all-season')
        max_outfits = data.get('max_outfits', 10)
        
        from app.models.database import WardrobeItem
        from app.services.wardrobe_service import WardrobeManager
        
        # Get user's wardrobe items
        items = WardrobeItem.query.filter_by(user_id=user_id).all()
        
        # Convert to dict format
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'primary_color': eval(item.primary_color) if item.primary_color else (128, 128, 128),
                'skin_tone_compatibility': item.skin_tone_compatibility or 50,
                'recommended_occasions': item.occasion.split(',') if item.occasion else []
            })
        
        # Generate outfit combinations
        wardrobe_manager = WardrobeManager()
        outfits = wardrobe_manager.generate_outfit_combinations(
            items_data, occasion, season, max_outfits
        )
        
        return jsonify({
            'success': True,
            'outfits': outfits,
            'total': len(outfits)
        })
        
    except Exception as e:
        logger.error(f"Outfit generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/shopping/search', methods=['POST'])
def search_shopping():
    """Search for shopping products based on color recommendations"""
    try:
        data = request.get_json()
        colors = data.get('colors', [])
        category = data.get('category', 'clothing')
        
        # Mock shopping results for now
        products = [
            {
                'id': 1,
                'name': f'Stylish {category.capitalize()}',
                'color': colors[0] if colors else 'Navy',
                'price': '$29.99',
                'image': '/static/images/placeholder.jpg',
                'brand': 'FashionBrand',
                'rating': 4.5
            }
        ]
        
        return jsonify({
            'success': True,
            'products': products,
            'total': len(products)
        })
        
    except Exception as e:
        logger.error(f"Shopping search failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate PDF report of color analysis"""
    try:
        data = request.get_json()
        analysis_data = data.get('analysis', {})
        
        return jsonify({
            'success': True,
            'message': 'Report generation feature coming soon!',
            'report_url': '/api/extended/reports/download?id=123'
        })
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AFFILIATE PRODUCT RECOMMENDATIONS ====================

@extended_bp.route('/products/recommend', methods=['POST'])
def recommend_products():
    """Get product recommendations from affiliate APIs"""
    try:
        data = request.get_json()
        
        # Extract parameters
        top_colors = data.get('top_colors', [])
        category = data.get('category', 'shirt')
        gender = data.get('gender', 'Male')
        max_results = data.get('max_results', 20)
        platform = data.get('platform', 'all')
        
        # Initialize affiliate service
        from app.services.affiliate_service import AffiliateAPIManager
        affiliate_manager = AffiliateAPIManager()
        
        # Extract color names
        color_names = [color.get('name', color.get('hex', '')) for color in top_colors[:5]]
        
        # Search products
        products = affiliate_manager.search_products(
            keywords=[category],
            colors=color_names,
            category=category,
            gender=gender,
            max_results=max_results,
            platform=platform
        )
        
        return jsonify({
            'success': True,
            'products': products,
            'total': len(products),
            'filters': {
                'colors': color_names,
                'category': category,
                'gender': gender,
                'platform': platform
            }
        })
        
    except Exception as e:
        logger.error(f"Product recommendation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== AR COLOR DRAPING ====================

@extended_bp.route('/ar/color-draping', methods=['POST'])
def apply_color_draping():
    """Apply AR color draping to user photo"""
    try:
        # Get parameters
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        color_hex = request.form.get('color', '#FF6B6B')
        opacity = float(request.form.get('opacity', 0.6))
        region = request.form.get('region', 'collar')
        
        # Convert hex to RGB
        color_hex = color_hex.lstrip('#')
        color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        
        # Save uploaded image
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = Path(current_app.config['UPLOAD_FOLDER']) / f"temp_{timestamp}_{filename}"
        file.save(str(temp_path))
        
        # Apply color draping
        from app.services.ar_styling_service import ARColorDraping
        ar_draping = ARColorDraping()
        
        result_image = ar_draping.apply_color_draping(
            str(temp_path), color_rgb, opacity, region
        )
        
        # Save result
        result_path = Path(current_app.config['UPLOAD_FOLDER']) / f"draped_{timestamp}_{filename}"
        import cv2
        cv2.imwrite(str(result_path), result_image)
        
        # Clean up temp file
        temp_path.unlink()
        
        return jsonify({
            'success': True,
            'result_image': f'/static/uploads/{result_path.name}',
            'color_applied': color_hex,
            'message': 'Color draping applied successfully'
        })
        
    except Exception as e:
        logger.error(f"AR color draping failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/ar/color-comparison', methods=['POST'])
def create_color_comparison():
    """Create side-by-side color comparison"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        colors_data = json.loads(request.form.get('colors', '[]'))
        
        # Save uploaded image
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = Path(current_app.config['UPLOAD_FOLDER']) / f"temp_{timestamp}_{filename}"
        file.save(str(temp_path))
        
        # Extract colors and names
        colors = []
        color_names = []
        for color_data in colors_data[:4]:  # Limit to 4 colors
            hex_color = color_data.get('hex', '#000000').lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            colors.append(rgb)
            color_names.append(color_data.get('name', 'Color'))
        
        # Create comparison
        from app.services.ar_styling_service import ARColorDraping
        ar_draping = ARColorDraping()
        
        comparison_image = ar_draping.create_color_comparison(
            str(temp_path), colors, color_names
        )
        
        # Save result
        result_path = Path(current_app.config['UPLOAD_FOLDER']) / f"comparison_{timestamp}_{filename}"
        import cv2
        cv2.imwrite(str(result_path), comparison_image)
        
        # Clean up
        temp_path.unlink()
        ar_draping.cleanup()
        
        return jsonify({
            'success': True,
            'comparison_image': f'/static/uploads/{result_path.name}',
            'colors_compared': len(colors)
        })
        
    except Exception as e:
        logger.error(f"Color comparison failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STYLE PROFILING ====================

@extended_bp.route('/style/quiz', methods=['GET'])
def get_style_quiz():
    """Get style DNA quiz questions"""
    try:
        from app.services.ar_styling_service import StyleProfiler
        profiler = StyleProfiler()
        
        questions = profiler.get_quiz_questions()
        
        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(questions)
        })
        
    except Exception as e:
        logger.error(f"Get style quiz failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/style/analyze', methods=['POST'])
def analyze_style_dna():
    """Analyze style DNA from quiz answers"""
    try:
        data = request.get_json()
        answers = data.get('answers', [])
        user_id = data.get('user_id')
        
        from app.services.ar_styling_service import StyleProfiler
        profiler = StyleProfiler()
        
        style_dna = profiler.calculate_style_dna(answers)
        
        # Save to database if user_id provided
        if user_id:
            try:
                from app.models.database import StyleQuizResult, User, db
                
                # Create quiz result
                quiz_result = StyleQuizResult(
                    user_id=user_id,
                    minimalist_score=style_dna['scores'].get('minimalist', 0),
                    bohemian_score=style_dna['scores'].get('bohemian', 0),
                    classic_score=style_dna['scores'].get('classic', 0),
                    edgy_score=style_dna['scores'].get('edgy', 0),
                    romantic_score=style_dna['scores'].get('romantic', 0),
                    sporty_score=style_dna['scores'].get('sporty', 0),
                    dominant_style=style_dna['dominant_style']
                )
                
                db.session.add(quiz_result)
                
                # Update user profile
                user = User.query.get(user_id)
                if user:
                    user.set_style_dna(style_dna['scores'])
                
                db.session.commit()
            except ImportError:
                pass
        
        return jsonify({
            'success': True,
            'style_dna': style_dna
        })
        
    except Exception as e:
        logger.error(f"Style DNA analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PDF REPORT GENERATION ====================

@extended_bp.route('/report/generate', methods=['POST'])
def generate_pdf_report():
    """Generate downloadable PDF color analysis report"""
    try:
        data = request.get_json()
        
        user_data = data.get('user_data', {})
        analysis_results = data.get('analysis_results', {})
        recommendations = data.get('recommendations', {})
        
        from app.services.pdf_generator import PDFReportGenerator
        pdf_generator = PDFReportGenerator(
            output_dir=str(current_app.config['REPORT_FOLDER'])
        )
        
        report_path = pdf_generator.generate_color_analysis_report(
            user_data, analysis_results, recommendations
        )
        
        if report_path:
            return jsonify({
                'success': True,
                'report_path': report_path,
                'download_url': f'/api/extended/report/download?file={Path(report_path).name}',
                'message': 'PDF report generated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Report generation failed'}), 500
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@extended_bp.route('/report/download', methods=['GET'])
def download_report():
    """Download generated PDF report"""
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        
        report_path = Path(current_app.config['REPORT_FOLDER']) / filename
        
        if not report_path.exists():
            return jsonify({'success': False, 'error': 'Report not found'}), 404
        
        return send_file(
            str(report_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Report download failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ANALYTICS ====================

@extended_bp.route('/analytics/wardrobe', methods=['GET'])
def get_wardrobe_analytics():
    """Get wardrobe usage analytics"""
    try:
        user_id = request.args.get('user_id', 1)
        
        from app.models.database import UserAnalytics, WardrobeItem
        
        analytics = UserAnalytics.query.filter_by(user_id=user_id).first()
        
        if not analytics:
            # Calculate analytics
            items = WardrobeItem.query.filter_by(user_id=user_id).all()
            
            # Calculate statistics
            total_items = len(items)
            total_carbon = sum(item.carbon_footprint or 0 for item in items)
            
            # Color usage stats
            color_counts = {}
            for item in items:
                color = item.primary_color or 'Unknown'
                color_counts[color] = color_counts.get(color, 0) + 1
            
            analytics_data = {
                'total_items': total_items,
                'total_carbon_footprint': total_carbon,
                'color_usage': color_counts,
                'most_worn': sorted(items, key=lambda x: x.times_worn or 0, reverse=True)[:5],
                'least_worn': sorted(items, key=lambda x: x.times_worn or 0)[:5]
            }
        else:
            analytics_data = {
                'total_items': analytics.total_items,
                'total_carbon_footprint': analytics.total_carbon_footprint,
                'color_usage': analytics.get_color_usage_stats(),
                'favorite_occasion': analytics.favorite_occasion,
                'favorite_season': analytics.favorite_season
            }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data
        })
        
    except Exception as e:
        logger.error(f"Get analytics failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
