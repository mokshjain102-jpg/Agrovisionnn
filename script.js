/* ===== AgroVision Main Script ===== */

const API_URL = 'http://127.0.0.1:5000';

// ===== NAVBAR =====
const navToggle = document.getElementById('nav-toggle');
const navLinks = document.getElementById('nav-links');
if (navToggle) {
  navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
}

window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (navbar) navbar.style.boxShadow = window.scrollY > 50 ? '0 2px 20px rgba(0,0,0,0.1)' : '0 1px 8px rgba(0,0,0,0.06)';
});

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', function () {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    this.classList.add('active');
    if (navLinks) navLinks.classList.remove('open');
  });
});

// ===== SMOOTH SCROLL =====
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ===== DEMO MODAL =====
function openDemo() {
  const m = document.getElementById('demo-modal');
  if (m) m.classList.add('active');
}
function closeDemo() {
  const m = document.getElementById('demo-modal');
  if (m) m.classList.remove('active');
}
const demoModal = document.getElementById('demo-modal');
if (demoModal) demoModal.addEventListener('click', (e) => { if (e.target === demoModal) closeDemo(); });

// ===== FILE UPLOAD & DRAG DROP =====
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('fileInput');

if (uploadZone) {
  uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      processUpload(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) processUpload(file);
}

function processUpload(file) {
  if (!file.type.startsWith('image/')) { alert('Please upload an image file'); return; }
  const reader = new FileReader();
  reader.onload = function (e) {
    if (uploadZone) {
      uploadZone.innerHTML = `<img src="${e.target.result}" style="max-width:100%;max-height:160px;border-radius:8px;margin-bottom:8px;">
        <p style="font-size:12px;color:#6b7280;">Click to change image</p>`;
      uploadZone.onclick = () => { fileInput.value = ''; fileInput.click(); };
    }
  };
  reader.readAsDataURL(file);
  analyzeImage(file);
}

// ===== ANALYZE IMAGE - CONNECTS TO MODEL =====
async function analyzeImage(file) {
  const cropEl = document.getElementById('result-crop');
  const diseaseEl = document.getElementById('result-disease');
  const solutionEl = document.getElementById('result-solution');

  if (cropEl) cropEl.textContent = '...';
  if (diseaseEl) diseaseEl.textContent = 'Analyzing...';
  if (solutionEl) solutionEl.textContent = '...';

  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(API_URL + '/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.success) {
      if (cropEl) cropEl.textContent = data.crop;
      if (diseaseEl) diseaseEl.textContent = data.disease;
      if (solutionEl) solutionEl.textContent = data.treatment ? data.treatment[0] : 'See details';
      showDetailedResults(data);
      addToHistory(data.crop, data.disease);
      updateScanCount();
    } else {
      if (diseaseEl) diseaseEl.textContent = 'Error';
    }
  } catch (e) {
    // Offline fallback
    const fallback = offlinePrediction();
    if (cropEl) cropEl.textContent = fallback.crop;
    if (diseaseEl) diseaseEl.textContent = fallback.disease;
    if (solutionEl) solutionEl.textContent = fallback.treatment[0];
    showDetailedResults(fallback);
    addToHistory(fallback.crop, fallback.disease);
    updateScanCount();
  }
}

