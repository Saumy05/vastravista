"""
Model Loader and Caching
Singleton pattern for model initialization
"""

from typing import Optional
from app.config.logging_config import get_clean_logger
from app.models.age_detector import AgeDetector
from app.models.gender_detector import GenderDetector
from app.models.skin_tone_detector import SkinToneDetector


class ModelLoader:
    """
    Singleton class for loading and caching models
    Ensures models are loaded only once
    """
    
    _instance = None
    _models = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = get_clean_logger(__name__)
            self._initialized = True
    
    def get_age_detector(self) -> Optional[AgeDetector]:
        """Get or initialize age detector"""
        if 'age_detector' not in self._models:
            try:
                self.logger.info("Loading Age Detector...")
                self._models['age_detector'] = AgeDetector()
                self.logger.info("✅ Age Detector loaded")
            except Exception as e:
                self.logger.error(f"❌ Failed to load Age Detector: {e}")
                self._models['age_detector'] = None
        
        return self._models.get('age_detector')
    
    def get_gender_detector(self) -> Optional[GenderDetector]:
        """Get or initialize gender detector"""
        if 'gender_detector' not in self._models:
            try:
                self.logger.info("Loading Gender Detector...")
                self._models['gender_detector'] = GenderDetector()
                self.logger.info("✅ Gender Detector loaded")
            except Exception as e:
                self.logger.error(f"❌ Failed to load Gender Detector: {e}")
                self._models['gender_detector'] = None
        
        return self._models.get('gender_detector')
    
    def get_skin_tone_detector(self) -> Optional[SkinToneDetector]:
        """Get or initialize skin tone detector"""
        if 'skin_tone_detector' not in self._models:
            try:
                self.logger.info("Loading Skin Tone Detector...")
                self._models['skin_tone_detector'] = SkinToneDetector()
                self.logger.info("✅ Skin Tone Detector loaded")
            except Exception as e:
                self.logger.error(f"❌ Failed to load Skin Tone Detector: {e}")
                self._models['skin_tone_detector'] = None
        
        return self._models.get('skin_tone_detector')
    
    def load_all_models(self):
        """Load all models at startup"""
        self.logger.info("🚀 Loading all VastraVista models...")
        
        age_detector = self.get_age_detector()
        gender_detector = self.get_gender_detector()
        skin_detector = self.get_skin_tone_detector()
        
        loaded = sum([
            age_detector is not None,
            gender_detector is not None,
            skin_detector is not None
        ])
        
        self.logger.info(f"📊 Models loaded: {loaded}/3")
        
        return {
            'age_detector': age_detector is not None,
            'gender_detector': gender_detector is not None,
            'skin_tone_detector': skin_detector is not None,
            'total_loaded': loaded
        }
    
    def cleanup(self):
        """Cleanup model resources"""
        try:
            for model_name, model in self._models.items():
                if model and hasattr(model, 'cleanup'):
                    model.cleanup()
            self.logger.info("🧹 Models cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Singleton instance
model_loader = ModelLoader()
