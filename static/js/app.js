// VastraVista 3.0 - Main Application JavaScript
// Handles all UI interactions and API calls

// Global state
const appState = {
    currentAnalysis: null,
    monkScaleData: null,
    cameraStream: null,
    arStream: null,
};

// DOM Elements
let elements = {};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
    loadMonkScaleData();
});

function initializeElements() {
    elements = {
        // Tabs
        tabs: document.querySelectorAll('.tab'),
        tabContents: document.querySelectorAll('.tab-content'),
        featureCards: document.querySelectorAll('.feature-card'),
        
        // Analysis tab
        uploadArea: document.getElementById('uploadArea'),
        fileInput: document.getElementById('fileInput'),
        startCamera: document.getElementById('startCamera'),
        captureBtn: document.getElementById('captureBtn'),
        stopCamera: document.getElementById('stopCamera'),
        webcam: document.getElementById('webcam'),
        cameraPreview: document.getElementById('cameraPreview'),
        analysisResults: document.getElementById('analysisResults'),
        
        // Wardrobe tab
        
        
        // Colors tab
        loadMonkScale: document.getElementById('loadMonkScale'),
        compareColors: document.getElementById('compareColors'),
        seasonalPalette: document.getElementById('seasonalPalette'),
        monkLevels: document.getElementById('monkLevels'),
        colorRecommendations: document.getElementById('colorRecommendations'),
        colorPalette: document.getElementById('colorPalette'),
        
        // AI Advice tab
        aiSkinTone: document.getElementById('aiSkinTone'),
        aiMonkLevel: document.getElementById('aiMonkLevel'),
        aiOccasion: document.getElementById('aiOccasion'),
        aiStylePrefs: document.getElementById('aiStylePrefs'),
        getAIAdvice: document.getElementById('getAIAdvice'),
        aiAdviceResults: document.getElementById('aiAdviceResults'),
        aiAdviceContent: document.getElementById('aiAdviceContent'),
        
        // AR tab
        startARCamera: document.getElementById('startARCamera'),
        stopARCamera: document.getElementById('stopARCamera'),
        arPreview: document.getElementById('arPreview'),
        arCanvas: document.getElementById('arCanvas'),
        colorTryBtns: document.querySelectorAll('.color-try-btn'),
        
        // Shopping tab
        
        
        // Analytics tab
        
        
        // Loading overlay
        loadingOverlay: document.getElementById('loadingOverlay'),
        loadingText: document.getElementById('loadingText'),
        loadingSubtext: document.getElementById('loadingSubtext'),
        progressFill: document.getElementById('progressFill'),
        
        // Canvas
        canvas: document.getElementById('canvas')
    };
}

function setupEventListeners() {
    // Tab navigation
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Feature cards navigation
    elements.featureCards.forEach(card => {
        card.addEventListener('click', () => {
            const feature = card.dataset.feature;
            if (feature) switchTab(feature);
        });
    });
    
    // Analysis tab
    if (elements.uploadArea && elements.fileInput) {
        elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
        elements.uploadArea.addEventListener('dragover', handleDragOver);
        elements.uploadArea.addEventListener('dragleave', handleDragLeave);
        elements.uploadArea.addEventListener('drop', handleDrop);
        elements.fileInput.addEventListener('change', handleFileSelect);
    }
    if (elements.startCamera) {
        elements.startCamera.addEventListener('click', startWebcam);
    }
    if (elements.captureBtn) {
        elements.captureBtn.addEventListener('click', captureImage);
    }
    if (elements.stopCamera) {
        elements.stopCamera.addEventListener('click', stopWebcam);
    }
    
    // Wardrobe tab
    
    
    // Colors tab
    elements.loadMonkScale.addEventListener('click', displayMonkScale);
    elements.compareColors.addEventListener('click', showColorComparison);
    elements.seasonalPalette.addEventListener('click', showSeasonalPalette);
    
    // AI Advice tab
    elements.getAIAdvice.addEventListener('click', getAIFashionAdvice);
    
    // AR tab
    elements.startARCamera.addEventListener('click', startARMode);
    elements.stopARCamera.addEventListener('click', stopARMode);
    elements.colorTryBtns.forEach(btn => {
        btn.addEventListener('click', () => applyARColor(btn.dataset.color));
    });
    
    // Shopping tab
    
    
    // Analytics tab
    
}

// ============ TAB SWITCHING ============
function switchTab(tabName) {
    // Update tab buttons
    elements.tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab contents
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
}

// ============ ANALYSIS TAB ============
function handleDragOver(e) {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        // Clear previous results and image
        elements.analysisResults.innerHTML = '';
        elements.analysisResults.classList.add('hidden');
        if (appState.currentImageUrl) {
            URL.revokeObjectURL(appState.currentImageUrl);
        }
        processImage(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        // Clear previous results and image
        elements.analysisResults.innerHTML = '';
        elements.analysisResults.classList.add('hidden');
        if (appState.currentImageUrl) {
            URL.revokeObjectURL(appState.currentImageUrl);
        }
        processImage(files[0]);
    }
}

async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'user' } 
        });
        appState.cameraStream = stream;
        elements.webcam.srcObject = stream;
        elements.cameraPreview.style.display = 'block';
        elements.startCamera.style.display = 'none';
        elements.captureBtn.style.display = 'inline-block';
        elements.stopCamera.style.display = 'inline-block';
    } catch (error) {
        console.error('Camera error:', error);
        alert('Could not access camera. Please check permissions.');
    }
}

function stopWebcam() {
    if (appState.cameraStream) {
        appState.cameraStream.getTracks().forEach(track => track.stop());
        appState.cameraStream = null;
    }
    elements.webcam.srcObject = null;
    elements.cameraPreview.style.display = 'none';
    elements.startCamera.style.display = 'inline-block';
    elements.captureBtn.style.display = 'none';
    elements.stopCamera.style.display = 'none';
}

function captureImage() {
    const ctx = elements.canvas.getContext('2d');
    elements.canvas.width = elements.webcam.videoWidth;
    elements.canvas.height = elements.webcam.videoHeight;
    ctx.drawImage(elements.webcam, 0, 0);
    
    elements.canvas.toBlob(blob => {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        // Clear previous results and image
        elements.analysisResults.innerHTML = '';
        elements.analysisResults.classList.add('hidden');
        if (appState.currentImageUrl) {
            URL.revokeObjectURL(appState.currentImageUrl);
        }
        processImage(file);
        stopWebcam();
    }, 'image/jpeg');
}