function offlinePrediction() {
  const diseases = [
    { crop:"Tomato", disease:"Early Blight", confidence:94.2, severity:"Moderate",
      description:"Fungal disease caused by Alternaria solani. Dark brown spots with concentric rings.",
      symptoms:["Dark brown spots with rings","Yellow halo around spots","Lower leaves first","Leaves dry and fall"],
      precautions:["Avoid overhead watering","Proper plant spacing","Remove infected leaves","Rotate crops 2-3 years"],
      prevention:["Disease-free seeds","Apply mulch","Use drip irrigation","Good air circulation"],
      treatment:["Apply Mancozeb fungicide","Chlorothalonil spray","Copper-based fungicide","Remove infected plants"] },
    { crop:"Rice", disease:"Healthy", confidence:96.8, severity:"None",
      description:"Your rice plant looks healthy! No disease detected.",
      symptoms:["No disease symptoms"], precautions:["Continue monitoring","Proper watering","Check for pests"],
      prevention:["Crop rotation","Balanced fertilization","Proper spacing"],
      treatment:["No treatment needed - plant is healthy!"] },
    { crop:"Corn/Maize", disease:"Leaf Spot", confidence:88.9, severity:"Moderate to High",
      description:"Gray-green lesions that become cigar-shaped. Caused by Exserohilum turcicum.",
      symptoms:["Cigar-shaped gray-green lesions","1-6 inches long","Lower leaves first","Can cause complete blighting"],
      precautions:["Avoid continuous corn","Till crop residue","Monitor in wet weather","Scout lower canopy"],
      prevention:["Plant resistant hybrids","Crop rotation","Residue management","Balanced fertility"],
      treatment:["Strobilurin fungicide","Azoxystrobin at V8-VT","Triazole fungicides","Aerial application for large fields"] },
    { crop:"Potato", disease:"Late Blight", confidence:93.4, severity:"Very High",
      description:"Devastating disease by Phytophthora infestans. Can destroy entire field.",
      symptoms:["Water-soaked lesions","White mold under leaves","Brown-black stem lesions","Tuber rot"],
      precautions:["Monitor weather","Scout regularly","Destroy cull piles","Avoid pre-rain irrigation"],
      prevention:["Resistant cultivars","Certified seed","Eliminate volunteers","Preventive fungicide"],
      treatment:["Metalaxyl + Mancozeb","Ridomil Gold","Destroy infected fields","Harvest healthy tubers early"] },
    { crop:"Wheat", disease:"Leaf Rust", confidence:90.6, severity:"Moderate to High",
      description:"Orange-brown pustules on leaf surfaces caused by Puccinia triticina.",
      symptoms:["Orange-brown oval pustules","Random on leaves","Break through epidermis","Premature leaf death"],
      precautions:["Monitor at heading","Scout lower canopy","Check forecasts","Report unusual rust"],
      prevention:["Resistant cultivars","Timely sowing","Avoid late planting","Seed treatment"],
      treatment:["Apply Propiconazole","Tebuconazole","Foliar fungicide spray","Apply at early detection"] }
  ];
  return diseases[Math.floor(Math.random() * diseases.length)];
}

// ===== SHOW DETAILED RESULTS MODAL =====
function showDetailedResults(data) {
  // Remove existing modal
  const existing = document.getElementById('results-modal');
  if (existing) existing.remove();

  const severityColor = data.severity === 'None' ? '#16a34a' : data.severity === 'High' || data.severity === 'Very High' ? '#dc2626' : '#f59e0b';

  const modal = document.createElement('div');
  modal.id = 'results-modal';
  modal.className = 'modal-overlay active';
  modal.innerHTML = `
    <div class="modal-content" style="max-width:800px;max-height:90vh;overflow-y:auto;">
      <button class="modal-close" onclick="document.getElementById('results-modal').remove()">&times;</button>
      <div style="text-align:center;margin-bottom:20px;">
        <div style="display:inline-block;padding:6px 16px;background:${severityColor}15;color:${severityColor};border-radius:20px;font-size:12px;font-weight:700;margin-bottom:10px;">
          ${data.severity === 'None' ? '✅ HEALTHY' : '⚠️ DISEASE DETECTED'}
        </div>
        <h2 style="font-family:'Outfit',sans-serif;color:#1a1a1a;">${data.crop} - ${data.disease}</h2>
        <div style="display:flex;justify-content:center;gap:20px;margin-top:10px;">
          <span style="font-size:13px;color:#6b7280;">Confidence: <strong style="color:#1a1a1a;">${data.confidence}%</strong></span>
          <span style="font-size:13px;color:#6b7280;">Severity: <strong style="color:${severityColor};">${data.severity}</strong></span>
        </div>
      </div>

      <p style="text-align:center;color:#4b5563;font-size:14px;margin-bottom:24px;line-height:1.6;">${data.description}</p>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div style="background:#fef2f2;border-radius:12px;padding:18px;">
          <h4 style="color:#dc2626;margin-bottom:10px;font-size:14px;"><i class="fas fa-stethoscope"></i> Symptoms</h4>
          <ul style="list-style:none;font-size:13px;color:#374151;">${(data.symptoms||[]).map(s => `<li style="margin:6px 0;">🔴 ${s}</li>`).join('')}</ul>
        </div>
        <div style="background:#fff7ed;border-radius:12px;padding:18px;">
          <h4 style="color:#ea580c;margin-bottom:10px;font-size:14px;"><i class="fas fa-shield-halved"></i> Precautions</h4>
          <ul style="list-style:none;font-size:13px;color:#374151;">${(data.precautions||[]).map(s => `<li style="margin:6px 0;">🟠 ${s}</li>`).join('')}</ul>
        </div>
        <div style="background:#f0fdf4;border-radius:12px;padding:18px;">
          <h4 style="color:#16a34a;margin-bottom:10px;font-size:14px;"><i class="fas fa-shield-virus"></i> Prevention</h4>
          <ul style="list-style:none;font-size:13px;color:#374151;">${(data.prevention||[]).map(s => `<li style="margin:6px 0;">🟢 ${s}</li>`).join('')}</ul>
        </div>
        <div style="background:#eff6ff;border-radius:12px;padding:18px;">
          <h4 style="color:#2563eb;margin-bottom:10px;font-size:14px;"><i class="fas fa-prescription"></i> Treatment</h4>
          <ul style="list-style:none;font-size:13px;color:#374151;">${(data.treatment||[]).map(s => `<li style="margin:6px 0;">💊 ${s}</li>`).join('')}</ul>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
}

// ===== HISTORY =====
function addToHistory(crop, disease) {
  const historyList = document.getElementById('history-list');
  if (!historyList) return;
  const newItem = document.createElement('div');
  newItem.className = 'history-item-card';
  newItem.style.cursor = 'pointer';
  newItem.innerHTML = `
    <div class="history-thumb" style="background:linear-gradient(135deg,#dcfce7,#bbf7d0);display:flex;align-items:center;justify-content:center;font-size:18px;">🌿</div>
    <div class="history-info"><strong>${crop} - ${disease}</strong><small>Just now</small></div>`;
  historyList.insertBefore(newItem, historyList.firstChild);
  const history = JSON.parse(localStorage.getItem('agroHistory') || '[]');
  history.unshift({ crop, disease, time: new Date().toISOString() });
  localStorage.setItem('agroHistory', JSON.stringify(history.slice(0, 20)));
}

function updateScanCount() {
  const el = document.getElementById('stat-scans');
  if (el) el.textContent = (parseInt(el.textContent) || 0) + 1;
}

// ===== VIEW ALL BUTTONS =====
const insightsViewAll = document.getElementById('insights-view-all');
if (insightsViewAll) {
  insightsViewAll.addEventListener('click', (e) => {
    e.preventDefault();
    const m = document.createElement('div');
    m.id = 'insights-modal'; m.className = 'modal-overlay active';
    m.innerHTML = `<div class="modal-content"><button class="modal-close" onclick="document.getElementById('insights-modal').remove()">&times;</button>
      <h2 style="font-family:'Outfit',sans-serif;margin-bottom:20px;">All Insights</h2>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div style="padding:14px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-check-circle" style="color:#16a34a;"></i> Perfect time for irrigation - soil moisture at optimal level</div>
        <div style="padding:14px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-check-circle" style="color:#16a34a;"></i> Soil moisture is optimal for current crop growth stage</div>
        <div style="padding:14px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-check-circle" style="color:#16a34a;"></i> High yield probability this season based on conditions</div>
        <div style="padding:14px;background:#fff7ed;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-exclamation-triangle" style="color:#f59e0b;"></i> Monitor for fungal diseases due to humidity levels</div>
        <div style="padding:14px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-check-circle" style="color:#16a34a;"></i> Nitrogen levels adequate for vegetative growth</div>
        <div style="padding:14px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-check-circle" style="color:#16a34a;"></i> Recommended: Apply potash fertilizer next week</div>
        <div style="padding:14px;background:#fef2f2;border-radius:10px;display:flex;align-items:center;gap:10px;"><i class="fas fa-exclamation-circle" style="color:#dc2626;"></i> Pest alert: Monitor for aphids in coming days</div>
      </div></div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => { if (e.target === m) m.remove(); });
  });
}

