"""
Production-Grade AR Pose Detection Service
Uses MediaPipe Pose for real-time body tracking
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import time

logger = logging.getLogger(__name__)


class ARPoseDetector:
    """
    Production AR Pose Detection using MediaPipe Pose
    Provides real-time body landmarks for clothing overlay
    """
    
    def __init__(self):
        """Initialize pose detector"""
        self.logger = logging.getLogger(__name__)
        self.mediapipe_available = False
        self.pose = None
        self.mp_pose = None
        
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6
            )
            self.mediapipe_available = True
            self.logger.info("✅ MediaPipe Pose initialized")
        except ImportError:
            self.logger.warning("⚠️ MediaPipe not available - AR features will be limited")
            self.mediapipe_available = False
    
    def detect_pose(self, image: np.ndarray) -> Dict:
        """
        Detect body pose in image
        
        Args:
            image: BGR image (numpy array)
            
        Returns:
            Dictionary with pose landmarks and confidence scores
        """
        if not self.mediapipe_available or self.pose is None:
            return {
                'success': False,
                'error': 'MediaPipe not available',
                'confidence': 0.0
            }
        
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process pose
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                return {
                    'success': False,
                    'error': 'No pose detected',
                    'confidence': 0.0
                }
            
            # Extract key landmarks
            landmarks = results.pose_landmarks.landmark
            h, w = image.shape[:2]
            
            # Key points for clothing overlay
            key_points = {
                'left_shoulder': self._get_landmark(landmarks, 11, w, h),  # Left shoulder
                'right_shoulder': self._get_landmark(landmarks, 12, w, h),  # Right shoulder
                'left_elbow': self._get_landmark(landmarks, 13, w, h),
                'right_elbow': self._get_landmark(landmarks, 14, w, h),
                'left_wrist': self._get_landmark(landmarks, 15, w, h),
                'right_wrist': self._get_landmark(landmarks, 16, w, h),
                'left_hip': self._get_landmark(landmarks, 23, w, h),
                'right_hip': self._get_landmark(landmarks, 24, w, h),
                'chest_center': self._get_landmark(landmarks, 0, w, h),  # Nose as reference
                'neck': self._calculate_neck(landmarks, w, h),
            }
            
            # Calculate confidence (average visibility of key points)
            confidences = [
                landmarks[11].visibility,  # Left shoulder
                landmarks[12].visibility,  # Right shoulder
                landmarks[23].visibility,  # Left hip
                landmarks[24].visibility,  # Right hip
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Validate confidence threshold (60% minimum)
            if avg_confidence < 0.6:
                return {
                    'success': False,
                    'error': f'Low confidence: {avg_confidence:.2%}. Please ensure good lighting and full body visibility.',
                    'confidence': avg_confidence
                }
            
            # Calculate body measurements
            shoulder_width = self._calculate_distance(
                key_points['left_shoulder'],
                key_points['right_shoulder']
            )
            
            chest_to_hip = self._calculate_distance(
                key_points['neck'],
                key_points['left_hip']
            )
            
            return {
                'success': True,
                'landmarks': key_points,
                'confidence': avg_confidence,
                'measurements': {
                    'shoulder_width': shoulder_width,
                    'chest_to_hip': chest_to_hip,
                    'body_center_x': (key_points['left_shoulder'][0] + key_points['right_shoulder'][0]) / 2,
                    'body_center_y': (key_points['left_shoulder'][1] + key_points['right_shoulder'][1]) / 2,
                },
                'all_landmarks': [(lm.x * w, lm.y * h, lm.visibility) for lm in landmarks]
            }
            
        except Exception as e:
            self.logger.error(f"Pose detection error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Detection failed: {str(e)}',
                'confidence': 0.0
            }
    
    def _get_landmark(self, landmarks, index: int, width: int, height: int) -> Tuple[float, float]:
        """Extract landmark coordinates"""
        if index < len(landmarks):
            lm = landmarks[index]
            return (lm.x * width, lm.y * height)
        return (0.0, 0.0)
    
    def _calculate_neck(self, landmarks, width: int, height: int) -> Tuple[float, float]:
        """Calculate neck position from shoulders"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        neck_x = ((left_shoulder.x + right_shoulder.x) / 2) * width
        neck_y = ((left_shoulder.y + right_shoulder.y) / 2) * height
        
        return (neck_x, neck_y)
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.pose:
                self.pose.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

