// ===== FLOATING LEAVES =====
function createLeaves() {
  const container = document.getElementById('leafContainer');
  if (!container) return;
  const emojis = ['🍃', '🌿', '🍂', '🌱', '☘️'];
  for (let i = 0; i < 15; i++) {
    const leaf = document.createElement('span');
    leaf.className = 'leaf';
    leaf.textContent = emojis[Math.floor(Math.random() * emojis.length)];
    leaf.style.left = Math.random() * 100 + '%';
    leaf.style.animationDuration = (8 + Math.random() * 12) + 's';
    leaf.style.animationDelay = Math.random() * 10 + 's';
    leaf.style.fontSize = (1 + Math.random() * 1.5) + 'rem';
    container.appendChild(leaf);
  }
}

// ===== NAVBAR SCROLL =====
function initNavbar() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// ===== SCROLL REVEAL =====
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ===== UPLOAD & SCAN =====
let selectedFile = null;

function initUpload() {
  const zone = document.getElementById('uploadZone');
  const input = document.getElementById('fileInput');
  const preview = document.getElementById('previewContainer');
  const previewImg = document.getElementById('previewImg');
  const scanBtn = document.getElementById('scanBtn');

  if (!zone) return;

  // Click to upload
  zone.addEventListener('click', () => input.click());

  // Drag and drop
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  // File input change
  input.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
  });

  function handleFile(file) {
    if (!file.type.startsWith('image/')) {
      showError('❌ कृपया एक image file (JPG/PNG) upload करें।', '');
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      preview.classList.add('show');
      scanBtn.disabled = false;
      // Hide previous results
      document.getElementById('resultSection').classList.remove('show');
      document.getElementById('errorSection').style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  // Scan button
  scanBtn.addEventListener('click', () => {
    if (!selectedFile) return;
    analyzeImage();
  });
}

async function analyzeImage() {
  const loading = document.getElementById('loadingOverlay');
  const resultSection = document.getElementById('resultSection');
  const errorSection = document.getElementById('errorSection');

  // Show loading
  loading.classList.add('show');
  resultSection.classList.remove('show');
  errorSection.style.display = 'none';

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const response = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await response.json();

    loading.classList.remove('show');

    if (data.error) {
      showError(data.message, data.suggestion || '');
    } else {
      showResult(data);
    }
  } catch (err) {
    loading.classList.remove('show');
    showError('❌ Server se connect nahi ho paya। कृपया server chalu karein।', '');
  }
}

