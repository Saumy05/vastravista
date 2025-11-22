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
    wardrobe_items = db.relationship('WardrobeItem', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    outfits = db.relationship('Outfit', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    color_analysis = db.relationship('ColorAnalysis', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    analytics = db.relationship('UserAnalytics', backref='user', uselist=False, cascade='all, delete-orphan')
    
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


class WardrobeItem(db.Model):
    """Digital wardrobe items uploaded by users"""
    __tablename__ = 'wardrobe_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Item details
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # shirt, pants, shoes, dress, etc.
    sub_category = db.Column(db.String(50))  # t-shirt, formal-shirt, jeans, etc.
    
    # Image
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    
    # Color analysis
    primary_color = db.Column(db.String(50))
    secondary_color = db.Column(db.String(50))
    color_palette = db.Column(db.Text)  # JSON: list of detected colors
    
    # Skin tone compatibility (Delta-E scores)
    skin_tone_compatibility = db.Column(db.Float)  # 0-100 score
    compatibility_rating = db.Column(db.String(20))  # Excellent, Good, Fair, Poor
    delta_e_score = db.Column(db.Float)  # CIE Delta-E 2000 score
    
    # Metadata
    brand = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    price = db.Column(db.Float)
    fabric_type = db.Column(db.String(100))
    season = db.Column(db.String(20))  # summer, winter, all-season
    occasion = db.Column(db.String(50))  # casual, formal, party, sports
    
    # Usage tracking
    times_worn = db.Column(db.Integer, default=0)
    last_worn = db.Column(db.Date)
    favorite = db.Column(db.Boolean, default=False)
    
    # Sustainability
    carbon_footprint = db.Column(db.Float)  # kg CO2
    sustainable_brand = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    outfit_items = db.relationship('OutfitItem', backref='wardrobe_item', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_color_palette(self):
        """Parse color palette from JSON"""
        return json.loads(self.color_palette) if self.color_palette else []
    
    def set_color_palette(self, colors):
        """Save color palette as JSON"""
        self.color_palette = json.dumps(colors)
    
    def __repr__(self):
        return f'<WardrobeItem {self.name} ({self.category})>'


class Outfit(db.Model):
    """Complete outfit combinations created by users or system"""
    __tablename__ = 'outfits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Outfit details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    occasion = db.Column(db.String(50))  # casual, formal, party, business, etc.
    season = db.Column(db.String(20))  # summer, winter, spring, fall, all
    
    # AI recommendations
    ai_generated = db.Column(db.Boolean, default=False)
    compatibility_score = db.Column(db.Float)  # 0-100 overall outfit score
    color_harmony_score = db.Column(db.Float)  # 0-100 color combination score
    skin_tone_match_score = db.Column(db.Float)  # 0-100 skin tone compatibility
    
    # Composite image
    outfit_image_path = db.Column(db.String(500))
    
    # Usage tracking
    times_worn = db.Column(db.Integer, default=0)
    last_worn = db.Column(db.Date)
    favorite = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)  # 1-5 user rating
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OutfitItem', backref='outfit', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Outfit {self.name} ({self.occasion})>'


class OutfitItem(db.Model):
    """Junction table linking outfits to wardrobe items"""
    __tablename__ = 'outfit_items'
    
    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'), nullable=False)
    wardrobe_item_id = db.Column(db.Integer, db.ForeignKey('wardrobe_items.id'), nullable=False)
    
    # Position in outfit (layering)
    layer_order = db.Column(db.Integer, default=0)  # 0=base, 1=mid, 2=outer
    
    def __repr__(self):
        return f'<OutfitItem outfit={self.outfit_id} item={self.wardrobe_item_id}>'


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


class UserAnalytics(db.Model):
    """Track user behavior and wardrobe analytics"""
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Wardrobe statistics
    total_items = db.Column(db.Integer, default=0)
    total_outfits = db.Column(db.Integer, default=0)
    
    # Color usage statistics (JSON)
    color_usage_stats = db.Column(db.Text)  # {"warm": 0.8, "cool": 0.2}
    most_worn_items = db.Column(db.Text)  # JSON: list of item IDs
    least_worn_items = db.Column(db.Text)  # JSON: list of item IDs
    
    # Sustainability metrics
    total_carbon_footprint = db.Column(db.Float, default=0.0)  # kg CO2
    sustainable_items_percentage = db.Column(db.Float, default=0.0)
    
    # Usage patterns
    favorite_occasion = db.Column(db.String(50))
    favorite_season = db.Column(db.String(20))
    average_outfit_rating = db.Column(db.Float)
    
    # Recommendations engagement
    recommendations_received = db.Column(db.Integer, default=0)
    recommendations_saved = db.Column(db.Integer, default=0)
    affiliate_clicks = db.Column(db.Integer, default=0)
    
    # Last updated
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_color_usage_stats(self):
        """Parse color usage stats from JSON"""
        return json.loads(self.color_usage_stats) if self.color_usage_stats else {}
    
    def set_color_usage_stats(self, stats):
        """Save color usage stats as JSON"""
        self.color_usage_stats = json.dumps(stats)
    
    def __repr__(self):
        return f'<UserAnalytics user={self.user_id}>'


class ProductRecommendation(db.Model):
    """Store product recommendations from affiliate APIs"""
    __tablename__ = 'product_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Product details
    product_name = db.Column(db.String(300), nullable=False)
    product_url = db.Column(db.String(500), nullable=False)
    affiliate_url = db.Column(db.String(500), nullable=False)
    product_image_url = db.Column(db.String(500))
    
    # Product attributes
    platform = db.Column(db.String(50))  # amazon, flipkart, myntra
    category = db.Column(db.String(100))
    price = db.Column(db.Float)
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    
    # Matching scores
    skin_tone_match_score = db.Column(db.Float)
    style_match_score = db.Column(db.Float)
    overall_match_score = db.Column(db.Float)
    
    # User interaction
    clicked = db.Column(db.Boolean, default=False)
    purchased = db.Column(db.Boolean, default=False)
    saved = db.Column(db.Boolean, default=False)
    
    # Timestamps
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicked_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ProductRec {self.product_name} ({self.platform})>'


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
