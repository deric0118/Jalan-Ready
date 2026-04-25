/**
 * ═══════════════════════════════════════════════════════════════════
 *  app.js  —  Jalan-Ready Main Application Controller
 *  Selangor Intelligent RoadCare Command Center
 *
 *  Responsibilities:
 *   - Bootstrap UI components
 *   - Enforce authentication (redirect to login if no token)
 *   - Verify token with backend on load
 *   - Handle citizen report (image upload + AI analysis)
 *   - Dispatch work order (with auth header)
 * ═══════════════════════════════════════════════════════════════════
 */

import { SIRCaAPI } from './api.js';   // changed to match export in api.js

// ─── Singleton ─────────────────────────────────────────────────────
const api = new SIRCaAPI();

// ─── DOMContentLoaded ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Check local storage for token
  const token = localStorage.getItem('auth_token');
  const userStr = localStorage.getItem('auth_user');
  if (!token || !userStr) {
    window.location.href = window.location.origin + '/login.html';
    return;
  }

  // 2. Verify token with backend
  try {
    const isValid = await api.verifyToken(token);
    if (!isValid) throw new Error('Invalid token');
  } catch (err) {
    console.warn('Token verification failed:', err);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    window.location.href = window.location.origin + '/login.html';
    return;
  }

  const user = JSON.parse(userStr);
  initClock();
  initMetricCounters();
  initReportPanel();
  initDispatchButton();
  initLogout();

  console.log(`Welcome back, ${user.name}`);
});

// ═══════════════════════════════════════════════════════════════════
//  CLOCK
// ═══════════════════════════════════════════════════════════════════
function initClock() {
  const timeEl = document.getElementById('live-time');
  const dateEl = document.getElementById('live-date');
  if (!timeEl || !dateEl) return;
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const DAYS   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  function tick() {
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('en-GB');
    dateEl.textContent = `${DAYS[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]} ${now.getFullYear()}`;
  }
  tick();
  setInterval(tick, 1000);
}

// ═══════════════════════════════════════════════════════════════════
//  METRIC COUNTERS
// ═══════════════════════════════════════════════════════════════════
function initMetricCounters() {
  const metricEls = document.querySelectorAll('.metric-value[data-count]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.count, 10);
        animateCount(el, target);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.3 });
  metricEls.forEach(el => observer.observe(el));
}
function animateCount(el, target, duration = 1200) {
  const start = performance.now();
  const startVal = 0;
  const step = (now) => {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(startVal + (target - startVal) * eased);
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ═══════════════════════════════════════════════════════════════════
//  REPORT PANEL (image upload + analysis call)
// ═══════════════════════════════════════════════════════════════════
function initReportPanel() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('imageInput');
  const submitBtn = document.getElementById('submitBtn');
  const locationInput = document.getElementById('locationInput');
  const noteInput = document.getElementById('noteInput');

  if (!dropzone) return;

  let selectedFile = null;

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

  function handleFile(file) {
    selectedFile = file;
    dropzone.innerHTML = `<i class="fa-regular fa-image text-3xl text-selangor-red mb-2"></i>
                          <p class="text-slate-700 font-medium">${file.name}</p>
                          <p class="text-xs text-slate-400">Click or drag to change</p>`;
    dropzone.classList.add('border-selangor-red/30', 'bg-selangor-red/5');
  }

  submitBtn.addEventListener('click', async () => {
    if (!selectedFile) {
      showToast('error', 'No image', 'Please upload a photo.');
      return;
    }
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analysing...';

    // Get location and note
    const location = locationInput?.value || '';
    const note = noteInput?.value || '';

    // Get GPS if available (optional)
    let lat = null, lon = null;
    if (navigator.geolocation) {
      await new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(pos => {
          lat = pos.coords.latitude;
          lon = pos.coords.longitude;
          resolve();
        }, () => resolve()); // fallback: continue without GPS
      });
    }

    try {
      // Use submitReport method from api.js
      const result = await api.submitReport({
        image: selectedFile,
        description: location + (note ? ` - ${note}` : ''),
        lat,
        lon
      });
      // Expected response structure: { success: true, work_order: {...} }
      if (result.success && result.work_order) {
        updateUI(result.work_order);
        showToast('success', 'Analysis complete', 'Work order generated.');
      } else {
        throw new Error(result.error || 'Unknown response');
      }
    } catch (err) {
      console.error(err);
      showToast('error', 'Analysis failed', err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit report';
    }
  });
}

function updateUI(wo) {
  const resultSection = document.getElementById('resultSection');
  if (resultSection) resultSection.classList.remove('hidden');
  document.getElementById('defectClass').innerText = wo.detections?.[0]?.class || 'Pothole';
  document.getElementById('confidence').innerText = (wo.detections?.[0]?.confidence * 100).toFixed(0) + '%';
  document.getElementById('authority').innerText = wo.decision?.assigned_to || 'MBPJ';
  document.getElementById('workOrderId').innerText = wo.id;
  document.getElementById('sla').innerText = wo.decision?.priority === 'P1' ? 'Within 48 hours' : 'Within 7 days';
  const priority = wo.decision?.priority || 'HIGH';
  const badge = document.getElementById('priorityBadge');
  badge.innerText = `PRIORITY: ${priority}`;
  badge.className = `result-chip px-4 py-1 text-sm font-semibold priority-${priority.toLowerCase() === 'p1' ? 'high' : (priority.toLowerCase() === 'p2' ? 'med' : 'low')}`;
  document.getElementById('reasoningPanel').innerText = wo.decision?.reasoning || 'No reasoning provided.';
  window.currentWorkOrderId = wo.id;
}

// ═══════════════════════════════════════════════════════════════════
//  DISPATCH BUTTON
// ═══════════════════════════════════════════════════════════════════
function initDispatchButton() {
  const btn = document.getElementById('dispatchBtn');
  btn?.addEventListener('click', async () => {
    if (!window.currentWorkOrderId) return;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dispatching...';
    try {
      const result = await api.dispatchWorkOrder(window.currentWorkOrderId);
      document.getElementById('dispatchSuccess').classList.remove('hidden');
      showToast('success', 'Dispatched', `Sent to ${result.dispatched_to}`);
    } catch (err) {
      showToast('error', 'Dispatch failed', err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-check-circle"></i> Approve & dispatch';
    }
  });
}

// ═══════════════════════════════════════════════════════════════════
//  LOGOUT
// ═══════════════════════════════════════════════════════════════════
function initLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login.html';
    });
  }
}

// ═══════════════════════════════════════════════════════════════════
//  TOAST SYSTEM
// ═══════════════════════════════════════════════════════════════════
function showToast(type, title, message, duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `bg-white rounded-xl shadow-lg px-4 py-2 flex items-center gap-3 text-sm animate-fade-up`;
  const icon = type === 'success' ? 'fa-check-circle text-emerald-500' : (type === 'error' ? 'fa-exclamation-circle text-red-500' : 'fa-info-circle text-selangor-red');
  toast.innerHTML = `<i class="fa-solid ${icon} text-lg"></i><div><div class="font-semibold">${title}</div><div class="text-slate-500 text-xs">${message}</div></div>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}
window.showToast = showToast;