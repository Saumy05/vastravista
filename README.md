# 🎨 VastraVista - AI Fashion Recommendation System

AI-powered fashion recommendation platform using computer vision and color science.

## 🌟 Features

- 📸 Live camera capture or image upload
- 👤 Gender & age detection
- 🎨 Skin tone analysis with undertone classification
- 🌈 Scientific color matching (Delta-E CIE2000)
- 👗 Personalized outfit recommendations
- 💯 Color confidence scoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Webcam (for live capture)

### Installation

```bash
# Clone repository
git clone https://github.com/Saumy05/vastravista.git
cd vastravista

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p logs data/uploads data/cache static/uploads

# Start application
./start.sh
# OR
python run.py
```

Visit: http://localhost:8080

## 📁 Project Structure

```
vastravista/
├── app/
│   ├── api/          # API routes
│   ├── config/       # Configuration
│   ├── models/       # AI models
│   ├── services/     # Business logic
│   └── utils/        # Utilities
├── static/           # CSS, JS, images
├── templates/        # HTML templates
├── logs/             # Application logs
├── data/             # Uploads & cache
├── run.py            # Development server
└── wsgi.py           # Production server
```

## 🎯 How It Works

1. **Image Capture** - Camera or upload
2. **Face Detection** - MediaPipe
3. **Skin Tone Analysis** - RGB extraction
4. **Gender/Age Detection** - AI models
5. **Color Matching** - Delta-E CIE2000 formula
6. **Recommendations** - Personalized outfits

## 🔬 Technology Stack

- **Backend**: Flask, Python
- **Computer Vision**: OpenCV, MediaPipe
- **AI/ML**: DeepFace, TensorFlow
- **Color Science**: Delta-E CIE2000
- **Frontend**: HTML, CSS, JavaScript

## 🎨 Color Science

Uses **Delta-E CIE2000** for perceptual color difference:

- **15 ≤ ΔE < 40**: Excellent match
- **40 ≤ ΔE < 60**: Good match
- **ΔE < 15**: Too similar
- **ΔE ≥ 60**: Too contrasting

## 📊 Models

- **Gender Detection**: DeepFace (95%+ accuracy)
- **Age Detection**: DeepFace (±10 years)
- **Skin Tone**: MediaPipe + RGB analysis

## 🚢 Production Deployment

```bash
# Using Gunicorn
gunicorn wsgi:app -w 4 -b 0.0.0.0:5000 --timeout 120
```

## 📝 License

MIT License - see LICENSE file

## 👨‍💻 Author

**Saumya Tiwari**
B.Tech CSE Final Year Project

## 🙏 Acknowledgments

- MediaPipe for face detection
- DeepFace for age/gender detection
- CIE Lab color space for color science
