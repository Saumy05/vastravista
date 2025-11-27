# AR API Examples & Testing Guide

## ✅ API Contract

### POST /api/ar/apply-clothing

**Content-Type**: `multipart/form-data`

**Required Fields**:
- `frame` (file) - Image file (jpg, jpeg, png, webp)
- `clothing_type` (string) - One of: `tshirt`, `shirt`, `kurta`, `dress`, `hoodie`, `jacket`
- `session_id` (string) - Unique session identifier

**Optional Fields**:
- `color` (string) - Hex color code (e.g., `#667eea` or `667eea`)
- `template_id` (string) - Template identifier
- `pose_landmarks` (JSON string) - Pre-detected pose landmarks
- `timestamp` (string) - Timestamp

**Response**:
```json
{
  "success": true,
  "image": "data:image/jpeg;base64,...",
  "clothing_type": "tshirt",
  "confidence": 0.85,
  "frozen": false
}
```

## 📝 Frontend Examples

### Using fetch()

```javascript
async function applyClothing(frameBlob, clothingType, sessionId, color = '#667eea') {
    const formData = new FormData();
    formData.append('frame', frameBlob, 'frame.jpg');
    formData.append('clothing_type', clothingType);
    formData.append('session_id', sessionId);
    formData.append('color', color);
    formData.append('timestamp', Date.now().toString());
    
    try {
        const response = await fetch('/api/ar/apply-clothing', {
            method: 'POST',
            body: formData,
            // Note: Don't set Content-Type header, browser will set it with boundary
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('API Error:', error);
            return null;
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Request failed:', error);
        return null;
    }
}

// Usage
const video = document.getElementById('arVideo');
const canvas = document.createElement('canvas');
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;
const ctx = canvas.getContext('2d');
ctx.drawImage(video, 0, 0);

canvas.toBlob(async (blob) => {
    const result = await applyClothing(blob, 'tshirt', 'session_123', '#667eea');
    if (result && result.success) {
        const img = new Image();
        img.src = result.image;
        // Display image
    }
}, 'image/jpeg', 0.9);
```

### Using axios

```javascript
import axios from 'axios';

async function applyClothingAxios(frameBlob, clothingType, sessionId, color = '#667eea') {
    const formData = new FormData();
    formData.append('frame', frameBlob, 'frame.jpg');
    formData.append('clothing_type', clothingType);
    formData.append('session_id', sessionId);
    formData.append('color', color);
    
    try {
        const response = await axios.post('/api/ar/apply-clothing', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        return response.data;
    } catch (error) {
        if (error.response) {
            console.error('API Error:', error.response.data);
        } else {
            console.error('Request failed:', error.message);
        }
        return null;
    }
}
```

## 🧪 cURL Examples

### Basic Request

```bash
curl -X POST http://localhost:5002/api/ar/apply-clothing \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "frame=@/path/to/image.jpg" \
  -F "clothing_type=tshirt" \
  -F "session_id=test_session_123" \
  -F "color=#667eea"
```

### With All Optional Fields

```bash
curl -X POST http://localhost:5002/api/ar/apply-clothing \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "frame=@/path/to/image.jpg" \
  -F "clothing_type=kurta" \
  -F "session_id=test_session_456" \
  -F "color=#ff6b6b" \
  -F "template_id=template_1" \
  -F "timestamp=1234567890"
```

### Test Health Endpoint

```bash
curl http://localhost:5002/api/health
```

### Get Recent Logs

```bash
curl -X GET http://localhost:5002/api/logs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 🔍 Error Responses

### Validation Error (400)

```json
{
  "success": false,
  "error": "Validation failed",
  "errors": [
    {
      "field": "frame",
      "error": "Required field \"frame\" (image file) is missing",
      "received_fields": ["image"],
      "expected": "frame"
    }
  ],
  "received_content_type": "multipart/form-data",
  "received_form_fields": ["outfit_type", "color"],
  "received_file_fields": ["image"]
}
```

### Processing Error (400)

```json
{
  "success": false,
  "error": "No pose detected",
  "confidence": 0.0
}
```

## ✅ Testing Checklist

1. **Test with correct fields**:
   ```bash
   curl -X POST http://localhost:5002/api/ar/apply-clothing \
     -F "frame=@test.jpg" \
     -F "clothing_type=tshirt" \
     -F "session_id=test_123"
   ```
   Expected: `200 OK` with image data

2. **Test with missing required field**:
   ```bash
   curl -X POST http://localhost:5002/api/ar/apply-clothing \
     -F "frame=@test.jpg" \
     -F "clothing_type=tshirt"
   ```
   Expected: `400 Bad Request` with validation error

3. **Test with invalid clothing_type**:
   ```bash
   curl -X POST http://localhost:5002/api/ar/apply-clothing \
     -F "frame=@test.jpg" \
     -F "clothing_type=invalid" \
     -F "session_id=test_123"
   ```
   Expected: `400 Bad Request` with validation error

4. **Test health endpoint**:
   ```bash
   curl http://localhost:5002/api/health
   ```
   Expected: `200 OK` with system status

## 🐛 Debugging

### Check Logs

```bash
# View recent errors
curl http://localhost:5002/api/logs?limit=10

# Check application logs
tail -f logs/app.log
```

### Common Issues

1. **400 Bad Request**: Check field names match API contract
2. **Missing frame**: Ensure file is uploaded as 'frame' not 'image'
3. **Invalid clothing_type**: Must be one of: tshirt, shirt, kurta, dress, hoodie, jacket
4. **Missing session_id**: Required field, provide unique identifier

