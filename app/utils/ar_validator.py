"""
AR API Request Validator
Strict validation with detailed error messages
"""

import logging
from typing import Dict, Tuple, Optional
from flask import request
import json

logger = logging.getLogger(__name__)


class ARValidator:
    """Validate AR API requests"""
    
    VALID_CLOTHING_TYPES = ['tshirt', 'shirt', 'kurta', 'dress', 'hoodie', 'jacket']
    
    @staticmethod
    def validate_apply_clothing_request() -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate POST /api/ar/apply-clothing request
        
        Returns:
            (is_valid, error_dict, error_message)
        """
        errors = []
        
        # Log request details for debugging
        logger.info(f"Request Content-Type: {request.content_type}")
        logger.info(f"Request Method: {request.method}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        logger.info(f"Request Form Keys: {list(request.form.keys())}")
        logger.info(f"Request Files: {list(request.files.keys())}")
        
        # Check Content-Type
        if not request.content_type or 'multipart/form-data' not in request.content_type:
            errors.append({
                'field': 'Content-Type',
                'error': f'Expected multipart/form-data, got: {request.content_type}',
                'received': request.content_type,
                'expected': 'multipart/form-data'
            })
        
        # Check required field: frame (image file)
        if 'frame' not in request.files:
            # Try alternative names
            if 'image' in request.files:
                logger.warning("Using 'image' field instead of 'frame'")
            else:
                errors.append({
                    'field': 'frame',
                    'error': 'Required field "frame" (image file) is missing',
                    'received_fields': list(request.files.keys()),
                    'expected': 'frame'
                })
        
        # Get frame file (try both 'frame' and 'image')
        frame_file = request.files.get('frame') or request.files.get('image')
        if frame_file:
            if not frame_file.filename:
                errors.append({
                    'field': 'frame',
                    'error': 'Image file is empty or invalid'
                })
            # Check file extension
            elif not frame_file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                errors.append({
                    'field': 'frame',
                    'error': f'Invalid image format: {frame_file.filename}. Expected: jpg, jpeg, png, webp'
                })
        else:
            errors.append({
                'field': 'frame',
                'error': 'No image file provided'
            })
        
        # Check required field: clothing_type
        clothing_type = request.form.get('clothing_type') or request.form.get('outfit_type')
        if not clothing_type:
            errors.append({
                'field': 'clothing_type',
                'error': 'Required field "clothing_type" is missing',
                'received_fields': list(request.form.keys()),
                'expected': 'clothing_type'
            })
        elif clothing_type not in ARValidator.VALID_CLOTHING_TYPES:
            errors.append({
                'field': 'clothing_type',
                'error': f'Invalid clothing_type: {clothing_type}',
                'received': clothing_type,
                'valid_options': ARValidator.VALID_CLOTHING_TYPES
            })
        
        # Check required field: session_id
        session_id = request.form.get('session_id')
        if not session_id:
            errors.append({
                'field': 'session_id',
                'error': 'Required field "session_id" is missing',
                'received_fields': list(request.form.keys()),
                'expected': 'session_id'
            })
        
        # Optional fields validation
        color_hex = request.form.get('color') or request.form.get('skin_tone')
        if color_hex:
            try:
                color_hex = color_hex.lstrip('#')
                if len(color_hex) != 6:
                    raise ValueError("Invalid hex length")
                int(color_hex, 16)  # Validate hex
            except Exception as e:
                errors.append({
                    'field': 'color',
                    'error': f'Invalid color format: {color_hex}. Expected: #RRGGBB or RRGGBB',
                    'received': color_hex
                })
        
        # Build error response
        if errors:
            error_response = {
                'success': False,
                'error': 'Validation failed',
                'errors': errors,
                'received_content_type': request.content_type,
                'received_form_fields': list(request.form.keys()),
                'received_file_fields': list(request.files.keys())
            }
            return False, error_response, f"Validation failed: {len(errors)} error(s)"
        
        return True, None, None
    
    @staticmethod
    def extract_request_data() -> Dict:
        """Extract and normalize request data"""
        # Get frame (try both names)
        frame_file = request.files.get('frame') or request.files.get('image')
        
        # Get clothing_type (try both names)
        clothing_type = request.form.get('clothing_type') or request.form.get('outfit_type')
        
        # Get session_id
        session_id = request.form.get('session_id', 'default')
        
        # Get optional fields
        color_hex = request.form.get('color') or request.form.get('skin_tone', '#667eea')
        template_id = request.form.get('template_id')
        timestamp = request.form.get('timestamp')
        
        # Parse pose_landmarks if provided
        pose_landmarks = None
        if 'pose_landmarks' in request.form:
            try:
                pose_landmarks = json.loads(request.form.get('pose_landmarks'))
            except:
                pass
        
        # Parse color
        color_rgb = None
        if color_hex:
            try:
                color_hex = color_hex.lstrip('#')
                if len(color_hex) == 6:
                    color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            except:
                color_rgb = (102, 126, 234)  # Default purple
        
        return {
            'frame_file': frame_file,
            'clothing_type': clothing_type,
            'session_id': session_id,
            'color_hex': color_hex,
            'color_rgb': color_rgb,
            'template_id': template_id,
            'pose_landmarks': pose_landmarks,
            'timestamp': timestamp
        }

