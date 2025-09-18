#!/usr/bin/env python3
"""
Standalone Skin Tone Analysis Demo - Works with your current setup!
"""

import cv2
import numpy as np
from skin_detector_simple import SkinDetector

def analyze_skin_color(rgb_values):
    """Simple but effective skin tone analysis"""
    r, g, b = rgb_values
    
    # Calculate skin tone metrics
    brightness = (r + g + b) / 3 / 255.0
    
    # Undertone detection
    red_ratio = r / (r + g + b + 1)
    blue_ratio = b / (r + g + b + 1)
    
    if red_ratio > blue_ratio + 0.02:
        undertone = "Warm"
        undertone_emoji = "🌅"
    elif blue_ratio > red_ratio + 0.02:
        undertone = "Cool" 
        undertone_emoji = "❄️"
    else:
        undertone = "Neutral"
        undertone_emoji = "⚖️"
    
    # Brightness categories
    if brightness > 0.8:
        brightness_cat = "Very Light"
        brightness_emoji = "☀️"
    elif brightness > 0.6:
        brightness_cat = "Light"
        brightness_emoji = "🌤️"
    elif brightness > 0.4:
        brightness_cat = "Medium"
        brightness_emoji = "🌥️"
    elif brightness > 0.2:
        brightness_cat = "Dark"
        brightness_emoji = "🌙"
    else:
        brightness_cat = "Very Dark"
        brightness_emoji = "🌑"
    
    # Simple color recommendations
    if undertone == "Warm":
        recommendations = ["Coral", "Peach", "Golden Yellow", "Warm Brown", "Orange"]
        avoid = ["Icy Blue", "Pure White", "Cool Gray"]
    elif undertone == "Cool":
        recommendations = ["Navy", "Royal Blue", "Emerald", "Cool Pink", "White"]  
        avoid = ["Orange", "Yellow", "Warm Brown"]
    else:
        recommendations = ["Dusty Blue", "Sage Green", "Soft Pink", "Warm Gray"]
        avoid = ["Neon Colors", "Very Bright Colors"]
    
    return {
        'brightness': brightness_cat,
        'brightness_emoji': brightness_emoji,
        'undertone': undertone,
        'undertone_emoji': undertone_emoji,
        'recommendations': recommendations[:3],
        'avoid': avoid[:2],
        'rgb': rgb_values
    }

def main():
    print("🎨 VastraVista Skin Tone Analysis Demo")
    print("=" * 50)
    
    skin_detector = SkinDetector()
    cap = cv2.VideoCapture(0)
    
    print("📸 Live Skin Analysis:")
    print("   👤 Press SPACE to analyze your skin tone")
    print("   🎯 Press 'r' to get color recommendations")
    print("   ❌ Press 'q' to quit")
    
    last_analysis = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect face and skin
        face_data = skin_detector.detect_face_and_skin(frame)
        result_frame = skin_detector.visualize_skin_detection(frame, face_data)
        
        # Add instructions
        cv2.putText(result_frame, "SPACE=Analyze | r=Recommendations | q=Quit", 
                   (10, result_frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Show analysis if available
        if last_analysis:
            y_pos = 60
            cv2.putText(result_frame, f"Skin: {last_analysis['brightness']} {last_analysis['brightness_emoji']}", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(result_frame, f"Undertone: {last_analysis['undertone']} {last_analysis['undertone_emoji']}", 
                       (10, y_pos + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('VastraVista - Skin Analysis', result_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # Analyze
            if face_data['faces_detected'] > 0:
                print(f"\n🔍 Analyzing skin tone...")
                
                # Get skin color
                face_bbox = face_data['face_regions'][0]
                skin_region = face_data['skin_regions'][0]
                x1, y1, x2, y2 = face_bbox
                face_image = frame[y1:y2, x1:x2]
                
                skin_color = skin_detector.get_average_skin_color(face_image, skin_region)
                
                if 'error' not in skin_color:
                    analysis = analyze_skin_color(skin_color['rgb'])
                    last_analysis = analysis
                    
                    print(f"📊 Analysis Results:")
                    print(f"   Skin Tone: {analysis['brightness']} {analysis['brightness_emoji']}")
                    print(f"   Undertone: {analysis['undertone']} {analysis['undertone_emoji']}")
                    print(f"   RGB Values: {analysis['rgb']}")
                    print(f"   Hex Color: {skin_color['hex']}")
                else:
                    print(f"❌ Analysis failed: {skin_color['error']}")
            else:
                print("❌ No face detected!")
                
        elif key == ord('r'):  # Recommendations
            if last_analysis:
                print(f"\n💡 Color Recommendations for {last_analysis['undertone']} undertones:")
                print(f"   ✅ Great colors for you:")
                for color in last_analysis['recommendations']:
                    print(f"      • {color}")
                print(f"   ❌ Colors to avoid:")
                for color in last_analysis['avoid']:
                    print(f"      • {color}")
                print(f"   🎯 Pro tip: Your {last_analysis['undertone'].lower()} undertones work best with {last_analysis['undertone'].lower()} colors!")
            else:
                print("❌ Please analyze your skin tone first (press SPACE)")
    
    cap.release()
    cv2.destroyAllWindows()
    skin_detector.cleanup()
    
    print(f"\n🎉 Analysis complete!")
    if last_analysis:
        print(f"📋 Your Results Summary:")
        print(f"   Skin Tone: {last_analysis['brightness']} {last_analysis['brightness_emoji']}")
        print(f"   Undertone: {last_analysis['undertone']} {last_analysis['undertone_emoji']}")

if __name__ == "__main__":
    main()
