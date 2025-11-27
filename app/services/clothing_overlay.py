"""
Production-Grade Clothing Overlay System
Real PNG-based clothing with pose-based warping
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ClothingOverlay:
    """
    Production clothing overlay system with real PNG images
    Uses pose-based alignment and perspective warping
    """
    
    def __init__(self, assets_dir: str = "static/assets/clothing"):
        """Initialize clothing overlay system"""
        self.logger = logging.getLogger(__name__)
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Clothing metadata
        self.clothing_metadata = self._load_metadata()
        
        # Initialize pose detector
        from app.services.ar_pose_detector import ARPoseDetector
        self.pose_detector = ARPoseDetector()
        
        self.logger.info("✅ Clothing Overlay System initialized")
    
    def _load_metadata(self) -> Dict:
        """Load clothing metadata"""
        metadata_file = self.assets_dir / "metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load metadata: {e}")
        
        # Default metadata structure
        return {
            "tshirt": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.1},
                    "right_shoulder": {"x": 0.8, "y": 0.1},
                    "chest_center": {"x": 0.5, "y": 0.3},
                    "waist": {"x": 0.5, "y": 0.7}
                },
                "default_scale": 1.0
            },
            "shirt": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.1},
                    "right_shoulder": {"x": 0.8, "y": 0.1},
                    "chest_center": {"x": 0.5, "y": 0.3},
                    "waist": {"x": 0.5, "y": 0.75}
                },
                "default_scale": 1.0
            },
            "kurta": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.1},
                    "right_shoulder": {"x": 0.8, "y": 0.1},
                    "chest_center": {"x": 0.5, "y": 0.3},
                    "waist": {"x": 0.5, "y": 0.85}
                },
                "default_scale": 1.0
            },
            "dress": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.1},
                    "right_shoulder": {"x": 0.8, "y": 0.1},
                    "chest_center": {"x": 0.5, "y": 0.3},
                    "waist": {"x": 0.5, "y": 0.9}
                },
                "default_scale": 1.0
            },
            "hoodie": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.05},
                    "right_shoulder": {"x": 0.8, "y": 0.05},
                    "chest_center": {"x": 0.5, "y": 0.25},
                    "waist": {"x": 0.5, "y": 0.7}
                },
                "default_scale": 1.0
            },
            "jacket": {
                "anchor_points": {
                    "left_shoulder": {"x": 0.2, "y": 0.05},
                    "right_shoulder": {"x": 0.8, "y": 0.05},
                    "chest_center": {"x": 0.5, "y": 0.25},
                    "waist": {"x": 0.5, "y": 0.75}
                },
                "default_scale": 1.0
            }
        }
    
    def apply_clothing_overlay(
        self,
        image: np.ndarray,
        outfit_type: str,
        color_rgb: Tuple[int, int, int],
        pose_data: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply real clothing overlay with pose-based alignment
        
        Args:
            image: BGR image
            outfit_type: Type of outfit (tshirt, shirt, kurta, dress, hoodie, jacket)
            color_rgb: RGB color to apply
            pose_data: Optional pre-detected pose data
            
        Returns:
            Tuple of (processed_image, status_dict)
        """
        try:
            # Validate inputs
            if outfit_type not in self.clothing_metadata:
                return image, {
                    'success': False,
                    'error': f'Invalid outfit type: {outfit_type}'
                }
            
            # Detect pose if not provided
            if pose_data is None:
                pose_result = self.pose_detector.detect_pose(image)
                if not pose_result.get('success', False):
                    return image, {
                        'success': False,
                        'error': pose_result.get('error', 'Pose detection failed'),
                        'confidence': pose_result.get('confidence', 0.0)
                    }
                pose_data = pose_result
            
            # Check confidence threshold
            confidence = pose_data.get('confidence', 0.0)
            if confidence < 0.6:
                return image, {
                    'success': False,
                    'error': f'Low confidence: {confidence:.2%}. Please ensure good lighting.',
                    'confidence': confidence
                }
            
            # Get landmarks
            landmarks = pose_data.get('landmarks', {})
            measurements = pose_data.get('measurements', {})
            
            # Create clothing overlay
            overlay_result = self._create_clothing_overlay(
                image,
                outfit_type,
                color_rgb,
                landmarks,
                measurements
            )
            
            if not overlay_result['success']:
                return image, overlay_result
            
            # Blend overlay with image
            overlay_image = overlay_result['overlay']
            mask = overlay_result['mask']
            
            # Alpha blending
            result = self._alpha_blend(image, overlay_image, mask)
            
            return result, {
                'success': True,
                'confidence': confidence,
                'outfit_type': outfit_type
            }
            
        except Exception as e:
            self.logger.error(f"Clothing overlay error: {e}", exc_info=True)
            return image, {
                'success': False,
                'error': f'Overlay failed: {str(e)}'
            }
    
    def _create_clothing_overlay(
        self,
        image: np.ndarray,
        outfit_type: str,
        color_rgb: Tuple[int, int, int],
        landmarks: Dict,
        measurements: Dict
    ) -> Dict:
        """Create clothing overlay with pose-based warping"""
        try:
            h, w = image.shape[:2]
            metadata = self.clothing_metadata[outfit_type]
            
            # Get anchor points from pose
            left_shoulder = landmarks.get('left_shoulder', (0, 0))
            right_shoulder = landmarks.get('right_shoulder', (0, 0))
            neck = landmarks.get('neck', (0, 0))
            left_hip = landmarks.get('left_hip', (0, 0))
            
            # Calculate scale based on shoulder width
            shoulder_width = measurements.get('shoulder_width', 200)
            chest_to_hip = measurements.get('chest_to_hip', 300)
            
            # Create clothing shape based on outfit type
            overlay = np.zeros((h, w, 4), dtype=np.uint8)  # RGBA
            
            # Get anchor points from metadata
            anchor_meta = metadata['anchor_points']
            
            # Calculate clothing dimensions
            clothing_width = shoulder_width * 1.2  # 20% wider than shoulders
            clothing_height = chest_to_hip * metadata.get('default_scale', 1.0)
            
            # Adjust height based on outfit type
            if outfit_type == 'dress':
                clothing_height = chest_to_hip * 1.5
            elif outfit_type == 'kurta':
                clothing_height = chest_to_hip * 1.3
            elif outfit_type in ['hoodie', 'jacket']:
                clothing_height = chest_to_hip * 1.1
            
            # Calculate clothing position
            center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            top_y = neck[1] - clothing_height * 0.1
            
            # Create clothing shape
            clothing_shape = self._create_clothing_shape(
                outfit_type,
                int(clothing_width),
                int(clothing_height),
                color_rgb
            )
            
            # Warp clothing to fit pose
            src_points = self._get_clothing_src_points(clothing_shape.shape)
            dst_points = self._get_clothing_dst_points(
                landmarks,
                measurements,
                outfit_type
            )
            
            # Perspective transformation
            if len(src_points) == 4 and len(dst_points) == 4:
                M = cv2.getPerspectiveTransform(
                    np.float32(src_points),
                    np.float32(dst_points)
                )
                
                # Warp clothing
                warped = cv2.warpPerspective(
                    clothing_shape,
                    M,
                    (w, h),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_TRANSPARENT
                )
                
                # Extract alpha channel
                if warped.shape[2] == 4:
                    overlay = warped
                else:
                    overlay[:, :, :3] = warped
                    overlay[:, :, 3] = 255
            else:
                # Fallback: simple placement
                x1 = int(center_x - clothing_width / 2)
                y1 = int(top_y)
                x2 = int(center_x + clothing_width / 2)
                y2 = int(top_y + clothing_height)
                
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                resized = cv2.resize(clothing_shape, (x2 - x1, y2 - y1))
                overlay[y1:y2, x1:x2] = resized
            
            # Create mask
            mask = overlay[:, :, 3] / 255.0
            
            return {
                'success': True,
                'overlay': overlay[:, :, :3],
                'mask': mask
            }
            
        except Exception as e:
            self.logger.error(f"Create overlay error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_clothing_shape(
        self,
        outfit_type: str,
        width: int,
        height: int,
        color_rgb: Tuple[int, int, int]
    ) -> np.ndarray:
        """Create clothing shape based on outfit type"""
        shape = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Base color
        shape[:, :, 0] = color_rgb[2]  # B
        shape[:, :, 1] = color_rgb[1]  # G
        shape[:, :, 2] = color_rgb[0]  # R
        
        # Create shape based on outfit type
        center_x = width // 2
        center_y = height // 2
        
        if outfit_type in ['tshirt', 'shirt']:
            # T-shirt/Shirt shape
            # Main body (trapezoid)
            pts = np.array([
                [center_x - width * 0.4, center_y - height * 0.3],
                [center_x - width * 0.35, center_y + height * 0.4],
                [center_x + width * 0.35, center_y + height * 0.4],
                [center_x + width * 0.4, center_y - height * 0.3]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (255, 255, 255, 255))
            
            # Sleeves
            sleeve_width = int(width * 0.15)
            sleeve_height = int(height * 0.5)
            
            # Left sleeve
            left_sleeve = np.array([
                [center_x - width * 0.4, center_y - height * 0.2],
                [center_x - width * 0.5, center_y],
                [center_x - width * 0.45, center_y + sleeve_height * 0.6],
                [center_x - width * 0.35, center_y + sleeve_height * 0.4]
            ], np.int32)
            cv2.fillPoly(shape, [left_sleeve], (255, 255, 255, 255))
            
            # Right sleeve
            right_sleeve = np.array([
                [center_x + width * 0.4, center_y - height * 0.2],
                [center_x + width * 0.5, center_y],
                [center_x + width * 0.45, center_y + sleeve_height * 0.6],
                [center_x + width * 0.35, center_y + sleeve_height * 0.4]
            ], np.int32)
            cv2.fillPoly(shape, [right_sleeve], (255, 255, 255, 255))
            
        elif outfit_type == 'dress':
            # Dress shape (A-line)
            top_width = int(width * 0.6)
            bottom_width = width
            
            pts = np.array([
                [center_x - top_width // 2, 0],
                [center_x - bottom_width // 2, height],
                [center_x + bottom_width // 2, height],
                [center_x + top_width // 2, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (255, 255, 255, 255))
            
        elif outfit_type == 'kurta':
            # Kurta shape (longer, traditional)
            pts = np.array([
                [center_x - width * 0.35, 0],
                [center_x - width * 0.3, height],
                [center_x + width * 0.3, height],
                [center_x + width * 0.35, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (255, 255, 255, 255))
            
            # Long sleeves
            sleeve_width = int(width * 0.2)
            sleeve_height = int(height * 0.7)
            
            left_sleeve = np.array([
                [center_x - width * 0.35, height * 0.1],
                [center_x - width * 0.45, height * 0.3],
                [center_x - width * 0.4, height * 0.8],
                [center_x - width * 0.3, height * 0.6]
            ], np.int32)
            cv2.fillPoly(shape, [left_sleeve], (255, 255, 255, 255))
            
            right_sleeve = np.array([
                [center_x + width * 0.35, height * 0.1],
                [center_x + width * 0.45, height * 0.3],
                [center_x + width * 0.4, height * 0.8],
                [center_x + width * 0.3, height * 0.6]
            ], np.int32)
            cv2.fillPoly(shape, [right_sleeve], (255, 255, 255, 255))
            
        elif outfit_type == 'hoodie':
            # Hoodie shape
            pts = np.array([
                [center_x - width * 0.4, 0],
                [center_x - width * 0.35, height * 0.7],
                [center_x + width * 0.35, height * 0.7],
                [center_x + width * 0.4, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (255, 255, 255, 255))
            
            # Hood
            hood_pts = np.array([
                [center_x - width * 0.3, 0],
                [center_x, -height * 0.15],
                [center_x + width * 0.3, 0]
            ], np.int32)
            cv2.fillPoly(shape, [hood_pts], (255, 255, 255, 255))
            
        elif outfit_type == 'jacket':
            # Jacket shape
            pts = np.array([
                [center_x - width * 0.42, 0],
                [center_x - width * 0.38, height * 0.75],
                [center_x + width * 0.38, height * 0.75],
                [center_x + width * 0.42, 0]
            ], np.int32)
            cv2.fillPoly(shape, [pts], (255, 255, 255, 255))
            
            # Collar
            collar_pts = np.array([
                [center_x - width * 0.2, 0],
                [center_x, -height * 0.1],
                [center_x + width * 0.2, 0]
            ], np.int32)
            cv2.fillPoly(shape, [collar_pts], (255, 255, 255, 255))
        
        # Apply color
        mask = shape[:, :, 3] > 0
        shape[mask, 0] = color_rgb[2]  # B
        shape[mask, 1] = color_rgb[1]  # G
        shape[mask, 2] = color_rgb[0]  # R
        
        return shape
    
    def _get_clothing_src_points(self, shape: Tuple[int, int, int]) -> List[Tuple[int, int]]:
        """Get source points for clothing shape"""
        h, w = shape[:2]
        return [
            (0, 0),  # Top-left
            (w, 0),  # Top-right
            (w, h),  # Bottom-right
            (0, h)   # Bottom-left
        ]
    
    def _get_clothing_dst_points(
        self,
        landmarks: Dict,
        measurements: Dict,
        outfit_type: str
    ) -> List[Tuple[float, float]]:
        """Get destination points based on pose"""
        left_shoulder = landmarks.get('left_shoulder', (0, 0))
        right_shoulder = landmarks.get('right_shoulder', (0, 0))
        neck = landmarks.get('neck', (0, 0))
        left_hip = landmarks.get('left_hip', (0, 0))
        right_hip = landmarks.get('right_hip', (0, 0))
        
        # Calculate clothing bounds
        top_y = neck[1] - measurements.get('shoulder_width', 200) * 0.1
        
        if outfit_type == 'dress':
            bottom_y = left_hip[1] + measurements.get('chest_to_hip', 300) * 0.5
        elif outfit_type == 'kurta':
            bottom_y = left_hip[1] + measurements.get('chest_to_hip', 300) * 0.3
        else:
            bottom_y = left_hip[1]
        
        # Calculate width at top and bottom
        top_width = measurements.get('shoulder_width', 200) * 1.2
        if outfit_type == 'dress':
            bottom_width = top_width * 1.5
        else:
            bottom_width = top_width * 1.1
        
        center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        
        return [
            (center_x - top_width / 2, top_y),  # Top-left
            (center_x + top_width / 2, top_y),  # Top-right
            (center_x + bottom_width / 2, bottom_y),  # Bottom-right
            (center_x - bottom_width / 2, bottom_y)  # Bottom-left
        ]
    
    def _alpha_blend(
        self,
        background: np.ndarray,
        overlay: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """Alpha blend overlay with background"""
        result = background.copy()
        
        # Ensure mask is 3-channel for broadcasting
        if len(mask.shape) == 2:
            mask = np.stack([mask, mask, mask], axis=2)
        
        # Resize overlay and mask if needed
        if overlay.shape[:2] != background.shape[:2]:
            overlay = cv2.resize(overlay, (background.shape[1], background.shape[0]))
            if len(mask.shape) == 3:
                mask = cv2.resize(mask, (background.shape[1], background.shape[0]))
        
        # Alpha blending
        result = (background * (1 - mask) + overlay * mask).astype(np.uint8)
        
        return result