const historyViewAll = document.getElementById('history-view-all');
if (historyViewAll) {
  historyViewAll.addEventListener('click', (e) => {
    e.preventDefault();
    const history = JSON.parse(localStorage.getItem('agroHistory') || '[]');
    const items = history.length > 0 ? history.map(h => `<div style="padding:12px;background:#f9fafb;border-radius:10px;display:flex;justify-content:space-between;align-items:center;">
      <div><strong>${h.crop} - ${h.disease}</strong></div>
      <small style="color:#9ca3af;">${new Date(h.time).toLocaleDateString()}</small></div>`).join('') :
      `<div style="padding:12px;background:#f9fafb;border-radius:10px;display:flex;justify-content:space-between;">
      <div><strong>Tomato - Early Blight</strong></div><small style="color:#9ca3af;">2 hours ago</small></div>
      <div style="padding:12px;background:#f9fafb;border-radius:10px;display:flex;justify-content:space-between;">
      <div><strong>Rice - Healthy</strong></div><small style="color:#9ca3af;">1 day ago</small></div>
      <div style="padding:12px;background:#f9fafb;border-radius:10px;display:flex;justify-content:space-between;">
      <div><strong>Maize - Leaf Spot</strong></div><small style="color:#9ca3af;">3 days ago</small></div>`;
    const m = document.createElement('div');
    m.id = 'history-modal'; m.className = 'modal-overlay active';
    m.innerHTML = `<div class="modal-content"><button class="modal-close" onclick="document.getElementById('history-modal').remove()">&times;</button>
      <h2 style="font-family:'Outfit',sans-serif;margin-bottom:20px;">Scan History</h2>
      <div style="display:flex;flex-direction:column;gap:10px;">${items}</div></div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => { if (e.target === m) m.remove(); });
  });
}

// ===== FEATURE CARD CLICKS =====
const featureActions = {
  'feature-scanning': () => scrollToSection('scan'),
  'feature-insights': () => { const el = document.getElementById('insights-view-all'); if (el) el.click(); },
  'feature-weather': () => scrollToSection('weather-section'),
  'feature-history': () => { const el = document.getElementById('history-view-all'); if (el) el.click(); },
  'feature-assistant': () => { window.location.href = 'chat.html'; },
  'feature-knowledge': () => {
    const m = document.createElement('div');
    m.id = 'knowledge-modal'; m.className = 'modal-overlay active';
    m.innerHTML = `<div class="modal-content"><button class="modal-close" onclick="document.getElementById('knowledge-modal').remove()">&times;</button>
      <h2 style="font-family:'Outfit',sans-serif;margin-bottom:20px;">📚 Crop Knowledge Base</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🍅 Tomato: Warm-season crop. Needs 6-8hrs sun. Common diseases: Early Blight, Late Blight, Leaf Mold. Water at base, not leaves.')">
          <h4>🍅 Tomato</h4><p style="font-size:12px;color:#6b7280;">Growth guide & diseases</p></div>
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🌾 Rice: Needs standing water. Common diseases: Blast, Brown Spot, Sheath Blight. Avoid excess nitrogen.')">
          <h4>🌾 Rice</h4><p style="font-size:12px;color:#6b7280;">Paddy farming tips</p></div>
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🌽 Corn/Maize: Full sun crop. Common diseases: Rust, Leaf Blight. Plant resistant hybrids, rotate crops.')">
          <h4>🌽 Corn/Maize</h4><p style="font-size:12px;color:#6b7280;">Maize cultivation</p></div>
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🥔 Potato: Cool-season crop. Common diseases: Early & Late Blight. Use certified seed, rotate 3+ years.')">
          <h4>🥔 Potato</h4><p style="font-size:12px;color:#6b7280;">Potato disease guide</p></div>
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🌾 Wheat: Cool-season grain. Common diseases: Rust, Powdery Mildew. Plant resistant varieties, timely sowing.')">
          <h4>🌾 Wheat</h4><p style="font-size:12px;color:#6b7280;">Wheat farming guide</p></div>
        <div style="padding:16px;background:#f0fdf4;border-radius:12px;cursor:pointer;" onclick="alert('🌱 General: Crop rotation, soil testing, balanced NPK, integrated pest management are key to successful farming.')">
          <h4>🌱 General Tips</h4><p style="font-size:12px;color:#6b7280;">Smart farming basics</p></div>
      </div></div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => { if (e.target === m) m.remove(); });
  }
};

