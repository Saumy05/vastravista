"""
VastraVista - Database Module (Fixed Version)
Author: Saumya Tiwari
Purpose: Store and manage wardrobe data, color analysis, and detection results
"""

import sqlite3
import json
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import uuid

class VastraVistaDatabase:
    """Main database class for VastraVista data storage"""
    
    def __init__(self, db_path: str = "data/vastravista.db"):
        """
        Initialize the database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        self.logger.info(f"🗄️ VastraVista Database initialized: {db_path}")
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        else:
            return obj
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        description TEXT,
                        image_path TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Create detections table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS detections (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        clothing_type TEXT,
                        bbox TEXT,
                        confidence REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                ''')
                
                # Create color_analysis table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS color_analysis (
                        id TEXT PRIMARY KEY,
                        detection_id TEXT,
                        session_id TEXT,
                        dominant_colors TEXT,
                        primary_color_hex TEXT,
                        primary_color_name TEXT,
                        analysis_method TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (detection_id) REFERENCES detections (id),
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                ''')
                
                # Create wardrobe_items table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wardrobe_items (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        category TEXT,
                        dominant_colors TEXT,
                        image_path TEXT,
                        tags TEXT,
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_worn DATETIME,
                        wear_count INTEGER DEFAULT 0
                    )
                ''')
                
                # Create recommendations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recommendations (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        recommendation_type TEXT,
                        recommended_colors TEXT,
                        reasoning TEXT,
                        confidence_score REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                ''')
                
                conn.commit()
                self.logger.info("✅ Database tables initialized successfully")
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def create_session(self, description: str = "VastraVista Analysis", 
                      image_path: Optional[str] = None, 
                      metadata: Optional[Dict] = None) -> str:
        """
        Create a new analysis session
        
        Args:
            description: Session description
            image_path: Path to analyzed image
            metadata: Additional metadata
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Convert metadata to handle numpy types
            clean_metadata = self._convert_numpy_types(metadata) if metadata else None
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sessions (id, description, image_path, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, description, image_path, 
                     json.dumps(clean_metadata) if clean_metadata else None))
                conn.commit()
            
            self.logger.info(f"📝 Created session: {session_id[:8]}...")
            return session_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create session: {e}")
            raise
    
    def save_detections(self, session_id: str, detections: Dict) -> List[str]:
        """
        Save clothing detections to database
        
        Args:
            session_id: Session ID
            detections: Detection results from cloth detection module
            
        Returns:
            List of detection IDs
        """
        try:
            detection_ids = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for item in detections.get('clothing_items', []):
                    detection_id = str(uuid.uuid4())
                    
                    # Convert numpy types to Python types
                    clean_item = self._convert_numpy_types(item)
                    
                    cursor.execute('''
                        INSERT INTO detections (id, session_id, clothing_type, bbox, confidence)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (detection_id, session_id, clean_item['type'], 
                         json.dumps(clean_item['bbox']), float(clean_item['confidence'])))
                    
                    detection_ids.append(detection_id)
                
                conn.commit()
            
            self.logger.info(f"💾 Saved {len(detection_ids)} detections for session {session_id[:8]}...")
            return detection_ids
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save detections: {e}")
            return []
    
    def save_color_analysis(self, session_id: str, detection_id: str, 
                           color_results: Dict) -> str:
        """
        Save color analysis results
        
        Args:
            session_id: Session ID
            detection_id: Detection ID
            color_results: Color analysis results
            
        Returns:
            Color analysis ID
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Convert numpy types
            clean_color_results = self._convert_numpy_types(color_results)
            
            # Extract primary color info
            primary_color_hex = None
            primary_color_name = None
            
            if clean_color_results.get('dominant_colors'):
                primary_color = clean_color_results['dominant_colors'][0]
                primary_color_hex = primary_color.get('hex')
                primary_color_name = primary_color.get('name')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO color_analysis 
                    (id, detection_id, session_id, dominant_colors, primary_color_hex, 
                     primary_color_name, analysis_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (analysis_id, detection_id, session_id,
                     json.dumps(clean_color_results.get('dominant_colors', [])),
                     primary_color_hex, primary_color_name,
                     clean_color_results.get('method', 'kmeans')))
                
                conn.commit()
            
            self.logger.info(f"🎨 Saved color analysis: {analysis_id[:8]}...")
            return analysis_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save color analysis: {e}")
            return ""
    
    def add_wardrobe_item(self, name: str, category: str, colors: List[Dict],
                         image_path: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """
        Add item to wardrobe
        
        Args:
            name: Item name
            category: Clothing category
            colors: Dominant colors
            image_path: Path to item image
            tags: Optional tags
            
        Returns:
            Wardrobe item ID
        """
        try:
            item_id = str(uuid.uuid4())
            
            # Convert numpy types
            clean_colors = self._convert_numpy_types(colors)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO wardrobe_items 
                    (id, name, category, dominant_colors, image_path, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (item_id, name, category, json.dumps(clean_colors),
                     image_path, json.dumps(tags) if tags else None))
                
                conn.commit()
            
            self.logger.info(f"👕 Added wardrobe item: {name} ({item_id[:8]}...)")
            return item_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add wardrobe item: {e}")
            return ""
    
    def get_session_data(self, session_id: str) -> Dict:
        """Get complete session data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get session info
                cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
                session = cursor.fetchone()
                
                if not session:
                    return {}
                
                # Get detections
                cursor.execute('SELECT * FROM detections WHERE session_id = ?', (session_id,))
                detections = cursor.fetchall()
                
                # Get color analysis
                cursor.execute('SELECT * FROM color_analysis WHERE session_id = ?', (session_id,))
                color_analyses = cursor.fetchall()
                
                # Format results
                result = {
                    'session': dict(session),
                    'detections': [dict(d) for d in detections],
                    'color_analyses': [dict(c) for c in color_analyses]
                }
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get session data: {e}")
            return {}
    
    def get_wardrobe_summary(self) -> Dict:
        """Get wardrobe summary statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total items
                cursor.execute('SELECT COUNT(*) FROM wardrobe_items')
                total_items = cursor.fetchone()[0]
                
                # Items by category
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM wardrobe_items 
                    GROUP BY category
                ''')
                categories = dict(cursor.fetchall())
                
                # Recent sessions
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM sessions 
                    WHERE timestamp >= datetime('now', '-7 days')
                ''')
                recent_sessions = cursor.fetchone()[0]
                
                # Total sessions
                cursor.execute('SELECT COUNT(*) FROM sessions')
                total_sessions = cursor.fetchone()[0]
                
                # Total detections
                cursor.execute('SELECT COUNT(*) FROM detections')
                total_detections = cursor.fetchone()[0]
                
                # Total color analyses
                cursor.execute('SELECT COUNT(*) FROM color_analysis')
                total_analyses = cursor.fetchone()[0]
                
                return {
                    'total_items': total_items,
                    'categories': categories,
                    'recent_sessions': recent_sessions,
                    'total_sessions': total_sessions,
                    'total_detections': total_detections,
                    'total_color_analyses': total_analyses
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get wardrobe summary: {e}")
            return {'total_items': 0, 'categories': {}, 'recent_sessions': 0, 'total_sessions': 0}
    
    def export_data(self, export_path: str) -> bool:
        """Export all data to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all data
                data = {}
                
                for table in ['sessions', 'detections', 'color_analysis', 'wardrobe_items', 'recommendations']:
                    cursor.execute(f'SELECT * FROM {table}')
                    data[table] = [dict(row) for row in cursor.fetchall()]
                
                # Add summary
                data['export_info'] = {
                    'export_date': datetime.now().isoformat(),
                    'total_tables': len(data),
                    'database_path': self.db_path
                }
                
                # Create directory if needed
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                
                # Save to JSON with numpy type conversion
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                self.logger.info(f"📤 Data exported to: {export_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Data export failed: {e}")
            return False
