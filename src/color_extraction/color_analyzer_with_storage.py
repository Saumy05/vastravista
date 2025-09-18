"""
VastraVista - Color Extraction Module with Database Storage
Enhanced version that saves analysis results to database
"""

import sys
from pathlib import Path
import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Any

# Add parent directory for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from color_extraction.color_analyzer import ColorAnalyzer
from wardrobe_database.database import VastraVistaDatabase

class ColorAnalyzerWithStorage(ColorAnalyzer):
    """Enhanced ColorAnalyzer that saves results to database"""
    
    def __init__(self, n_colors: int = 5, db_path: str = "data/vastravista.db"):
        """
        Initialize with database connection
        
        Args:
            n_colors: Number of dominant colors to extract
            db_path: Path to database file
        """
        super().__init__(n_colors)
        self.db = VastraVistaDatabase(db_path)
        self.logger.info("🗄️ ColorAnalyzer with database storage initialized")
    
    def analyze_and_store_clothing_colors(self, image: np.ndarray, detections: Dict,
                                        session_description: str = "Color Analysis Session",
                                        image_path: Optional[str] = None) -> Dict:
        """
        Analyze colors and store results in database
        
        Args:
            image: Original image
            detections: Detection results from cloth detection module
            session_description: Description for this analysis session
            image_path: Optional path to source image
            
        Returns:
            Dictionary with analysis results and session info
        """
        try:
            # Create new session
            session_id = self.db.create_session(
                description=session_description,
                image_path=image_path,
                metadata={
                    'image_shape': image.shape,
                    'detection_count': len(detections.get('clothing_items', []))
                }
            )
            
            # Save detections to database
            detection_ids = self.db.save_detections(session_id, detections)
            
            # Analyze colors for each clothing item
            results = {
                'session_id': session_id,
                'clothing_color_analysis': [],
                'total_items': 0,
                'analysis_method': 'kmeans',
                'stored_in_database': True
            }
            
            for i, item in enumerate(detections.get('clothing_items', [])):
                # Extract colors for this clothing item
                color_data = self.extract_dominant_colors(
                    image, 
                    bbox=item['bbox'],
                    method='kmeans'
                )
                
                # Save color analysis to database
                analysis_id = ""
                if i < len(detection_ids):
                    analysis_id = self.db.save_color_analysis(
                        session_id, detection_ids[i], color_data
                    )
                
                # Add to results
                item_analysis = {
                    'clothing_type': item['type'],
                    'bbox': item['bbox'],
                    'confidence': item['confidence'],
                    'color_analysis': color_data,
                    'primary_color': color_data['dominant_colors'][0] if color_data['dominant_colors'] else None,
                    'analysis_id': analysis_id
                }
                
                results['clothing_color_analysis'].append(item_analysis)
            
            results['total_items'] = len(results['clothing_color_analysis'])
            
            self.logger.info(f"✅ Analyzed and stored colors for {results['total_items']} items in session {session_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Color analysis and storage failed: {e}")
            return {'clothing_color_analysis': [], 'total_items': 0, 'stored_in_database': False}
    
    def get_wardrobe_colors(self) -> Dict:
        """Get color summary from stored wardrobe items"""
        return self.db.get_wardrobe_summary()
    
    def export_analysis_data(self, export_path: str = "data/vastravista_export.json") -> bool:
        """Export all analysis data"""
        return self.db.export_data(export_path)
