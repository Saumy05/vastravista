# VastraVista Desktop - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Choose Your Interface

**Option A: Streamlit (Recommended)**
```bash
streamlit run vastravista_desktop.py
```

**Option B: OpenCV (Lightweight)**
```bash
python vastravista_opencv.py
```

**Option C: Use Launcher**
```bash
python run_desktop.py
```

### Step 3: Use the App!

**Keyboard Controls:**
- **1-6**: Switch outfit categories
- **A**: Analyze user (skin tone, gender, age)
- **K**: Toggle pose keypoints
- **Q/ESC**: Quit

## 📋 What You Need

✅ Python 3.8+  
✅ Webcam  
✅ Good lighting (for best pose detection)  
✅ Ollama (optional, for AI chatbot)  

## 🎯 First Time Setup

1. **Test your camera:**
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   print("Camera works!" if ret else "Camera not working")
   cap.release()
   ```

2. **Install Ollama (optional):**
   ```bash
   # macOS
   brew install ollama
   
   # Then pull a model
   ollama pull llama3.2
   ```

3. **Run the app:**
   ```bash
   python run_desktop.py
   ```

## 🎨 Outfit Categories

Press **1-6** to switch:
1. T-Shirt
2. Shirt  
3. Kurta
4. Dress
5. Hoodie
6. Jacket

## 💡 Tips

- **Stand 3-6 feet from camera** for best results
- **Face camera directly** for accurate pose detection
- **Ensure good lighting** - pose confidence should be >60%
- **Press A** to analyze yourself and get fashion recommendations
- **Use Streamlit version** for chat interface and recommendations panel

## 🐛 Troubleshooting

**Camera not working?**
- Check camera permissions
- Try different camera index: `app.initialize_camera(1)`

**Low pose confidence?**
- Improve lighting
- Stand further from camera
- Ensure shoulders are visible

**AI chatbot not working?**
- Install Ollama: `brew install ollama`
- Pull model: `ollama pull llama3.2`
- App will use templates if Ollama unavailable

## 📚 More Information

See [DESKTOP_APP_README.md](DESKTOP_APP_README.md) for detailed documentation.

## 🎬 Example Workflow

1. Start app: `streamlit run vastravista_desktop.py`
2. Click "Start Camera"
3. Stand in front of camera
4. Press **1-6** to try different outfits
5. Press **A** to analyze yourself
6. Check recommendations panel
7. Chat with fashion bot
8. Press **Q** to quit

Enjoy! 👗✨

