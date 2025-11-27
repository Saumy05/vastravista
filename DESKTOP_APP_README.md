# VastraVista Desktop Application

Fully Python-based AR Fashion Try-On desktop application with live webcam, pose detection, clothing overlay, and AI chatbot.

## Features

✅ **Live Webcam Feed** - Real-time camera capture using OpenCV  
✅ **Pose Detection** - MediaPipe-based body pose estimation  
✅ **AR Clothing Overlay** - Realistic clothing try-on with warping  
✅ **Skin Tone Analysis** - Automatic skin tone detection and classification  
✅ **Gender & Age Detection** - AI-powered demographic analysis  
✅ **Fashion Recommendations** - Personalized color and style suggestions  
✅ **AI Chatbot** - LLaMA/Ollama-powered fashion advice  
✅ **Keyboard Controls** - Quick outfit switching and controls  
✅ **Confidence Scoring** - Real-time pose confidence monitoring  
✅ **FPS Meter** - Performance monitoring  

## Installation

### Prerequisites

1. **Python 3.8+** installed
2. **Webcam** connected
3. **Ollama** (optional, for AI chatbot) - [Install Ollama](https://ollama.ai)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Ollama (Optional, for AI Chatbot)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

Then pull a model:
```bash
ollama pull llama3.2
```

## Usage

### Option 1: Streamlit Desktop App (Recommended)

Modern UI with chat interface and recommendations panel:

```bash
streamlit run vastravista_desktop.py
```

**Features:**
- Live video feed with AR overlay
- Sidebar controls for outfit selection
- Fashion chatbot interface
- Real-time recommendations display
- Analysis results panel

**Controls:**
- **1-6**: Switch outfit categories (T-Shirt, Shirt, Kurta, Dress, Hoodie, Jacket)
- **A**: Analyze user (skin tone, gender, age)
- **K**: Toggle pose keypoints display
- **Q/ESC**: Quit

### Option 2: OpenCV Standalone (Lightweight)

Pure OpenCV interface - no Streamlit required:

```bash
python vastravista_opencv.py
```

**Features:**
- Full-screen OpenCV window
- Keyboard controls
- Console output for analysis
- Lower resource usage

**Controls:**
- **1-6**: Switch outfit categories
- **A**: Analyze user
- **K**: Toggle keypoints
- **I**: Toggle info overlay
- **Q/ESC**: Quit

## Outfit Categories

1. **T-Shirt** - Casual t-shirt overlay
2. **Shirt** - Formal shirt overlay
3. **Kurta** - Traditional kurta overlay
4. **Dress** - Dress overlay
5. **Hoodie** - Hoodie with hood
6. **Jacket** - Structured jacket overlay

## How It Works

### 1. Camera Input
- Uses OpenCV to capture live webcam feed
- Supports Mac, Windows, Linux
- Configurable resolution (default: 1280x720)

### 2. Pose Detection
- MediaPipe Pose for real-time body tracking
- Detects shoulders, elbows, torso keypoints
- Calculates pose confidence score
- Temporal smoothing for stability

### 3. AR Clothing Overlay
- Warps clothing images onto detected body regions
- Uses OpenCV perspective transformation
- Realistic cloth simulation using NumPy
- Supports multiple clothing items

### 4. User Analysis
- **Skin Tone**: MediaPipe face detection + color analysis
- **Gender**: AI model-based detection
- **Age**: Age estimation with grouping
- **Recommendations**: Personalized fashion advice based on analysis

### 5. AI Chatbot
- Uses Ollama/LLaMA for fashion advice
- Context-aware responses based on user analysis
- Fallback to template responses if AI unavailable
- Real-time chat interface (Streamlit version)

## Technical Details

### Architecture
- **Single Python Process** - All components run in one process
- **No Browser Required** - Pure desktop application
- **No API Calls** - Fully offline capable (except optional Ollama)
- **Real-time Processing** - Frame-by-frame analysis

### Performance
- **Target FPS**: 30 FPS
- **Pose Confidence Threshold**: 60% minimum
- **Frame Skipping**: Automatic if confidence too low
- **GPU Support**: MPS (Mac) / CUDA (if available)

### Libraries Used
- **OpenCV**: Camera capture, image processing, AR overlay
- **MediaPipe**: Pose detection, face detection
- **NumPy**: Matrix operations, cloth warping
- **Pillow**: Image handling
- **Streamlit**: UI framework (optional)
- **Ollama**: LLM for chatbot (optional)

## Troubleshooting

### Camera Not Working
```bash
# Check available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

### Low Pose Confidence
- Ensure good lighting
- Stand 3-6 feet from camera
- Face camera directly
- Ensure shoulders are visible

### AI Chatbot Not Responding
- Check if Ollama is running: `ollama list`
- Verify model is installed: `ollama pull llama3.2`
- Check environment variables:
  ```bash
  export OLLAMA_URL=http://localhost:11434
  export OLLAMA_MODEL=llama3.2
  ```

### Performance Issues
- Reduce camera resolution in code
- Disable keypoints display
- Close other applications
- Use OpenCV version instead of Streamlit

## Configuration

### Environment Variables

```bash
# Ollama Configuration
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2

# Camera Index (default: 0)
export CAMERA_INDEX=0
```

### Code Configuration

Edit `vastravista_desktop.py` or `vastravista_opencv.py`:

```python
# Camera settings
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Width
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Height
self.camera.set(cv2.CAP_PROP_FPS, 30)           # FPS

# Confidence threshold
if confidence < 0.6:  # Adjust threshold
    # Skip frame
```

## Examples

### Basic Usage
```bash
# Start Streamlit app
streamlit run vastravista_desktop.py

# Or start OpenCV app
python vastravista_opencv.py
```

### With Custom Camera
```python
# In code, change camera index
app.initialize_camera(camera_index=1)  # Use camera 1
```

## File Structure

```
vastravista/
├── vastravista_desktop.py      # Streamlit desktop app
├── vastravista_opencv.py        # OpenCV standalone app
├── app/
│   ├── services/
│   │   ├── half_body_ar_engine.py    # AR engine
│   │   ├── clothing_overlay.py       # Clothing overlay
│   │   ├── ar_pose_detector.py       # Pose detection
│   │   ├── recommendation_engine.py   # Fashion recommendations
│   │   └── ai_stylist.py              # AI chatbot
│   ├── models/
│   │   ├── skin_tone_detector.py     # Skin analysis
│   │   ├── gender_detector.py        # Gender detection
│   │   └── age_detector.py           # Age detection
│   └── ...
└── requirements.txt
```

## License

Same as main VastraVista project.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review logs in console
3. Ensure all dependencies are installed
4. Verify camera permissions

## Future Enhancements

- [ ] Multiple clothing items simultaneously
- [ ] Save snapshots with AR overlay
- [ ] Export analysis reports
- [ ] Custom clothing image upload
- [ ] Video recording with AR
- [ ] Multi-person support

