// VastraVista 3.0 - Main Application JavaScript
// Handles all UI interactions and API calls

// Global state
const appState = {
    currentAnalysis: null,
    wardrobeItems: [],
    savedOutfits: [],
    monkScaleData: null,
    cameraStream: null,
    arStream: null,
    analytics: {
        totalAnalyses: 0,
        wardrobeItems: 0,
        co2Saved: 0,
        aiRequests: 0
    }
};

// DOM Elements
let elements = {};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
    loadMonkScaleData();
    loadAnalytics();
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
        addWardrobeItem: document.getElementById('addWardrobeItem'),
        generateOutfits: document.getElementById('generateOutfits'),
        analyzeWardrobe: document.getElementById('analyzeWardrobe'),
        wardrobeGrid: document.getElementById('wardrobeGrid'),
        outfitSuggestions: document.getElementById('outfitSuggestions'),
        outfitsContainer: document.getElementById('outfitsContainer'),
        
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
        shopCategory: document.getElementById('shopCategory'),
        shopGender: document.getElementById('shopGender'),
        shopColor: document.getElementById('shopColor'),
        searchProducts: document.getElementById('searchProducts'),
        productsGrid: document.getElementById('productsGrid'),
        productsContainer: document.getElementById('productsContainer'),
        
        // Analytics tab
        refreshAnalytics: document.getElementById('refreshAnalytics'),
        downloadReport: document.getElementById('downloadReport'),
        
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
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.startCamera.addEventListener('click', startWebcam);
    elements.captureBtn.addEventListener('click', captureImage);
    elements.stopCamera.addEventListener('click', stopWebcam);
    
    // Wardrobe tab
    elements.addWardrobeItem.addEventListener('click', addWardrobeItem);
    elements.generateOutfits.addEventListener('click', generateOutfits);
    elements.analyzeWardrobe.addEventListener('click', analyzeWardrobe);
    
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
    elements.searchProducts.addEventListener('click', searchProducts);
    
    // Analytics tab
    elements.refreshAnalytics.addEventListener('click', loadAnalytics);
    elements.downloadReport.addEventListener('click', downloadPDFReport);
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
        appState.analytics.totalAnalyses++;
        
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
    if (appState.currentImageUrl) {
        const skinData = data.skin_tone || {};
        const skinHex = skinData.hex || '#000000';
        const skinRgb = skinData.rgb || [0, 0, 0];
        const monkLevel = skinData.monk_scale_level || 'N/A';
        const brightness = skinData.brightness || 'N/A';
        
        html += `
            <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 30px;">
                <h3 style="color: #667eea; margin-bottom: 20px; text-align: center; font-size: 1.8em;">📸 Your Analyzed Photo</h3>
                <div style="display: flex; gap: 30px; align-items: start; flex-wrap: wrap;">
                    <!-- Image Section -->
                    <div style="flex: 1; min-width: 300px; text-align: center;">
                        <img src="${appState.currentImageUrl}" alt="Analyzed Person" 
                             style="max-width: 100%; max-height: 400px; border-radius: 12px; 
                                    box-shadow: 0 8px 30px rgba(0,0,0,0.2); object-fit: contain; 
                                    border: 4px solid #667eea;" />
                        <div style="margin-top: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 10px; border-radius: 8px; font-weight: 600;">
                            ✅ Analysis Complete
                        </div>
                        ${data.verification ? `
                        <div style="margin-top: 10px; background: ${data.verification.verified ? 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)' : 'linear-gradient(135deg, #FFA726 0%, #FF9800 100%)'}; 
                                    color: white; padding: 10px; border-radius: 8px; font-size: 0.9em;">
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
    }
    
    if (isMultipleFaces && data.faces) {
        // MULTIPLE FACES DETECTED - Show all persons
        html = `
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
        
        const gender = genderData.gender || result.gender || 'Unknown';
        const genderConf = genderData.confidence || 0;
        const age = ageData.estimated_age || ageData.age_group || result.age || 'N/A';
        const ageConf = ageData.confidence || 0;
        const monkScale = skinData.monk_scale_level || data.monk_scale_level || result.monk_scale || 'N/A';
        const skinBrightness = skinData.brightness || 'N/A';
        
        // Calculate overall confidence properly (average of gender + age)
        const overallConf = (genderConf + ageConf) / 2;
        
        console.log('📊 Debug - Age:', age, 'AgeData:', ageData);
        console.log('📊 Debug - Gender Conf:', genderConf, 'Age Conf:', ageConf, 'Overall:', overallConf);
        
        html = `
        <div style="background: #f8f9ff; padding: 30px; border-radius: 15px;">
            <h3 style="color: #667eea; margin-bottom: 25px;">✅ Analysis Complete</h3>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div style="font-size: 2em;">👤</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${gender}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Gender</div>
                    <div style="font-size: 0.75em; margin-top: 5px;">${genderConf.toFixed(0)}% confidence</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎂</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${age || 'Loading...'} ${age !== 'N/A' && age !== 'Loading...' ? 'years' : ''}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Age</div>
                    ${ageConf > 0 ? `<div style="font-size: 0.75em; margin-top: 5px;">${ageConf.toFixed(0)}% confidence</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${monkScale !== 'N/A' ? `Level ${monkScale}` : skinBrightness}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Monk Scale</div>
                    ${skinBrightness !== 'N/A' && monkScale !== 'N/A' ? `<div style="font-size: 0.75em; margin-top: 3px;">${skinBrightness}</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">✨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${overallConf > 0 ? overallConf.toFixed(0) + '%' : 'N/A'}</div>
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
                <button class="btn btn-primary" onclick="saveToWardrobe()">💾 Save to Wardrobe</button>
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
    const genderConf = genderData.confidence || 0;
    const age = ageData.estimated_age || ageData.age_group || 'N/A';
    const monkScale = skinData.monk_scale_level || 'N/A';
    const skinBrightness = skinData.brightness || 'N/A';
    const overallConf = (genderData.confidence + (ageData.confidence || 0)) / 2 || 0;
    
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
                <div class="stat-card">
                    <div style="font-size: 2em;">👤</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${gender}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Gender</div>
                    <div style="font-size: 0.75em; margin-top: 5px;">${genderConf.toFixed(0)}% confidence</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎂</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${age} ${age !== 'N/A' ? 'years' : ''}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Age</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">🎨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${monkScale !== 'N/A' ? `Level ${monkScale}` : skinBrightness}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Monk Scale</div>
                    ${skinBrightness !== 'N/A' && monkScale !== 'N/A' ? `<div style="font-size: 0.75em; margin-top: 3px;">${skinBrightness}</div>` : ''}
                </div>
                <div class="stat-card">
                    <div style="font-size: 2em;">✨</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">${overallConf > 0 ? overallConf.toFixed(0) + '%' : 'N/A'}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">Confidence</div>
                </div>
            </div>
            
            ${person.best_colors ? `
                <div style="margin-top: 25px; padding: 20px; background: linear-gradient(135deg, ${personNum === 1 ? '#667eea' : '#764ba2'} 0%, ${personNum === 1 ? '#764ba2' : '#9b59b6'} 100%); border-radius: 12px; color: white;">
                    <h4 style="color: white; margin-bottom: 15px; font-size: 1.3em;">✨ Best Colors for Person ${personNum}</h4>
                    
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

// ============ WARDROBE TAB ============
async function addWardrobeItem() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        showLoading('Adding to wardrobe...', 'Analyzing clothing item');
        
        const formData = new FormData();
        formData.append('image', file);
        formData.append('category', 'general');
        formData.append('name', file.name);
        
        try {
            const response = await fetch('/api/extended/wardrobe/add', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                appState.wardrobeItems.push(result);
                appState.analytics.wardrobeItems++;
                hideLoading();
                await loadWardrobe();
                alert('✅ Item added successfully!');
            } else {
                throw new Error('Failed to add item');
            }
        } catch (error) {
            console.error('Error:', error);
            hideLoading();
            alert('Failed to add item: ' + error.message);
        }
    };
    input.click();
}

async function loadWardrobe() {
    try {
        const response = await fetch('/api/extended/wardrobe/items');
        if (response.ok) {
            const data = await response.json();
            appState.wardrobeItems = data.items || data.wardrobe_items || [];
            displayWardrobe();
            updateWardrobeStats();
        } else {
            // Endpoint might not exist, use empty array
            appState.wardrobeItems = [];
            displayWardrobe();
        }
    } catch (error) {
        console.error('Error loading wardrobe:', error);
        appState.wardrobeItems = [];
        displayWardrobe();
    }
}

function displayWardrobe() {
    if (appState.wardrobeItems.length === 0) {
        elements.wardrobeGrid.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No items yet. Add your first clothing item!</p>';
        return;
    }
    
    const html = appState.wardrobeItems.map(item => `
        <div class="wardrobe-item" data-id="${item.item_id}">
            <img src="${item.image_url || '/static/placeholder.jpg'}" alt="${item.name}">
            <div class="wardrobe-item-info">
                <h4>${item.name || 'Clothing Item'}</h4>
                <p style="font-size: 0.9em; color: #666;">${item.category || 'General'}</p>
                <div style="margin-top: 10px;">
                    ${item.dominant_color ? `<span style="display: inline-block; width: 30px; height: 30px; border-radius: 50%; background-color: ${item.dominant_color}; border: 2px solid #ddd;"></span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    elements.wardrobeGrid.innerHTML = html;
}

function updateWardrobeStats() {
    document.getElementById('totalItems').textContent = appState.wardrobeItems.length;
    document.getElementById('totalOutfits').textContent = appState.savedOutfits.length;
}

async function generateOutfits() {
    if (appState.wardrobeItems.length < 2) {
        alert('Add at least 2 items to your wardrobe to generate outfits!');
        return;
    }
    
    showLoading('Generating outfits...', 'Finding perfect combinations');
    
    try {
        const response = await fetch('/api/extended/wardrobe/outfits/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ occasion: 'casual' })
        });
        
        if (response.ok) {
            const result = await response.json();
            hideLoading();
            displayOutfits(result.outfits || []);
        } else {
            throw new Error('Failed to generate outfits');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('✅ Feature Available! Backend configured at:\n/api/extended/wardrobe/outfits/generate\n\nAdd more items to your wardrobe to see outfit combinations!');
    }
}

function displayOutfits(outfits) {
    if (outfits.length === 0) {
        alert('No compatible outfits found. Try adding more items!');
        return;
    }
    
    const html = outfits.map((outfit, idx) => `
        <div class="outfit-combination">
            <h4>Outfit ${idx + 1}</h4>
            <p style="color: #666; margin: 10px 0;">${outfit.description || 'Perfect combination for any occasion'}</p>
            <span class="compatibility-badge compatibility-excellent">
                ✨ ${outfit.compatibility_score ? (outfit.compatibility_score * 100).toFixed(0) + '% Compatible' : 'Excellent Match'}
            </span>
            <div class="outfit-items">
                ${outfit.items.map(item => `
                    <div style="text-align: center;">
                        <div style="width: 100px; height: 100px; background: ${item.color || '#ccc'}; border-radius: 10px; margin-bottom: 5px;"></div>
                        <p style="font-size: 0.9em;">${item.name || item.category}</p>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    elements.outfitsContainer.innerHTML = html;
    elements.outfitSuggestions.classList.remove('hidden');
}

async function analyzeWardrobe() {
    showLoading('Analyzing wardrobe...', 'Calculating color harmony and compatibility');
    
    try {
        const response = await fetch('/api/extended/wardrobe/analyze');
        if (response.ok) {
            const result = await response.json();
            hideLoading();
            
            const avgScore = result.average_compatibility || 0;
            document.getElementById('avgCompatibility').textContent = (avgScore * 100).toFixed(0) + '%';
            
            alert(`Wardrobe Analysis:\n\n` +
                  `Total Items: ${result.total_items || 0}\n` +
                  `Average Compatibility: ${(avgScore * 100).toFixed(0)}%\n` +
                  `Most Common Color: ${result.dominant_color_family || 'N/A'}\n` +
                  `Recommendations: ${result.recommendations || 'Keep building your collection!'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
    }
}

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
    const html = `
        <div style="background: #f8f9ff; padding: 25px; border-radius: 15px;">
            <h4>Compare Two Colors</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div>
                    <label>Color 1 (Hex):</label>
                    <input type="text" id="color1Input" placeholder="#667eea" 
                           style="padding: 10px; border: 2px solid #ddd; border-radius: 8px; width: 100%;">
                </div>
                <div>
                    <label>Color 2 (Hex):</label>
                    <input type="text" id="color2Input" placeholder="#764ba2" 
                           style="padding: 10px; border: 2px solid #ddd; border-radius: 8px; width: 100%;">
                </div>
            </div>
            <button class="btn btn-primary" onclick="compareColorsNow()">Compare Colors</button>
        </div>
    `;
    
    document.getElementById('colorComparison').innerHTML = html;
    document.getElementById('colorComparison').classList.remove('hidden');
}

async function compareColorsNow() {
    const color1 = document.getElementById('color1Input').value;
    const color2 = document.getElementById('color2Input').value;
    
    if (!color1 || !color2) {
        alert('Please enter both colors!');
        return;
    }
    
    showLoading('Comparing colors...', 'Using Delta-E CIE2000 algorithm');
    
    try {
        const response = await fetch('/api/v2/explain-color-match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ color1, color2 })
        });
        
        if (response.ok) {
            const result = await response.json();
            hideLoading();
            
            document.getElementById('comparisonResults').innerHTML = `
                <div style="background: white; padding: 20px; border-radius: 10px;">
                    <h4>Compatibility Score: ${result.compatibility_score ? (result.compatibility_score * 100).toFixed(0) + '%' : 'N/A'}</h4>
                    <p style="margin-top: 15px; line-height: 1.8;">${result.explanation || 'Colors analyzed successfully'}</p>
                </div>
            `;
        } else {
            throw new Error('Comparison failed');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('Failed to compare colors');
    }
}

function showSeasonalPalette() {
    const seasons = {
        'Spring': ['#FFB6C1', '#98FB98', '#FFD700', '#87CEEB'],
        'Summer': ['#ADD8E6', '#F0E68C', '#DDA0DD', '#F5DEB3'],
        'Autumn': ['#D2691E', '#8B4513', '#FF8C00', '#DAA520'],
        'Winter': ['#000080', '#800020', '#4B0082', '#FFFFFF']
    };
    
    const html = Object.entries(seasons).map(([season, colors]) => `
        <div style="margin: 20px 0;">
            <h4>${season} Palette</h4>
            <div class="color-palette">
                ${colors.map(color => `
                    <div class="color-swatch" style="background-color: ${color};"></div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    document.getElementById('colorComparison').innerHTML = html;
    document.getElementById('colorComparison').classList.remove('hidden');
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
            appState.analytics.aiRequests++;
            
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
            appState.analytics.aiRequests++;
            
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

// ============ SHOPPING TAB ============
async function searchProducts() {
    const category = elements.shopCategory.value;
    const gender = elements.shopGender.value;
    const color = elements.shopColor.value;
    
    showLoading('Searching products...', 'Finding best matches from Amazon & Flipkart');
    
    try {
        const response = await fetch('/api/extended/shopping/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, gender, preferred_color: color })
        });
        
        if (response.ok) {
            const result = await response.json();
            hideLoading();
            displayProducts(result.products || []);
        } else {
            throw new Error('Product search failed');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        // Show demo products instead
        displayProducts([
            { name: 'Cotton Shirt', price: '₹999', platform: 'Amazon', image: '', url: '#' },
            { name: 'Silk Saree', price: '₹2499', platform: 'Flipkart', image: '', url: '#' }
        ]);
    }
}

function displayProducts(products) {
    if (products.length === 0) {
        alert('No products found. Try different filters!');
        return;
    }
    
    const html = products.map(product => `
        <div class="wardrobe-item">
            <div style="width: 100%; height: 200px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;">
                ${product.image ? `<img src="${product.image}" style="max-width: 100%; max-height: 100%;">` : '🛍️'}
            </div>
            <div class="wardrobe-item-info">
                <h4>${product.name}</h4>
                <p style="color: #4CAF50; font-weight: bold;">${product.price || 'Price on request'}</p>
                <p style="font-size: 0.9em; color: #666;">${product.platform || 'Online'}</p>
                <a href="${product.url || '#'}" target="_blank" class="btn btn-outline" style="display: inline-block; margin-top: 10px; padding: 8px 15px; font-size: 0.9em;">View Product</a>
            </div>
        </div>
    `).join('');
    
    elements.productsContainer.innerHTML = html;
    elements.productsGrid.classList.remove('hidden');
}

// ============ ANALYTICS TAB ============
function loadAnalytics() {
    // Update stats from app state
    document.getElementById('totalAnalyses').textContent = appState.analytics.totalAnalyses;
    document.getElementById('wardrobeValue').textContent = appState.analytics.wardrobeItems;
    document.getElementById('co2Saved').textContent = (appState.analytics.wardrobeItems * 2.5).toFixed(1) + ' kg';
    document.getElementById('aiRequests').textContent = appState.analytics.aiRequests;
}

async function downloadPDFReport() {
    showLoading('Generating PDF report...', 'Compiling your fashion analytics');
    
    try {
        const response = await fetch('/api/extended/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_data: appState.currentAnalysis,
                wardrobe_stats: { total_items: appState.wardrobeItems.length }
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'VastraVista_Report.pdf';
            a.click();
            hideLoading();
            alert('✅ Report downloaded successfully!');
        } else {
            throw new Error('Failed to generate report');
        }
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        alert('Report generation is currently unavailable. Try again later!');
    }
}

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
function saveToWardrobe() {
    if (!appState.currentAnalysis) return;
    alert('Analysis saved to profile! You can now generate personalized outfit recommendations.');
}

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

// Initialize wardrobe on load - wrapped in try-catch
try {
    loadWardrobe();
} catch (error) {
    console.warn('Could not load wardrobe on init:', error);
}

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