function showError(message, suggestion) {
  const errorSection = document.getElementById('errorSection');
  document.getElementById('resultSection').classList.remove('show');
  errorSection.style.display = 'block';
  errorSection.innerHTML = `
    <div class="error-card">
      <div class="error-icon">⚠️</div>
      <p style="font-size:1.05rem;color:var(--text);font-weight:500;">${message}</p>
      ${suggestion ? `<p class="suggestion">${suggestion}</p>` : ''}
      <button class="btn-secondary" style="margin-top:16px;" onclick="resetScan()">🔄 Dobara Try Karein</button>
    </div>
  `;
  errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function showResult(data) {
  const section = document.getElementById('resultSection');
  document.getElementById('errorSection').style.display = 'none';

  const severityClass = data.severity.toLowerCase();
  const headerClass = data.is_healthy ? 'healthy' : (severityClass === 'critical' ? 'critical' : 'diseased');
  const statusEmoji = data.is_healthy ? '✅' : (severityClass === 'critical' ? '🚨' : '⚠️');

  let symptomsHtml = '';
  if (data.symptoms && data.symptoms.length > 0) {
    symptomsHtml = data.symptoms.map(s => `<li>🔸 ${s}</li>`).join('');
  } else {
    symptomsHtml = '<li>✅ No disease symptoms detected</li>';
  }

  const precautionsHtml = data.precautions.map(p => `<li>🛡️ ${p}</li>`).join('');
  const preventionHtml = data.prevention.map(p => `<li>🌿 ${p}</li>`).join('');
  const treatmentHtml = data.treatment.map(t => `<li>💊 ${t}</li>`).join('');

  section.innerHTML = `
    <div class="result-card">
      <div class="result-header ${headerClass}">
        <div>
          <div class="result-disease-name">${statusEmoji} ${data.disease}</div>
          <div class="result-hindi">${data.hindi_name} | ${data.crop}</div>
        </div>
        <span class="severity-badge ${severityClass}">${data.severity === 'None' ? '✅ Healthy' : '⚠ ' + data.severity}</span>
      </div>
      <div class="result-body">
        <p class="result-desc">${data.description}</p>
        <div class="confidence-bar">
          <div class="confidence-label">
            <span>Confidence Level</span>
            <span style="color:var(--green-1);font-weight:600;">${data.confidence}%</span>
          </div>
          <div class="confidence-track">
            <div class="confidence-fill" id="confFill" style="width:0%"></div>
          </div>
        </div>
        <div class="info-tabs">
          <button class="info-tab active" onclick="switchTab('symptoms',this)">🔍 Symptoms</button>
          <button class="info-tab" onclick="switchTab('precautions',this)">🛡️ Precautions</button>
          <button class="info-tab" onclick="switchTab('prevention',this)">🌿 Prevention</button>
          <button class="info-tab" onclick="switchTab('treatment',this)">💊 Treatment</button>
        </div>
        <div class="info-panel active" id="panel-symptoms"><ul class="info-list">${symptomsHtml}</ul></div>
        <div class="info-panel" id="panel-precautions"><ul class="info-list">${precautionsHtml}</ul></div>
        <div class="info-panel" id="panel-prevention"><ul class="info-list">${preventionHtml}</ul></div>
        <div class="info-panel" id="panel-treatment"><ul class="info-list">${treatmentHtml}</ul></div>
        <button class="btn-secondary" style="margin-top:20px;width:100%;" onclick="resetScan()">🔄 Nayi Photo Scan Karein</button>
      </div>
    </div>
  `;

  section.classList.add('show');
  // Animate confidence bar
  setTimeout(() => {
    document.getElementById('confFill').style.width = data.confidence + '%';
  }, 300);
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function switchTab(name, btn) {
  document.querySelectorAll('.info-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.info-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  btn.classList.add('active');
}

function resetScan() {
  selectedFile = null;
  document.getElementById('previewContainer').classList.remove('show');
  document.getElementById('resultSection').classList.remove('show');
  document.getElementById('errorSection').style.display = 'none';
  document.getElementById('scanBtn').disabled = true;
  document.getElementById('fileInput').value = '';
  document.getElementById('uploadZone').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ===== CROP CALENDAR =====
async function loadCalendar() {
  try {
    const res = await fetch('/api/calendar');
    const data = await res.json();
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;
    const now = new Date();
    const currentMonth = now.toLocaleString('en', { month: 'short' });
    grid.innerHTML = data.map(item => `
      <div class="cal-card ${item.month === currentMonth ? 'current' : ''}">
        <div class="cal-month">${item.month}</div>
        <div class="cal-crops">${item.crops}</div>
        <div class="cal-activity">${item.activity}</div>
      </div>
    `).join('');
  } catch (e) { /* Calendar is optional */ }
}

// ===== KRISHI TIPS =====
async function loadTips() {
  try {
    const res = await fetch('/api/tips');
    const data = await res.json();
    const grid = document.getElementById('tipsGrid');
    if (!grid) return;
    grid.innerHTML = data.map(tip => `
      <div class="tip-card">
        <span class="tip-icon">${tip.icon}</span>
        <h3>${tip.title}</h3>
        <p>${tip.tip}</p>
        <span class="tip-season">${tip.season}</span>
      </div>
    `).join('');
  } catch (e) { /* Tips are optional */ }
}

// ===== SMOOTH SCROLL =====
function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
}

// ===== COUNTER ANIMATION =====
function animateCounters() {
  document.querySelectorAll('.stat-num').forEach(el => {
    const target = parseInt(el.getAttribute('data-target'));
    const suffix = el.getAttribute('data-suffix') || '';
    let current = 0;
    const step = Math.max(1, Math.floor(target / 60));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = current + suffix;
    }, 30);
  });
}

// ===== CONTACT FORM =====
function submitContact(e) {
  e.preventDefault();
  document.querySelector('.contact-form').style.display = 'none';
  document.getElementById('contactSuccess').style.display = 'block';
}

// ===== CHATBOT =====
let chatOpen = false;

function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatWindow').classList.toggle('open', chatOpen);
  document.getElementById('chatFab').classList.toggle('open', chatOpen);
  document.getElementById('chatFab').textContent = chatOpen ? '✕' : '🤖';
  if (chatOpen) {
    document.getElementById('chatInput').focus();
    loadChatSuggestions();
  }
}

async function loadChatSuggestions() {
  try {
    const res = await fetch('/api/suggestions');
    const suggestions = await res.json();
    renderSuggestions(suggestions);
  } catch (e) { /* optional */ }
}

function renderSuggestions(suggestions) {
  const container = document.getElementById('chatSuggestions');
  container.innerHTML = suggestions.map(s =>
    `<button class="chat-sug-btn" onclick="askSuggestion(this)">${s}</button>`
  ).join('');
}

function askSuggestion(btn) {
  const text = btn.textContent;
  document.getElementById('chatInput').value = text;
  sendChat();
}

function addMessage(text, type) {
  const container = document.getElementById('chatMessages');
  const msg = document.createElement('div');
  msg.className = 'chat-msg ' + type;
  // Simple markdown: **bold**, \n to <br>, • to bullet
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\n/g, '<br>');
  msg.innerHTML = html;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('chatMessages');
  const typing = document.createElement('div');
  typing.className = 'chat-typing';
  typing.id = 'typingIndicator';
  typing.innerHTML = '<span></span><span></span><span></span>';
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, 'user');
  input.value = '';
  document.getElementById('chatSuggestions').innerHTML = '';

  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();

    // Simulate typing delay
    await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
    hideTyping();

    addMessage(data.reply, 'bot');
    if (data.suggestions && data.suggestions.length > 0) {
      renderSuggestions(data.suggestions);
    }
  } catch (err) {
    hideTyping();
    addMessage('❌ Server se connect nahi ho paya. Kripya server chalu karein.', 'bot');
  }
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
  createLeaves();
  initNavbar();
  initReveal();
  initUpload();
  loadCalendar();
  loadTips();
  setTimeout(animateCounters, 500);
});
