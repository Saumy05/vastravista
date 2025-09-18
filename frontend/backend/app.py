"""
VastraVista Web API - Uses existing VastraVista modules
Author: Saumya Tiwari
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import numpy as np
import cv2
import base64
import io
from PIL import Image
from datetime import datetime

# Add your existing src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import YOUR existing modules (no changes needed)
try:
    from cloth_detection.detector import ClothDetector
    from color_extraction.color_analyzer_with_storage import ColorAnalyzerWithStorage
    from skin_tone_analysis.skin_detector_simple import SkinDetector
    from wardrobe_database.database import VastraVistaDatabase
    
    print("✅ Successfully imported your existing VastraVista modules!")
    
    # Initialize using your existing modules
    cloth_detector = ClothDetector(device="cpu")
    color_analyzer = ColorAnalyzerWithStorage(n_colors=5)
    skin_analyzer = SkinDetector()
    database = VastraVistaDatabase()
    
    print("✅ All modules initialized - ready for web interface!")
    
except ImportError as e:
    print(f"❌ Module import error: {e}")
    cloth_detector = color_analyzer = skin_analyzer = database = None

app = Flask(__name__)
CORS(app)

def base64_to_opencv(base64_string):
    """Convert base64 to OpenCV image"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        img_data = base64.b64decode(base64_string)
        img = Image.open(io.BytesIO(img_data))
        opencv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return opencv_image
    except Exception as e:
        print(f"Image conversion error: {e}")
        return None

def analyze_skin_complete(rgb_values):
    """Use your existing skin analysis logic"""
    r, g, b = rgb_values
    brightness = (r + g + b) / 3 / 255.0
    
    if brightness > 0.6:
        tone, emoji = "Light", "☀️"
    elif brightness > 0.3:
        tone, emoji = "Medium", "🌤️"  
    else:
        tone, emoji = "Dark", "🌙"
    
    red_ratio = r / (r + g + b + 1)
    blue_ratio = b / (r + g + b + 1)
    
    if red_ratio > blue_ratio + 0.02:
        undertone, u_emoji = "Warm", "🌅"
        recs = ["Coral", "Peach", "Golden Yellow"]
        avoid = ["Icy Blue", "Pure White"]
        tip = "Gold jewelry complements your warm undertones!"
    elif blue_ratio > red_ratio + 0.02:
        undertone, u_emoji = "Cool", "❄️"
        recs = ["Navy", "Royal Blue", "Emerald"]
        avoid = ["Orange", "Yellow"]
        tip = "Silver jewelry enhances your cool undertones!"
    else:
        undertone, u_emoji = "Neutral", "⚖️"
        recs = ["Dusty Blue", "Sage Green", "Soft Pink"]
        avoid = ["Neon Colors"]
        tip = "Both gold and silver work well for you!"
    
    return {
        'brightness': tone,
        'brightness_emoji': emoji,
        'undertone': undertone,
        'undertone_emoji': u_emoji,
        'recommendations': recs,
        'avoid': avoid,
        'styling_tip': tip,
        'rgb': rgb_values
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'modules': {
            'cloth_detector': cloth_detector is not None,
            'color_analyzer': color_analyzer is not None,
            'skin_analyzer': skin_analyzer is not None,
            'database': database is not None
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def web_analyze():
    """Web analysis endpoint - uses your existing pipeline"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Convert image
        image = base64_to_opencv(data['image'])
        if image is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        results = {'timestamp': datetime.now().isoformat()}
        
        # Use YOUR existing cloth detection
        if cloth_detector:
            cloth_results = cloth_detector.detect_clothing(image, confidence=0.3)
            results['cloth_detection'] = cloth_results
            
            # Use YOUR existing color analysis
            if color_analyzer and cloth_results['clothing_items']:
                color_results = color_analyzer.analyze_clothing_colors(image, cloth_results)
                results['color_analysis'] = color_results
        
        # Use YOUR existing skin analysis
        if skin_analyzer:
            face_data = skin_analyzer.detect_face_and_skin(image)
            
            if face_data['faces_detected'] > 0:
                face_bbox = face_data['face_regions'][0]
                skin_region = face_data['skin_regions'][0] if face_data['skin_regions'] else None
                
                if skin_region is not None:
                    x1, y1, x2, y2 = face_bbox
                    face_image = image[y1:y2, x1:x2]
                    skin_color = skin_analyzer.get_average_skin_color(face_image, skin_region)
                    
                    if 'error' not in skin_color:
                        skin_analysis = analyze_skin_complete(skin_color['rgb'])
                        skin_analysis['skin_color'] = skin_color
                        results['skin_analysis'] = skin_analysis
        
        # Use YOUR existing database
        if database:
            try:
                session_id = database.create_session(
                    description="Web App Analysis", 
                    metadata=results
                )
                results['session_id'] = session_id
            except Exception as e:
                print(f"Database save error: {e}")
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics using your existing database"""
    try:
        if database:
            summary = database.get_wardrobe_summary()
            return jsonify(summary)
        else:
            return jsonify({'error': 'Database not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 VastraVista Web API Starting...")
    print("🔗 Using your existing AI modules from src/")
    print("📡 API will be available at http://localhost:5001")  # Changed to 5001
    
    app.run(debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
EOF