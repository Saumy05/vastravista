#!/usr/bin/env python3
"""
VastraVista - Complete AI Fashion Recommendation System
Author: Saumya Tiwari
B.Tech CSE Final Year Project

Integrates all 3 core modules:
1. Cloth Detection (YOLOv8)
2. Color Extraction (K-means + AI)  
3. Skin Tone Analysis (MediaPipe + Color Theory)
"""

import sys
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

class VastraVistaSystem:
    """Complete VastraVista AI Fashion Recommendation System"""
    
    def __init__(self):
        """Initialize all modules"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print("🎨 VastraVista - AI Fashion Recommendation System")
        print("=" * 60)
        print("👨‍🎓 Author: Saumya Tiwari | B.Tech CSE Final Year Project")
        print("=" * 60)
        
        # Initialize modules
        self.modules = {}
        self._initialize_modules()
        
        # Analysis storage
        self.current_analysis = {
            'cloth_detection': None,
            'color_analysis': None,
            'skin_analysis': None,
            'recommendations': None
        }
        
    def _initialize_modules(self):
        """Initialize all available modules"""
        print("\n📦 Initializing VastraVista Modules...")
        
        # Module 1: Cloth Detection
        try:
            from cloth_detection.detector import ClothDetector
            self.modules['cloth_detector'] = ClothDetector(device="cpu")
            print("   ✅ Module 1: Cloth Detection (YOLOv8) - READY")
        except Exception as e:
            print(f"   ❌ Module 1: Cloth Detection - {e}")
            self.modules['cloth_detector'] = None
        
        # Module 2: Color Extraction
        try:
            from color_extraction.color_analyzer_with_storage import ColorAnalyzerWithStorage
            self.modules['color_analyzer'] = ColorAnalyzerWithStorage(n_colors=5)
            print("   ✅ Module 2: Color Extraction (K-means + Storage) - READY")
        except Exception as e:
            try:
                from color_extraction.color_analyzer import ColorAnalyzer
                self.modules['color_analyzer'] = ColorAnalyzer(n_colors=5)
                print("   ✅ Module 2: Color Extraction (K-means) - READY")
            except Exception as e2:
                print(f"   ❌ Module 2: Color Extraction - {e2}")
                self.modules['color_analyzer'] = None
        
        # Module 3: Skin Tone Analysis
        try:
            from skin_tone_analysis.skin_detector_simple import SkinDetector
            self.modules['skin_analyzer'] = SkinDetector()
            print("   ✅ Module 3: Skin Tone Analysis (MediaPipe + AI) - READY")
        except Exception as e:
            print(f"   ❌ Module 3: Skin Tone Analysis - {e}")
            self.modules['skin_analyzer'] = None
        
        # Database (if available)
        try:
            from wardrobe_database.database import VastraVistaDatabase
            self.modules['database'] = VastraVistaDatabase()
            print("   ✅ Database: Data Storage - READY")
        except Exception as e:
            print(f"   ⚠️ Database: Optional storage - {e}")
            self.modules['database'] = None
        
        # Count working modules
        working_modules = sum(1 for k, v in self.modules.items() if v is not None and k != 'database')
        print(f"\n📊 System Status: {working_modules}/3 core modules operational")
        
        if working_modules == 0:
            print("❌ No modules working. Install: pip install ultralytics opencv-python scikit-learn webcolors mediapipe")
            sys.exit(1)
        elif working_modules < 3:
            print("⚠️ Partial system ready. Some features may be limited.")
        else:
            print("🎉 Complete system ready! All modules operational.")
    
    def run_complete_analysis(self, image: np.ndarray) -> Dict:
        """Run complete analysis pipeline on image"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_complete': False,
            'modules_used': [],
            'results': {}
        }
        
        try:
            print("\n🔍 Running Complete VastraVista Analysis...")
            
            # Step 1: Cloth Detection
            if self.modules['cloth_detector']:
                print("   👔 Analyzing clothing items...")
                cloth_results = self.modules['cloth_detector'].detect_clothing(image, confidence=0.3)
                self.current_analysis['cloth_detection'] = cloth_results
                results['results']['cloth_detection'] = cloth_results
                results['modules_used'].append('cloth_detection')
                
                print(f"      ✅ Found {len(cloth_results['clothing_items'])} clothing items")
                for item in cloth_results['clothing_items']:
                    print(f"         - {item['type']} (confidence: {item['confidence']:.2f})")
            
            # Step 2: Color Analysis
            if self.modules['color_analyzer'] and self.current_analysis['cloth_detection']:
                print("   🎨 Extracting clothing colors...")
                color_results = self.modules['color_analyzer'].analyze_clothing_colors(
                    image, self.current_analysis['cloth_detection'])
                self.current_analysis['color_analysis'] = color_results
                results['results']['color_analysis'] = color_results
                results['modules_used'].append('color_analysis')
                
                print(f"      ✅ Analyzed colors for {color_results['total_items']} items")
                for item in color_results['clothing_color_analysis']:
                    if item['primary_color']:
                        pc = item['primary_color']
                        print(f"         {item['clothing_type']}: {pc['name']} ({pc['hex']}) - {pc['percentage']:.1f}%")
            
            # Step 3: Skin Tone Analysis
            if self.modules['skin_analyzer']:
                print("   👤 Analyzing skin tone...")
                face_data = self.modules['skin_analyzer'].detect_face_and_skin(image)
                
                if face_data['faces_detected'] > 0:
                    # Extract skin color
                    face_bbox = face_data['face_regions'][0]
                    skin_region = face_data['skin_regions'][0] if face_data['skin_regions'] else None
                    
                    if skin_region is not None:
                        x1, y1, x2, y2 = face_bbox
                        face_image = image[y1:y2, x1:x2]
                        skin_color = self.modules['skin_analyzer'].get_average_skin_color(face_image, skin_region)
                        
                        if 'error' not in skin_color:
                            # Analyze skin tone
                            skin_analysis = self._analyze_skin_tone_complete(skin_color['rgb'])
                            skin_analysis['face_data'] = face_data
                            skin_analysis['skin_color'] = skin_color
                            
                            self.current_analysis['skin_analysis'] = skin_analysis
                            results['results']['skin_analysis'] = skin_analysis
                            results['modules_used'].append('skin_analysis')
                            
                            print(f"      ✅ Skin Analysis: {skin_analysis['brightness']} {skin_analysis['brightness_emoji']}")
                            print(f"         Undertone: {skin_analysis['undertone']} {skin_analysis['undertone_emoji']}")
                            print(f"         RGB: {skin_color['rgb']}, Hex: {skin_color['hex']}")
                        else:
                            print(f"      ❌ Skin color extraction failed")
                    else:
                        print(f"      ❌ No skin region detected")
                else:
                    print(f"      ❌ No face detected")
            
            # Step 4: Generate Recommendations
            if self.current_analysis['skin_analysis']:
                print("   💡 Generating personalized recommendations...")
                recommendations = self._generate_complete_recommendations()
                self.current_analysis['recommendations'] = recommendations
                results['results']['recommendations'] = recommendations
                results['modules_used'].append('recommendations')
                
                print(f"      ✅ Generated personalized color recommendations")
                print(f"         Best colors: {', '.join(recommendations['excellent_colors'][:3])}")
                print(f"         Avoid: {', '.join(recommendations['avoid_colors'][:2])}")
            
            # Step 5: Save to Database (if available)
            if self.modules['database'] and len(results['modules_used']) > 0:
                try:
                    session_id = self.modules['database'].create_session(
                        description="Complete VastraVista Analysis",
                        metadata=results
                    )
                    results['session_id'] = session_id
                    print(f"      ✅ Results saved to database: {session_id[:8]}...")
                except Exception as e:
                    print(f"      ⚠️ Database save failed: {e}")
            
            results['analysis_complete'] = True
            print("   🎉 Complete analysis finished!")
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_skin_tone_complete(self, rgb_values: List[int]) -> Dict:
        """Complete skin tone analysis with recommendations"""
        r, g, b = rgb_values
        
        # Brightness analysis
        brightness = (r + g + b) / 3 / 255.0
        
        if brightness > 0.8:
            brightness_cat, brightness_emoji = "Very Light", "☀️"
        elif brightness > 0.6:
            brightness_cat, brightness_emoji = "Light", "🌤️"
        elif brightness > 0.4:
            brightness_cat, brightness_emoji = "Medium", "🌥️"
        elif brightness > 0.2:
            brightness_cat, brightness_emoji = "Dark", "🌙"
        else:
            brightness_cat, brightness_emoji = "Very Dark", "🌑"
        
        # Undertone analysis
        red_ratio = r / (r + g + b + 1)
        blue_ratio = b / (r + g + b + 1)
        green_ratio = g / (r + g + b + 1)
        
        if red_ratio > blue_ratio + 0.02:
            undertone, undertone_emoji = "Warm", "🌅"
        elif blue_ratio > red_ratio + 0.02:
            undertone, undertone_emoji = "Cool", "❄️"
        elif green_ratio > max(red_ratio, blue_ratio) + 0.01:
            undertone, undertone_emoji = "Olive", "🫒"
        else:
            undertone, undertone_emoji = "Neutral", "⚖️"
        
        # Seasonal analysis (simplified)
        intensity = max(r, g, b) - min(r, g, b)
        if undertone == "Warm":
            if intensity > 100:
                seasonal_type = "Bright Spring"
            elif brightness > 0.5:
                seasonal_type = "True Spring" 
            else:
                seasonal_type = "Deep Autumn"
        else:
            if intensity > 100:
                seasonal_type = "Bright Winter"
            elif brightness > 0.5:
                seasonal_type = "True Summer"
            else:
                seasonal_type = "Deep Winter"
        
        return {
            'brightness': brightness_cat,
            'brightness_emoji': brightness_emoji,
            'brightness_value': round(brightness, 3),
            'undertone': undertone,
            'undertone_emoji': undertone_emoji,
            'seasonal_type': seasonal_type,
            'rgb': rgb_values,
            'analysis_confidence': 0.85
        }
    
    def _generate_complete_recommendations(self) -> Dict:
        """Generate complete color recommendations based on analysis"""
        if not self.current_analysis['skin_analysis']:
            return {}
        
        undertone = self.current_analysis['skin_analysis']['undertone']
        brightness = self.current_analysis['skin_analysis']['brightness']
        seasonal_type = self.current_analysis['skin_analysis']['seasonal_type']
        
        # Base recommendations by undertone
        recommendations = {
            'Warm': {
                'excellent': ['Coral', 'Peach', 'Golden Yellow', 'Warm Brown', 'Orange', 'Rust'],
                'good': ['Beige', 'Camel', 'Olive', 'Warm Red', 'Cream', 'Gold'],
                'avoid': ['Icy Blue', 'Pure White', 'Cool Gray', 'Purple', 'Silver']
            },
            'Cool': {
                'excellent': ['Navy', 'Royal Blue', 'Emerald', 'Cool Pink', 'White', 'Magenta'],
                'good': ['Gray', 'Black', 'Cool Red', 'Lavender', 'Mint', 'Silver'],
                'avoid': ['Orange', 'Yellow', 'Warm Brown', 'Gold', 'Coral']
            },
            'Neutral': {
                'excellent': ['Dusty Blue', 'Sage Green', 'Soft Pink', 'Warm Gray', 'Burgundy'],
                'good': ['Navy', 'Cream', 'Taupe', 'Soft Yellow', 'Muted Purple'],
                'avoid': ['Neon Colors', 'Very Bright Orange', 'Electric Blue']
            },
            'Olive': {
                'excellent': ['Earth Tones', 'Deep Green', 'Warm Brown', 'Golden Yellow', 'Rust'],
                'good': ['Navy', 'Cream', 'Burgundy', 'Deep Red', 'Camel'],
                'avoid': ['Bright Pink', 'Icy Blue', 'Pure White', 'Neon Green']
            }
        }
        
        base_recs = recommendations.get(undertone, recommendations['Neutral'])
        
        # Outfit suggestions
        outfit_suggestions = []
        if undertone in ['Warm', 'Olive']:
            outfit_suggestions = [
                {
                    'occasion': 'Professional',
                    'outfit': 'Navy blazer + cream blouse + camel trousers',
                    'why': 'Warm neutrals complement your undertone while maintaining professionalism'
                },
                {
                    'occasion': 'Casual',
                    'outfit': 'Coral/peach top + dark jeans + brown accessories',
                    'why': 'Brings out your warm undertones, grounded by neutral denim'
                }
            ]
        else:
            outfit_suggestions = [
                {
                    'occasion': 'Professional',
                    'outfit': 'Black suit + white shirt + silver accessories',
                    'why': 'Classic cool colors create striking contrast with your complexion'
                },
                {
                    'occasion': 'Casual',
                    'outfit': 'Royal blue sweater + gray pants + black boots',
                    'why': 'Cool blues enhance your natural coloring'
                }
            ]
        
        # Styling tips
        styling_tips = []
        if undertone == 'Warm':
            styling_tips = [
                "Gold jewelry complements your warm undertones better than silver",
                "Earth tones and warm colors will make your skin glow",
                "Avoid icy colors that can make you look washed out"
            ]
        elif undertone == 'Cool':
            styling_tips = [
                "Silver jewelry enhances your cool undertones perfectly",
                "Blues, purples, and cool pinks bring out your natural radiance",
                "Avoid yellow-based colors that clash with your cool complexion"
            ]
        else:
            styling_tips = [
                "You can wear both gold and silver jewelry successfully",
                "Focus on colors that enhance your natural glow",
                "Avoid colors that are too neon or overwhelming"
            ]
        
        return {
            'excellent_colors': base_recs['excellent'],
            'good_colors': base_recs['good'],
            'avoid_colors': base_recs['avoid'],
            'outfit_suggestions': outfit_suggestions,
            'styling_tips': styling_tips,
            'undertone_focus': undertone,
            'brightness_consideration': brightness,
            'seasonal_type': seasonal_type,
            'confidence_score': 0.9
        }
    
    def visualize_complete_analysis(self, image: np.ndarray) -> np.ndarray:
        """Create complete visualization of all analysis results"""
        result_image = image.copy()
        
        try:
            # Draw cloth detection
            if self.current_analysis['cloth_detection'] and self.modules['cloth_detector']:
                result_image = self.modules['cloth_detector'].draw_detections(
                    result_image, self.current_analysis['cloth_detection'])
            
            # Draw face detection
            if self.current_analysis['skin_analysis'] and 'face_data' in self.current_analysis['skin_analysis']:
                face_data = self.current_analysis['skin_analysis']['face_data']
                result_image = self.modules['skin_analyzer'].visualize_skin_detection(result_image, face_data)
            
            # Add analysis summary
            y_offset = 60
            if self.current_analysis['skin_analysis']:
                skin = self.current_analysis['skin_analysis']
                cv2.putText(result_image, f"Skin: {skin['brightness']} {skin['brightness_emoji']}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(result_image, f"Undertone: {skin['undertone']} {skin['undertone_emoji']}", 
                           (10, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 70
            
            if self.current_analysis['recommendations']:
                recs = self.current_analysis['recommendations']
                cv2.putText(result_image, f"Best: {', '.join(recs['excellent_colors'][:2])}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        except Exception as e:
            cv2.putText(result_image, f"Visualization Error", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return result_image
    
    def run_interactive_demo(self):
        """Run interactive webcam demo"""
        print(f"\n🚀 Starting VastraVista Interactive Demo...")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot access webcam")
            return False
        
        print("\n📹 Interactive Demo Controls:")
        print("   📸 Press SPACE - Complete Analysis")
        print("   🔄 Press 'r' - Show Recommendations")
        print("   💾 Press 's' - Save Analysis")
        print("   📊 Press 'i' - Show Info")
        print("   ❌ Press 'q' - Quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Create display frame
            display_frame = frame.copy()
            
            # Add current analysis overlay if available
            if any(self.current_analysis.values()):
                display_frame = self.visualize_complete_analysis(display_frame)
            
            # Add instructions
            cv2.putText(display_frame, "VastraVista AI Fashion System", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display_frame, "SPACE=Analyze | r=Recommendations | s=Save | i=Info | q=Quit", 
                       (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('VastraVista - AI Fashion Recommendation System', display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Complete analysis
                results = self.run_complete_analysis(frame)
                
            elif key == ord('r'):  # Show recommendations
                if self.current_analysis['recommendations']:
                    recs = self.current_analysis['recommendations']
                    print(f"\n💡 Personalized Recommendations:")
                    print(f"   ✅ Excellent colors: {', '.join(recs['excellent_colors'][:3])}")
                    print(f"   👍 Good colors: {', '.join(recs['good_colors'][:3])}")
                    print(f"   ❌ Avoid: {', '.join(recs['avoid_colors'][:2])}")
                    print(f"   👗 Style tip: {recs['styling_tips'][0]}")
                else:
                    print("⚠️ Run analysis first (press SPACE)")
            
            elif key == ord('s'):  # Save analysis
                if any(self.current_analysis.values()):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"data/analysis_{timestamp}.json"
                    try:
                        import os
                        os.makedirs("data", exist_ok=True)
                        with open(filename, 'w') as f:
                            json.dump(self.current_analysis, f, indent=2, default=str)
                        print(f"💾 Analysis saved to {filename}")
                    except Exception as e:
                        print(f"❌ Save failed: {e}")
                else:
                    print("⚠️ No analysis to save")
            
            elif key == ord('i'):  # Show info
                working_modules = sum(1 for k, v in self.modules.items() if v is not None and k != 'database')
                print(f"\n📊 VastraVista System Information:")
                print(f"   Operational Modules: {working_modules}/3")
                print(f"   Cloth Detection: {'✅' if self.modules['cloth_detector'] else '❌'}")
                print(f"   Color Extraction: {'✅' if self.modules['color_analyzer'] else '❌'}")
                print(f"   Skin Analysis: {'✅' if self.modules['skin_analyzer'] else '❌'}")
                print(f"   Database Storage: {'✅' if self.modules['database'] else '❌'}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Cleanup
        if self.modules['skin_analyzer']:
            try:
                self.modules['skin_analyzer'].cleanup()
            except:
                pass
        
        print("\n🎉 VastraVista Demo completed!")
        return True
    
    def export_complete_report(self, filename: str = None) -> str:
        """Export complete analysis report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VastraVista_Report_{timestamp}.json"
        
        report = {
            'system_info': {
                'name': 'VastraVista AI Fashion Recommendation System',
                'author': 'Saumya Tiwari',
                'project': 'B.Tech CSE Final Year Project',
                'timestamp': datetime.now().isoformat(),
                'modules_operational': [k for k, v in self.modules.items() if v is not None]
            },
            'current_analysis': self.current_analysis,
            'system_capabilities': {
                'cloth_detection': bool(self.modules['cloth_detector']),
                'color_extraction': bool(self.modules['color_analyzer']),
                'skin_analysis': bool(self.modules['skin_analyzer']),
                'data_storage': bool(self.modules['database'])
            }
        }
        
        try:
            import os
            os.makedirs("data", exist_ok=True)
            filepath = f"data/{filename}"
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Complete report exported to: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Report export failed: {e}")
            return ""

def main():
    """Main function"""
    print("🚀 Starting VastraVista AI Fashion Recommendation System...")
    
    try:
        # Initialize system
        vastravista = VastraVistaSystem()
        
        # Run interactive demo
        success = vastravista.run_interactive_demo()
        
        # Export final report
        if success:
            vastravista.export_complete_report()
        
        print("\n👨‍🎓 VastraVista Project by Saumya Tiwari")
        print("🎓 B.Tech Computer Science Engineering - Final Year")
        print("🏫 AKS University")
        print("\n🎉 Thank you for using VastraVista!")
        
    except KeyboardInterrupt:
        print("\n👋 VastraVista session ended by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