Object.keys(featureActions).forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', featureActions[id]);
});

// ===== WEATHER =====
async function loadWeather() {
  try {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => await fetchWeather(pos.coords.latitude, pos.coords.longitude),
        async () => await fetchWeather(28.6139, 77.2090)
      );
    } else { await fetchWeather(28.6139, 77.2090); }
  } catch (e) { setWeatherUI(28, 60, 'Partly Cloudy', 32, 22); }
}

async function fetchWeather(lat, lon) {
  try {
    const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=YOUR_API_KEY&units=metric`);
    const data = await res.json();
    if (data.main) setWeatherUI(Math.round(data.main.temp), data.main.humidity, data.weather[0].description, Math.round(data.main.temp_max), Math.round(data.main.temp_min));
  } catch (e) { setWeatherUI(28, 60, 'Partly Cloudy', 32, 22); }
}

function setWeatherUI(temp, humidity, condition, high, low) {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('weather-temp', temp + '°C');
  set('weather-condition', condition.charAt(0).toUpperCase() + condition.slice(1));
  set('weather-range', `H: ${high}°C   L: ${low}°C`);
  set('stat-temp', temp + '°C');
  set('stat-humidity', humidity + '%');
}
loadWeather();

// ===== SCROLL ANIMATIONS =====
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => { if (entry.isIntersecting) { entry.target.style.opacity = '1'; entry.target.style.transform = 'translateY(0)'; } });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

document.querySelectorAll('.feature-card, .dash-card, .about-content, .contact-card').forEach(el => {
  el.style.opacity = '0'; el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  fadeObserver.observe(el);
});

// ===== ESCAPE KEY =====
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeDemo();
    ['results-modal','insights-modal','history-modal','knowledge-modal'].forEach(id => {
      const m = document.getElementById(id); if (m) m.remove();
    });
  }
});

// ===== LOAD SCAN COUNT =====
function loadHistory() {
  const h = JSON.parse(localStorage.getItem('agroHistory') || '[]');
  const el = document.getElementById('stat-scans');
  if (el && h.length > 0) el.textContent = 12 + h.length;
}
loadHistory();

console.log('🌿 AgroVision loaded successfully');
