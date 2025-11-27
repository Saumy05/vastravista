"""
Production Half-Body AR Try-On Engine
Uses only shoulders + face (no hips/full body required)
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from collections import deque
import time

logger = logging.getLogger(__name__)


class HalfBodyAREngine:
    """
    Half-body AR engine using only shoulders + face
    No hips or full body required
    """
    
    def __init__(self):
        """Initialize half-body AR engine"""
        self.logger = logging.getLogger(__name__)
        self.mediapipe_available = False
        self.pose = None
        self.face_mesh = None
        self.mp_pose = None
        self.mp_face_mesh = None
        
        # Temporal smoothing buffers
        self.pose_history = deque(maxlen=5)
        self.last_stable_pose = None
        self.last_stable_cloth = None
        
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_face_mesh = mp.solutions.face_mesh
            
            # Pose for shoulders
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,  # NO SEGMENTATION
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Face mesh for nose reference
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                min_detection_confidence=0.5
            )
            
            self.mediapipe_available = True
            self.logger.info("✅ Half-Body AR Engine initialized")
        except ImportError:
            self.logger.warning("⚠️ MediaPipe not available")
            self.mediapipe_available = False
    
    def detect_half_body_pose(self, image: np.ndarray) -> Dict:
        """
        Detect half-body pose (shoulders + face only)
        NO hips or full body required
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
            h, w = image.shape[:2]
            
            # Detect pose (for shoulders)
            pose_results = self.pose.process(image_rgb)
            
            # Detect face (for nose reference)
            face_results = self.face_mesh.process(image_rgb)
            
            # Extract key points (shoulders only, no hips)
            if not pose_results.pose_landmarks:
                # Use last stable pose if available
                if self.last_stable_pose:
                    return self.last_stable_pose
                return {
                    'success': False,
                    'error': 'No pose detected',
                    'confidence': 0.0
                }
            
            landmarks = pose_results.pose_landmarks.landmark
            
            # Get shoulders (required)
            left_shoulder = self._get_landmark(landmarks, 11, w, h)  # Left shoulder
            right_shoulder = self._get_landmark(landmarks, 12, w, h)  # Right shoulder
            
            # Get elbows (optional, for sleeves)
            left_elbow = self._get_landmark(landmarks, 13, w, h)
            right_elbow = self._get_landmark(landmarks, 14, w, h)
            
            # Get nose from face or pose
            nose = None
            if face_results.multi_face_landmarks:
                face_landmarks = face_results.multi_face_landmarks[0].landmark
                # Nose tip (landmark 1)
                nose = (face_landmarks[1].x * w, face_landmarks[1].y * h)
            else:
                # Fallback to pose nose
                nose = self._get_landmark(landmarks, 0, w, h)
            
            # Calculate confidence (shoulder visibility)
            left_shoulder_vis = landmarks[11].visibility
            right_shoulder_vis = landmarks[12].visibility
            avg_confidence = (left_shoulder_vis + right_shoulder_vis) / 2.0
            
            # Calculate shoulder distance
            shoulder_distance = self._calculate_distance(left_shoulder, right_shoulder)
            
            # Calculate shoulder tilt (rotation compensation)
            shoulder_tilt = self._calculate_angle(left_shoulder, right_shoulder)
            
            # Calculate depth (distance from camera) - using shoulder width as proxy
            # Closer = wider shoulders, farther = narrower
            depth_scale = shoulder_distance / 200.0  # Normalize to ~200px baseline
            
            # Build pose data
            pose_data = {
                'success': True,
                'landmarks': {
                    'left_shoulder': left_shoulder,
                    'right_shoulder': right_shoulder,
                    'left_elbow': left_elbow,
                    'right_elbow': right_elbow,
                    'nose': nose,
                },
                'measurements': {
                    'shoulder_distance': shoulder_distance,
                    'shoulder_tilt': shoulder_tilt,
                    'depth_scale': depth_scale,
                    'body_center_x': (left_shoulder[0] + right_shoulder[0]) / 2,
                    'body_center_y': (left_shoulder[1] + right_shoulder[1]) / 2,
                },
                'confidence': avg_confidence,
                'timestamp': time.time()
            }
            
            # Temporal smoothing
            self.pose_history.append(pose_data)
            smoothed_pose = self._temporal_smooth()
            
            # Freeze-last-stable if confidence too low
            if smoothed_pose['confidence'] < 0.60:
                if self.last_stable_pose and self.last_stable_pose['confidence'] >= 0.60:
                    self.logger.debug(f"Low confidence ({smoothed_pose['confidence']:.2f}), using last stable pose")
                    return self.last_stable_pose
            else:
                # Update last stable pose
                self.last_stable_pose = smoothed_pose.copy()
            
            return smoothed_pose
            
        except Exception as e:
            self.logger.error(f"Half-body pose detection error: {e}", exc_info=True)
            # Return last stable pose if available
            if self.last_stable_pose:
                return self.last_stable_pose
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
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _calculate_angle(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate angle of line between two points (for rotation compensation)"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return np.arctan2(dy, dx)
    
    def _temporal_smooth(self) -> Dict:
        """Apply temporal smoothing to pose history"""
        if len(self.pose_history) == 0:
            return self.last_stable_pose or {'success': False}
        
        # Average recent poses
        recent = list(self.pose_history)[-3:]  # Last 3 poses
        
        # Average shoulder positions
        avg_left_shoulder = (
            sum(p['landmarks']['left_shoulder'][0] for p in recent) / len(recent),
            sum(p['landmarks']['left_shoulder'][1] for p in recent) / len(recent)
        )
        avg_right_shoulder = (
            sum(p['landmarks']['right_shoulder'][0] for p in recent) / len(recent),
            sum(p['landmarks']['right_shoulder'][1] for p in recent) / len(recent)
        )
        
        # Average confidence
        avg_confidence = sum(p['confidence'] for p in recent) / len(recent)
        
        # Average measurements
        avg_shoulder_distance = sum(p['measurements']['shoulder_distance'] for p in recent) / len(recent)
        avg_tilt = sum(p['measurements']['shoulder_tilt'] for p in recent) / len(recent)
        avg_depth = sum(p['measurements']['depth_scale'] for p in recent) / len(recent)
        
        # Build smoothed pose
        smoothed = recent[-1].copy()
        smoothed['landmarks']['left_shoulder'] = avg_left_shoulder
        smoothed['landmarks']['right_shoulder'] = avg_right_shoulder
        smoothed['confidence'] = avg_confidence
        smoothed['measurements']['shoulder_distance'] = avg_shoulder_distance
        smoothed['measurements']['shoulder_tilt'] = avg_tilt
        smoothed['measurements']['depth_scale'] = avg_depth
        smoothed['measurements']['body_center_x'] = (avg_left_shoulder[0] + avg_right_shoulder[0]) / 2
        smoothed['measurements']['body_center_y'] = (avg_left_shoulder[1] + avg_right_shoulder[1]) / 2
        
        return smoothed
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.pose:
                self.pose.close()
            if self.face_mesh:
                self.face_mesh.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

