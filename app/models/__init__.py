"""
VastraVista Models Package
"""

from app.models.age_detector import AgeDetector
from app.models.gender_detector import GenderDetector
from app.models.skin_tone_detector import SkinToneDetector

__all__ = ['AgeDetector', 'GenderDetector', 'SkinToneDetector']
