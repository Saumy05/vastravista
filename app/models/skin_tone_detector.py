"""
VastraVista - Simplified Skin Tone Detection Module
Author: Saumya Tiwari  
Purpose: Detect faces and extract skin tone information using MediaPipe (No sklearn)
Enhanced with Monk Skin Tone Scale (10-level) integration
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import colorsys
from app.config.logging_config import get_clean_logger
from app.models.monk_skin_tone import MonkSkinToneScale

class SkinToneDetector:
    """Face detection and skin region extraction using MediaPipe with Monk Scale"""
    
    def __init__(self):
        """Initialize MediaPipe face detection and Monk Skin Tone Scale"""
        # Lazy import MediaPipe to avoid startup conflicts
        import mediapipe as mp
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5)
        
        # Initialize Monk Skin Tone Scale (10-level scientific classification)
        self.monk_scale = MonkSkinToneScale()
        
        # Setup logging
        self.logger = get_clean_logger(__name__)
        self.logger.info("🎯 SkinDetector initialized with MediaPipe + Monk Scale")
    
    def detect_face_and_skin(self, image: np.ndarray) -> Dict:
        """
        Detect face and extract skin regions
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary containing face detection results and skin regions
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = self.face_detection.process(rgb_image)
            
            face_data = {
                'faces_detected': 0,
                'face_regions': [],
                'skin_regions': [],
                'face_landmarks': []
            }
            
            if results.detections:
                face_data['faces_detected'] = len(results.detections)
                
                for detection in results.detections:
                    # Extract face bounding box
                    face_bbox = self._get_face_bbox(detection, image.shape)
                    face_data['face_regions'].append(face_bbox)
                    
                    # Extract skin region from face
                    skin_region = self._extract_skin_region(image, face_bbox)
                    if skin_region is not None:
                        face_data['skin_regions'].append(skin_region)
                    
                    # Get face landmarks
                    landmarks = self._get_face_landmarks(detection)
                    face_data['face_landmarks'].append(landmarks)
            
            self.logger.info(f"👤 Detected {face_data['faces_detected']} face(s)")
            return face_data
            
        except Exception as e:
            self.logger.error(f"❌ Face detection failed: {e}")
            return {'faces_detected': 0, 'face_regions': [], 'skin_regions': [], 'face_landmarks': []}
    
    def _get_face_bbox(self, detection, image_shape: Tuple) -> List[int]:
        """Extract face bounding box coordinates"""
        try:
            height, width = image_shape[:2]
            
            bbox = detection.location_data.relative_bounding_box
            x1 = int(bbox.xmin * width)
            y1 = int(bbox.ymin * height)
            x2 = int((bbox.xmin + bbox.width) * width)
            y2 = int((bbox.ymin + bbox.height) * height)
            
            # Ensure coordinates are within image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)
            
            return [x1, y1, x2, y2]
            
        except Exception as e:
            self.logger.error(f"Failed to extract face bbox: {e}")
            return [0, 0, 0, 0]
    
    def _extract_skin_region(self, image: np.ndarray, face_bbox: List[int]) -> Optional[np.ndarray]:
        """
        Extract skin region from detected face area
        
        Args:
            image: Original image
            face_bbox: Face bounding box [x1, y1, x2, y2]
            
        Returns:
            Skin region mask or None if extraction fails
        """
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return None
            
            # Convert to HSV for better skin detection
            hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # Define skin color ranges in HSV
            # These ranges cover various skin tones
            lower_skin1 = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin1 = np.array([20, 255, 255], dtype=np.uint8)
            
            lower_skin2 = np.array([0, 0, 0], dtype=np.uint8)
            upper_skin2 = np.array([25, 255, 255], dtype=np.uint8)
            
            # Create skin masks
            mask1 = cv2.inRange(hsv_face, lower_skin1, upper_skin1)
            mask2 = cv2.inRange(hsv_face, lower_skin2, upper_skin2)
            
            # Combine masks
            skin_mask = cv2.bitwise_or(mask1, mask2)
            
            # Apply morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
            
            # Apply Gaussian blur for smoother results
            skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)
            
            return skin_mask
            
        except Exception as e:
            self.logger.error(f"Skin region extraction failed: {e}")
            return None
    
    def _get_face_landmarks(self, detection) -> Dict:
        """Extract face landmarks for detailed analysis"""
        try:
            landmarks = {}
            
            # Get key points if available
            if hasattr(detection, 'location_data') and hasattr(detection.location_data, 'relative_keypoints'):
                for i, keypoint in enumerate(detection.location_data.relative_keypoints):
                    landmarks[f'point_{i}'] = {
                        'x': keypoint.x,
                        'y': keypoint.y
                    }
            
            return landmarks
            
        except Exception as e:
            self.logger.error(f"Landmark extraction failed: {e}")
            return {}
    
    def get_average_skin_color(self, image: np.ndarray, skin_mask: np.ndarray) -> Dict:
        """
        Calculate average skin color from masked region with Monk Scale classification
        
        Args:
            image: Original image
            skin_mask: Binary mask of skin regions
            
        Returns:
            Dictionary with average skin color information + Monk Scale level
        """
        try:
            # Apply mask to extract skin pixels only
            skin_pixels = cv2.bitwise_and(image, image, mask=skin_mask)
            
            # Get non-zero (skin) pixels
            skin_pixels_flat = skin_pixels[skin_mask > 0]
            
            if len(skin_pixels_flat) == 0:
                return {'error': 'No skin pixels found'}
            
            # Calculate average color
            avg_color_bgr = np.mean(skin_pixels_flat, axis=0)
            avg_color_rgb = avg_color_bgr[::-1]  # Convert BGR to RGB
            
            # Convert to different color spaces
            avg_color_hsv = self._rgb_to_hsv(avg_color_rgb)
            avg_color_hex = self._rgb_to_hex(avg_color_rgb)
            
            # Classify using Monk Skin Tone Scale (10-level)
            rgb_tuple = tuple(int(c) for c in avg_color_rgb)
            monk_classification = self.monk_scale.classify_skin_tone(rgb_tuple, use_delta_e=True)
            
            return {
                'rgb': [int(c) for c in avg_color_rgb],
                'bgr': [int(c) for c in avg_color_bgr],
                'hex': avg_color_hex,
                'hsv': avg_color_hsv,
                'pixel_count': len(skin_pixels_flat),
                'monk_scale': monk_classification,  # 10-level scientific classification
                'monk_level': monk_classification['monk_level'],
                'monk_confidence': monk_classification['confidence']
            }
            
        except Exception as e:
            self.logger.error(f"Average skin color calculation failed: {e}")
            return {'error': str(e)}
    
    def _rgb_to_hex(self, rgb: np.ndarray) -> str:
        """Convert RGB to hex color code"""
        try:
            return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        except:
            return "#000000"
    
    def _rgb_to_hsv(self, rgb: np.ndarray) -> List[float]:
        """Convert RGB to HSV"""
        try:
            r, g, b = np.array(rgb) / 255.0
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            return [round(h * 360, 2), round(s * 100, 2), round(v * 100, 2)]
        except:
            return [0, 0, 0]
    
    def visualize_skin_detection(self, image: np.ndarray, face_data: Dict) -> np.ndarray:
        """
        Visualize face detection and skin regions
        
        Args:
            image: Original image
            face_data: Face detection results
            
        Returns:
            Annotated image with face detection visualization
        """
        try:
            result_image = image.copy()
            
            # Draw face bounding boxes
            for i, face_bbox in enumerate(face_data['face_regions']):
                x1, y1, x2, y2 = face_bbox
                
                # Draw face rectangle
                cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Add face label
                cv2.putText(result_image, f'Face {i+1}', (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # If skin region is available, overlay it
                if i < len(face_data['skin_regions']) and face_data['skin_regions'][i] is not None:
                    skin_mask = face_data['skin_regions'][i]
                    
                    # Resize mask to face region
                    face_region = result_image[y1:y2, x1:x2]
                    if face_region.shape[:2] == skin_mask.shape[:2]:
                        # Create colored overlay for skin regions
                        skin_overlay = np.zeros_like(face_region)
                        skin_overlay[:, :, 1] = skin_mask  # Green channel
                        
                        # Blend with original
                        alpha = 0.3
                        result_image[y1:y2, x1:x2] = cv2.addWeighted(
                            face_region, 1-alpha, skin_overlay, alpha, 0)
            
            # Add info text
            info_text = f"Detected {face_data['faces_detected']} face(s)"
            cv2.putText(result_image, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            return result_image
            
        except Exception as e:
            self.logger.error(f"Visualization failed: {e}")
            return image
    
    def cleanup(self):
        """Clean up MediaPipe resources"""
        try:
            self.face_detection.close()
            self.logger.info("🧹 SkinDetector resources cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
