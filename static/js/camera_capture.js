/**
 * VastraVista - Camera Capture and Image Upload
 */

// ============================================================
// AGGRESSIVE CACHE CLEARING - CRITICAL FOR FRESH ANALYSIS
// ============================================================
(function() {
    console.log('🧹 AGGRESSIVE CACHE CLEARING INITIATED');
    
    // Clear ALL sessionStorage (not just analysisResults)
    sessionStorage.clear();
    console.log('✅ SessionStorage completely cleared');
    
    // Clear ALL localStorage as well (belt and suspenders)
    localStorage.clear();
    console.log('✅ LocalStorage completely cleared');
    
    // Force browser to not cache this page
    if (performance.navigation.type === 1) {
        console.log('🔄 Page was refreshed - ensuring fresh state');
    }
    
    console.log('✅ All caches cleared - ready for fresh analysis');
})();

let stream = null;
let selectedFile = null;

// DOM Elements
const webcam = document.getElementById('webcam');
const startCameraBtn = document.getElementById('startCamera');
const captureImageBtn = document.getElementById('captureImage');
const stopCameraBtn = document.getElementById('stopCamera');
const fileInput = document.getElementById('fileInput');
const uploadButton = document.getElementById('uploadButton');
const fileName = document.getElementById('fileName');
const loading = document.getElementById('loading');
const canvas = document.getElementById('canvas');

// Camera Controls
startCameraBtn.addEventListener('click', startCamera);
captureImageBtn.addEventListener('click', captureAndAnalyze);
stopCameraBtn.addEventListener('click', stopCamera);

// File Upload
fileInput.addEventListener('change', handleFileSelect);
uploadButton.addEventListener('click', uploadAndAnalyze);

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            } 
        });
        
        webcam.srcObject = stream;
        
        startCameraBtn.disabled = true;
        captureImageBtn.disabled = false;
        stopCameraBtn.disabled = false;
        
        console.log('✅ Camera started');
    } catch (error) {
        console.error('Camera error:', error);
        alert('Could not access camera. Please check permissions.');
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        webcam.srcObject = null;
        stream = null;
        
        startCameraBtn.disabled = false;
        captureImageBtn.disabled = true;
        stopCameraBtn.disabled = true;
        
        console.log('🛑 Camera stopped');
    }
}

async function captureAndAnalyze() {
    try {
        // Capture image from webcam
        canvas.width = webcam.videoWidth;
        canvas.height = webcam.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(webcam, 0, 0);
        
        // Convert to blob
        canvas.toBlob(async (blob) => {
            if (!blob) {
                alert('Failed to capture image');
                return;
            }
            
            // Create FormData
            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');
            formData.append('enhance', 'true');
            
            // Stop camera
            stopCamera();
            
            // Send to API
            await analyzeImage(formData);
        }, 'image/jpeg', 0.95);
        
    } catch (error) {
        console.error('Capture error:', error);
        alert('Failed to capture image. Please try again.');
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        alert('Invalid file type. Please upload JPG, PNG, or WEBP image.');
        return;
    }
    
    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('File too large. Maximum size is 10MB.');
        return;
    }
    
    selectedFile = file;
    fileName.textContent = `Selected: ${file.name}`;
    uploadButton.style.display = 'inline-block';
    
    console.log('✅ File selected:', file.name);
}

// Helper function to convert file/blob to base64 data URL
function fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e);
        reader.readAsDataURL(file);
    });
}

async function uploadAndAnalyze() {
    if (!selectedFile) {
        alert('Please select a file first');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('enhance', 'true');
    
    await analyzeImage(formData);
}

async function analyzeImage(formData) {
    try {
        // CRITICAL: Clear any old cached results first!
        sessionStorage.removeItem('analysisResults');
        console.log('🗑️ Cleared old analysis cache');
        
        // Convert uploaded image to base64 for display in results
        const imageFile = formData.get('image');
        const imageDataUrl = await fileToDataUrl(imageFile);
        
        // Show loading
        loading.style.display = 'block';
        startCameraBtn.disabled = true;
        captureImageBtn.disabled = true;
        uploadButton.disabled = true;
        
        // Scroll to loading section
        loading.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        console.log('🔍 Sending image for analysis...');
        
        // Start progress animation
        animateProgress();
        
        // Send to API
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Analysis failed');
        }
        
        console.log('✅ Analysis complete:', data);
        
        // Complete all steps
        completeAllSteps();
        
        // Wait a moment to show completion
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Add timestamp and image to results for cache validation
        data.analysisTimestamp = Date.now();
        data.analyzedImage = imageDataUrl;  // Store image for display
        
        // Store results - CRITICAL: ensure this completes before redirect
        const resultsJson = JSON.stringify(data);
        sessionStorage.setItem('analysisResults', resultsJson);
        
        // Verify storage succeeded
        const stored = sessionStorage.getItem('analysisResults');
        if (!stored) {
            throw new Error('Failed to store analysis results');
        }
        
        console.log('✅ New results stored with timestamp:', data.analysisTimestamp);
        console.log('📦 Stored data size:', resultsJson.length, 'bytes');
        
        // Small delay to ensure storage is flushed, then redirect
        await new Promise(resolve => setTimeout(resolve, 100));
        window.location.href = '/api/results';
        
    } catch (error) {
        console.error('❌ Analysis error:', error);
        alert(`Analysis failed: ${error.message}`);
        
        // Hide loading
        loading.style.display = 'none';
        startCameraBtn.disabled = false;
        uploadButton.disabled = false;
        resetProgressSteps();
    }
}

function animateProgress() {
    const steps = [
        { id: 'step1', delay: 200 },   // Upload
        { id: 'step2', delay: 1500 },  // Face detection
        { id: 'step3', delay: 3000 },  // Gender (DeepFace takes time)
        { id: 'step4', delay: 5000 },  // Age (DeepFace takes time)
        { id: 'step5', delay: 7000 },  // Color analysis
        { id: 'step6', delay: 9000 }   // Recommendations
    ];
    
    steps.forEach(({ id, delay }) => {
        setTimeout(() => {
            const step = document.getElementById(id);
            if (step) {
                // Mark previous steps as completed
                const allSteps = document.querySelectorAll('.progress-step');
                let foundCurrent = false;
                allSteps.forEach(s => {
                    if (s.id === id) {
                        foundCurrent = true;
                        s.classList.add('active');
                    } else if (!foundCurrent) {
                        s.classList.remove('active');
                        s.classList.add('completed');
                    }
                });
            }
        }, delay);
    });
}

function completeAllSteps() {
    const allSteps = document.querySelectorAll('.progress-step');
    allSteps.forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
    });
}

function resetProgressSteps() {
    const allSteps = document.querySelectorAll('.progress-step');
    allSteps.forEach(step => {
        step.classList.remove('active', 'completed');
    });
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopCamera();
});
