/**
 * VastraVista - Results Display
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔍 Results page loaded - checking for fresh analysis data');
    
    // Retrieve results from session storage
    const resultsData = sessionStorage.getItem('analysisResults');
    
    if (!resultsData) {
        console.error('❌ No analysis results found in sessionStorage');
        alert('No analysis results found. Redirecting...');
        window.location.href = '/';
        return;
    }
    
    try {
        const results = JSON.parse(resultsData);
        
        // CRITICAL: Validate this is a FRESH analysis
        const now = Date.now();
        const analysisTime = results.analysisTimestamp || 0;
        const ageMinutes = (now - analysisTime) / 1000 / 60;
        const ageSeconds = (now - analysisTime) / 1000;
        
        console.log('═══════════════════════════════════════════════════');
        console.log('📊 ANALYSIS DATA VALIDATION');
        console.log('═══════════════════════════════════════════════════');
        console.log(`🆔 Analysis ID: ${results.analysis_id || 'N/A'}`);
        console.log(`⏱️  Age: ${ageSeconds.toFixed(1)} seconds (${ageMinutes.toFixed(2)} minutes)`);
        console.log(`� Timestamp: ${new Date(analysisTime).toLocaleString()}`);
        console.log(`👤 Gender: ${results.data?.gender?.gender} (${results.data?.gender?.confidence}%)`);
        console.log(`🎂 Age: ${results.data?.age?.estimated_age} years (${results.data?.age?.age_group})`);
        console.log(`🎨 Skin: ${results.data?.skin_tone?.hex} - ${results.data?.skin_tone?.brightness}`);
        console.log('═══════════════════════════════════════════════════');
        
        // Reject stale results (older than 5 minutes)
        if (ageMinutes > 5) {
            console.error('❌ STALE RESULTS DETECTED - Results are >5 minutes old');
            sessionStorage.clear();
            alert('Previous results expired. Please analyze a new image.');
            window.location.href = '/';
            return;
        }
        
        // Warn if results are suspiciously old (>30 seconds suggests caching issue)
        if (ageSeconds > 30) {
            console.warn(`⚠️  Results are ${ageSeconds.toFixed(0)}s old - may be cached`);
        } else {
            console.log('✅ Results are FRESH (<30s old)');
        }
        
        displayResults(results);
    } catch (error) {
        console.error('Error parsing results:', error);
        alert('Failed to load results. Please try again.');
        window.location.href = '/';
    }
});

function displayResults(results) {
    const { data, analyzedImage } = results;
    
    if (!data) {
        console.error('No data in results');
        return;
    }
    
    // Display Analyzed Image
    if (analyzedImage) {
        displayAnalyzedImage(analyzedImage);
    }
    
    // Display Verification Badge (if available)
    if (data.verification) {
        displayVerification(data.verification);
    }
    
    // Display AI Insights (if available)
    if (data.ai_insights) {
        displayAIInsights(data.ai_insights);
    }
    
    // Display Profile
    displayProfile(data);
    console.log('✅ Profile displayed');
    
    // Display Best Colors
    displayBestColors(data.best_colors);
    console.log('✅ Best colors displayed:', data.best_colors?.length || 0, 'colors');
    
    // Display Outfit Recommendations
    if (data.recommendations && data.recommendations.outfit_recommendations) {
        displayOutfits(data.recommendations.outfit_recommendations);
        console.log('✅ Outfits displayed:', data.recommendations.outfit_recommendations?.length || 0, 'outfits');
    } else {
        console.warn('⚠️ No outfit recommendations found');
    }
    
    // Display Style Tips
    if (data.recommendations && data.recommendations.style_tips) {
        displayStyleTips(data.recommendations.style_tips);
        console.log('✅ Style tips displayed');
    } else {
        console.warn('⚠️ No style tips found');
    }
    
    // Display Summary
    displaySummary(data.summary);
    console.log('✅ Summary displayed');
    
    // Add scroll hint after a moment
    setTimeout(() => {
        console.log('📜 TIP: Scroll down to see all sections!');
    }, 1000);
}

function displayAnalyzedImage(imageDataUrl) {
    const profileSection = document.getElementById('profileSection');
    
    // Create image display section before profile with better styling
    const imageHtml = `
        <div class="analyzed-image-container" style="text-align: center; margin-bottom: 30px; 
                    background: white; padding: 25px; border-radius: 15px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #5B8DEE; margin-bottom: 20px; font-size: 24px; font-weight: 600;">
                📸 Analyzed Photo
            </h2>
            <div style="display: inline-block; position: relative;">
                <img src="${imageDataUrl}" 
                     alt="Analyzed photo" 
                     style="max-width: 350px; max-height: 350px; width: 100%; height: auto;
                            border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                            border: 4px solid #5B8DEE; object-fit: cover;" />
                <div style="position: absolute; bottom: 10px; right: 10px; 
                            background: rgba(91, 141, 238, 0.9); color: white; 
                            padding: 6px 12px; border-radius: 20px; font-size: 12px; 
                            font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    ✓ Analyzed
                </div>
            </div>
        </div>
    `;
    
    profileSection.insertAdjacentHTML('beforebegin', imageHtml);
    console.log('✅ Analyzed image displayed with enhanced styling');
}

function displayVerification(verification) {
    const profileSection = document.getElementById('profileSection');
    
    const isVerified = verification.verified;
    const confidence = verification.confidence || 0;
    const method = verification.method || 'unknown';
    const concerns = verification.concerns || [];
    
    const bgColor = isVerified ? 
        (confidence >= 90 ? 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)' : 
         confidence >= 75 ? 'linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%)' : 
         'linear-gradient(135deg, #9CCC65 0%, #8BC34A 100%)') :
        'linear-gradient(135deg, #FFA726 0%, #FF9800 100%)';
    
    const icon = isVerified ? 
        (confidence >= 90 ? '✓✓' : '✓') : '⚠';
    
    const verificationHtml = `
        <div class="verification-badge" style="margin-bottom: 30px; 
                    background: ${bgColor}; 
                    padding: 20px 25px; border-radius: 15px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                    color: white; text-align: center;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 15px; flex-wrap: wrap;">
                <div style="font-size: 48px; line-height: 1;">${icon}</div>
                <div style="text-align: left;">
                    <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px;">
                        ${isVerified ? 'Analysis Verified' : 'Verification Warning'}
                    </div>
                    <div style="font-size: 18px; font-weight: 600; opacity: 0.95;">
                        ${confidence}% Confidence
                    </div>
                    <div style="font-size: 13px; opacity: 0.85; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Method: ${method}
                    </div>
                </div>
            </div>
            ${concerns.length > 0 ? `
                <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.2); 
                            border-radius: 8px; font-size: 14px; text-align: left;">
                    <strong>⚠ Concerns:</strong><br>
                    ${concerns.map(c => `• ${c}`).join('<br>')}
                </div>
            ` : ''}
            ${confidence >= 90 ? `
                <div style="margin-top: 12px; font-size: 14px; opacity: 0.9;">
                    🎯 High accuracy - AI confirms all measurements are consistent
                </div>
            ` : ''}
        </div>
    `;
    
    profileSection.insertAdjacentHTML('beforebegin', verificationHtml);
    console.log('✅ Verification badge displayed');
}

function displayAIInsights(aiInsights) {
    if (!aiInsights || !aiInsights.success) {
        console.log('ℹ️ No AI insights available');
        return;
    }
    
    const profileSection = document.getElementById('profileSection');
    
    const insightsHtml = `
        <div class="ai-insights-container" style="margin-bottom: 30px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 15px; 
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    color: white;">
            <h2 style="color: white; margin-bottom: 15px; font-size: 24px; font-weight: 600; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 28px;">🤖</span>
                <span>AI Fashion Analysis</span>
                <span style="font-size: 12px; background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 12px; font-weight: 500;">
                    Powered by ${aiInsights.model}
                </span>
            </h2>
            <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 12px; backdrop-filter: blur(10px);">
                <p style="font-size: 16px; line-height: 1.8; margin: 0; color: white; font-weight: 400;">
                    ${aiInsights.analysis}
                </p>
            </div>
            <div style="margin-top: 15px; font-size: 13px; opacity: 0.85; text-align: center;">
                ✨ This personalized analysis is generated by AI based on your unique features and color palette
            </div>
        </div>
    `;
    
    profileSection.insertAdjacentHTML('beforebegin', insightsHtml);
    console.log('✅ AI insights displayed');
}

function displayProfile(data) {
    const profileSection = document.getElementById('profileSection');
    
    // Debug: Log age data structure
    console.log('📊 Age data received:', data.age);
    console.log('   - age:', data.age.age);
    console.log('   - estimated_age:', data.age.estimated_age);
    console.log('   - method:', data.age.method);
    
    const html = `
        <div class="profile-card">
            <h2>👤 Your Profile</h2>
            <div class="profile-details">
                <div class="detail-item">
                    <span class="label">Gender:</span>
                    <span class="value">${data.gender.gender} (${data.gender.confidence}% confident)</span>
                </div>
                <div class="detail-item">
                    <span class="label">Predicted Age:</span>
                    <span class="value" style="font-size: 1.3em; font-weight: bold; color: #667eea;">${data.age.age || data.age.estimated_age || 'N/A'} years</span>
                </div>
                <div class="detail-item">
                    <span class="label">Age Group:</span>
                    <span class="value">${data.age.age_group} (${data.age.age_range})</span>
                </div>
                <div class="detail-item" style="font-size: 0.8em; color: #666;">
                    <span class="label">Detection Method:</span>
                    <span class="value">${data.age.method || 'Unknown'}</span>
                </div>
                <div class="detail-item" style="font-size: 0.85em; color: #2d8f2d; font-style: italic; background: #e8f5e9; padding: 8px; border-radius: 5px;">
                    <span class="label" style="font-weight: normal;">✅ Custom Model:</span>
                    <span class="value" style="font-weight: normal;">Using trained age detection model with ±9.6 years accuracy (trained on 380 diverse face images including Indian ethnicity).</span>
                </div>
                <div class="detail-item">
                    <span class="label">Skin Tone:</span>
                    <span class="value">
                        <span class="color-swatch" style="background-color: ${data.skin_tone.hex}"></span>
                        ${data.skin_tone.hex} - ${data.skin_tone.brightness}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="label">Undertone:</span>
                    <span class="value">${data.skin_tone.undertone}</span>
                </div>
            </div>
            
            <!-- Scroll Down Indicator -->
            <div style="text-align: center; margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
                <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 8px;">
                    👇 Scroll Down for More
                </div>
                <div style="font-size: 0.9em; opacity: 0.9;">
                    Color Palette • Outfit Recommendations • Style Tips • Analysis Summary
                </div>
                <div style="font-size: 2em; margin-top: 10px; animation: bounce 2s infinite;">
                    ⬇️
                </div>
            </div>
        </div>
    `;
    
    profileSection.innerHTML = html;
    
    // Add bounce animation if not exists
    if (!document.querySelector('style[data-bounce]')) {
        const style = document.createElement('style');
        style.setAttribute('data-bounce', 'true');
        style.textContent = `
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                60% { transform: translateY(-5px); }
            }
        `;
        document.head.appendChild(style);
    }
}

function displayBestColors(colors) {
    const colorsSection = document.getElementById('colorsSection');
    
    if (!colors || !colors.excellent) {
        return;
    }
    
    const excellentColors = colors.excellent.slice(0, 10);
    
    const colorCards = excellentColors.map(color => `
        <div class="color-card">
            <div class="color-preview" style="background-color: ${color.hex}"></div>
            <h4>${color.color_name}</h4>
            <p class="color-hex">${color.hex}</p>
            <div class="confidence-badge ${getRatingClass(color.rating)}">
                ${color.confidence_score.toFixed(1)}% - ${color.rating}
            </div>
            <p class="delta-e">ΔE: ${color.delta_e.toFixed(2)}</p>
        </div>
    `).join('');
    
    const html = `
        <h2>🎨 Your Best Color Palette</h2>
        <p class="section-subtitle">Based on Delta-E color science in Lab color space</p>
        <div class="colors-grid">
            ${colorCards}
        </div>
    `;
    
    colorsSection.innerHTML = html;
}

function displayOutfits(outfits) {
    const outfitsSection = document.getElementById('outfitsSection');
    
    const outfitCards = outfits.slice(0, 6).map(outfit => `
        <div class="outfit-card">
            <div class="outfit-header">
                <h3>${outfit.occasion}</h3>
                <div class="confidence-badge ${getRatingClass(outfit.rating)}">
                    ${outfit.color_confidence_score.toFixed(1)}%
                </div>
            </div>
            <div class="outfit-color">
                <div class="color-preview" style="background-color: ${outfit.primary_color.hex}"></div>
                <div>
                    <p class="color-name">${outfit.primary_color.name}</p>
                    <p class="color-hex">${outfit.primary_color.hex}</p>
                </div>
            </div>
            <div class="outfit-items">
                <h4>Items:</h4>
                <ul>
                    ${outfit.items.map(item => `
                        <li>${item.type} in ${item.color}</li>
                    `).join('')}
                </ul>
            </div>
            <p class="styling-note">💡 ${outfit.styling_note}</p>
            <p class="delta-e-info">ΔE: ${outfit.delta_e.toFixed(2)} - ${outfit.rating}</p>
        </div>
    `).join('');
    
    const html = `
        <h2>👗 Personalized Outfit Recommendations</h2>
        <div class="outfits-grid">
            ${outfitCards}
        </div>
    `;
    
    outfitsSection.innerHTML = html;
}

function displayStyleTips(tips) {
    const tipsSection = document.getElementById('tipsSection');
    
    const tipsList = tips.map(tip => `<li>${tip}</li>`).join('');
    
    const html = `
        <h2>💡 Personalized Style Tips</h2>
        <ul class="tips-list">
            ${tipsList}
        </ul>
    `;
    
    tipsSection.innerHTML = html;
}

function displaySummary(summary) {
    const summarySection = document.getElementById('summarySection');
    
    const html = `
        <h2>📊 Analysis Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-value">${summary.gender}</div>
                <div class="summary-label">Gender</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${summary.age_group}</div>
                <div class="summary-label">Age Group</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${summary.skin_undertone}</div>
                <div class="summary-label">Undertone</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${summary.total_excellent_colors}</div>
                <div class="summary-label">Excellent Colors</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${summary.total_outfits}</div>
                <div class="summary-label">Outfit Options</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${summary.avg_confidence.toFixed(1)}%</div>
                <div class="summary-label">Avg Confidence</div>
            </div>
        </div>
    `;
    
    summarySection.innerHTML = html;
}

function getRatingClass(rating) {
    const map = {
        'Excellent': 'excellent',
        'Good': 'good',
        'Fair': 'fair',
        'Poor - Too Similar': 'poor',
        'Poor - Too Contrasting': 'poor'
    };
    return map[rating] || 'fair';
}

// New Analysis Button
document.getElementById('newAnalysisBtn')?.addEventListener('click', () => {
    sessionStorage.removeItem('analysisResults');
    window.location.href = '/';
});

// Download Results
document.getElementById('downloadBtn')?.addEventListener('click', () => {
    const resultsData = sessionStorage.getItem('analysisResults');
    if (resultsData) {
        const blob = new Blob([resultsData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vastravista_results_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
});
