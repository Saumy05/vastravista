"""
VastraVista - PDF Report Generation Service
Author: Saumya Tiwari
Purpose: Generate downloadable color analysis reports with palettes and recommendations
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List
import io

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Generate professional color analysis PDF reports
    """
    
    def __init__(self, output_dir: str = 'data/reports'):
        """Initialize PDF generator"""
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        self.logger.info("📄 PDF Report Generator initialized")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=rl_colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=rl_colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHead',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=rl_colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
    
    def generate_color_analysis_report(self, user_data: Dict, analysis_results: Dict,
                                      recommendations: Dict, output_filename: str = None) -> str:
        """
        Generate complete color analysis PDF report
        
        Args:
            user_data: User profile information
            analysis_results: Color analysis results
            recommendations: Fashion recommendations
            output_filename: Optional custom filename
            
        Returns:
            Path to generated PDF file
        """
        try:
            # Generate filename
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                username = user_data.get('username', 'user')
                output_filename = f"color_analysis_{username}_{timestamp}.pdf"
            
            output_path = self.output_dir / output_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build document content
            story = []
            
            # Title page
            story.extend(self._create_title_page(user_data))
            
            # Personal profile section
            story.extend(self._create_profile_section(user_data, analysis_results))
            
            # Skin tone analysis
            story.extend(self._create_skin_tone_section(analysis_results))
            
            # Color palette section
            story.extend(self._create_color_palette_section(analysis_results))
            
            # Recommendations section
            story.extend(self._create_recommendations_section(recommendations))
            
            # Styling tips
            story.extend(self._create_styling_tips_section(analysis_results, recommendations))
            
            # Shopping guide
            story.extend(self._create_shopping_guide(recommendations))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"✅ PDF report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            return None
    
    def _create_title_page(self, user_data: Dict) -> List:
        """Create title page elements"""
        elements = []
        
        # Logo/Title
        title = Paragraph("VastraVista", self.styles['CustomTitle'])
        elements.append(title)
        
        subtitle = Paragraph("Personal Color Analysis Report", self.styles['Subtitle'])
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.5 * inch))
        
        # User info
        date_text = f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}"
        elements.append(Paragraph(date_text, self.styles['Normal']))
        
        username = user_data.get('username', 'Valued Customer')
        name_text = f"<b>Prepared for:</b> {username}"
        elements.append(Paragraph(name_text, self.styles['Normal']))
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_profile_section(self, user_data: Dict, analysis_results: Dict) -> List:
        """Create personal profile section"""
        elements = []
        
        elements.append(Paragraph("Your Profile", self.styles['SectionHead']))
        
        # Profile table
        profile_data = [
            ['Gender:', analysis_results.get('gender', 'N/A')],
            ['Age Group:', analysis_results.get('age_group', 'N/A')],
            ['Skin Tone:', analysis_results.get('skin_tone', 'N/A')],
            ['Undertone:', analysis_results.get('undertone', 'N/A')],
            ['Season Type:', analysis_results.get('season_type', 'N/A')]
        ]
        
        table = Table(profile_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), rl_colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), rl_colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, rl_colors.grey)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_skin_tone_section(self, analysis_results: Dict) -> List:
        """Create skin tone analysis section"""
        elements = []
        
        elements.append(Paragraph("Skin Tone Analysis", self.styles['SectionHead']))
        
        description = f"""
        Your skin tone has been analyzed using advanced colorimetry techniques (CIE Delta-E 2000).
        This scientific approach ensures accurate color matching for your unique complexion.
        """
        elements.append(Paragraph(description, self.styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Skin tone color swatch (simplified representation)
        skin_hex = analysis_results.get('skin_tone_hex', '#C89B7B')
        color_text = f"""
        <b>Your Skin Tone Color:</b> {skin_hex}<br/>
        <b>RGB Values:</b> {analysis_results.get('skin_tone_rgb', 'N/A')}<br/>
        <b>Undertone:</b> {analysis_results.get('undertone', 'Neutral')} - 
        {self._get_undertone_description(analysis_results.get('undertone', 'Neutral'))}
        """
        elements.append(Paragraph(color_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_color_palette_section(self, analysis_results: Dict) -> List:
        """Create recommended color palette section"""
        elements = []
        
        elements.append(Paragraph("Your Perfect Color Palette", self.styles['SectionHead']))
        
        intro = """
        Based on your skin tone analysis, these colors will enhance your natural beauty
        and make you look vibrant and confident.
        """
        elements.append(Paragraph(intro, self.styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Top colors table
        top_colors = analysis_results.get('top_colors', [])[:10]
        if top_colors:
            color_data = [['Color Name', 'Hex Code', 'Match Score', 'Rating']]
            
            for color in top_colors:
                color_data.append([
                    color.get('name', 'N/A'),
                    color.get('hex', '#000000'),
                    f"{color.get('delta_e', 0):.1f}",
                    color.get('rating', 'N/A')
                ])
            
            table = Table(color_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), rl_colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, rl_colors.black)
            ]))
            
            elements.append(table)
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_recommendations_section(self, recommendations: Dict) -> List:
        """Create fashion recommendations section"""
        elements = []
        
        elements.append(Paragraph("Fashion Recommendations", self.styles['SectionHead']))
        
        # Recommended clothing items
        clothing_items = recommendations.get('clothing_items', {})
        for category, items in clothing_items.items():
            elements.append(Paragraph(f"<b>{category.title()}:</b>", self.styles['Normal']))
            items_text = ", ".join(items[:5]) if isinstance(items, list) else str(items)
            elements.append(Paragraph(items_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_styling_tips_section(self, analysis_results: Dict, recommendations: Dict) -> List:
        """Create styling tips section"""
        elements = []
        
        elements.append(Paragraph("Personalized Styling Tips", self.styles['SectionHead']))
        
        tips = [
            "Focus on colors from your 'Excellent Match' category for important occasions",
            "Mix and match colors within your palette for harmonious outfits",
            "Use neutrals from your palette as base pieces",
            "Add pops of your best colors through accessories",
            "Avoid colors that clash with your undertone"
        ]
        
        for i, tip in enumerate(tips, 1):
            elements.append(Paragraph(f"{i}. {tip}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_shopping_guide(self, recommendations: Dict) -> List:
        """Create shopping guide section"""
        elements = []
        
        elements.append(Paragraph("Smart Shopping Guide", self.styles['SectionHead']))
        
        guide_text = """
        When shopping for new clothes, use this report as your guide. Look for items in your
        recommended colors and check the color against your palette. Remember, the goal is to
        build a cohesive wardrobe where everything works together and enhances your natural beauty.
        """
        elements.append(Paragraph(guide_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _get_undertone_description(self, undertone: str) -> str:
        """Get description for undertone"""
        descriptions = {
            'Warm': 'golden, peachy, or yellow undertones',
            'Cool': 'pink, red, or blue undertones',
            'Neutral': 'balanced mix of warm and cool tones'
        }
        return descriptions.get(undertone, 'balanced skin tone')
