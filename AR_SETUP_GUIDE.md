# VastraVista AR Setup Guide

## ✅ Installation

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure MediaPipe is installed
pip install mediapipe>=0.10.0

# For Mac Apple Silicon (M1/M2/M3/M4)
# MediaPipe should work natively
```

### 2. Verify Installation

```bash
# Test MediaPipe
python -c "import mediapipe as mp; print('MediaPipe OK')"

# Test OpenCV
python -c "import cv2; print(f'OpenCV {cv2.__version__}')"
```

## 🚀 Running the Application

### Development Mode

```bash
# Set environment
export FLASK_APP=run.py
export FLASK_ENV=development

# Run server
python run.py
```

### Production Mode

```bash
# Use gunicorn or uwsgi
gunicorn -w 4 -b 0.0.0.0:5002 run:app
```

## 🧪 Testing the AR API

### 1. Health Check

```bash
curl http://localhost:5002/api/health
```

Expected response:
```json
{
  "status": "ok",
  "models_loaded": true,
  "mps_available": true,
  "fps_estimate": 5.0,
  "half_body_support": true
}
```

### 2. Test AR Try-On

```bash
# Create test image (or use existing)
# Then test API:

curl -X POST http://localhost:5002/api/ar/apply-clothing \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -F "frame=@test_image.jpg" \
  -F "clothing_type=tshirt" \
  -F "session_id=test_123" \
  -F "color=#667eea"
```

### 3. Check Logs

```bash
# View recent errors
curl http://localhost:5002/api/logs

# View application logs
tail -f logs/app.log
```

## 📋 Frontend Integration

### Basic Example

```javascript
// Initialize session
const sessionId = `ar_session_${Date.now()}`;

// Capture frame from video
const video = document.getElementById('arVideo');
const canvas = document.createElement('canvas');
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;
const ctx = canvas.getContext('2d');
ctx.drawImage(video, 0, 0);

// Convert to blob
canvas.toBlob(async (blob) => {
    const formData = new FormData();
    formData.append('frame', blob, 'frame.jpg');
    formData.append('clothing_type', 'tshirt');
    formData.append('session_id', sessionId);
    formData.append('color', '#667eea');
    
    const response = await fetch('/api/ar/apply-clothing', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    if (result.success) {
        // Display result.image
        const img = new Image();
        img.src = result.image;
        document.getElementById('result').appendChild(img);
    }
}, 'image/jpeg', 0.9);
```

## 🔧 Configuration

### Environment Variables

```bash
# .env file
FLASK_ENV=development
UPLOAD_FOLDER=data/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
```

### AR Settings

The AR engine uses these defaults:
- Confidence threshold: 60%
- Temporal smoothing: Last 5 frames
- Freeze-last-stable: Enabled
- Half-body mode: Enabled (shoulders + face only)

## 🐛 Troubleshooting

### Issue: 400 Bad Request

**Solution**: Check field names match API contract:
- Use `frame` not `image`
- Use `clothing_type` not `outfit_type`
- Include `session_id`

### Issue: No pose detected

**Solution**:
- Ensure good lighting
- Show shoulders and face clearly
- Move closer to camera
- Check MediaPipe is installed

### Issue: Red segmentation mask

**Solution**: This should NOT happen. The new system uses real clothing shapes, not segmentation masks. If you see this, check:
- Using correct API endpoint
- Using half-body AR engine
- Not using old code paths

### Issue: Clothes disappear

**Solution**: The new system uses freeze-last-stable. Clothes should stay visible even with low confidence. If they disappear:
- Check confidence threshold (should freeze below 60%)
- Verify freeze_on_low_confidence is True
- Check last_stable_cloth is being maintained

## 📊 Performance

### Expected FPS

- Backend processing: ~5 FPS (200ms per frame)
- Frontend display: 60 FPS (cached frames)
- Total latency: ~80-100ms per frame

### Optimization Tips

1. Reduce image size before sending
2. Use frame caching in frontend
3. Process every 3-5 frames, not every frame
4. Use lower quality JPEG compression (0.85)

## ✅ Verification Checklist

- [ ] MediaPipe installed and working
- [ ] Health endpoint returns OK
- [ ] AR API accepts correct field names
- [ ] Half-body pose detection works
- [ ] Clothing overlay appears (not segmentation mask)
- [ ] Freeze-last-stable works (clothes don't disappear)
- [ ] No 400 errors with correct request format
- [ ] Logs endpoint shows recent requests

## 📝 Next Steps

1. Test with real camera feed
2. Verify all clothing types work
3. Test with different lighting conditions
4. Verify freeze-last-stable behavior
5. Check performance on Mac M-series

