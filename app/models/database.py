"""
VastraVista - Database Models
Author: Saumya Tiwari
Purpose: SQLAlchemy models for user data, wardrobe, outfits, and analytics
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and personalization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6))
    otp_expires_at = db.Column(db.DateTime)
    otp_last_sent_at = db.Column(db.DateTime)
    otp_attempts = db.Column(db.Integer, default=0)
    otp_attempt_window_start = db.Column(db.DateTime)
    
    # Profile information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Analysis results (stored from last analysis)
    gender = db.Column(db.String(20))
    age_group = db.Column(db.String(30))
    skin_tone = db.Column(db.String(50))
    skin_undertone = db.Column(db.String(20))
    season_type = db.Column(db.String(20))  # Spring, Summer, Autumn, Winter
    
    # Style profile
    style_dna = db.Column(db.Text)  # JSON: {minimalist: 0.8, bohemian: 0.2, ...}
    color_preferences = db.Column(db.Text)  # JSON: list of preferred colors
    
    # Relationships
    color_analysis = db.relationship('ColorAnalysis', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_style_dna(self):
        """Parse style DNA from JSON"""
        return json.loads(self.style_dna) if self.style_dna else {}
    
    def set_style_dna(self, style_dict):
        """Save style DNA as JSON"""
        self.style_dna = json.dumps(style_dict)
    
    def __repr__(self):
        return f'<User {self.username}>'




class ColorAnalysis(db.Model):
    """Store detailed color analysis results for users"""
    __tablename__ = 'color_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Analysis results
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(500))
    
    # Detected attributes
    gender = db.Column(db.String(20))
    gender_confidence = db.Column(db.Float)
    age_group = db.Column(db.String(30))
    age_confidence = db.Column(db.Float)
    
    # Skin analysis
    skin_tone = db.Column(db.String(50))
    skin_tone_rgb = db.Column(db.String(50))  # RGB values
    skin_tone_hex = db.Column(db.String(10))
    skin_undertone = db.Column(db.String(20))
    season_type = db.Column(db.String(20))
    
    # Recommended colors (JSON)
    top_colors = db.Column(db.Text)  # JSON: list of best colors with Delta-E scores
    avoid_colors = db.Column(db.Text)  # JSON: list of worst colors
    color_palette_full = db.Column(db.Text)  # JSON: complete 60+ color database analysis
    
    # PDF report path
    report_pdf_path = db.Column(db.String(500))
    
    def get_top_colors(self):
        """Parse top colors from JSON"""
        return json.loads(self.top_colors) if self.top_colors else []
    
    def set_top_colors(self, colors):
        """Save top colors as JSON"""
        self.top_colors = json.dumps(colors)
    
    def __repr__(self):
        return f'<ColorAnalysis user={self.user_id} date={self.analysis_date}>'


 


 


class StyleQuizResult(db.Model):
    """Store style DNA quiz results"""
    __tablename__ = 'style_quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Style scores (0-100 for each category)
    minimalist_score = db.Column(db.Float, default=0.0)
    bohemian_score = db.Column(db.Float, default=0.0)
    classic_score = db.Column(db.Float, default=0.0)
    edgy_score = db.Column(db.Float, default=0.0)
    romantic_score = db.Column(db.Float, default=0.0)
    sporty_score = db.Column(db.Float, default=0.0)
    
    # Dominant style
    dominant_style = db.Column(db.String(50))
    
    # Quiz metadata
    quiz_version = db.Column(db.String(20))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StyleQuiz user={self.user_id} style={self.dominant_style}>'
