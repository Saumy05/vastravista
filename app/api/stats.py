"""
Statistics and Analytics API
Provides user statistics and analytics for presentation
"""

from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.database import db, User, ColorAnalysis

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        user = current_user
        
        # Get analysis count
        analysis_count = ColorAnalysis.query.filter_by(user_id=user.id).count()
        
        # Get recent analyses
        recent_analyses = ColorAnalysis.query.filter_by(user_id=user.id)\
            .order_by(ColorAnalysis.analysis_date.desc())\
            .limit(5).all()
        
        # Calculate days active
        days_active = 0
        if user.created_at:
            days_active = (datetime.utcnow() - user.created_at).days
        
        # Get most common skin tone
        most_common_skin_tone = None
        skin_tone_counts = db.session.query(
            ColorAnalysis.skin_tone,
            db.func.count(ColorAnalysis.id).label('count')
        ).filter_by(user_id=user.id)\
         .group_by(ColorAnalysis.skin_tone)\
         .order_by(db.desc('count'))\
         .first()
        
        if skin_tone_counts:
            most_common_skin_tone = skin_tone_counts[0]
        
        # Get favorite colors (from top_colors JSON)
        favorite_colors = []
        if recent_analyses:
            for analysis in recent_analyses[:3]:
                if analysis.top_colors:
                    try:
                        import json
                        colors = json.loads(analysis.top_colors)
                        if colors:
                            favorite_colors.extend(colors[:2])
                    except:
                        pass
        
        stats = {
            'total_analyses': analysis_count,
            'days_active': days_active,
            'most_common_skin_tone': most_common_skin_tone,
            'recent_analyses_count': len(recent_analyses),
            'favorite_colors': favorite_colors[:6],  # Top 6
            'account_created': user.created_at.isoformat() if user.created_at else None,
            'last_analysis': recent_analyses[0].analysis_date.isoformat() if recent_analyses else None
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        current_app.logger.error(f"Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stats_bp.route('/api/stats/global', methods=['GET'])
@login_required
def get_global_stats():
    """Get global platform statistics"""
    try:
        total_users = User.query.count()
        total_analyses = ColorAnalysis.query.count()
        
        # Users created in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Analyses in last 30 days
        recent_analyses = ColorAnalysis.query.filter(
            ColorAnalysis.analysis_date >= thirty_days_ago
        ).count()
        
        stats = {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'recent_users_30d': recent_users,
            'recent_analyses_30d': recent_analyses,
            'avg_analyses_per_user': round(total_analyses / total_users, 2) if total_users > 0 else 0
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        current_app.logger.error(f"Global stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

