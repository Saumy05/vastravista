"""
VastraVista - AR Color Draping and Virtual Try-On Service
Author: Saumya Tiwari
Purpose: Augmented reality features for color visualization
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ARColorDraping:
    """
    AR-based color draping and visualization
    Shows how different colors look against user's skin tone
    """
    
    def __init__(self):
        """Initialize AR color draping system"""
        self.logger = logging.getLogger(__name__)
        
        # Import MediaPipe for face mesh detection
        import mediapipe as mp
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=5,
            min_detection_confidence=0.5
        )
        
        # Define draping regions (neck/shoulder area landmarks)
        self.draping_landmarks = {
            'collar': [234, 454, 10, 151, 9, 8, 168, 6, 197, 195, 5],  # Neck/collar area
            'shoulder_left': [234, 127, 162, 21, 54, 103, 67],
            'shoulder_right': [454, 356, 389, 251, 284, 332, 297]
        }
        
        self.logger.info("🎨 AR Color Draping initialized")
    
    def apply_color_draping(self, image_path: str, color_rgb: Tuple[int, int, int],
                           opacity: float = 0.6, region: str = 'collar') -> np.ndarray:
        """
        Apply color draping overlay on user's photo
        
        Args:
            image_path: Path to user's photo
            color_rgb: RGB color to drape
            opacity: Overlay opacity (0-1)
            region: Region to apply color ('collar', 'shoulder_left', 'shoulder_right', 'all')
            
        Returns:
            Image with color overlay
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect face mesh
            results = self.face_mesh.process(image_rgb)
            
            if not results.multi_face_landmarks:
                self.logger.warning("No face detected for color draping")
                return image
            
            # Get face landmarks
            face_landmarks = results.multi_face_landmarks[0]
            h, w, _ = image.shape
            
            # Create mask for draping region
            mask = np.zeros((h, w), dtype=np.uint8)
            
            # Get landmarks for specified region
            if region == 'all':
                regions = ['collar', 'shoulder_left', 'shoulder_right']
            else:
                regions = [region]
            
            for reg in regions:
                landmarks_idx = self.draping_landmarks.get(reg, [])
                points = []
                
                for idx in landmarks_idx:
                    landmark = face_landmarks.landmark[idx]
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    points.append([x, y])
                
                if points:
                    points = np.array(points, dtype=np.int32)
                    cv2.fillPoly(mask, [points], 255)
            
            # Expand mask to draping area (below face)
            mask = self._expand_draping_mask(mask, image.shape)
            
            # Create color overlay
            color_overlay = np.zeros_like(image)
            color_overlay[:] = color_rgb[::-1]  # BGR format
            
            # Apply overlay with mask
            mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            result = image * (1 - mask_3channel * opacity) + color_overlay * mask_3channel * opacity
            result = result.astype(np.uint8)
            
            self.logger.info(f"✅ Applied color draping: RGB{color_rgb}")
            return result
            
        except Exception as e:
            self.logger.error(f"Color draping failed: {e}")
            return cv2.imread(image_path) if image_path else None

    def extract_dominant_clothing_color(self, image_path: str, region: str = 'collar') -> Dict:
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {}
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)
            if not results.multi_face_landmarks:
                return {}
            face_landmarks = results.multi_face_landmarks[0]
            h, w, _ = image.shape
            mask = np.zeros((h, w), dtype=np.uint8)
            regions = ['collar', 'shoulder_left', 'shoulder_right'] if region == 'all' else [region]
            for reg in regions:
                landmarks_idx = self.draping_landmarks.get(reg, [])
                points = []
                for idx in landmarks_idx:
                    lm = face_landmarks.landmark[idx]
                    x = int(lm.x * w)
                    y = int(lm.y * h)
                    points.append([x, y])
                if points:
                    pts = np.array(points, dtype=np.int32)
                    cv2.fillPoly(mask, [pts], 255)
            mask = self._expand_draping_mask(mask, image.shape)
            pixels = image_rgb[mask > 0]
            if pixels.size == 0:
                return {}
            Z = pixels.reshape(-1, 3).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 3
            ret, labels, centers = cv2.kmeans(Z, K, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
            counts = np.bincount(labels.flatten())
            idx = int(np.argmax(counts))
            dominant = centers[idx].astype(np.int32).tolist()
            rgb = (int(dominant[0]), int(dominant[1]), int(dominant[2]))
            from app.services.color_analyzer import ColorAnalyzer
            from app.utils.color_utils import rgb_to_hex, calculate_color_distance
            analyzer = ColorAnalyzer()
            nearest = None
            best_delta = 1e9
            for name, data in analyzer.fashion_colors.items():
                d = calculate_color_distance(rgb, tuple(data['rgb']))
                if d < best_delta:
                    best_delta = d
                    nearest = {
                        'color_name': name,
                        'rgb': data['rgb'],
                        'hex': data['hex'],
                        'delta_e': float(d)
                    }
            return {
                'rgb': list(rgb),
                'hex': rgb_to_hex(rgb),
                'nearest_fashion_color': nearest,
                'region': region
            }
        except Exception:
            return {}

    def extract_clothing_color_for_bbox(self, image_path: str, bbox: Tuple[int, int, int, int], region: str = 'collar') -> Dict:
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {}
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1); y1 = max(0, y1); x2 = min(image.shape[1], x2); y2 = min(image.shape[0], y2)
            roi = image[y1:y2, x1:x2]
            if roi is None or roi.size == 0:
                return {}
            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(roi_rgb)
            if not results.multi_face_landmarks:
                return {}
            h, w, _ = roi.shape
            mask = np.zeros((h, w), dtype=np.uint8)
            regions = ['collar', 'shoulder_left', 'shoulder_right'] if region == 'all' else [region]
            face_landmarks = results.multi_face_landmarks[0]
            for reg in regions:
                landmarks_idx = self.draping_landmarks.get(reg, [])
                points = []
                for idx in landmarks_idx:
                    lm = face_landmarks.landmark[idx]
                    x = int(lm.x * w)
                    y = int(lm.y * h)
                    points.append([x, y])
                if points:
                    pts = np.array(points, dtype=np.int32)
                    cv2.fillPoly(mask, [pts], 255)
            mask = self._expand_draping_mask(mask, roi.shape)
            pixels = roi_rgb[mask > 0]
            if pixels.size == 0:
                return {}
            Z = pixels.reshape(-1, 3).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 3
            ret, labels, centers = cv2.kmeans(Z, K, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
            counts = np.bincount(labels.flatten())
            idx = int(np.argmax(counts))
            dominant = centers[idx].astype(np.int32).tolist()
            rgb = (int(dominant[0]), int(dominant[1]), int(dominant[2]))
            from app.services.color_analyzer import ColorAnalyzer
            from app.utils.color_utils import rgb_to_hex, calculate_color_distance
            analyzer = ColorAnalyzer()
            nearest = None
            best_delta = 1e9
            for name, data in analyzer.fashion_colors.items():
                d = calculate_color_distance(rgb, tuple(data['rgb']))
                if d < best_delta:
                    best_delta = d
                    nearest = {
                        'color_name': name,
                        'rgb': data['rgb'],
                        'hex': data['hex'],
                        'delta_e': float(d)
                    }
            return {
                'rgb': [rgb[0], rgb[1], rgb[2]],
                'hex': rgb_to_hex(rgb),
                'nearest_fashion_color': nearest,
                'region': region
            }
        except Exception:
            return {}
    
    def _expand_draping_mask(self, mask: np.ndarray, image_shape: Tuple) -> np.ndarray:
        """Expand mask to cover typical clothing draping area"""
        h, w = image_shape[:2]
        
        # Find the lowest point of current mask
        mask_coords = np.where(mask > 0)
        if len(mask_coords[0]) == 0:
            return mask
        
        min_y = np.min(mask_coords[0])
        max_y = np.max(mask_coords[0])
        min_x = np.min(mask_coords[1])
        max_x = np.max(mask_coords[1])
        
        # Extend downward to cover shoulder/chest area
        extension_height = int((h - max_y) * 0.4)
        extension_region = np.zeros_like(mask)
        
        # Create trapezoid shape (wider at bottom)
        for y in range(max_y, min(max_y + extension_height, h)):
            progress = (y - max_y) / extension_height if extension_height > 0 else 0
            width_expansion = int(progress * (max_x - min_x) * 0.3)
            x_start = max(0, min_x - width_expansion)
            x_end = min(w, max_x + width_expansion)
            extension_region[y, x_start:x_end] = 255
        
        # Combine masks
        combined_mask = np.maximum(mask, extension_region)
        
        # Smooth edges
        combined_mask = cv2.GaussianBlur(combined_mask, (21, 21), 0)
        
        return combined_mask
    
    def create_color_comparison(self, image_path: str, colors: List[Tuple[int, int, int]],
                               color_names: List[str]) -> np.ndarray:
        """
        Create side-by-side comparison of multiple colors
        
        Args:
            image_path: Path to user's photo
            colors: List of RGB colors to compare
            color_names: Names of colors
            
        Returns:
            Combined comparison image
        """
        try:
            comparisons = []
            
            for i, (color, name) in enumerate(zip(colors, color_names)):
                draped = self.apply_color_draping(image_path, color)
                
                # Add color label
                label_height = 40
                labeled = np.zeros((draped.shape[0] + label_height, draped.shape[1], 3), dtype=np.uint8)
                labeled[:draped.shape[0], :] = draped
                labeled[draped.shape[0]:, :] = (240, 240, 240)  # Light gray background
                
                # Add text
                cv2.putText(labeled, name, (10, draped.shape[0] + 28),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)
                
                comparisons.append(labeled)
            
            # Stack images horizontally
            if len(comparisons) <= 3:
                result = np.hstack(comparisons)
            else:
                # Stack in grid
                rows = []
                for i in range(0, len(comparisons), 3):
                    row = np.hstack(comparisons[i:i+3])
                    rows.append(row)
                result = np.vstack(rows)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Color comparison failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'face_mesh'):
                self.face_mesh.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


