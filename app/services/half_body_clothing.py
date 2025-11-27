"""
Half-Body Clothing Overlay System
NO segmentation masks - only real clothing shapes
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import math

logger = logging.getLogger(__name__)


class HalfBodyClothingOverlay:
    """
    Half-body clothing overlay (shoulders + face only)
    NO segmentation masks - only real clothing shapes
    """
    
    def __init__(self):
        """Initialize half-body clothing overlay"""
        self.logger = logging.getLogger(__name__)
        self.last_stable_cloth = None
        self.logger.info("✅ Half-Body Clothing Overlay initialized")
    
    def apply_clothing(
        self,
        image: np.ndarray,
        clothing_type: str,
        color_rgb: Tuple[int, int, int],
        pose_data: Dict,
        freeze_on_low_confidence: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply clothing overlay (NO SEGMENTATION MASKS)
        
        Args:
            image: BGR image
            clothing_type: tshirt, shirt, kurta, dress, hoodie, jacket
            color_rgb: RGB color
            pose_data: Pose detection result
            freeze_on_low_confidence: Use last stable cloth if confidence low
            
        Returns:
            Tuple of (processed_image, status_dict)
        """
        try:
            # Validate inputs
            valid_types = ['tshirt', 'shirt', 'kurta', 'dress', 'hoodie', 'jacket']
            if clothing_type not in valid_types:
                return image, {
                    'success': False,
                    'error': f'Invalid clothing_type: {clothing_type}. Must be one of: {valid_types}'
                }
            
            # Check pose data
            if not pose_data.get('success', False):
                error = pose_data.get('error', 'Pose detection failed')
                # Use last stable cloth if available and freeze enabled
                if freeze_on_low_confidence and self.last_stable_cloth is not None:
                    self.logger.debug(f"Pose failed ({error}), using last stable cloth")
                    return self.last_stable_cloth, {
                        'success': True,
                        'frozen': True,
                        'message': 'Using last stable pose'
                    }
                return image, {
                    'success': False,
                    'error': error
                }
            
            # Get landmarks and measurements
            landmarks = pose_data.get('landmarks', {})
            measurements = pose_data.get('measurements', {})
            confidence = pose_data.get('confidence', 0.0)
            
            # Freeze-last-stable if confidence too low
            if freeze_on_low_confidence and confidence < 0.60:
                if self.last_stable_cloth is not None:
                    self.logger.debug(f"Low confidence ({confidence:.2f}), using last stable cloth")
                    return self.last_stable_cloth, {
                        'success': True,
                        'frozen': True,
                        'confidence': confidence
                    }
            
            # Get shoulder positions
            left_shoulder = landmarks.get('left_shoulder', (0, 0))
            right_shoulder = landmarks.get('right_shoulder', (0, 0))
            nose = landmarks.get('nose', (0, 0))
            
            # Get measurements
            shoulder_distance = measurements.get('shoulder_distance', 200)
            shoulder_tilt = measurements.get('shoulder_tilt', 0.0)
            depth_scale = measurements.get('depth_scale', 1.0)
            
            # Dynamic scaling based on shoulder distance
            shirt_width = shoulder_distance * 1.4
            shirt_height = shoulder_distance * 1.6
            
            # Adjust for depth (closer = larger, farther = smaller)
            shirt_width *= depth_scale
            shirt_height *= depth_scale
            
            # Create clothing shape (NO SEGMENTATION MASK)
            clothing_shape = self._create_clothing_shape(
                clothing_type,
                int(shirt_width),
                int(shirt_height),
                color_rgb
            )
            
            # Calculate clothing position (anchored to shoulders)
            center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            top_y = min(left_shoulder[1], right_shoulder[1]) - shirt_height * 0.1
            
            # Apply rotation compensation
            if abs(shoulder_tilt) > 0.1:  # Significant tilt
                clothing_shape = self._rotate_clothing(clothing_shape, shoulder_tilt)
            
            # Warp clothing to fit shoulders
            warped_cloth = self._warp_to_shoulders(
                clothing_shape,
                image.shape,
                left_shoulder,
                right_shoulder,
                nose,
                shirt_width,
                shirt_height
            )
            
            # Alpha blend (NO SEGMENTATION MASK)
            result = self._alpha_blend(image, warped_cloth)
            
            # Update last stable cloth if confidence good
            if confidence >= 0.60:
                self.last_stable_cloth = result.copy()
            
            return result, {
                'success': True,
                'confidence': confidence,
                'clothing_type': clothing_type,
                'frozen': False
            }
            
        except Exception as e:
            self.logger.error(f"Clothing overlay error: {e}", exc_info=True)
            # Use last stable cloth if available
            if freeze_on_low_confidence and self.last_stable_cloth is not None:
                return self.last_stable_cloth, {
                    'success': True,
                    'frozen': True,
                    'error': str(e)
                }
            return image, {
                'success': False,
                'error': f'Overlay failed: {str(e)}'
            }
    
    def _create_clothing_shape(
        self,
        clothing_type: str,
        width: int,
        height: int,
        color_rgb: Tuple[int, int, int]
    ) -> np.ndarray:
        """Create clothing shape (NO SEGMENTATION MASK)"""
        shape = np.zeros((height, width, 4), dtype=np.uint8)
        center_x = width // 2
        center_y = height // 2
        
        # Base color
        b, g, r = color_rgb[2], color_rgb[1], color_rgb[0]
        
        if clothing_type in ['tshirt', 'shirt']:
            # T-shirt/Shirt shape
            # Main body
            pts = np.array([
                [center_x - width * 0.4, center_y - height * 0.3],
                [center_x - width * 0.35, center_y + height * 0.4],
                [center_x + width * 0.35, center_y + height * 0.4],
                [center_x + width * 0.4, center_y - height * 0.3]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (b, g, r, 255))
            
            # Sleeves
            sleeve_w = int(width * 0.15)
            sleeve_h = int(height * 0.5)
            
            # Left sleeve
            left_sleeve = np.array([
                [center_x - width * 0.4, center_y - height * 0.2],
                [center_x - width * 0.5, center_y],
                [center_x - width * 0.45, center_y + sleeve_h * 0.6],
                [center_x - width * 0.35, center_y + sleeve_h * 0.4]
            ], np.int32)
            cv2.fillPoly(shape, [left_sleeve], (b, g, r, 255))
            
            # Right sleeve
            right_sleeve = np.array([
                [center_x + width * 0.4, center_y - height * 0.2],
                [center_x + width * 0.5, center_y],
                [center_x + width * 0.45, center_y + sleeve_h * 0.6],
                [center_x + width * 0.35, center_y + sleeve_h * 0.4]
            ], np.int32)
            cv2.fillPoly(shape, [right_sleeve], (b, g, r, 255))
            
        elif clothing_type == 'dress':
            # Dress shape (A-line)
            top_w = int(width * 0.6)
            bottom_w = width
            
            pts = np.array([
                [center_x - top_w // 2, 0],
                [center_x - bottom_w // 2, height],
                [center_x + bottom_w // 2, height],
                [center_x + top_w // 2, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (b, g, r, 255))
            
        elif clothing_type == 'kurta':
            # Kurta shape
            pts = np.array([
                [center_x - width * 0.35, 0],
                [center_x - width * 0.3, height],
                [center_x + width * 0.3, height],
                [center_x + width * 0.35, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (b, g, r, 255))
            
            # Long sleeves
            sleeve_w = int(width * 0.2)
            sleeve_h = int(height * 0.7)
            
            left_sleeve = np.array([
                [center_x - width * 0.35, height * 0.1],
                [center_x - width * 0.45, height * 0.3],
                [center_x - width * 0.4, height * 0.8],
                [center_x - width * 0.3, height * 0.6]
            ], np.int32)
            cv2.fillPoly(shape, [left_sleeve], (b, g, r, 255))
            
            right_sleeve = np.array([
                [center_x + width * 0.35, height * 0.1],
                [center_x + width * 0.45, height * 0.3],
                [center_x + width * 0.4, height * 0.8],
                [center_x + width * 0.3, height * 0.6]
            ], np.int32)
            cv2.fillPoly(shape, [right_sleeve], (b, g, r, 255))
            
        elif clothing_type == 'hoodie':
            # Hoodie shape
            pts = np.array([
                [center_x - width * 0.4, 0],
                [center_x - width * 0.35, height * 0.7],
                [center_x + width * 0.35, height * 0.7],
                [center_x + width * 0.4, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (b, g, r, 255))
            
            # Hood
            hood_pts = np.array([
                [center_x - width * 0.3, 0],
                [center_x, -height * 0.15],
                [center_x + width * 0.3, 0]
            ], np.int32)
            cv2.fillPoly(shape, [hood_pts], (b, g, r, 255))
            
        elif clothing_type == 'jacket':
            # Jacket shape
            pts = np.array([
                [center_x - width * 0.42, 0],
                [center_x - width * 0.38, height * 0.75],
                [center_x + width * 0.38, height * 0.75],
                [center_x + width * 0.42, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (b, g, r, 255))
            
            # Collar
            collar_pts = np.array([
                [center_x - width * 0.2, 0],
                [center_x, -height * 0.1],
                [center_x + width * 0.2, 0]
            ], np.int32)
            cv2.fillPoly(shape, [collar_pts], (b, g, r, 255))
        
        # Smooth edges
        shape = cv2.GaussianBlur(shape, (5, 5), 0)
        
        return shape
    
    def _rotate_clothing(self, shape: np.ndarray, angle: float) -> np.ndarray:
        """Apply rotation compensation"""
        h, w = shape.shape[:2]
        center = (w // 2, h // 2)
        
        # Convert angle to degrees
        angle_deg = math.degrees(angle)
        
        # Rotate
        M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
        rotated = cv2.warpAffine(shape, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
        
        return rotated
    
    def _warp_to_shoulders(
        self,
        clothing_shape: np.ndarray,
        image_shape: Tuple[int, int, int],
        left_shoulder: Tuple[float, float],
        right_shoulder: Tuple[float, float],
        nose: Tuple[float, float],
        shirt_width: float,
        shirt_height: float
    ) -> np.ndarray:
        """Warp clothing to fit shoulders"""
        h, w = image_shape[:2]
        cloth_h, cloth_w = clothing_shape.shape[:2]
        
        # Source points (clothing shape)
        src_pts = np.float32([
            [0, 0],  # Top-left
            [cloth_w, 0],  # Top-right
            [cloth_w, cloth_h],  # Bottom-right
            [0, cloth_h]  # Bottom-left
        ])
        
        # Destination points (shoulders)
        center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        top_y = min(left_shoulder[1], right_shoulder[1]) - shirt_height * 0.1
        bottom_y = top_y + shirt_height
        
        # Calculate width at top and bottom
        top_width = abs(right_shoulder[0] - left_shoulder[0]) * 1.2
        bottom_width = top_width * 1.1
        
        dst_pts = np.float32([
            [center_x - top_width / 2, top_y],  # Top-left
            [center_x + top_width / 2, top_y],  # Top-right
            [center_x + bottom_width / 2, bottom_y],  # Bottom-right
            [center_x - bottom_width / 2, bottom_y]  # Bottom-left
        ])
        
        # Perspective transform
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(
            clothing_shape,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_TRANSPARENT
        )
        
        return warped
    
    def _alpha_blend(self, background: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """Alpha blend overlay with background (NO SEGMENTATION MASK)"""
        result = background.copy()
        
        if overlay.shape[2] == 4:
            # Has alpha channel
            alpha = overlay[:, :, 3:4] / 255.0
            rgb = overlay[:, :, :3]
            
            # Resize if needed
            if overlay.shape[:2] != background.shape[:2]:
                alpha = cv2.resize(alpha, (background.shape[1], background.shape[0]))
                rgb = cv2.resize(rgb, (background.shape[1], background.shape[0]))
            
            # Blend
            result = (background * (1 - alpha) + rgb * alpha).astype(np.uint8)
        else:
            # No alpha, use simple overlay
            if overlay.shape[:2] != background.shape[:2]:
                overlay = cv2.resize(overlay, (background.shape[1], background.shape[0]))
            result = overlay
        
        return result