async function processImage(file) {
    // Store the image file for display
    const imageUrl = URL.createObjectURL(file);
    appState.currentImageUrl = imageUrl;
    if (elements.analysisResults) {
        let w = 0, h = 0;
        try {
            const bmp = await createImageBitmap(file);
            w = bmp.width; h = bmp.height; bmp.close();
        } catch (e) {}
        const containerStyle = w && h
            ? `width:100%; max-width:480px; aspect-ratio: ${w} / ${h}; margin:0 auto; border-radius:12px; border:3px solid #667eea; background:#f8f9ff; display:flex; align-items:center; justify-content:center; overflow:hidden;`
            : `width:100%; max-width:480px; min-height:220px; margin:0 auto; border-radius:12px; border:3px solid #667eea; background:#f8f9ff; display:flex; align-items:center; justify-content:center; overflow:hidden;`;
        const previewHtml = `
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4 style="color:#667eea; margin-bottom:10px; text-align:center;">Analyzing Selected Image…</h4>
                <div style="${containerStyle}">
                    <img src="${imageUrl}" alt="Selected image" style="max-width:100%; max-height:100%; object-fit:contain; border-radius:8px;" />
                </div>
            </div>`;
        elements.analysisResults.innerHTML = previewHtml;
        elements.analysisResults.classList.remove('hidden');
    }
    
    showLoading('Analyzing image...', 'Detecting face and extracting features');
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        updateProgress(10);
        elements.loadingSubtext.textContent = 'Step 1/5: Detecting face...';
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(30);
        elements.loadingSubtext.textContent = 'Step 2/5: Analyzing gender with multiple AI models...';
        
        await new Promise(resolve => setTimeout(resolve, 500)); // Show progress
        updateProgress(50);
        elements.loadingSubtext.textContent = 'Step 3/5: Detecting age range...';
        
        await new Promise(resolve => setTimeout(resolve, 500));
        updateProgress(70);
        elements.loadingSubtext.textContent = 'Step 4/5: Analyzing skin tone with Monk Scale...';
        
        await new Promise(resolve => setTimeout(resolve, 500));
        updateProgress(90);
        elements.loadingSubtext.textContent = 'Step 5/5: Generating color recommendations...';
        
        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        updateProgress(100);
        
        appState.currentAnalysis = result;
        
        setTimeout(() => {
            hideLoading();
            displayAnalysisResults(result);
        }, 500);
        
    } catch (error) {
        console.error('Analysis error:', error);
        hideLoading();
        alert('Analysis failed: ' + error.message);
    }
}

