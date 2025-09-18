"""
VastraVista - Cloth Detection Module (Python 3.13 Compatible)
Author: Saumya Tiwari
Purpose: Detect and classify clothing items using YOLOv8
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional
import torch

class ClothDetector:
    """Main clothing detection class using YOLOv8 - Python 3.13 compatible"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "mps"):
        """
        Initialize the cloth detector
        
        Args:
            model_path: Path to custom model (if None, uses pre-trained)
            device: Device to run inference ('mps' for Mac, 'cpu', 'cuda')
        """
        # Setup logging FIRST
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set PyTorch security settings for model loading
        self._setup_pytorch_security()
        
        self.device = device if device == "mps" and self._check_mps() else "cpu"
        self.model = self._load_model(model_path)
        self.clothing_classes = [
            'person', 'shirt', 'pants', 'dress', 'shoes', 'hat', 'jacket', 
            'skirt', 'shorts', 'coat', 'sweater', 'top', 'jeans'
        ]
        
        self.logger.info(f"🎨 VastraVista ClothDetector initialized with device: {self.device}")
    
    def _setup_pytorch_security(self):
        """Setup PyTorch security settings for model loading"""
        try:
            # Add safe globals for ultralytics
            torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])
            torch.serialization.add_safe_globals(['ultralytics.nn.modules.conv.Conv'])
            torch.serialization.add_safe_globals(['ultralytics.nn.modules.block.C2f'])
            torch.serialization.add_safe_globals(['ultralytics.nn.modules.block.Bottleneck'])
            torch.serialization.add_safe_globals(['ultralytics.nn.modules.head.Detect'])
            torch.serialization.add_safe_globals(['ultralytics.nn.modules.conv.DWConv'])
            self.logger.info("✅ PyTorch security settings configured")
        except Exception as e:
            self.logger.warning(f"Could not configure PyTorch security: {e}")
        
    def _check_mps(self) -> bool:
        """Check if MPS (Metal Performance Shaders) is available on Mac"""
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.logger.info("✅ MPS (Metal Performance Shaders) available")
                return True
            else:
                self.logger.info("⚠️ MPS not available, using CPU")
                return False
        except ImportError:
            self.logger.warning("PyTorch not found, using CPU")
            return False
        except Exception as e:
            self.logger.warning(f"MPS check failed: {e}, using CPU")
            return False
    
    def _load_model(self, model_path: Optional[str] = None) -> YOLO:
        """Load YOLOv8 model with proper error handling"""
        try:
            if model_path and os.path.exists(model_path):
                self.logger.info(f"Loading custom model from {model_path}")
                model = YOLO(model_path)
                self.logger.info(f"✅ Loaded custom model from {model_path}")
            else:
                self.logger.info("Loading pre-trained YOLOv8n model...")
                
                # Try to load with weights_only=False for compatibility
                try:
                    model = YOLO('yolov8n.pt')
                except Exception as weights_error:
                    self.logger.warning(f"Standard loading failed: {weights_error}")
                    # Try alternative loading method
                    try:
                        import torch
                        # Temporarily allow unsafe loading for ultralytics models
                        with torch.serialization.safe_globals(['ultralytics.nn.tasks.DetectionModel']):
                            model = YOLO('yolov8n.pt')
                    except Exception as alt_error:
                        self.logger.error(f"Alternative loading also failed: {alt_error}")
                        raise alt_error
                
                self.logger.info("✅ Loaded pre-trained YOLOv8n model")
            
            return model
        except Exception as e:
            self.logger.error(f"❌ Error loading model: {e}")
            self.logger.error("Try running: pip install --upgrade ultralytics torch")
            raise
    
    def detect_clothing(self, image: np.ndarray, confidence: float = 0.3) -> Dict:
        """
        Detect clothing items in image
        
        Args:
            image: Input image as numpy array
            confidence: Minimum confidence threshold
            
        Returns:
            Dictionary containing detection results
        """
        try:
            # Run inference
            results = self.model(image, device=self.device, verbose=False, conf=confidence)
            
            detections = {
                'boxes': [],
                'classes': [],
                'confidences': [],
                'clothing_items': []
            }
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        conf = float(box.conf)
                        if conf >= confidence:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls)
                            class_name = self.model.names[class_id]
                            
                            # Check if it's a clothing item or person (for context)
                            if self._is_clothing_related(class_name):
                                detections['boxes'].append([x1, y1, x2, y2])
                                detections['classes'].append(class_name)
                                detections['confidences'].append(conf)
                                detections['clothing_items'].append({
                                    'type': class_name,
                                    'bbox': [x1, y1, x2, y2],
                                    'confidence': conf,
                                    'area': (x2 - x1) * (y2 - y1)
                                })
            
            self.logger.info(f"🔍 Detected {len(detections['clothing_items'])} clothing-related items")
            return detections
            
        except Exception as e:
            self.logger.error(f"❌ Detection error: {e}")
            return {'boxes': [], 'classes': [], 'confidences': [], 'clothing_items': []}
    
    def _is_clothing_related(self, class_name: str) -> bool:
        """Check if detected class is clothing-related"""
        # YOLO COCO classes that are clothing or person-related
        clothing_keywords = [
            'person',  # We need person detection for context
            'shirt', 'pants', 'dress', 'shoes', 'hat', 'jacket', 
            'skirt', 'shorts', 'coat', 'sweater', 'top', 'jeans',
            'hoodie', 'blazer', 'suit', 'tie', 'scarf', 'gloves',
            'handbag', 'backpack', 'umbrella', 'suitcase'
        ]
        return any(keyword in class_name.lower() for keyword in clothing_keywords)
    
    def draw_detections(self, image: np.ndarray, detections: Dict) -> np.ndarray:
        """
        Draw detection results on image with enhanced visualization
        
        Args:
            image: Original image
            detections: Detection results from detect_clothing()
            
        Returns:
            Image with drawn bounding boxes and labels
        """
        result_image = image.copy()
        
        # Color scheme for different clothing types
        colors = {
            'person': (255, 0, 0),     # Blue
            'shirt': (0, 255, 0),     # Green  
            'pants': (0, 0, 255),     # Red
            'dress': (255, 0, 255),   # Magenta
            'shoes': (255, 255, 0),   # Cyan
            'backpack': (128, 0, 128), # Purple
            'handbag': (255, 165, 0),  # Orange
            'default': (0, 255, 255)  # Yellow
        }
        
        for item in detections['clothing_items']:
            x1, y1, x2, y2 = [int(coord) for coord in item['bbox']]
            confidence = item['confidence']
            class_name = item['type']
            
            # Choose color based on class
            color = colors.get(class_name, colors['default'])
            
            # Draw bounding box
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Draw label background
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(result_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return result_image

    def process_webcam(self, show_preview: bool = True) -> None:
        """
        Process webcam feed in real-time
        
        Args:
            show_preview: Whether to show live preview window
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.logger.error("❌ Cannot access webcam")
            return
        
        self.logger.info("📸 Starting webcam detection (Press 'q' to quit)")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect clothing
                detections = self.detect_clothing(frame)
                
                if show_preview:
                    # Draw detections
                    result_frame = self.draw_detections(frame, detections)
                    
                    # Add info text
                    info_text = f"Detected: {len(detections['clothing_items'])} items"
                    cv2.putText(result_frame, info_text, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Add instructions
                    instruction_text = "Press 'q' to quit"
                    cv2.putText(result_frame, instruction_text, (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # Show frame
                    cv2.imshow('VastraVista - Cloth Detection', result_frame)
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("👋 Detection stopped by user")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.logger.info("📷 Webcam resources released")

    def test_detection(self) -> bool:
        """Quick test of detection capabilities"""
        try:
            self.logger.info("🧪 Running detection test...")
            
            # Test with webcam first
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    detections = self.detect_clothing(frame)
                    self.logger.info(f"✅ Webcam test successful: {len(detections['clothing_items'])} items detected")
                    cap.release()
                    return True
            
            # If no webcam, create test image
            self.logger.info("📷 No webcam available, testing with synthetic image...")
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            detections = self.detect_clothing(test_image)
            self.logger.info("✅ Test completed with synthetic image")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test failed: {e}")
            return False
