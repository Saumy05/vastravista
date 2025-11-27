"""
VastraVista OpenCV - Standalone Desktop Application
Pure OpenCV interface with keyboard controls - No Streamlit required
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, Tuple
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import VastraVista services
from app.services.half_body_ar_engine import HalfBodyAREngine
from app.services.clothing_overlay import ClothingOverlay
from app.models.skin_tone_detector import SkinToneDetector
from app.models.gender_detector import GenderDetector
from app.models.age_detector import AgeDetector
from app.services.recommendation_engine import FashionRecommendationEngine
from app.services.ai_stylist import AIStyler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clothing categories
CLOTHING_CATEGORIES = {
    1: {'name': 'T-Shirt', 'type': 'tshirt', 'color': (100, 150, 200)},
    2: {'name': 'Shirt', 'type': 'shirt', 'color': (80, 120, 180)},
    3: {'name': 'Kurta', 'type': 'kurta', 'color': (150, 100, 50)},
    4: {'name': 'Dress', 'type': 'dress', 'color': (200, 100, 150)},
    5: {'name': 'Hoodie', 'type': 'hoodie', 'color': (60, 60, 60)},
    6: {'name': 'Jacket', 'type': 'jacket', 'color': (40, 40, 100)}
}


class VastraVistaOpenCV:
    """OpenCV-based desktop application"""
    
    def __init__(self):
        """Initialize application"""
        logger.info("🚀 Initializing VastraVista OpenCV...")
        
        # Initialize services
        self.half_body_engine = HalfBodyAREngine()
        self.clothing_overlay = ClothingOverlay()
        self.skin_detector = SkinToneDetector()
        self.gender_detector = GenderDetector()
        self.age_detector = AgeDetector()
        self.recommendation_engine = FashionRecommendationEngine()
        self.ai_stylist = AIStyler()
        
        # State
        self.current_outfit = 1
        self.camera = None
        self.show_keypoints = False
        self.show_info = True
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.pose_confidence = 0.0
        self.last_analysis = None
        
        logger.info("✅ VastraVista OpenCV initialized")
    
    def initialize_camera(self, camera_index: int = 0):
        """Initialize webcam"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception(f"Could not open camera {camera_index}")
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info(f"✅ Camera {camera_index} initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Process frame with AR overlay"""
        try:
            # Detect pose
            pose_data = self.half_body_engine.detect_half_body_pose(frame)
            
            if pose_data.get('success', False):
                self.pose_confidence = pose_data.get('confidence', 0.0)
                
                # Get outfit info
                outfit_info = CLOTHING_CATEGORIES.get(self.current_outfit, CLOTHING_CATEGORIES[1])
                outfit_type = outfit_info['type']
                outfit_color = outfit_info['color']
                
                # Apply overlay
                result_frame, overlay_status = self.clothing_overlay.apply_clothing_overlay(
                    frame,
                    outfit_type,
                    outfit_color,
                    pose_data
                )
                
                # Draw keypoints if enabled
                if self.show_keypoints:
                    result_frame = self._draw_keypoints(result_frame, pose_data)
                
                metadata = {
                    'pose_detected': True,
                    'confidence': self.pose_confidence,
                    'outfit_type': outfit_type
                }
            else:
                result_frame = frame.copy()
                self.pose_confidence = 0.0
                metadata = {'pose_detected': False, 'confidence': 0.0}
            
            # Update FPS
            self._update_fps()
            metadata['fps'] = self.current_fps
            
            return result_frame, metadata
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return frame, {'error': str(e)}
    
    def _draw_keypoints(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """Draw pose keypoints"""
        result = frame.copy()
        landmarks = pose_data.get('landmarks', {})
        
        # Draw shoulders
        for key in ['left_shoulder', 'right_shoulder']:
            if key in landmarks:
                pt = landmarks[key]
                cv2.circle(result, (int(pt[0]), int(pt[1])), 8, (0, 255, 0), -1)
        
        # Draw connection
        if 'left_shoulder' in landmarks and 'right_shoulder' in landmarks:
            pt1 = landmarks['left_shoulder']
            pt2 = landmarks['right_shoulder']
            cv2.line(result, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), (0, 255, 0), 2)
        
        return result
    
    def _draw_info_overlay(self, frame: np.ndarray, metadata: Dict):
        """Draw information overlay on frame"""
        h, w = frame.shape[:2]
        
        # Background panel
        panel_height = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # FPS
        fps_text = f"FPS: {metadata.get('fps', 0):.1f}"
        cv2.putText(frame, fps_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Confidence
        conf = metadata.get('confidence', 0.0)
        conf_color = (0, 255, 0) if conf >= 0.7 else (0, 165, 255) if conf >= 0.5 else (0, 0, 255)
        conf_text = f"Pose Confidence: {conf*100:.0f}%"
        cv2.putText(frame, conf_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, conf_color, 2)
        
        # Current outfit
        outfit_name = CLOTHING_CATEGORIES[self.current_outfit]['name']
        outfit_text = f"Outfit: {outfit_name} (Press 1-6 to change)"
        cv2.putText(frame, outfit_text, (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Instructions
        inst_text = "Controls: 1-6=Outfit | A=Analyze | K=Keypoints | I=Info | Q=Quit"
        cv2.putText(frame, inst_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()
    
    def analyze_user(self, frame: np.ndarray) -> Dict:
        """Analyze user from frame"""
        try:
            logger.info("🔬 Starting user analysis...")
            
            # Detect face and skin
            face_data = self.skin_detector.detect_face_and_skin(frame)
            
            if face_data['faces_detected'] > 0 and face_data['skin_regions']:
                skin_mask = face_data['skin_regions'][0]
                skin_color_data = self.skin_detector.get_average_skin_color(frame, skin_mask)
                
                if 'rgb' in skin_color_data:
                    skin_rgb = tuple(skin_color_data['rgb'])
                    
                    # Detect gender and age
                    gender_result = self.gender_detector.detect_gender(frame)
                    age_result = self.age_detector.detect_age(frame)
                    
                    # Generate recommendations
                    gender = gender_result.get('gender', 'Male')
                    age_group = age_result.get('age_group', 'Young Adult')
                    
                    recommendations = self.recommendation_engine.generate_recommendations(
                        gender,
                        age_group,
                        skin_rgb,
                        skin_color_data.get('undertone')
                    )
                    
                    analysis = {
                        'skin_tone': skin_color_data,
                        'gender': gender_result,
                        'age': age_result,
                        'recommendations': recommendations
                    }
                    
                    self.last_analysis = analysis
                    logger.info("✅ Analysis complete")
                    return analysis
            
            logger.warning("⚠️ No face detected for analysis")
            return {'error': 'No face detected'}
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'error': str(e)}
    
    def print_analysis(self, analysis: Dict):
        """Print analysis results to console"""
        print("\n" + "="*60)
        print("🎨 VASTRAVISTA - USER ANALYSIS RESULTS")
        print("="*60)
        
        if 'skin_tone' in analysis:
            skin = analysis['skin_tone']
            print(f"\n👤 SKIN TONE:")
            print(f"   RGB: {skin.get('rgb', 'N/A')}")
            print(f"   Hex: {skin.get('hex', 'N/A')}")
            if 'monk_scale' in skin:
                print(f"   Monk Scale: {skin['monk_scale'].get('monk_level', 'N/A')}")
        
        if 'gender' in analysis:
            print(f"\n👔 GENDER: {analysis['gender'].get('gender', 'Unknown')}")
        
        if 'age' in analysis:
            age = analysis['age']
            print(f"\n🎂 AGE: {age.get('estimated_age', 'Unknown')} years ({age.get('age_group', 'Unknown')})")
        
        if 'recommendations' in analysis:
            recs = analysis['recommendations']
            print(f"\n🎨 BEST COLORS:")
            if 'color_analysis' in recs:
                excellent = recs['color_analysis'].get('excellent_colors', [])
                for i, color in enumerate(excellent[:5], 1):
                    print(f"   {i}. {color.get('name', 'Unknown')} ({color.get('hex', '#000')})")
            
            if 'style_tips' in recs:
                print(f"\n💡 STYLE TIPS:")
                for tip in recs['style_tips'][:5]:
                    print(f"   • {tip}")
        
        print("\n" + "="*60 + "\n")
    
    def run(self):
        """Main application loop"""
        logger.info("🎬 Starting VastraVista OpenCV application...")
        
        # Initialize camera
        if not self.initialize_camera():
            logger.error("Failed to initialize camera. Exiting.")
            return
        
        window_name = "VastraVista Desktop - AR Fashion Try-On"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        
        print("\n" + "="*60)
        print("👗 VASTRAVISTA DESKTOP - AR FASHION TRY-ON")
        print("="*60)
        print("\n⌨️  KEYBOARD CONTROLS:")
        print("   1-6: Switch outfit categories")
        print("   A: Analyze user (skin tone, gender, age)")
        print("   K: Toggle pose keypoints display")
        print("   I: Toggle info overlay")
        print("   Q/ESC: Quit application")
        print("\n" + "="*60 + "\n")
        
        try:
            while True:
                ret, frame = self.camera.read()
                
                if not ret:
                    logger.error("Failed to read frame")
                    break
                
                # Process frame
                processed_frame, metadata = self.process_frame(frame)
                
                # Draw info overlay
                if self.show_info:
                    processed_frame = self._draw_info_overlay(processed_frame, metadata)
                
                # Display frame
                cv2.imshow(window_name, processed_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:  # Q or ESC
                    logger.info("Quit requested")
                    break
                
                elif key >= ord('1') and key <= ord('6'):
                    outfit_num = key - ord('0')
                    self.current_outfit = outfit_num
                    outfit_name = CLOTHING_CATEGORIES[outfit_num]['name']
                    logger.info(f"Switched to outfit: {outfit_name}")
                    print(f"✅ Switched to: {outfit_name}")
                
                elif key == ord('a') or key == ord('A'):
                    logger.info("User analysis requested")
                    print("\n🔬 Analyzing user...")
                    analysis = self.analyze_user(frame)
                    if 'error' not in analysis:
                        self.print_analysis(analysis)
                    else:
                        print(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
                
                elif key == ord('k') or key == ord('K'):
                    self.show_keypoints = not self.show_keypoints
                    status = "ON" if self.show_keypoints else "OFF"
                    logger.info(f"Keypoints display: {status}")
                    print(f"✅ Keypoints display: {status}")
                
                elif key == ord('i') or key == ord('I'):
                    self.show_info = not self.show_info
                    status = "ON" if self.show_info else "OFF"
                    logger.info(f"Info overlay: {status}")
                    print(f"✅ Info overlay: {status}")
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
        finally:
            # Cleanup
            self.camera.release()
            cv2.destroyAllWindows()
            if self.half_body_engine:
                self.half_body_engine.cleanup()
            logger.info("🧹 Application closed")


def main():
    """Entry point"""
    app = VastraVistaOpenCV()
    app.run()


if __name__ == "__main__":
    main()

