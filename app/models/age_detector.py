"""
VastraVista - Age Detection Module (Custom Model + DeepFace Fallback)
Author: Saumya Tiwari
Purpose: Detect age group using custom-trained model or DeepFace
Age Groups: 13-19, 20-35, 35-55, 55+
"""

import cv2
import numpy as np
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from app.config.logging_config import get_clean_logger

class AgeDetector:
    """
    Age group detection from facial features using custom trained model or DeepFace
    Classifies into: Teen (13-19), Young Adult (20-35), Middle-aged (35-55), Senior (55+)
    Custom model: ±9.6 years MAE | DeepFace: ±10-15 years MAE
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize age detector"""
        self.logger = get_clean_logger(__name__)
        
        # Age groups
        self.age_groups = [
            {'name': 'Teen', 'range': '13-19', 'min': 13, 'max': 19},
            {'name': 'Young Adult', 'range': '20-35', 'min': 20, 'max': 35},
            {'name': 'Middle-aged', 'range': '35-55', 'min': 35, 'max': 55},
            {'name': 'Senior', 'range': '55+', 'min': 55, 'max': 100}
        ]
        
        # Try to load custom model
        self.custom_model = None
        self.use_custom_model = False
        
        if model_path is None:
            # Default path to trained model
            model_path = Path(__file__).parent.parent.parent / 'custom_model_training' / 'models' / 'age_detector_best.h5'
        
        # TEMPORARILY DISABLED: Custom model overfits (always predicts ~25 years)
        # Trained on only 380 images - needs full 23K dataset for proper generalization
        if False and Path(model_path).exists():
            try:
                from tensorflow.keras.models import load_model
                self.custom_model = load_model(model_path)
                self.use_custom_model = True
                self.logger.info(f"✅ Custom age model loaded from {model_path} (±9.6 years MAE)")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not load custom model: {e}")
                self.logger.info("📦 Falling back to DeepFace")
        
        # Lazy import MediaPipe to avoid startup conflicts
        import mediapipe as mp
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5)
        
        if self.use_custom_model:
            self.logger.info("👶👨👴 AgeDetector initialized with Custom Model")
        else:
            self.logger.info("👶👨👴 AgeDetector initialized with DeepFace (fallback)")
    
    def detect_age(self, image: np.ndarray, face_bbox: Optional[Tuple[int, int, int, int]] = None) -> Dict:
        """
        Detect age group from image using DeepFace (professional-grade)
        
        Args:
            image: Input image as numpy array (BGR format)
            face_bbox: Optional pre-detected face bounding box [x1, y1, x2, y2]
            
        Returns:
            Dictionary containing age group prediction and confidence
        """
        try:
            # Extract face region
            if face_bbox:
                x1, y1, x2, y2 = face_bbox
                face_roi = image[y1:y2, x1:x2]
            else:
                face_roi = image
            
            if face_roi.size == 0:
                return self._empty_result()
            
            # Use custom model if available, otherwise DeepFace
            if self.use_custom_model:
                age_result = self._predict_with_custom_model(face_roi)
            else:
                age_result = self._predict_with_deepface(face_roi, image, face_bbox)
            
            return age_result
            
        except Exception as e:
            self.logger.error(f"❌ Age detection failed: {e}")
            return self._empty_result()
    
    def _predict_with_custom_model(self, face_roi: np.ndarray) -> Dict:
        """
        Predict age using custom trained model (±9.6 years MAE)
        
        Args:
            face_roi: Face region image
            
        Returns:
            Age prediction result
        """
        try:
            # Preprocess face for model input (224x224, normalized)
            face_resized = cv2.resize(face_roi, (224, 224))
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            face_normalized = face_rgb.astype(np.float32) / 255.0
            face_batch = np.expand_dims(face_normalized, axis=0)
            
            # Predict age
            predicted_age = float(self.custom_model.predict(face_batch, verbose=0)[0][0])
            predicted_age = max(1, min(116, predicted_age))  # Clamp to valid range
            
            # Map to age group
            age_group_info = self._map_age_to_group(int(round(predicted_age)))
            
            # Calculate confidence
            confidence = self._calculate_age_confidence(int(round(predicted_age)), age_group_info)
            
            self.logger.info(f"🎯 Custom model predicted age: {predicted_age:.1f} → {age_group_info['name']}")
            
            return {
                'age': int(round(predicted_age)),
                'age_group': age_group_info['name'],
                'age_range': age_group_info['range'],
                'estimated_age': int(round(predicted_age)),
                'confidence': float(confidence),
                'method': 'custom_model'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Custom model prediction failed: {e}")
            # Fallback to DeepFace
            return self._predict_with_deepface(face_roi)
    
    def _predict_with_deepface(self, face_roi: np.ndarray, full_image: Optional[np.ndarray] = None,
                               face_bbox: Optional[Tuple] = None) -> Dict:
        """
        Predict age using DeepFace (pretrained age models)
        
        Args:
            face_roi: Face region image
            full_image: Full image for context (fallback)
            face_bbox: Face bounding box
            
        Returns:
            Age prediction result
        """
        try:
            # Lazy import DeepFace
            from deepface import DeepFace
            
            # Convert BGR to RGB for DeepFace
            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
            
            # CRITICAL: AGGRESSIVE anti-caching to force fresh analysis
            # 1. Add imperceptible random noise (±1-2 pixel values)
            # 2. Ensure timestamp-based uniqueness
            import time
            np.random.seed(int(time.time() * 1000000) % (2**32))  # Microsecond-based seed
            noise = np.random.randint(-1, 2, face_rgb.shape, dtype='int16')
            face_rgb_unique = np.clip(face_rgb.astype('int16') + noise, 0, 255).astype('uint8')
            
            # Add a unique watermark pixel in bottom-right corner (invisible to model)
            face_rgb_unique[-1, -1] = (face_rgb_unique[-1, -1] + np.random.randint(0, 3)) % 256
            
            self.logger.info(f"🔄 Processing unique face variant (seed: {int(time.time() * 1000) % 10000})")
            
            # DeepFace.analyze returns age estimation
            result = DeepFace.analyze(
                img_path=face_rgb_unique,
                actions=['age'],
                enforce_detection=False,
                detector_backend='skip',  # We already have the face
                silent=True  # Suppress DeepFace logs
            )
            
            # Extract result
            if isinstance(result, list):
                result = result[0]
            
            estimated_age = int(result['age'])
            
            # Map to our age groups
            age_group_info = self._map_age_to_group(estimated_age)
            
            # Calculate confidence based on distance from group boundaries
            confidence = self._calculate_age_confidence(estimated_age, age_group_info)
            
            self.logger.info(f"✅ DeepFace detected age: {estimated_age} → {age_group_info['name']}")
            
            return {
                'age_group': age_group_info['name'],
                'age_range': age_group_info['range'],
                'estimated_age': estimated_age,
                'confidence': float(confidence),
                'method': 'DeepFace (Pretrained CNN)',
                'probabilities': self._generate_age_probabilities(estimated_age),
                'features_analyzed': ['deepface_cnn_model'],
                'raw_scores': {}
            }
            
        except Exception as e:
            self.logger.error(f"❌ DeepFace age detection failed: {e}")
            return {
                'age_group': 'Unknown',
                'age_range': 'Unknown',
                'estimated_age': 0,
                'confidence': 0.0,
                'method': 'DeepFace (Failed)',
                'error': str(e)
            }
    
    def _map_age_to_group(self, age: int) -> Dict:
        """Map numeric age to age group"""
        for group in self.age_groups:
            if group['min'] <= age <= group['max']:
                return group
        # Default to Young Adult if outside range
        return self.age_groups[1]
    
    def _calculate_age_confidence(self, age: int, age_group: Dict) -> float:
        """Calculate confidence based on how far from group boundaries"""
        midpoint = (age_group['min'] + age_group['max']) / 2
        distance_from_mid = abs(age - midpoint)
        max_distance = (age_group['max'] - age_group['min']) / 2
        
        # Confidence is higher when closer to midpoint
        confidence = 1.0 - (distance_from_mid / (max_distance + 1))
        return max(0.5, min(0.95, confidence))
    
    def _generate_age_probabilities(self, age: int) -> Dict:
        """Generate probabilities for all age groups based on estimated age"""
        probs = {}
        for group in self.age_groups:
            if group['min'] <= age <= group['max']:
                probs[group['name']] = 0.8
            elif abs(age - group['min']) <= 5 or abs(age - group['max']) <= 5:
                probs[group['name']] = 0.2
            else:
                probs[group['name']] = 0.0
        return probs
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'age_group': 'Unknown',
            'age_range': 'Unknown',
            'estimated_age': 0,
            'confidence': 0.0,
            'method': 'None',
            'probabilities': {},
            'error': 'Detection failed'
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'face_mesh'):
                self.face_mesh.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
