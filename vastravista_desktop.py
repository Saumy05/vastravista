"""
VastraVista Desktop - Fully Python AR Fashion Try-On Application
Single-process desktop application with live webcam, AR try-on, and AI chatbot
"""

import cv2
import numpy as np
import streamlit as st
import time
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys
import os

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import VastraVista services
from app.services.half_body_ar_engine import HalfBodyAREngine
from app.services.clothing_overlay import ClothingOverlay
from app.services.ar_pose_detector import ARPoseDetector
from app.models.skin_tone_detector import SkinToneDetector
from app.models.gender_detector import GenderDetector
from app.models.age_detector import AgeDetector
from app.services.recommendation_engine import FashionRecommendationEngine
from app.services.ai_stylist import AIStyler
from app.services.color_analyzer import ColorAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clothing categories mapping
CLOTHING_CATEGORIES = {
    1: {'name': 'T-Shirt', 'type': 'tshirt', 'color': (100, 150, 200)},
    2: {'name': 'Shirt', 'type': 'shirt', 'color': (80, 120, 180)},
    3: {'name': 'Kurta', 'type': 'kurta', 'color': (150, 100, 50)},
    4: {'name': 'Dress', 'type': 'dress', 'color': (200, 100, 150)},
    5: {'name': 'Hoodie', 'type': 'hoodie', 'color': (60, 60, 60)},
    6: {'name': 'Jacket', 'type': 'jacket', 'color': (40, 40, 100)}
}