function displayAnalysisResults(result) {
    console.log('Full API Response:', result); // Debug log
    
    // Extract data from nested structure
    const data = result.data || result;
    
    // Check if multiple faces detected
    const numFaces = data.num_faces || (data.faces ? data.faces.length : 1);
    const isMultipleFaces = numFaces > 1;
    
    let html = '';
    
    // Display uploaded image and AI insights at the top
    {
        const skinData = data.skin_tone || {};
        const skinHex = skinData.hex || '#000000';
        const skinRgb = skinData.rgb || [0, 0, 0];
        const monkLevel = skinData.monk_scale_level || 'N/A';
        const bRaw = skinData.brightness || skinData.brightness_val;
        const brightness = typeof bRaw === 'number' ? `${Math.max(0, Math.min(100, Math.round((bRaw/255)*100)))}%` : (bRaw || 'N/A');
        const undertone = skinData.undertone || '';
        const backendPath = data.image_path || '';
        const fileName = backendPath ? backendPath.split('/').pop() : '';
        const displayUrl = appState.currentImageUrl || (fileName ? '/uploads/' + fileName : '');
        
        html += `
            <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 30px;">
                <h3 style="color: #667eea; margin-bottom: 20px; text-align: center; font-size: 1.8em;">📸 Your Analyzed Photo</h3>
                <div style="display: flex; gap: 30px; align-items: start; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <div style="width: 100%; max-width: 480px; min-height: 220px; margin: 0 auto; border-radius: 12px; border: 4px solid #667eea; background: #f8f9ff; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 30px rgba(0,0,0,0.12); overflow: hidden;">
                            ${displayUrl ? `
                                <img src="${displayUrl}" data-backend="${backendPath}" onerror="handleAnalyzedImageError(this)" onload="if(this.naturalWidth&&this.naturalHeight){this.parentElement.style.aspectRatio=this.naturalWidth+' / '+this.naturalHeight;}" alt="Analyzed Person" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px;" />
                            ` : `
                                <div style="text-align:center; color:#667eea; font-weight:600;">Image loading...</div>
                            `}
                        </div>
                        <div style="margin-top: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px; border-radius: 8px; font-weight: 600; text-align:center;">✅ Analysis Complete</div>
                        ${data.verification ? `
                        <div style="margin-top: 10px; background: ${data.verification.verified ? 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)' : 'linear-gradient(135deg, #FFA726 0%, #FF9800 100%)'}; color: white; padding: 10px; border-radius: 8px; font-size: 0.9em; text-align:center;">
                            ${data.verification.verified ? '✓' : '⚠'} AI Verified: ${data.verification.confidence}%
                            <div style="font-size: 0.8em; opacity: 0.9; margin-top: 5px;">${data.verification.method}</div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <!-- Skin Tone Visualization -->
                    <div style="flex: 1; min-width: 300px; background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%); 
                                padding: 25px; border-radius: 12px; border: 2px solid #667eea;">
                        <h4 style="color: #667eea; margin-bottom: 20px; font-size: 1.4em;">🎨 Detected Skin Tone</h4>
                        
                        <!-- Large Skin Color Swatch -->
                        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                            <div style="background-color: ${skinHex}; 
                                        width: 150px; height: 150px; 
                                        border-radius: 50%; 
                                        box-shadow: 0 8px 25px rgba(0,0,0,0.3), inset 0 2px 10px rgba(255,255,255,0.3);
                                        border: 5px solid white;"></div>
                        </div>
                        
                        <!-- Color Details -->
                        <div style="text-align: center; margin-bottom: 15px;">
                            <div style="font-size: 1.3em; font-weight: bold; color: #333; margin-bottom: 8px;">
                                ${skinHex}
                            </div>
                            <div style="font-size: 0.95em; color: #666;">
                                RGB(${skinRgb[0]}, ${skinRgb[1]}, ${skinRgb[2]})
                            </div>
                        </div>
                        
                        <!-- Monk Scale Info -->
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="font-weight: 600; color: #667eea;">Monk Scale:</span>
                                <span style="font-size: 1.2em; font-weight: bold; color: #764ba2;">${monkLevel}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 600; color: #667eea;">Brightness:</span>
                                <span style="color: #333;">${brightness}</span>
                            </div>
                            ${undertone ? `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top:8px;">
                                <span style="font-weight: 600; color: #667eea;">Undertone:</span>
                                <span style="color: #333;">${undertone}</span>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div style="margin-top: 15px; padding: 12px; background: rgba(102, 126, 234, 0.1); 
                                    border-radius: 8px; font-size: 0.85em; color: #555; text-align: center;">
                            💡 All color recommendations are matched to YOUR unique skin tone
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Display AI vs Technical Comparison if available
        if (data.comparison && data.comparison.comparison_available) {
            const comp = data.comparison;
            const score = comp.agreement_score || 0;
            
            // Color coding for agreement score
            let scoreColor, scoreGrade, scoreEmoji;
            if (score >= 90) {
                scoreColor = '#10b981'; // Green
                scoreGrade = 'Excellent';
                scoreEmoji = '✓✓';
            } else if (score >= 75) {
                scoreColor = '#3b82f6'; // Blue
                scoreGrade = 'Good';
                scoreEmoji = '✓';
            } else if (score >= 60) {
                scoreColor = '#f59e0b'; // Orange
                scoreGrade = 'Fair';
                scoreEmoji = '⚠';
            } else {
                scoreColor = '#ef4444'; // Red
                scoreGrade = 'Low';
                scoreEmoji = '⚠';
            }
            
            html += `
                <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                            padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                            color: white; margin-bottom: 30px;">
                    <h3 style="color: white; margin-bottom: 15px; font-size: 1.6em; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 1.3em;">🔄</span>
                        <span>Technical vs AI Analysis Comparison</span>
                    </h3>
                    
                    <!-- Agreement Score -->
                    <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; 
                                text-align: center; margin-bottom: 20px; border: 2px solid ${scoreColor};">
                        <div style="font-size: 3em; margin-bottom: 10px;">${scoreEmoji}</div>
                        <div style="font-size: 2.5em; font-weight: bold; color: ${scoreColor}; margin-bottom: 5px;">
                            ${score.toFixed(0)}%
                        </div>
                        <div style="font-size: 1.1em; color: rgba(255,255,255,0.9); font-weight: 500;">
                            ${scoreGrade} Agreement
                        </div>
                    </div>
                    
                    <!-- Agreements -->
                    ${comp.agreements && comp.agreements.length > 0 ? `
                        <div style="background: rgba(16, 185, 129, 0.15); padding: 18px; border-radius: 10px; 
                                    margin-bottom: 15px; border-left: 4px solid #10b981;">
                            <h4 style="color: #10b981; margin: 0 0 12px 0; font-size: 1.1em; display: flex; align-items: center; gap: 8px;">
                                <span>✓</span> Agreements
                            </h4>
                            <div style="color: rgba(255,255,255,0.9); line-height: 1.8;">
                                ${comp.agreements.map(a => `<div style="margin-bottom: 8px;">• ${a}</div>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Differences -->
                    ${comp.differences && comp.differences.length > 0 ? `
                        <div style="background: rgba(245, 158, 11, 0.15); padding: 18px; border-radius: 10px; 
                                    border-left: 4px solid #f59e0b;">
                            <h4 style="color: #f59e0b; margin: 0 0 12px 0; font-size: 1.1em; display: flex; align-items: center; gap: 8px;">
                                <span>⚠</span> Differences
                            </h4>
                            <div style="color: rgba(255,255,255,0.9); line-height: 1.8;">
                                ${comp.differences.map(d => `<div style="margin-bottom: 8px;">• ${d}</div>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div style="margin-top: 15px; font-size: 0.85em; opacity: 0.75; text-align: center; font-style: italic;">
                        🤖 AI analyzed the image independently, then compared with technical results
                    </div>
                </div>
            `;
        }

        // Display AI Insights if available
        if (data.ai_insights && data.ai_insights.success) {
            html += `
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                            color: white; margin-bottom: 30px;">
                    <h3 style="color: white; margin-bottom: 15px; font-size: 1.6em; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 1.3em;">🤖</span>
                        <span>AI Fashion Analysis</span>
                        <span style="font-size: 0.7em; background: rgba(255,255,255,0.25); padding: 5px 12px; 
                                     border-radius: 15px; font-weight: 500;">
                            ${data.ai_insights.model}
                        </span>
                    </h3>
                    <div style="background: rgba(255,255,255,0.15); padding: 22px; border-radius: 12px; 
                                backdrop-filter: blur(10px); line-height: 1.8;">
                        <p style="font-size: 1.05em; margin: 0; color: white;">
                            ${data.ai_insights.analysis}
                        </p>
                    </div>
                    <div style="margin-top: 15px; font-size: 0.9em; opacity: 0.85; text-align: center; font-style: italic;">
                        ✨ Personalized analysis generated by AI based on your unique features and color palette
                    </div>
                </div>
            `;
        }

        if (data.clothing_feedback && data.clothing_color) {
            const fb = data.clothing_feedback;
            const cc = data.clothing_color;
            const badgeColor = fb.quality === 'excellent' ? '#10b981' : (fb.quality === 'good' ? '#3b82f6' : '#ef4444');
            const badgeText = fb.quality === 'excellent' ? 'Excellent' : (fb.quality === 'good' ? 'Good' : 'Needs Improvement');
            const detectedHex = cc.hex || '#666';
            const detectedName = (cc.nearest && cc.nearest.color_name) || 'Current Color';
            const recName = (fb.closest_recommendation && (fb.closest_recommendation.color_name || fb.closest_recommendation.name)) || '';
            html += `
                <div style="background: #ffffff; padding: 24px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 30px; border-left: 6px solid ${badgeColor};">
                    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
                        <h3 style="margin:0; color:#333; font-size:1.4em; display:flex; align-items:center; gap:10px;">
                            <span>👗 Outfit Color Feedback</span>
                            <span style="background:${badgeColor}; color:white; padding:6px 10px; border-radius:12px; font-size:0.8em;">${badgeText}</span>
                        </h3>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div title="Detected" style="width:32px; height:32px; border-radius:6px; border:2px solid #ddd; background:${detectedHex}"></div>
                            ${recName ? `<div title="Closest recommended" style="width:32px; height:32px; border-radius:6px; border:2px solid ${badgeColor}; background:${(fb.closest_recommendation && fb.closest_recommendation.hex) || '#ccc'}"></div>` : ''}
                        </div>
                    </div>
                    <div style="margin-top:12px; color:#555; font-size:1em;">${fb.message}</div>
                    ${recName ? `<div style="margin-top:8px; color:#666; font-size:0.9em;">Closest recommended: <strong>${recName}</strong> • ΔE ${Number(fb.delta_e || 0).toFixed(1)}</div>` : ''}
                </div>
            `;
        }
    }
    
    if (isMultipleFaces && data.faces) {
        // MULTIPLE FACES DETECTED - Show all persons
        html += `
            <div style="background: #f8f9ff; padding: 30px; border-radius: 15px;">
                <h3 style="color: #667eea; margin-bottom: 10px;">✅ Analysis Complete</h3>
                <div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin-bottom: 30px; text-align: center;">
                    <h4 style="color: white; margin: 0; font-size: 1.3em;">👥 Detected ${numFaces} People in Image!</h4>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 0.95em;">Showing personalized analysis for each person</p>
                </div>
        `;
        
        // Display each person's analysis
        data.faces.forEach((person, index) => {
            html += generatePersonAnalysis(person, index + 1, numFaces);
        });
        
        html += '</div>';
        
    } else {
        // SINGLE FACE - Use original display format
        const genderData = data.gender || {};
        const ageData = data.age || {};
        const skinData = data.skin_tone || data.monk_scale_analysis || {};
        
        const gender = (data.final && data.final.gender) || genderData.gender || result.gender || 'Unknown';
        const genderConf = Number(genderData.confidence || 0);
        const age = (data.final && data.final.estimated_age) || ageData.estimated_age || ageData.age_group || result.age || 'N/A';
        const ageConf = Number(ageData.confidence || 0);
        const monkScale = skinData.monk_scale_level || data.monk_scale_level || result.monk_scale || 'N/A';
        const sbRaw = skinData.brightness || skinData.brightness_val;
        const skinBrightness = typeof sbRaw === 'number' ? `${Math.max(0, Math.min(100, Math.round((sbRaw/255)*100)))}%` : (sbRaw || 'N/A');
        
        // Calculate overall confidence properly (average of gender + age)
        const overallConf = (genderConf + ageConf) / 2;
        const genderConfPct = Math.max(0, Math.min(100, Math.round(genderConf <= 1 ? genderConf * 100 : genderConf)));
        const ageConfPct = Math.max(0, Math.min(100, Math.round(ageConf <= 1 ? ageConf * 100 : ageConf)));
        const overallConfPct = Math.max(0, Math.min(100, Math.round(overallConf <= 1 ? overallConf * 100 : overallConf)));
        const finalAgeNum = typeof ((data.final && data.final.estimated_age)) === 'number' ? (data.final && data.final.estimated_age) : ageData.estimated_age;
        const ageIsNumber = typeof finalAgeNum === 'number' && isFinite(finalAgeNum);
        const ageText = ageIsNumber ? `${finalAgeNum} years` : (typeof age === 'string' ? age : 'N/A');
        
        console.log('📊 Debug - Age:', age, 'AgeData:', ageData);
        console.log('📊 Debug - Gender Conf:', genderConf, 'Age Conf:', ageConf, 'Overall:', overallConf);
        
        html += `
        <div style="background: #f8f9ff; padding: 30px; border-radius: 15px;">
            <h3 style="color: #667eea; margin-bottom: 25px;">✅ Analysis Complete</h3>
            
            <div class="stats-grid">
                <div class="stat-card" style="background: ${getGradientByConfidence(genderConfPct)};">
                    <div style="font-size: 2em;">👤</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${gender}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Gender</div>
                    <div style="font-size: 0.75em; margin-top: 5px;">${genderConfPct}% confidence</div>
                </div>
                <div class="stat-card" style="background: ${getGradientByConfidence(ageConfPct)};">
                    <div style="font-size: 2em;">🎂</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${ageText}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Age</div>
                    ${ageConfPct > 0 ? `<div style="font-size: 0.75em; margin-top: 5px;">${ageConfPct}% confidence</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${monkScale !== 'N/A' ? `Level ${monkScale}` : skinBrightness}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Monk Scale</div>
                    ${skinBrightness !== 'N/A' && monkScale !== 'N/A' ? `<div style="font-size: 0.75em; margin-top: 3px;">${skinBrightness}</div>` : ''}
                </div>
                <div class="stat-card" style="background: ${getGradientByConfidence(overallConfPct)};">
                    <div style="font-size: 2em;">✨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${overallConfPct > 0 ? overallConfPct + '%' : 'N/A'}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Overall Confidence</div>
                </div>
            </div>
            
            ${genderData.models_used ? `
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 10px; border-left: 4px solid #4CAF50;">
                    <h4 style="color: #4CAF50; margin-bottom: 10px;">🔬 Analysis Details</h4>
                    <p style="color: #666; font-size: 0.95em; line-height: 1.6;">
                        <strong>Gender Detection:</strong> Used ${genderData.models_used} AI model(s) for maximum accuracy<br>
                        <strong>Method:</strong> ${genderData.method || 'Multi-model ensemble'}<br>
                        <strong>Confidence:</strong> ${genderConf.toFixed(1)}% (High accuracy)
                    </p>
                </div>
            ` : ''}
            
            ${data.best_colors ? `
                <div style="margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
                    <h3 style="color: white; margin-bottom: 20px; text-align: center; font-size: 1.8em;">✨ Colors That Suit You PERFECTLY ✨</h3>
                    
                    ${data.best_colors.excellent && data.best_colors.excellent.length > 0 ? `
                        <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                            <h4 style="color: #d63384; margin-bottom: 15px; font-size: 1.3em;">🌟 EXCELLENT MATCHES (Highly Recommended)</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-bottom: 10px;">
                                ${data.best_colors.excellent.map(color => `
                                    <div style="text-align: center;">
                                        <div style="background-color: ${color.hex}; width: 100%; height: 80px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 3px solid #d63384; margin-bottom: 8px;"></div>
                                        <div style="color: #333; font-weight: bold; font-size: 0.9em;">${color.color_name || color.name || 'Color'}</div>
                                        <div style="color: #666; font-size: 0.75em;">${color.hex}</div>
                                    </div>
                                `).join('')}
                            </div>
                            <p style="color: #d63384; font-size: 0.9em; text-align: center; margin-top: 10px; font-weight: 600;">These colors complement your skin tone beautifully!</p>
                        </div>
                    ` : ''}
                    
                    ${data.best_colors.good && data.best_colors.good.length > 0 ? `
                        <div style="background: rgba(255,255,255,0.9); padding: 20px; border-radius: 12px;">
                            <h4 style="color: #0d6efd; margin-bottom: 15px; font-size: 1.2em;">👍 GOOD MATCHES (Great Options)</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px;">
                                ${data.best_colors.good.map(color => `
                                    <div style="text-align: center;">
                                        <div style="background-color: ${color.hex}; width: 100%; height: 60px; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.2); border: 2px solid #0d6efd; margin-bottom: 6px;"></div>
                                        <div style="color: #333; font-weight: 600; font-size: 0.85em;">${color.color_name || color.name || 'Color'}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            ${data.recommendations && data.recommendations.seasonal_palette ? `
                <div style="margin-top: 25px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h4 style="color: #667eea; margin-bottom: 10px; font-size: 1.3em;">🍂 Your Personalized Seasonal Palette</h4>
                    <p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">✨ These are colors from YOUR best matches, organized by season - all perfectly suited for YOUR skin tone!</p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;">
                        ${Object.entries(data.recommendations.seasonal_palette || {}).map(([season, colors]) => `
                            <div style="padding: 18px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border: 2px solid #dee2e6;">
                                <h5 style="color: #495057; margin-bottom: 12px; text-transform: capitalize; font-size: 1.1em; font-weight: 600;">
                                    ${season === 'spring' ? '🌸' : season === 'summer' ? '☀️' : season === 'fall' ? '🍂' : '❄️'} ${season.charAt(0).toUpperCase() + season.slice(1)}
                                </h5>
                                ${colors && colors.length > 0 ? `
                                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                                        ${colors.map(color => `
                                            <div style="text-align: center;">
                                                <div style="background-color: ${color.hex}; width: 100%; height: 50px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 5px;"></div>
                                                <div style="color: #495057; font-size: 0.7em; font-weight: 500; line-height: 1.2;">${color.name || color.color_name || ''}</div>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : `<p style="color: #999; font-size: 0.85em; font-style: italic;">No perfect matches for this season</p>`}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${result.outfit_recommendations ? `
                <div style="margin-top: 30px;">
                    <h4 style="color: #667eea; margin-bottom: 15px;">👔 Outfit Suggestions</h4>
                    ${result.outfit_recommendations.map(outfit => `
                        <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>${outfit.occasion || 'General'}:</strong> ${outfit.description || outfit.suggestion || ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div style="margin-top: 30px; text-align: center;">
                <button class="btn btn-secondary" onclick="getDetailedAIAdvice()">🤖 Get AI Advice</button>
                <button class="btn btn-outline" onclick="tryARMode()">✨ Try AR Mode</button>
            </div>
        </div>
    `;
    }
    
    elements.analysisResults.innerHTML = html;
    elements.analysisResults.classList.remove('hidden');
}

function generatePersonAnalysis(person, personNum, totalPeople) {
    const genderData = person.gender || {};
    const ageData = person.age || {};
    const skinData = person.skin_tone || {};
    
    const gender = genderData.gender || 'Unknown';
    const genderConf = Number(genderData.confidence || 0);
    const genderConfPct = Math.max(0, Math.min(100, Math.round(genderConf <= 1 ? genderConf * 100 : genderConf)));
    const age = ageData.estimated_age || ageData.age_group || 'N/A';
    const monkScale = skinData.monk_scale_level || 'N/A';
    const sbRaw = skinData.brightness || skinData.brightness_val;
    const skinBrightness = typeof sbRaw === 'number' ? `${Math.max(0, Math.min(100, Math.round((sbRaw/255)*100)))}%` : (sbRaw || 'N/A');
    const overallConfRaw = ((genderData.confidence || 0) + (ageData.confidence || 0)) / 2;
    const overallConfPct = Math.max(0, Math.min(100, Math.round(overallConfRaw <= 1 ? overallConfRaw * 100 : overallConfRaw)));
    const ageConfPct = Math.max(0, Math.min(100, Math.round((Number(ageData.confidence || 0)) <= 1 ? Number(ageData.confidence || 0) * 100 : Number(ageData.confidence || 0))));
    const ageIsNumber = typeof ageData.estimated_age === 'number' && isFinite(ageData.estimated_age);
    const ageText = ageIsNumber ? `${ageData.estimated_age} years` : (typeof age === 'string' ? age : 'N/A');
    
    return `
        <div style="margin-bottom: 40px; padding: 25px; background: white; border-radius: 15px; border: 3px solid ${personNum === 1 ? '#667eea' : '#764ba2'}; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e0e0e0;">
                <h3 style="color: ${personNum === 1 ? '#667eea' : '#764ba2'}; margin: 0;">
                    ${personNum === 1 ? '🙋' : personNum === 2 ? '🙋‍♂️' : '👤'} Person ${personNum} of ${totalPeople}
                </h3>
                <div style="padding: 8px 16px; background: linear-gradient(135deg, ${personNum === 1 ? '#667eea' : '#764ba2'} 0%, ${personNum === 1 ? '#764ba2' : '#9b59b6'} 100%); border-radius: 20px; color: white; font-weight: bold;">
                    ${gender} ${genderData.models_used ? `• ${genderData.models_used} AI Models` : ''}
                </div>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 25px;">
                <div class="stat-card" style="background: ${getGradientByConfidence(genderConfPct)};">
                    <div style="font-size: 2em;">👤</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${gender}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Gender</div>
                    <div style="font-size: 0.75em; margin-top: 5px;">${genderConfPct}% confidence</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎂</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${ageText}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Age</div>
                    ${ageConfPct > 0 ? `<div style="font-size: 0.75em; margin-top: 5px;">${ageConfPct}% confidence</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${monkScale !== 'N/A' ? `Level ${monkScale}` : skinBrightness}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Monk Scale</div>
                    ${skinBrightness !== 'N/A' && monkScale !== 'N/A' ? `<div style="font-size: 0.75em; margin-top: 3px;">${skinBrightness}</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">✨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${overallConfPct > 0 ? overallConfPct + '%' : 'N/A'}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Confidence</div>
                </div>
            </div>
            
            ${person.best_colors ? `
                <div style="margin-top: 25px; padding: 20px; background: linear-gradient(135deg, ${personNum === 1 ? '#667eea' : '#764ba2'} 0%, ${personNum === 1 ? '#764ba2' : '#9b59b6'} 100%); border-radius: 12px; color: white;">
                    <h4 style="color: white; margin-bottom: 15px; font-size: 1.3em;">✨ Best Colors for Person ${personNum}</h4>
                    ${person.clothing_feedback && person.clothing_color ? `
                        <div style="background:#ffffff; color:#333; padding:16px; border-radius:10px; margin-bottom:16px; border-left:5px solid ${person.clothing_feedback.quality === 'excellent' ? '#10b981' : (person.clothing_feedback.quality === 'good' ? '#3b82f6' : '#ef4444')};">
                            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                                <div style="font-weight:600;">👗 Outfit Color Feedback</div>
                                <div style="display:flex; gap:8px;">
                                    <div title="Detected" style="width:24px; height:24px; border-radius:6px; border:2px solid #ddd; background:${person.clothing_color.hex}"></div>
                                    ${person.clothing_feedback.closest_recommendation ? `<div title="Closest recommended" style="width:24px; height:24px; border-radius:6px; border:2px solid #ddd; background:${person.clothing_feedback.closest_recommendation.hex || '#ccc'}"></div>` : ''}
                                </div>
                            </div>
                            <div style="margin-top:8px; font-size:0.95em;">${person.clothing_feedback.message}</div>
                            ${person.clothing_feedback.closest_recommendation ? `<div style="margin-top:6px; font-size:0.85em; color:#666;">Closest recommended: <strong>${person.clothing_feedback.closest_recommendation.color_name || person.clothing_feedback.closest_recommendation.name}</strong> • ΔE ${Number(person.clothing_feedback.delta_e || 0).toFixed(1)}</div>` : ''}
                        </div>
                    ` : ''}
                    ${person.best_colors.excellent && person.best_colors.excellent.length > 0 ? `
                        <div style="background: rgba(255,255,255,0.95); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <h5 style="color: #d63384; margin-bottom: 12px;">🌟 EXCELLENT MATCHES</h5>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 12px;">
                                ${person.best_colors.excellent.map(color => `
                                    <div style="text-align: center;">
                                        <div style="background-color: ${color.hex}; width: 100%; height: 60px; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.3); border: 2px solid #d63384; margin-bottom: 6px;"></div>
                                        <div style="color: #333; font-weight: bold; font-size: 0.8em;">${color.color_name || color.name || 'Color'}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${person.best_colors.good && person.best_colors.good.length > 0 ? `
                        <div style="background: rgba(255,255,255,0.9); padding: 15px; border-radius: 10px;">
                            <h5 style="color: #0d6efd; margin-bottom: 12px;">👍 GOOD MATCHES</h5>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px;">
                                ${person.best_colors.good.map(color => `
                                    <div style="text-align: center;">
                                        <div style="background-color: ${color.hex}; width: 100%; height: 50px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); border: 2px solid #0d6efd; margin-bottom: 5px;"></div>
                                        <div style="color: #333; font-weight: 600; font-size: 0.75em;">${color.color_name || color.name || 'Color'}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

// (Wardrobe feature removed)

// ============ COLORS TAB ============
async function loadMonkScaleData() {
    try {
        const response = await fetch('/api/v2/monk-scale-info');
        if (response.ok) {
            const data = await response.json();
            appState.monkScaleData = data;
        }
    } catch (error) {
        console.error('Error loading Monk Scale:', error);
    }
}

function displayMonkScale() {
    if (!appState.monkScaleData) {
        alert('Loading Monk Scale data...');
        loadMonkScaleData().then(() => displayMonkScale());
        return;
    }
    
    const levels = appState.monkScaleData.monk_scale_levels || {};
    const html = Object.entries(levels).map(([level, data]) => `
        <div class="monk-level" data-level="${level}" style="background-color: ${data.reference_rgb ? rgbToHex(data.reference_rgb) : '#ccc'}; color: ${shouldUseDarkText(data.reference_rgb) ? '#000' : '#fff'};"
             onclick="showColorRecommendationsForLevel('${level}')">
            <strong>${level}</strong>
            <p style="margin-top: 5px; font-size: 0.9em;">${data.description || ''}</p>
        </div>
    `).join('');
    
    elements.monkLevels.innerHTML = html;
}

function showColorRecommendationsForLevel(level) {
    if (!appState.monkScaleData) return;
    
    const levelData = appState.monkScaleData.monk_scale_levels[level];
    if (!levelData) return;
    
    // Highlight selected level
    document.querySelectorAll('.monk-level').forEach(el => {
        el.classList.toggle('selected', el.dataset.level === level);
    });
    
    document.getElementById('selectedLevel').textContent = `${level} - ${levelData.description}`;
    
    // Generate color recommendations from backend data
    const colorMap = {
        'Navy': '#001F3F', 'Burgundy': '#800020', 'Deep Purple': '#440055',
        'Emerald': '#50C878', 'Coral': '#FF7F50', 'Royal Blue': '#4169E1',
        'Wine': '#722F37', 'Teal': '#008080', 'Gold': '#FFD700', 'Rust': '#B7410E',
        'Mustard': '#FFDB58', 'Bronze': '#CD7F32', 'Warm golds': '#FFD700',
        'Olive': '#808000', 'Terracotta': '#E2725B', 'Chocolate': '#7B3F00',
        'Copper': '#B87333', 'Deep red': '#8B0000', 'Amber': '#FFBF00',
        'Cobalt': '#0047AB', 'Orange': '#FF8C00', 'Magenta': '#FF00FF',
        'Turquoise': '#40E0D0', 'Red': '#FF0000', 'Bright colors': '#FF6B6B',
        'Jewel tones': '#6A5ACD'
    };
    
    const colors = levelData.best_colors.map(name => ({
        hex: colorMap[name] || '#999999',
        name: name
    }));
    
    const html = colors.map(color => `
        <div style="display: inline-block; margin: 15px; text-align: center; cursor: pointer;"
             onmouseover="this.style.transform='scale(1.1)'" 
             onmouseout="this.style.transform='scale(1)'"
             style="transition: transform 0.2s;" 
             title="Click to copy hex"
             onclick="copyToClipboard('${color.hex}')">
            <div class="color-swatch" style="background-color: ${color.hex}; width: 100px; height: 100px; border-radius: 8px; border: 3px solid #ddd; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                 data-name="${color.name}"></div>
            <p style="margin-top: 10px; font-weight: 600; color: #333;">${color.name}</p>
            <small style="color: #999; font-size: 12px;">${color.hex}</small>
        </div>
    `).join('');
    
    elements.colorPalette.innerHTML = html;
    elements.colorRecommendations.classList.remove('hidden');
}

function generateColorRecommendations(level) {
    // This is now handled by showColorRecommendationsForLevel using backend data
    return [];
}

function showColorComparison() {
    // If user has an analysis available, prefill Color 1 with the detected skin tone
    let skinHex = '';
    if (appState.currentAnalysis) {
        const data = appState.currentAnalysis.data || appState.currentAnalysis;
        if (data.skin_tone && data.skin_tone.hex) skinHex = data.skin_tone.hex;
        else if (data.skin_tone_hex) skinHex = data.skin_tone_hex;
    }

    const html = `
        <div style="background: #f8f9ff; padding: 25px; border-radius: 15px;">
            <h4>Compare Colors (Skin vs Choice)</h4>
            <p style="color:#666; margin-top:6px;">Compare your detected skin color with another color to see compatibility (Delta‑E).</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div>
                    <label>Skin Color (Hex):</label>
                    <input type="text" id="color1Input" placeholder="#B9966A" value="${skinHex}" 
                           style="padding: 10px; border: 2px solid #ddd; border-radius: 8px; width: 100%;">
                    <small style="color:#888;">Automatically filled from your latest analysis (editable).</small>
                </div>
                <div>
                    <label>Compare With (Hex):</label>
                    <input type="text" id="color2Input" placeholder="#764ba2" 
                           style="padding: 10px; border: 2px solid #ddd; border-radius: 8px; width: 100%;">
                </div>
            </div>
            <button class="btn btn-primary" onclick="compareColorsNow()">Compare Colors</button>
        </div>
    `;

    const container = document.getElementById('colorComparison');
    if (container) {
        container.innerHTML = html;
        container.classList.remove('hidden');
    }
}

async function compareColorsNow() {
    const color1El = document.getElementById('color1Input');
    const color2El = document.getElementById('color2Input');
    if (!color1El || !color2El) {
        alert('Color comparison inputs not found.');
        return;
    }

    let color1 = color1El.value && color1El.value.trim();
    const color2 = color2El.value && color2El.value.trim();

    // If color1 empty but analysis exists, use detected skin color
    if ((!color1 || color1 === '') && appState.currentAnalysis) {
        const data = appState.currentAnalysis.data || appState.currentAnalysis;
        color1 = (data.skin_tone && data.skin_tone.hex) || data.skin_tone_hex || '';
        if (color1) color1El.value = color1;
    }

    if (!color1 || !color2) {
        alert('Please provide both colors (skin and comparison color).');
        return;
    }
    
    showLoading('Comparing colors...', 'Using Delta-E CIE2000 algorithm');
    
    try {
        // Resolve color input: supports hex (#RRGGBB or RRGGBB), short hex (#RGB), or common color names
        const NAME_TO_HEX = {
            'aliceblue':'#f0f8ff','antiquewhite':'#faebd7','aqua':'#00ffff','aquamarine':'#7fffd4','azure':'#f0ffff',
            'beige':'#f5f5dc','bisque':'#ffe4c4','black':'#000000','blanchedalmond':'#ffebcd','blue':'#0000ff','blueviolet':'#8a2be2',
            'brown':'#a52a2a','burlywood':'#deb887','cadetblue':'#5f9ea0','chartreuse':'#7fff00','chocolate':'#d2691e','coral':'#ff7f50',
            'cornflowerblue':'#6495ed','cornsilk':'#fff8dc','crimson':'#dc143c','cyan':'#00ffff','darkblue':'#00008b','darkcyan':'#008b8b',
            'darkgoldenrod':'#b8860b','darkgray':'#a9a9a9','darkgreen':'#006400','darkkhaki':'#bdb76b','darkmagenta':'#8b008b','darkolivegreen':'#556b2f',
            'darkorange':'#ff8c00','darkorchid':'#9932cc','darkred':'#8b0000','darksalmon':'#e9967a','darkseagreen':'#8fbc8f','darkslateblue':'#483d8b',
            'darkslategray':'#2f4f4f','darkturquoise':'#00ced1','darkviolet':'#9400d3','deeppink':'#ff1493','deepskyblue':'#00bfff','dimgray':'#696969',
            'dodgerblue':'#1e90ff','firebrick':'#b22222','floralwhite':'#fffaf0','forestgreen':'#228b22','fuchsia':'#ff00ff','gainsboro':'#dcdcdc',
            'ghostwhite':'#f8f8ff','gold':'#ffd700','goldenrod':'#daa520','gray':'#808080','green':'#008000','greenyellow':'#adff2f','honeydew':'#f0fff0',
            'hotpink':'#ff69b4','indianred':'#cd5c5c','indigo':'#4b0082','ivory':'#fffff0','khaki':'#f0e68c','lavender':'#e6e6fa','lavenderblush':'#fff0f5',
            'lawngreen':'#7cfc00','lemonchiffon':'#fffacd','lightblue':'#add8e6','lightcoral':'#f08080','lightcyan':'#e0ffff','lightgoldenrodyellow':'#fafad2',
            'lightgray':'#d3d3d3','lightgreen':'#90ee90','lightpink':'#ffb6c1','lightsalmon':'#ffa07a','lightseagreen':'#20b2aa','lightskyblue':'#87cefa',
            'lightslategray':'#778899','lightsteelblue':'#b0c4de','lightyellow':'#ffffe0','lime':'#00ff00','limegreen':'#32cd32','linen':'#faf0e6',
            'magenta':'#ff00ff','maroon':'#800000','mediumaquamarine':'#66cdaa','mediumblue':'#0000cd','mediumorchid':'#ba55d3','mediumpurple':'#9370db',
            'mediumseagreen':'#3cb371','mediumslateblue':'#7b68ee','mediumspringgreen':'#00fa9a','mediumturquoise':'#48d1cc','mediumvioletred':'#c71585',
            'midnightblue':'#191970','mintcream':'#f5fffa','mistyrose':'#ffe4e1','moccasin':'#ffe4b5','navajowhite':'#ffdead','navy':'#001f3f',
            'oldlace':'#fdf5e6','olive':'#808000','olivedrab':'#6b8e23','orange':'#ffa500','orangered':'#ff4500','orchid':'#da70d6','palegoldenrod':'#eee8aa',
            'palegreen':'#98fb98','paleturquoise':'#afeeee','palevioletred':'#db7093','papayawhip':'#ffefd5','peachpuff':'#ffdab9','peru':'#cd853f','pink':'#ffc0cb',
            'plum':'#dda0dd','powderblue':'#b0e0e6','purple':'#800080','rebeccapurple':'#663399','red':'#ff0000','rosybrown':'#bc8f8f','royalblue':'#4169e1',
            'saddlebrown':'#8b4513','salmon':'#fa8072','sandybrown':'#f4a460','seagreen':'#2e8b57','seashell':'#fff5ee','sienna':'#a0522d','silver':'#c0c0c0',
            'skyblue':'#87ceeb','slateblue':'#6a5acd','slategray':'#708090','snow':'#fffafa','springgreen':'#00ff7f','steelblue':'#4682b4','tan':'#d2b48c',
            'teal':'#008080','thistle':'#d8bfd8','tomato':'#ff6347','turquoise':'#40e0d0','violet':'#ee82ee','wheat':'#f5deb3','white':'#ffffff','whitesmoke':'#f5f5f5',
            'yellow':'#ffff00','yellowgreen':'#9acd32','mustard':'#ffd658','burgundy':'#800020','rust':'#b7410e','cobalt':'#0047ab','bronze':'#cd7f32'
        };

        function normalizeHex(input) {
            if (!input) return null;
            let hex = input.trim().toLowerCase();
            // If it's a named color
            if (!hex.startsWith('#') && /^[a-z\s]+$/.test(hex)) {
                const lookup = NAME_TO_HEX[hex];
                return lookup || null;
            }
            // Remove whitespace
            hex = hex.replace(/\s+/g, '');
            // Allow formats like 'fff' or '#fff' or 'ffffff' or '#ffffff'
            if (hex.startsWith('#')) hex = hex.slice(1);
            if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
            if (hex.length !== 6) return null;
            return '#' + hex;
        }

        function hexToRgbArray(hex) {
            if (!hex) return null;
            hex = hex.replace('#', '');
            const bigint = parseInt(hex, 16);
            const r = (bigint >> 16) & 255;
            const g = (bigint >> 8) & 255;
            const b = bigint & 255;
            return [r, g, b];
        }

        const resolvedHex1 = normalizeHex(color1);
        const resolvedHex2 = normalizeHex(color2);

        // If color1 empty and analysis exists, attempt to use skin hex from analysis
        let finalHex1 = resolvedHex1;
        if ((!finalHex1 || finalHex1 === null) && appState.currentAnalysis) {
            const data = appState.currentAnalysis.data || appState.currentAnalysis;
            finalHex1 = data.skin_tone && data.skin_tone.hex ? data.skin_tone.hex : (data.skin_tone_hex || null);
        }

        if (!finalHex1 || !resolvedHex2) {
            hideLoading();
            alert('Please provide valid colors. You can enter a color name (e.g. "navy") or a hex code (e.g. #667eea).');
            return;
        }

        const color1_rgb = hexToRgbArray(finalHex1.replace('#',''));
        const color2_rgb = hexToRgbArray(resolvedHex2.replace('#',''));
        const skin_rgb = color1_rgb;

        const response = await fetch('/api/v2/explain-color-match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ color1_rgb, color2_rgb, skin_tone_rgb: skin_rgb })
        });

        if (response.ok) {
            const result = await response.json();
            hideLoading();
            // Backend returns delta_e_analysis and ai_explanation
            const delta = result.delta_e_analysis || {};
            const aiText = result.ai_explanation || '';
            const score = delta.score !== undefined ? delta.score : null;
            const compat = delta.compatibility || delta.compatibility_level || null;

            document.getElementById('comparisonResults').innerHTML = `
                <div style="background: white; padding: 20px; border-radius: 10px;">
                    <div style="display:flex; gap:16px; align-items:center;">
                        <div style="text-align:center;">
                            <div style="width:64px; height:64px; border-radius:8px; background:${color1}; border:1px solid #ddd"></div>
                            <small style="display:block; margin-top:6px;">Skin</small>
                        </div>
                        <div style="text-align:center;">
                            <div style="width:64px; height:64px; border-radius:8px; background:${color2}; border:1px solid #ddd"></div>
                            <small style="display:block; margin-top:6px;">Compare</small>
                        </div>
                        <div style="flex:1;">
                            <h4 style="margin:0;">Compatibility: ${compat ? compat : 'N/A'}</h4>
                            <p style="margin:6px 0 0; color:#555;">Delta‑E Score: ${score !== null ? score.toFixed(2) : 'N/A'}</p>
                        </div>
                    </div>
                    <hr style="margin:16px 0;">
                    <p style="margin-top: 8px; line-height: 1.6; color:#333;">${aiText}</p>
                </div>
            `;
        } else {
            const errText = await response.text();
            throw new Error('Comparison failed: ' + errText);
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('Failed to compare colors: ' + error.message);
    }
}

function showSeasonalPalette() {
    if (!appState.currentAnalysis) return;
    const data = appState.currentAnalysis.data || appState.currentAnalysis;
    const advice = (data.fashion_advice || {}).seasonal_palette || {};
    const seasons = ['spring','summer','fall','winter'];
    const html = seasons.map(season => {
        const colors = advice[season] || [];
        if (!colors.length) return '';
        return `
        <div style="margin: 20px 0;">
            <h4>${season.charAt(0).toUpperCase() + season.slice(1)} Palette</h4>
            <div class="color-palette">
                ${colors.map(c => `
                    <div class="color-swatch" title="${c.name}" style="background-color: ${c.hex};"></div>
                `).join('')}
            </div>
        </div>`;
    }).join('');
    const el = document.getElementById('colorComparison');
    el.innerHTML = html || '<p>No seasonal palette available for this analysis.</p>';
    el.classList.remove('hidden');
}

// ============ AI ADVICE TAB ============
async function getAIFashionAdviceFromAnalysis(analysisData) {
    showLoading('Consulting AI Stylist...', 'Analyzing your personalized style recommendations');
    
    try {
        const response = await fetch('/api/v2/ai-fashion-advice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skin_tone_hex: analysisData.skin_tone_hex,
                monk_scale_level: analysisData.monk_scale_level,
                brightness: analysisData.brightness,
                occasion: analysisData.occasion,
                style_preferences: analysisData.style_preferences,
                gender: analysisData.gender || 'both',
                best_colors: analysisData.best_colors,
                age_group: analysisData.age_group
            })
        });
        
        updateProgress(70);
        
        if (response.ok) {
            const result = await response.json();
            updateProgress(100);
            
            setTimeout(() => {
                hideLoading();
                elements.aiAdviceContent.innerHTML = result.advice || result.recommendations || 'No advice available';
                elements.aiAdviceResults.classList.remove('hidden');
                // Scroll to results
                elements.aiAdviceResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 500);
        } else {
            throw new Error('AI advice failed');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('Failed to get AI advice: ' + error.message);
    }
}

async function getAIFashionAdvice() {
    const skinTone = elements.aiSkinTone.value || '#B9966A';
    const monkLevel = elements.aiMonkLevel.value;
    const occasion = elements.aiOccasion.value;
    const stylePrefs = elements.aiStylePrefs.value.split(',').map(s => s.trim()).filter(s => s);
    
    showLoading('Consulting AI Stylist...', 'DeepSeek R1 is analyzing your request');
    
    try {
        const response = await fetch('/api/v2/ai-fashion-advice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skin_tone_hex: skinTone,
                monk_scale_level: monkLevel,
                occasion: occasion,
                style_preferences: stylePrefs,
                gender: 'both'
            })
        });
        
        updateProgress(70);
        
        if (response.ok) {
            const result = await response.json();
            updateProgress(100);
            
            setTimeout(() => {
                hideLoading();
                elements.aiAdviceContent.innerHTML = result.advice || result.recommendations || 'No advice available';
                elements.aiAdviceResults.classList.remove('hidden');
                // Scroll to results
                elements.aiAdviceResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 500);
        } else {
            throw new Error('AI advice failed');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('Failed to get AI advice: ' + error.message);
    }
}

// ============ AR TAB ============
async function startARMode() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        appState.arStream = stream;
        
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        video.playsInline = true;
        
        video.onloadedmetadata = () => {
            elements.arCanvas.width = video.videoWidth;
            elements.arCanvas.height = video.videoHeight;
            
            const ctx = elements.arCanvas.getContext('2d');
            
            function drawFrame() {
                if (!appState.arStream) return;
                ctx.drawImage(video, 0, 0);
                requestAnimationFrame(drawFrame);
            }
            
            drawFrame();
        };
        
        elements.arPreview.style.display = 'block';
        elements.startARCamera.style.display = 'none';
        elements.stopARCamera.style.display = 'inline-block';
        
    } catch (error) {
        console.error('AR error:', error);
        alert('Could not access camera for AR mode');
    }
}

function stopARMode() {
    if (appState.arStream) {
        appState.arStream.getTracks().forEach(track => track.stop());
        appState.arStream = null;
    }
    elements.arPreview.style.display = 'none';
    elements.startARCamera.style.display = 'inline-block';
    elements.stopARCamera.style.display = 'none';
}

function applyARColor(colorRGB) {
    if (!appState.arStream) {
        alert('Please start AR mode first!');
        return;
    }
    
    // In a real implementation, this would apply color overlay to detected clothing
    alert(`Applying color: RGB(${colorRGB})\nThis is a demo - full AR implementation requires additional processing.`);
}

// (Shopping feature removed)

// ============ ANALYTICS TAB ============
// (Analytics feature removed)

// ============ UTILITY FUNCTIONS ============
function showLoading(title, subtitle) {
    elements.loadingText.textContent = title;
    elements.loadingSubtext.textContent = subtitle;
    elements.progressFill.style.width = '0%';
    elements.loadingOverlay.classList.add('active');
}

function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

function updateProgress(percent) {
    elements.progressFill.style.width = percent + '%';
}

function rgbToHex(rgb) {
    if (!rgb || !Array.isArray(rgb)) return '#cccccc';
    const [r, g, b] = rgb;
    return '#' + [r, g, b].map(x => {
        const hex = Math.round(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

function shouldUseDarkText(rgb) {
    if (!rgb || !Array.isArray(rgb)) return true;
    const [r, g, b] = rgb;
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5;
}

// Helper functions for buttons in dynamically generated content
// (Wardrobe save removed)

function getDetailedAIAdvice() {
    if (!appState.currentAnalysis) {
        alert('Please analyze an image first!');
        return;
    }
    
    // Extract analysis data
    const data = appState.currentAnalysis.data || appState.currentAnalysis;
    const skinData = data.skin_tone || {};
    const genderData = data.gender || {};
    const ageData = data.age || {};
    const colors = data.best_colors || {};
    
    // Switch to AI advice tab
    switchTab('ai-advice');
    
    // Pre-fill form with analysis data
    if (skinData.hex) {
        elements.aiSkinTone.value = skinData.hex;
    }
    if (skinData.monk_scale_level) {
        elements.aiMonkLevel.value = skinData.monk_scale_level;
    }
    
    // Set default occasion to casual if not set
    if (!elements.aiOccasion.value) {
        elements.aiOccasion.value = 'casual';
    }
    
    // Automatically trigger AI advice with analysis data
    setTimeout(() => {
        getAIFashionAdviceFromAnalysis({
            skin_tone_hex: skinData.hex,
            monk_scale_level: skinData.monk_scale_level,
            brightness: skinData.brightness,
            gender: genderData.gender,
            age_group: ageData.age_group,
            best_colors: colors,
            occasion: elements.aiOccasion.value,
            style_preferences: elements.aiStylePrefs.value.split(',').map(s => s.trim()).filter(s => s)
        });
    }, 300);
}

function tryARMode() {
    switchTab('ar');
    setTimeout(() => startARMode(), 300);
}

// Copy hex color to clipboard
function copyToClipboard(hex) {
    navigator.clipboard.writeText(hex).then(() => {
        alert(`Copied: ${hex}`);
    }).catch(() => {
        console.log('Could not copy to clipboard');
    });
}

// (Wardrobe init removed)

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // Prevent default error handling that might break the UI
    event.preventDefault();
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

console.log('🎨 VastraVista 3.0 initialized successfully!');
function handleAnalyzedImageError(img) {
    const backendPath = img.getAttribute('data-backend') || '';
    const fileName = backendPath ? backendPath.split('/').pop() : '';
    if (fileName && img.dataset.fallbackTried !== '1') {
        img.dataset.fallbackTried = '1';
        img.src = '/uploads/' + fileName;
        return;
    }
    img.style.display = 'none';
    const parent = img.parentElement;
    if (parent) {
        parent.innerHTML = '<div style="text-align:center; color:#667eea; font-weight:600;">Image unavailable</div>';
    }
}
function getGradientByConfidence(pct) {
    const p = Number(pct || 0);
    if (p >= 80) return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    if (p >= 60) return 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)';
    if (p >= 40) return 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)';
    return 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)';
}
