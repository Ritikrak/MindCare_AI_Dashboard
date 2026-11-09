const form = document.getElementById('prediction-form');
const predictButton = document.getElementById('predict-button');
const buttonLabel = predictButton.querySelector('.button-label');
const scoreValue = document.getElementById('score-value');
const scoreLabel = document.getElementById('score-label');
const scoreSummary = document.getElementById('score-summary');
const insightMessage = document.getElementById('insight-message');
const statusMessage = document.getElementById('status-message');
const headerStatus = document.getElementById('header-status');
const meterFill = document.getElementById('meter-fill');
const meterValue = document.getElementById('meter-value');
const meterTrack = document.querySelector('.meter-track');
const scoreRing = document.getElementById('score-ring');
const headerStatusLabel = headerStatus.querySelector('.status-label');
const visitorCount = document.getElementById('visitor-count');

const API_BASE_URL = 'https://mindcare-ai-dashboard.onrender.com';

const updateVisitorCount = async () => {
  try {
    let visitorId = localStorage.getItem('mindcare-visitor-id');
    if (!visitorId) {
      const randomBytes = crypto.getRandomValues(new Uint8Array(16));
      randomBytes[6] = (randomBytes[6] & 0x0f) | 0x40;
      randomBytes[8] = (randomBytes[8] & 0x3f) | 0x80;
      const hex = Array.from(randomBytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
      visitorId = `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
      localStorage.setItem('mindcare-visitor-id', visitorId);
    }

    const response = await fetch(`${API_BASE_URL}/api/visitor-count`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visitor_id: visitorId })
    });

    if (!response.ok) {
      throw new Error('Could not load the visitor count.');
    }

    const result = await response.json();
    const count = Number(result.unique_visitors);
    if (!Number.isSafeInteger(count) || count < 0) {
      throw new Error('The visitor count response was invalid.');
    }

    visitorCount.textContent = count.toLocaleString();
  } catch (error) {
    visitorCount.textContent = 'Unavailable';
    visitorCount.title = error instanceof Error ? error.message : 'Visitor count could not be loaded.';
  }
};

const getInterpretation = (score) => {
  if (score < 4) {
    return {
      label: 'Positive signs',
      summary: 'This estimate points to encouraging wellbeing patterns.',
      guidance: 'Keep making space for the routines and connections that help you feel your best.',
      color: '#29886f'
    };
  }

  if (score < 6) {
    return {
      label: 'Room to reset',
      summary: 'A few areas may benefit from a little extra attention.',
      guidance: 'A regular sleep routine, mindful breaks, and a conversation with someone you trust can help.',
      color: '#b67b22'
    };
  }

  return {
    label: 'Check in with yourself',
    summary: 'This estimate suggests it may be helpful to pause and seek support.',
    guidance: 'Consider reaching out to someone you trust or a qualified mental health professional.',
    color: '#bd5865'
  };
};

const setHeaderStatus = (state, label, color) => {
  headerStatus.dataset.state = state;
  headerStatusLabel.textContent = label;

  if (color) {
    headerStatus.style.color = color;
    headerStatus.style.borderColor = `${color}35`;
    headerStatus.style.backgroundColor = `${color}12`;
    headerStatus.style.setProperty('--status-color', color);
  } else {
    headerStatus.style.removeProperty('color');
    headerStatus.style.removeProperty('border-color');
    headerStatus.style.removeProperty('background-color');
    headerStatus.style.removeProperty('--status-color');
  }
};

const updateScoreVisuals = (score) => {
  const safeScore = Math.min(Math.max(score, 0), 10);
  const percent = (safeScore / 10) * 100;
  const interpretation = getInterpretation(safeScore);

  scoreValue.textContent = safeScore.toFixed(2);
  scoreLabel.textContent = interpretation.label;
  scoreSummary.textContent = interpretation.summary;
  insightMessage.textContent = interpretation.guidance;
  scoreRing.style.setProperty('--progress', percent);
  scoreRing.style.setProperty('--ring-color', interpretation.color);
  scoreRing.setAttribute('aria-label', `Wellbeing estimate: ${safeScore.toFixed(2)} out of 10`);
  meterFill.style.width = `${percent}%`;
  meterValue.innerHTML = `${safeScore.toFixed(2)} <small>/ 10</small>`;
  meterTrack.setAttribute('aria-valuenow', safeScore.toFixed(2));
  setHeaderStatus('result', interpretation.label, interpretation.color);
};

const normalizeForm = (data) => ({
  age: Number(data.age),
  gender: data.gender,
  country: data.country,
  academic_level: data.academic_level,
  most_used_platform: data.most_used_platform,
  purpose_of_use: data.purpose_of_use,
  avg_daily_usage_hours: Number(data.avg_daily_usage_hours),
  daily_unlocks: Number(data.daily_unlocks),
  study_hours: Number(data.study_hours),
  physical_activity_hours: Number(data.physical_activity_hours),
  sleep_hours_per_night: Number(data.sleep_hours_per_night),
  stress_level: data.stress_level
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  predictButton.disabled = true;
  buttonLabel.textContent = 'Creating your insight…';
  statusMessage.textContent = 'Reviewing your check-in…';
  statusMessage.style.color = '';
  setHeaderStatus('loading', 'Analyzing');

  const payload = normalizeForm(Object.fromEntries(new FormData(form).entries()));

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = typeof errorData?.detail === 'string' ? errorData.detail : 'Please try again in a moment.';
      throw new Error(detail);
    }

    const result = await response.json();
    const score = Number(result.mental_health_score);
    if (!Number.isFinite(score)) {
      throw new Error('The model returned an invalid score. Please try again.');
    }

    updateScoreVisuals(score);
    statusMessage.textContent = 'Your wellbeing snapshot is ready.';
    statusMessage.style.color = '#347e68';
  } catch (error) {
    statusMessage.textContent = error instanceof Error ? error.message : 'Something went wrong. Please try again.';
    statusMessage.style.color = '#bd5865';
    setHeaderStatus('error', 'Try again', '#bd5865');
  } finally {
    predictButton.disabled = false;
    buttonLabel.textContent = 'Generate my wellbeing insight';
  }
});

updateVisitorCount();