class StyleProfiler:
    """
    Style DNA profiling and personalization
    """
    
    def __init__(self):
        """Initialize style profiler"""
        self.logger = logging.getLogger(__name__)
        
        # Style categories
        self.style_categories = {
            'minimalist': {
                'keywords': ['simple', 'clean', 'neutral', 'basic', 'classic'],
                'colors': ['black', 'white', 'gray', 'beige', 'navy'],
                'patterns': ['solid', 'minimal']
            },
            'bohemian': {
                'keywords': ['flowy', 'layered', 'ethnic', 'artistic', 'relaxed'],
                'colors': ['earth tones', 'burgundy', 'mustard', 'olive'],
                'patterns': ['floral', 'paisley', 'tribal']
            },
            'classic': {
                'keywords': ['timeless', 'elegant', 'tailored', 'sophisticated'],
                'colors': ['navy', 'camel', 'burgundy', 'forest green'],
                'patterns': ['stripes', 'checks', 'solid']
            },
            'edgy': {
                'keywords': ['bold', 'leather', 'dark', 'asymmetric', 'modern'],
                'colors': ['black', 'dark gray', 'burgundy', 'metallic'],
                'patterns': ['geometric', 'bold']
            },
            'romantic': {
                'keywords': ['feminine', 'soft', 'delicate', 'flowing', 'vintage'],
                'colors': ['blush', 'lavender', 'cream', 'rose'],
                'patterns': ['floral', 'lace', 'soft']
            },
            'sporty': {
                'keywords': ['athletic', 'comfortable', 'casual', 'functional'],
                'colors': ['bright', 'primary colors', 'neon'],
                'patterns': ['stripes', 'color blocks']
            }
        }
        
        # Quiz questions
        self.quiz_questions = self._build_style_quiz()
        
        self.logger.info("💎 Style Profiler initialized")
    
    def _build_style_quiz(self) -> List[Dict]:
        """Build style DNA quiz questions"""
        return [
            {
                'question': 'How would you describe your ideal outfit?',
                'options': {
                    'Simple and understated': {'minimalist': 3, 'classic': 1},
                    'Colorful and expressive': {'bohemian': 3, 'romantic': 1},
                    'Polished and put-together': {'classic': 3, 'minimalist': 1},
                    'Bold and eye-catching': {'edgy': 3, 'bohemian': 1},
                    'Comfortable and practical': {'sporty': 3, 'minimalist': 1}
                }
            },
            {
                'question': 'What patterns do you prefer?',
                'options': {
                    'Solid colors only': {'minimalist': 3, 'classic': 2},
                    'Floral and nature-inspired': {'bohemian': 3, 'romantic': 2},
                    'Classic stripes or checks': {'classic': 3, 'minimalist': 1},
                    'Bold geometric patterns': {'edgy': 3, 'sporty': 1},
                    'Soft, delicate prints': {'romantic': 3, 'bohemian': 1}
                }
            },
            {
                'question': 'Your go-to color palette is:',
                'options': {
                    'Neutrals (black, white, gray, beige)': {'minimalist': 3, 'classic': 2},
                    'Earth tones and warm colors': {'bohemian': 3, 'romantic': 1},
                    'Navy, burgundy, and rich tones': {'classic': 3, 'edgy': 1},
                    'Dark and moody colors': {'edgy': 3, 'minimalist': 1},
                    'Pastels and soft colors': {'romantic': 3, 'bohemian': 1},
                    'Bright and energetic colors': {'sporty': 3, 'edgy': 1}
                }
            },
            {
                'question': 'Your fashion inspiration comes from:',
                'options': {
                    'Scandinavian minimalism': {'minimalist': 3},
                    'Free-spirited travel and culture': {'bohemian': 3},
                    'Classic Hollywood glamour': {'classic': 3, 'romantic': 2},
                    'Fashion-forward street style': {'edgy': 3, 'sporty': 1},
                    'Vintage romance': {'romantic': 3, 'classic': 1},
                    'Athletic wear brands': {'sporty': 3}
                }
            },
            {
                'question': 'For a night out, you would wear:',
                'options': {
                    'A sleek black dress or suit': {'minimalist': 2, 'classic': 2, 'edgy': 2},
                    'A flowing printed dress with layered jewelry': {'bohemian': 3, 'romantic': 1},
                    'A tailored dress with classic heels': {'classic': 3},
                    'Leather jacket with statement pieces': {'edgy': 3},
                    'A soft, feminine dress with delicate accessories': {'romantic': 3},
                    'Stylish athleisure with trendy sneakers': {'sporty': 3}
                }
            }
        ]
    
    def calculate_style_dna(self, quiz_answers: List[str]) -> Dict:
        """
        Calculate style DNA from quiz answers
        
        Args:
            quiz_answers: List of selected answer texts
            
        Returns:
            Style DNA profile with scores for each category
        """
        try:
            # Initialize scores
            scores = {style: 0 for style in self.style_categories.keys()}
            
            # Process each answer
            for i, answer in enumerate(quiz_answers):
                if i < len(self.quiz_questions):
                    question = self.quiz_questions[i]
                    if answer in question['options']:
                        style_points = question['options'][answer]
                        for style, points in style_points.items():
                            scores[style] += points
            
            # Normalize scores to 0-100 scale
            max_score = max(scores.values()) if scores.values() else 1
            if max_score > 0:
                normalized_scores = {style: (score / max_score) * 100 
                                    for style, score in scores.items()}
            else:
                normalized_scores = {style: 0 for style in scores.keys()}
            
            # Find dominant style
            dominant_style = max(normalized_scores, key=normalized_scores.get)
            
            result = {
                'scores': normalized_scores,
                'dominant_style': dominant_style,
                'secondary_styles': self._get_secondary_styles(normalized_scores),
                'style_description': self._get_style_description(dominant_style),
                'recommended_items': self._get_style_recommendations(dominant_style)
            }
            
            self.logger.info(f"✅ Style DNA calculated: {dominant_style}")
            return result
            
        except Exception as e:
            self.logger.error(f"Style DNA calculation failed: {e}")
            return {}
    
    def _get_secondary_styles(self, scores: Dict) -> List[str]:
        """Get secondary style preferences"""
        sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [style for style, score in sorted_styles[1:3] if score > 30]
    
    def _get_style_description(self, style: str) -> str:
        """Get description for style type"""
        descriptions = {
            'minimalist': 'You appreciate clean lines, neutral colors, and timeless pieces. Your wardrobe is functional yet stylish.',
            'bohemian': 'You love free-spirited, artistic fashion with rich textures, patterns, and layered looks.',
            'classic': 'You prefer timeless, elegant pieces that never go out of style. Quality and sophistication are your priorities.',
            'edgy': 'You embrace bold, modern fashion with dark colors, leather, and statement pieces.',
            'romantic': 'You adore feminine, delicate pieces with soft colors, flowing fabrics, and vintage-inspired details.',
            'sporty': 'You prioritize comfort and functionality with athletic-inspired pieces and casual cool vibes.'
        }
        return descriptions.get(style, 'Your unique style blends multiple influences.')
    
    def _get_style_recommendations(self, style: str) -> List[str]:
        """Get clothing recommendations for style type"""
        recommendations = {
            'minimalist': ['Basic white tee', 'Black trousers', 'Structured blazer', 'Leather accessories'],
            'bohemian': ['Maxi dress', 'Embroidered top', 'Layered jewelry', 'Suede ankle boots'],
            'classic': ['Trench coat', 'White button-down', 'Tailored pants', 'Pumps'],
            'edgy': ['Leather jacket', 'Combat boots', 'Dark denim', 'Statement belt'],
            'romantic': ['Lace blouse', 'Flowing skirt', 'Delicate jewelry', 'Ballet flats'],
            'sporty': ['Track pants', 'Bomber jacket', 'Sneakers', 'Athletic tops']
        }
        return recommendations.get(style, [])
    
    def get_quiz_questions(self) -> List[Dict]:
        """Return quiz questions for frontend"""
        return self.quiz_questions
