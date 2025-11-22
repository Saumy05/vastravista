"""
Image Processing Service
OpenCV and MediaPipe preprocessing
"""

import cv2
import numpy as np
import logging
from typing import Dict, Optional
from pathlib import Path


class ImageProcessor:
    """
    Image preprocessing and face detection
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image from file path
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.error(f"Failed to load image: {image_path}")
                return None
            
            return image
        except Exception as e:
            self.logger.error(f"Error loading image: {e}")
            return None
    
    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Load image from bytes
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error("Failed to decode image from bytes")
                return None
            
            return image
        except Exception as e:
            self.logger.error(f"Error loading image from bytes: {e}")
            return None
    
    def resize_image(self, image: np.ndarray, max_width: int = 1920, 
                    max_height: int = 1080) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio
        
        Args:
            image: Input image
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized image
        """
        try:
            height, width = image.shape[:2]
            
            if width <= max_width and height <= max_height:
                return image
            
            # Calculate scaling factor
            scale = min(max_width / width, max_height / height)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), 
                               interpolation=cv2.INTER_AREA)
            
            self.logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized
            
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            return image
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better detection
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels
            enhanced = cv2.merge([l, a, b])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing image: {e}")
            return image
    
    def preprocess_image(self, image_path: str, enhance: bool = True) -> Dict:
        """
        Complete preprocessing pipeline
        
        Args:
            image_path: Path to image file
            enhance: Whether to enhance image quality
            
        Returns:
            Dictionary with original and processed image
        """
        result = {
            'success': False,
            'original': None,
            'processed': None,
            'error': None
        }
        
        try:
            # Load image
            image = self.load_image(image_path)
            if image is None:
                result['error'] = "Failed to load image"
                return result
            
            result['original'] = image.copy()
            
            # Resize if needed
            processed = self.resize_image(image)
            
            # Enhance if requested
            if enhance:
                processed = self.enhance_image(processed)
            
            result['processed'] = processed
            result['success'] = True
            
            self.logger.info(f"Image preprocessing complete: {image_path}")
            
        except Exception as e:
            self.logger.error(f"Preprocessing error: {e}")
            result['error'] = str(e)
        
        return result
    
    def save_image(self, image: np.ndarray, output_path: str) -> bool:
        """
        Save image to file
        
        Args:
            image: Image to save
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if not exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(output_path, image)
            self.logger.info(f"Image saved to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            return False