class VastraVistaDesktop:
    """Main desktop application class"""
    
    def __init__(self):
        """Initialize all components"""
        logger.info("🚀 Initializing VastraVista Desktop...")
        
        # Initialize services
        self.half_body_engine = HalfBodyAREngine()
        self.clothing_overlay = ClothingOverlay()
        self.pose_detector = ARPoseDetector()
        self.skin_detector = SkinToneDetector()
        self.gender_detector = GenderDetector()
        self.age_detector = AgeDetector()
        self.recommendation_engine = FashionRecommendationEngine()
        self.ai_stylist = AIStyler()
        self.color_analyzer = ColorAnalyzer()
        
        # State variables
        self.current_outfit = 1  # 1-6
        self.camera = None
        self.is_running = False
        self.last_frame = None
        self.last_pose_data = None
        self.last_skin_data = None
        self.last_recommendations = None
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.pose_confidence = 0.0
        
        # Chatbot state
        self.chat_history = []
        
        logger.info("✅ VastraVista Desktop initialized")
    
    def initialize_camera(self, camera_index: int = 0):
        """Initialize webcam"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception(f"Could not open camera {camera_index}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info(f"✅ Camera {camera_index} initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            return False
    
    def release_camera(self):
        """Release camera resources"""
        if self.camera:
            self.camera.release()
            self.camera = None
            logger.info("📷 Camera released")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame: detect pose, apply AR overlay, calculate metrics
        
        Returns:
            Tuple of (processed_frame, metadata_dict)
        """
        try:
            # Detect pose
            pose_data = self.half_body_engine.detect_half_body_pose(frame)
            
            if pose_data.get('success', False):
                self.pose_confidence = pose_data.get('confidence', 0.0)
                self.last_pose_data = pose_data
                
                # Get current outfit category
                outfit_info = CLOTHING_CATEGORIES.get(self.current_outfit, CLOTHING_CATEGORIES[1])
                outfit_type = outfit_info['type']
                outfit_color = outfit_info['color']
                
                # Apply clothing overlay
                result_frame, overlay_status = self.clothing_overlay.apply_clothing_overlay(
                    frame,
                    outfit_type,
                    outfit_color,
                    pose_data
                )
                
                # Draw pose keypoints (optional, for debugging)
                if st.session_state.get('show_keypoints', False):
                    result_frame = self._draw_keypoints(result_frame, pose_data)
                
                # Draw confidence indicator
                result_frame = self._draw_confidence_indicator(result_frame, self.pose_confidence)
                
                metadata = {
                    'pose_detected': True,
                    'confidence': self.pose_confidence,
                    'outfit_type': outfit_type,
                    'overlay_success': overlay_status.get('success', False)
                }
            else:
                # No pose detected
                result_frame = frame.copy()
                self.pose_confidence = 0.0
                metadata = {
                    'pose_detected': False,
                    'confidence': 0.0,
                    'error': pose_data.get('error', 'No pose detected')
                }
            
            # Update FPS
            self._update_fps()
            metadata['fps'] = self.current_fps
            
            return result_frame, metadata
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}", exc_info=True)
            return frame, {'error': str(e)}
    
    def _draw_keypoints(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """Draw pose keypoints on frame"""
        result = frame.copy()
        landmarks = pose_data.get('landmarks', {})
        
        # Draw shoulders
        if 'left_shoulder' in landmarks:
            pt = landmarks['left_shoulder']
            cv2.circle(result, (int(pt[0]), int(pt[1])), 5, (0, 255, 0), -1)
        
        if 'right_shoulder' in landmarks:
            pt = landmarks['right_shoulder']
            cv2.circle(result, (int(pt[0]), int(pt[1])), 5, (0, 255, 0), -1)
        
        # Draw connection line
        if 'left_shoulder' in landmarks and 'right_shoulder' in landmarks:
            pt1 = landmarks['left_shoulder']
            pt2 = landmarks['right_shoulder']
            cv2.line(result, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), (0, 255, 0), 2)
        
        return result
    
    def _draw_confidence_indicator(self, frame: np.ndarray, confidence: float) -> np.ndarray:
        """Draw confidence score on frame"""
        result = frame.copy()
        h, w = frame.shape[:2]
        
        # Color based on confidence
        if confidence >= 0.7:
            color = (0, 255, 0)  # Green
        elif confidence >= 0.5:
            color = (0, 165, 255)  # Orange
        else:
            color = (0, 0, 255)  # Red
        
        # Draw confidence bar
        bar_width = int(w * 0.3)
        bar_height = 20
        bar_x = 10
        bar_y = 10
        
        # Background
        cv2.rectangle(result, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Confidence fill
        fill_width = int(bar_width * confidence)
        cv2.rectangle(result, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), color, -1)
        
        # Text
        conf_text = f"Pose: {confidence*100:.0f}%"
        cv2.putText(result, conf_text, (bar_x + 5, bar_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()
    
    def analyze_user(self, frame: np.ndarray) -> Dict:
        """
        Analyze user from frame: skin tone, gender, age
        
        Returns:
            Analysis dictionary
        """
        try:
            analysis = {}
            
            # Detect face and skin tone
            face_data = self.skin_detector.detect_face_and_skin(frame)
            
            if face_data['faces_detected'] > 0 and face_data['skin_regions']:
                # Get average skin color
                skin_mask = face_data['skin_regions'][0]
                skin_color_data = self.skin_detector.get_average_skin_color(frame, skin_mask)
                
                if 'rgb' in skin_color_data:
                    skin_rgb = tuple(skin_color_data['rgb'])
                    analysis['skin_tone'] = skin_color_data
                    
                    # Detect gender
                    try:
                        gender_result = self.gender_detector.detect_gender(frame)
                        analysis['gender'] = gender_result
                    except Exception as e:
                        logger.warning(f"Gender detection failed: {e}")
                        analysis['gender'] = {'gender': 'Unknown'}
                    
                    # Detect age
                    try:
                        age_result = self.age_detector.detect_age(frame)
                        analysis['age'] = age_result
                    except Exception as e:
                        logger.warning(f"Age detection failed: {e}")
                        analysis['age'] = {'age_group': 'Young Adult'}
                    
                    # Generate recommendations
                    try:
                        gender = analysis['gender'].get('gender', 'Male')
                        age_group = analysis['age'].get('age_group', 'Young Adult')
                        
                        recommendations = self.recommendation_engine.generate_recommendations(
                            gender,
                            age_group,
                            skin_rgb,
                            skin_color_data.get('undertone')
                        )
                        analysis['recommendations'] = recommendations
                        self.last_recommendations = recommendations
                    except Exception as e:
                        logger.warning(f"Recommendation generation failed: {e}")
            
            self.last_skin_data = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"User analysis error: {e}", exc_info=True)
            return {'error': str(e)}
    
    def get_chatbot_response(self, user_message: str, context: Dict = None) -> str:
        """
        Get chatbot response using LLaMA/Ollama
        
        Args:
            user_message: User's message
            context: Optional context (skin tone, gender, etc.)
        
        Returns:
            Bot response
        """
        try:
            if not self.ai_stylist.use_ai:
                # Fallback to template responses
                return self._get_template_response(user_message, context)
            
            # Use AI stylist for fashion advice
            import requests
            
            # Build context-aware prompt
            prompt = f"""You are a friendly fashion stylist chatbot. The user asks: "{user_message}"
            
"""
            
            if context:
                skin_info = context.get('skin_tone', {})
                gender = context.get('gender', {}).get('gender', 'Person')
                age_group = context.get('age', {}).get('age_group', 'Adult')
                
                if skin_info:
                    monk_level = skin_info.get('monk_scale', {}).get('monk_level', 'medium')
                    colors = context.get('recommendations', {}).get('color_analysis', {}).get('excellent_colors', [])
                    color_names = [c.get('name', '') for c in colors[:3]]
                    
                    prompt += f"""User Profile:
- Gender: {gender}
- Age Group: {age_group}
- Skin Tone: {monk_level}
- Best Colors: {', '.join(color_names) if color_names else 'Various'}

"""
            
            prompt += """Give a helpful, friendly fashion advice response. Keep it concise (2-3 sentences)."""
            
            # Call Ollama
            payload = {
                "model": self.ai_stylist.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            }
            
            response = self.ai_stylist._call_generate(payload, timeout=30, retries=1)
            
            if response and response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '').strip()
                return ai_text if ai_text else self._get_template_response(user_message, context)
            else:
                return self._get_template_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return self._get_template_response(user_message, context)
    
    def _get_template_response(self, user_message: str, context: Dict = None) -> str:
        """Fallback template responses"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['color', 'colour', 'what color']):
            return "Based on your skin tone analysis, I recommend colors that complement your complexion. Try navy blue, burgundy, or emerald green for best results!"
        
        elif any(word in message_lower for word in ['outfit', 'wear', 'what to wear']):
            return "For a great outfit, start with your best colors and build from there. A well-fitted piece in your top color will make you look confident and polished!"
        
        elif any(word in message_lower for word in ['style', 'fashion', 'tips']):
            return "Fashion is about confidence! Choose pieces that fit well and colors that make you feel great. Your best colors will enhance your natural features."
        
        else:
            return "I'm here to help with fashion advice! Ask me about colors, outfits, or styling tips based on your analysis."
    
    def cleanup(self):
        """Clean up all resources"""
        self.release_camera()
        if self.half_body_engine:
            self.half_body_engine.cleanup()
        if self.pose_detector:
            self.pose_detector.cleanup()
        if self.skin_detector:
            self.skin_detector.cleanup()
        logger.info("🧹 Cleanup complete")


# Streamlit UI
def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="VastraVista Desktop",
        page_icon="👗",
        layout="wide"
    )
    
    # Initialize session state
    if 'app' not in st.session_state:
        st.session_state.app = VastraVistaDesktop()
        st.session_state.app.initialize_camera()
        st.session_state.is_running = False
        st.session_state.show_keypoints = False
        st.session_state.current_outfit = 1
    
    app = st.session_state.app
    
    # Title
    st.title("👗 VastraVista Desktop - AR Fashion Try-On")
    st.markdown("**Fully Python-based AR Try-On with Live Webcam & AI Chatbot**")
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Camera controls
        st.subheader("📷 Camera")
        if st.button("▶️ Start Camera" if not st.session_state.is_running else "⏸️ Stop Camera"):
            st.session_state.is_running = not st.session_state.is_running
        
        # Outfit selection
        st.subheader("👔 Outfit Selection")
        outfit_names = [f"{i}. {CLOTHING_CATEGORIES[i]['name']}" for i in range(1, 7)]
        selected_outfit = st.selectbox(
            "Choose Outfit",
            options=range(1, 7),
            format_func=lambda x: CLOTHING_CATEGORIES[x]['name'],
            index=st.session_state.current_outfit - 1
        )
        st.session_state.current_outfit = selected_outfit
        app.current_outfit = selected_outfit
        
        # Display keyboard shortcuts
        st.subheader("⌨️ Keyboard Shortcuts")
        st.markdown("""
        - **1-6**: Switch outfit categories
        - **A**: Analyze user (skin tone, gender, age)
        - **K**: Toggle keypoints display
        - **Q/ESC**: Quit
        """)
        
        # Settings
        st.subheader("⚙️ Settings")
        st.session_state.show_keypoints = st.checkbox("Show Pose Keypoints", value=st.session_state.show_keypoints)
        
        # Analysis button
        st.subheader("🔍 Analysis")
        if st.button("🔬 Analyze User"):
            if app.last_frame is not None:
                with st.spinner("Analyzing..."):
                    analysis = app.analyze_user(app.last_frame)
                    st.session_state.last_analysis = analysis
                    st.success("Analysis complete!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Live Camera Feed")
        
        # Video frame placeholder
        video_placeholder = st.empty()
        
        # Status info
        status_placeholder = st.empty()
        
        # Run camera loop
        if st.session_state.is_running:
            ret, frame = app.camera.read()
            
            if ret:
                # Process frame
                app.last_frame = frame.copy()
                processed_frame, metadata = app.process_frame(frame)
                
                # Convert BGR to RGB for Streamlit
                display_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # Display frame
                video_placeholder.image(display_frame, channels="RGB", use_container_width=True)
                
                # Display status
                with status_placeholder.container():
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("FPS", f"{metadata.get('fps', 0):.1f}")
                    with col_b:
                        conf = metadata.get('confidence', 0.0)
                        st.metric("Pose Confidence", f"{conf*100:.0f}%")
                    with col_c:
                        outfit_name = CLOTHING_CATEGORIES[app.current_outfit]['name']
                        st.metric("Current Outfit", outfit_name)
            else:
                st.error("Failed to read from camera")
                st.session_state.is_running = False
        else:
            # Show placeholder when camera is off
            placeholder_img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder_img, "Camera Off - Click Start Camera", 
                       (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            video_placeholder.image(placeholder_img, channels="BGR", use_container_width=True)
        
        # Auto-refresh when camera is running
        if st.session_state.is_running:
            time.sleep(0.03)  # ~30 FPS
            st.rerun()
    
    with col2:
        st.subheader("💬 Fashion Chatbot")
        
        # Chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.get('chat_history', []):
                if msg['role'] == 'user':
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**VastraVista:** {msg['content']}")
        
        # Chat input
        user_input = st.text_input("Ask me about fashion, colors, or styling!", key="chat_input")
        
        if st.button("Send") and user_input:
            # Add user message to history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Get context from last analysis
            context = st.session_state.get('last_analysis', {})
            
            # Get bot response
            with st.spinner("Thinking..."):
                bot_response = app.get_chatbot_response(user_input, context)
            
            st.session_state.chat_history.append({'role': 'assistant', 'content': bot_response})
            
            # Rerun to update chat display
            st.rerun()
        
        # Recommendations display
        if 'last_analysis' in st.session_state:
            st.subheader("🎨 Recommendations")
            analysis = st.session_state.last_analysis
            
            if 'recommendations' in analysis:
                recs = analysis['recommendations']
                
                # Best colors
                if 'color_analysis' in recs:
                    st.markdown("**Best Colors:**")
                    excellent = recs['color_analysis'].get('excellent_colors', [])
                    for color in excellent[:5]:
                        st.markdown(f"- {color.get('name', 'Unknown')} ({color.get('hex', '#000')})")
                
                # Style tips
                if 'style_tips' in recs:
                    st.markdown("**Style Tips:**")
                    for tip in recs['style_tips'][:3]:
                        st.markdown(f"- {tip}")
    
    # Cleanup on exit
    if st.button("🚪 Exit Application"):
        app.cleanup()
        st.stop()


if __name__ == "__main__":
    main()

