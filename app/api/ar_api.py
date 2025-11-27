"""
Production-Grade AR Try-On API
Handles real-time clothing overlay with proper body detection
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required
import cv2
import numpy as np
import logging
from pathlib import Path
import base64
import io
from PIL import Image
from typing import Dict, Tuple, Optional
import time

from app.services.ar_styling_service import ARColorDraping
from app.services.image_processor import ImageProcessor
from app.services.half_body_ar_engine import HalfBodyAREngine
from app.services.half_body_clothing import HalfBodyClothingOverlay
from app.utils.ar_validator import ARValidator
from app.utils.ar_logger import ar_logger

ar_api_bp = Blueprint('ar_api', __name__)
logger = logging.getLogger(__name__)

# Initialize services
ar_engine = HalfBodyAREngine()
clothing_overlay = HalfBodyClothingOverlay()


@ar_api_bp.route('/api/ar/apply-clothing', methods=['POST'])
@login_required
def apply_clothing_overlay():
    """
    Production API: Apply clothing overlay to uploaded image
    Content-Type: multipart/form-data
    Required: frame (image), clothing_type, session_id
    """
    try:
        # STRICT VALIDATION
        is_valid, error_response, error_msg = ARValidator.validate_apply_clothing_request()
        
        if not is_valid:
            # Log validation error
            ar_logger.log_error(
                '/api/ar/apply-clothing',
                'validation_error',
                error_msg,
                error_response
            )
            return jsonify(error_response), 400
        
        # Extract validated data
        data = ARValidator.extract_request_data()
        frame_file = data['frame_file']
        clothing_type = data['clothing_type']
        session_id = data['session_id']
        color_rgb = data['color_rgb'] or (102, 126, 234)  # Default purple
        
        # Save temporary image
        temp_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'data/uploads'))
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"ar_{session_id}_{int(time.time() * 1000)}.jpg"
        frame_file.save(str(temp_path))
        
        try:
            # Load image
            image = cv2.imread(str(temp_path))
            if image is None:
                ar_logger.log_error('/api/ar/apply-clothing', 'image_load_error', 'Failed to load image')
                return jsonify({
                    'success': False,
                    'error': 'Failed to load image file'
                }), 500
            
            # Detect half-body pose (shoulders + face only)
            pose_result = ar_engine.detect_half_body_pose(image)
            
            # Apply clothing overlay (NO SEGMENTATION MASKS)
            result_image, status = clothing_overlay.apply_clothing(
                image,
                clothing_type,
                color_rgb,
                pose_result,
                freeze_on_low_confidence=True  # Freeze-last-stable
            )
            
            if not status.get('success', False):
                error_msg = status.get('error', 'Failed to process image')
                ar_logger.log_error('/api/ar/apply-clothing', 'processing_error', error_msg)
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'confidence': status.get('confidence', 0.0)
                }), 400
            
            # Convert to base64 for response
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Log successful request
            ar_logger.log_request(
                '/api/ar/apply-clothing',
                'POST',
                'success',
                {'clothing_type': clothing_type, 'confidence': status.get('confidence', 0.0)}
            )
            
            return jsonify({
                'success': True,
                'image': f'data:image/jpeg;base64,{img_base64}',
                'clothing_type': clothing_type,
                'confidence': status.get('confidence', 1.0),
                'frozen': status.get('frozen', False)
            })
            
        finally:
            # Cleanup temp file
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
                
    except Exception as e:
        logger.error(f"AR overlay error: {e}", exc_info=True)
        ar_logger.log_error('/api/ar/apply-clothing', 'exception', str(e))
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'details': str(e) if current_app.debug else None
        }), 500


@ar_api_bp.route('/api/ar/detect-pose', methods=['POST'])
@login_required
def detect_pose():
    """
    Production API: Detect half-body pose (shoulders + face)
    Returns pose landmarks for AR overlay positioning
    """
    try:
        # Get image (try both field names for compatibility)
        frame_file = request.files.get('frame') or request.files.get('image')
        
        if not frame_file or not frame_file.filename:
            return jsonify({
                'success': False,
                'error': 'No image provided. Use "frame" or "image" field.'
            }), 400
        
        # Save temporary image
        temp_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'data/uploads'))
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"ar_pose_{int(time.time() * 1000)}.jpg"
        frame_file.save(str(temp_path))
        
        try:
            # Load image
            image = cv2.imread(str(temp_path))
            if image is None:
                return jsonify({'success': False, 'error': 'Failed to load image'}), 500
            
            # Detect half-body pose (shoulders + face only)
            pose_result = ar_engine.detect_half_body_pose(image)
            
            if not pose_result.get('success', False):
                return jsonify({
                    'success': False,
                    'error': pose_result.get('error', 'Pose detection failed'),
                    'confidence': pose_result.get('confidence', 0.0)
                }), 400
            
            return jsonify({
                'success': True,
                'pose_data': pose_result
            })
            
        finally:
            # Cleanup
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
                
    except Exception as e:
        logger.error(f"Pose detection error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Detection failed'}), 500


@ar_api_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns system status and model availability
    """
    try:
        import mediapipe as mp
        mps_available = True
    except ImportError:
        mps_available = False
    
    # Estimate FPS (rough estimate)
    fps_estimate = 5.0  # Conservative estimate for half-body processing
    
    return jsonify({
        'status': 'ok',
        'models_loaded': ar_engine.mediapipe_available,
        'mps_available': mps_available,
        'fps_estimate': fps_estimate,
        'half_body_support': True
    })


@ar_api_bp.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    """
    Get recent request validation errors
    """
    limit = int(request.args.get('limit', 20))
    
    return jsonify({
        'success': True,
        'recent_errors': ar_logger.get_recent_errors(limit),
        'recent_requests': ar_logger.get_recent_requests(limit)
    })


@ar_api_bp.route('/api/ar/get-skin-tone-colors', methods=['GET'])
@login_required
def get_skin_tone_colors():
    """
    Production API: Get user's skin-tone matched colors from latest analysis
    """
    try:
        from flask_login import current_user
        from app.models.database import ColorAnalysis
        
        # Get latest analysis for user
        latest_analysis = ColorAnalysis.query.filter_by(user_id=current_user.id)\
            .order_by(ColorAnalysis.analysis_date.desc())\
            .first()
        
        if not latest_analysis:
            return jsonify({
                'success': False,
                'error': 'No analysis found. Please run an analysis first.',
                'colors': []
            }), 404
        
        # Parse colors from JSON
        import json
        top_colors = json.loads(latest_analysis.top_colors) if latest_analysis.top_colors else []
        
        # Format for frontend
        colors = []
        for color in top_colors[:12]:  # Top 12 colors
            colors.append({
                'hex': color.get('hex', color.get('color_hex', '#667eea')),
                'name': color.get('color_name', color.get('name', 'Color')),
                'rgb': color.get('rgb', [102, 126, 234])
            })
        
        return jsonify({
            'success': True,
            'colors': colors,
            'skin_tone': {
                'hex': latest_analysis.skin_tone_hex,
                'monk_level': latest_analysis.skin_tone
            }
        })
        
    except Exception as e:
        logger.error(f"Get skin tone colors error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get colors'}), 500

