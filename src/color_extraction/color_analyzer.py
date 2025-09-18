"""
VastraVista - Color Extraction Module (Fixed Version)
Author: Saumya Tiwari
Purpose: Extract dominant colors from clothing regions using K-means clustering
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.utils import shuffle
from collections import Counter
import logging
from typing import List, Dict, Tuple, Optional
import colorsys
import webcolors

class ColorAnalyzer:
    """Main color analysis class for extracting dominant colors from clothing"""
    
    def __init__(self, n_colors: int = 5):
        """
        Initialize the color analyzer
        
        Args:
            n_colors: Number of dominant colors to extract
        """
        self.n_colors = n_colors
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger.info(f"🎨 ColorAnalyzer initialized with {n_colors} colors")
        
    def extract_dominant_colors(self, image: np.ndarray, bbox: Optional[List[int]] = None,
                              method: str = "kmeans") -> Dict:
        """
        Extract dominant colors from image or clothing region
        
        Args:
            image: Input image as numpy array
            bbox: Optional bounding box [x1, y1, x2, y2] for clothing region
            method: Color extraction method ('kmeans', 'histogram')
            
        Returns:
            Dictionary containing dominant colors and their information
        """
        try:
            # Extract region of interest
            if bbox is not None:
                x1, y1, x2, y2 = [int(coord) for coord in bbox]
                roi = image[y1:y2, x1:x2]
            else:
                roi = image
            
            if roi.size == 0:
                self.logger.warning("Empty ROI provided")
                return self._empty_result()
            
            if method == "kmeans":
                return self._extract_colors_kmeans(roi)
            elif method == "histogram":
                return self._extract_colors_histogram(roi)
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Color extraction failed: {e}")
            return self._empty_result()
    
    def _extract_colors_kmeans(self, image: np.ndarray) -> Dict:
        """Extract colors using K-means clustering with improved error handling"""
        try:
            # Reshape image to pixel array
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # Remove any invalid values (NaN, inf)
            data = data[~np.isnan(data).any(axis=1)]
            data = data[~np.isinf(data).any(axis=1)]
            
            if len(data) == 0:
                return self._empty_result()
            
            # Shuffle data for better clustering performance
            data = shuffle(data, random_state=42)
            
            # Limit data size for performance (sample max 5000 pixels)
            if len(data) > 5000:
                data = data[:5000]
            
            # Ensure we don't have more clusters than data points
            n_clusters = min(self.n_colors, len(data))
            
            if n_clusters < 1:
                return self._empty_result()
            
            # Apply K-means clustering with improved settings
            kmeans = KMeans(
                n_clusters=n_clusters, 
                random_state=42, 
                n_init=3,  # Reduced iterations for stability
                max_iter=100,  # Reduced max iterations
                tol=1e-3  # Relaxed tolerance
            )
            
            # Suppress warnings for this operation
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                kmeans.fit(data)
            
            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            colors = np.clip(colors, 0, 255)  # Ensure valid RGB range
            
            # Get labels and calculate color percentages
            labels = kmeans.labels_
            label_counts = Counter(labels)
            total_pixels = len(labels)
            
            # Create color information
            color_info = []
            for i, color in enumerate(colors):
                # Convert BGR to RGB for display
                rgb_color = color[::-1]  # OpenCV uses BGR
                percentage = (label_counts[i] / total_pixels) * 100
                
                color_data = {
                    'rgb': [int(c) for c in rgb_color],
                    'bgr': [int(c) for c in color],
                    'hex': self._rgb_to_hex(rgb_color),
                    'percentage': round(percentage, 2),
                    'name': self._get_color_name(rgb_color),
                    'hsv': self._rgb_to_hsv(rgb_color),
                    'dominance_rank': i + 1
                }
                color_info.append(color_data)
            
            # Sort by percentage (most dominant first)
            color_info.sort(key=lambda x: x['percentage'], reverse=True)
            
            result = {
                'dominant_colors': color_info,
                'method': 'kmeans',
                'total_colors': len(color_info),
                'image_size': image.shape[:2]
            }
            
            self.logger.info(f"✅ Extracted {len(color_info)} dominant colors using K-means")
            return result
            
        except Exception as e:
            self.logger.error(f"K-means color extraction failed: {e}")
            return self._empty_result()
    
    def _extract_colors_histogram(self, image: np.ndarray) -> Dict:
        """Extract colors using color histogram analysis"""
        try:
            # Convert to HSV for better color analysis
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate histogram
            hist = cv2.calcHist([hsv_image], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
            
            # Find peaks in histogram
            flat_hist = hist.flatten()
            peak_indices = np.argsort(flat_hist)[-self.n_colors:]
            
            # Convert indices back to HSV values
            colors = []
            for idx in reversed(peak_indices):
                h = (idx // (60 * 60)) * (180 / 50)
                s = ((idx // 60) % 60) * (256 / 60)  
                v = (idx % 60) * (256 / 60)
                
                # Convert HSV to BGR
                hsv_color = np.uint8([[[h, s, v]]])
                bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
                rgb_color = bgr_color[::-1]
                
                color_data = {
                    'rgb': [int(c) for c in rgb_color],
                    'bgr': [int(c) for c in bgr_color],
                    'hex': self._rgb_to_hex(rgb_color),
                    'percentage': round(float(flat_hist[idx]) / np.sum(flat_hist) * 100, 2),
                    'name': self._get_color_name(rgb_color),
                    'hsv': [round(h, 2), round(s/256*100, 2), round(v/256*100, 2)],
                    'dominance_rank': len(colors) + 1
                }
                colors.append(color_data)
            
            result = {
                'dominant_colors': colors,
                'method': 'histogram',
                'total_colors': len(colors),
                'image_size': image.shape[:2]
            }
            
            self.logger.info(f"✅ Extracted {len(colors)} dominant colors using histogram")
            return result
            
        except Exception as e:
            self.logger.error(f"Histogram color extraction failed: {e}")
            return self._empty_result()
    
    def _rgb_to_hex(self, rgb: np.ndarray) -> str:
        """Convert RGB to hex color code"""
        try:
            return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        except:
            return "#000000"
    
    def _rgb_to_hsv(self, rgb: np.ndarray) -> List[float]:
        """Convert RGB to HSV"""
        try:
            r, g, b = np.array(rgb) / 255.0
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            return [round(h * 360, 2), round(s * 100, 2), round(v * 100, 2)]
        except:
            return [0, 0, 0]
    
    def _get_color_name(self, rgb: np.ndarray) -> str:
        """Get the closest color name for RGB values using fixed webcolors API"""
        try:
            # Try to get exact color name
            return webcolors.rgb_to_name(tuple(int(c) for c in rgb))
        except ValueError:
            # Find closest color name using CSS3 colors
            try:
                # Get all CSS3 color names and their RGB values
                css3_colors = webcolors.CSS3_NAMES_TO_HEX
                min_distance = float('inf')
                closest_name = 'unknown'
                
                for name, hex_value in css3_colors.items():
                    try:
                        name_rgb = webcolors.hex_to_rgb(hex_value)
                        # Calculate Euclidean distance
                        distance = sum([(a - b) ** 2 for a, b in zip(rgb, name_rgb)]) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_name = name
                    except:
                        continue
                
                return closest_name
            except Exception:
                # Fallback to basic color classification
                r, g, b = rgb
                if r > 200 and g > 200 and b > 200:
                    return 'white'
                elif r < 50 and g < 50 and b < 50:
                    return 'black'
                elif r > g and r > b:
                    return 'red'
                elif g > r and g > b:
                    return 'green'
                elif b > r and b > g:
                    return 'blue'
                else:
                    return 'gray'
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'dominant_colors': [],
            'method': 'none',
            'total_colors': 0,
            'image_size': (0, 0)
        }
    
    def visualize_colors(self, colors_data: Dict, save_path: Optional[str] = None) -> np.ndarray:
        """
        Create a color palette visualization
        
        Args:
            colors_data: Color data from extract_dominant_colors()
            save_path: Optional path to save the visualization
            
        Returns:
            Color palette image
        """
        try:
            colors = colors_data['dominant_colors']
            if not colors:
                return np.zeros((100, 500, 3), dtype=np.uint8)
            
            # Create palette image
            palette_height = 100
            palette_width = 500
            color_width = palette_width // len(colors)
            
            palette = np.zeros((palette_height, palette_width, 3), dtype=np.uint8)
            
            for i, color_info in enumerate(colors):
                x_start = i * color_width
                x_end = (i + 1) * color_width
                
                # Fill color section
                palette[:, x_start:x_end] = color_info['bgr']
                
                # Add text labels
                y_pos = palette_height // 2
                
                # Choose text color based on background brightness
                brightness = sum(color_info['rgb']) / 3
                text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
                
                cv2.putText(palette, f"{color_info['percentage']:.1f}%", 
                           (x_start + 5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.4, text_color, 1)
            
            if save_path:
                cv2.imwrite(save_path, palette)
                self.logger.info(f"Color palette saved to {save_path}")
            
            return palette
            
        except Exception as e:
            self.logger.error(f"Color visualization failed: {e}")
            return np.zeros((100, 500, 3), dtype=np.uint8)
    
    def analyze_clothing_colors(self, image: np.ndarray, detections: Dict) -> Dict:
        """
        Analyze colors for all detected clothing items
        
        Args:
            image: Original image
            detections: Detection results from cloth detection module
            
        Returns:
            Dictionary with color analysis for each clothing item
        """
        try:
            results = {
                'clothing_color_analysis': [],
                'total_items': 0,
                'analysis_method': 'kmeans'
            }
            
            for item in detections.get('clothing_items', []):
                # Extract colors for this clothing item
                color_data = self.extract_dominant_colors(
                    image, 
                    bbox=item['bbox'],
                    method='kmeans'
                )
                
                # Add item information
                item_analysis = {
                    'clothing_type': item['type'],
                    'bbox': item['bbox'],
                    'confidence': item['confidence'],
                    'color_analysis': color_data,
                    'primary_color': color_data['dominant_colors'][0] if color_data['dominant_colors'] else None
                }
                
                results['clothing_color_analysis'].append(item_analysis)
            
            results['total_items'] = len(results['clothing_color_analysis'])
            
            self.logger.info(f"✅ Analyzed colors for {results['total_items']} clothing items")
            return results
            
        except Exception as e:
            self.logger.error(f"Clothing color analysis failed: {e}")
            return {'clothing_color_analysis': [], 'total_items': 0, 'analysis_method': 'none'}
