/**
 * ═══════════════════════════════════════════════════════════════════
 *  api.js  —  Jalan-Ready Backend Integration Layer ("The Doors")
 *  Selangor Intelligent RoadCare
 *
 *  Refactored to connect to real FastAPI backend endpoints.
 * ═══════════════════════════════════════════════════════════════════
 */

// ─── Configuration ───────────────────────────────────────────────────────────
const BASE_URL =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://api.jalan-ready.tk'; // Replace with your production API URL

const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept':       'application/json',
  'X-Client-App': 'Jalan-Ready/1.0',
};

// Helper to get auth token from localStorage
function getAuthToken() {
  return localStorage.getItem('auth_token');
}

// ─── SIRCaAPI Class (renamed to JalanReadyAPI optionally) ────────────────────
export class SIRCaAPI {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Private fetch with authentication
  async _fetch(endpoint, method = 'GET', body = null, isFormData = false) {
    const headers = { ...DEFAULT_HEADERS };
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    const options = { method, headers };
    if (body && method !== 'GET') {
      options.body = isFormData ? body : JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, options);
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errText}`);
    }
    return response.json();
  }

  // ── AUTHENTICATION ───────────────────────────────────────────────────────
  async verifyToken(token) {
    try {
      const res = await fetch(`${this.baseUrl}/api/verify`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ── DOOR 1: SUBMIT REPORT (with image) ──────────────────────────────────
async submitReport(data) {
  // data contains: { image: File, description: string, lat?: number, lon?: number }
  const formData = new FormData();
  formData.append('image', data.image);
  formData.append('location', data.description || '');
  if (data.lat) formData.append('lat', data.lat);
  if (data.lon) formData.append('lon', data.lon);
  
  // Call backend
  const response = await this._fetch('/api/analyze', 'POST', formData, true);
  
  // Optional: validate response shape and throw if backend indicates failure
  if (response && response.success === false) {
    throw new Error(response.error || 'Analysis failed');
  }
  
  // Return the full response (which contains success and work_order)
  return response;
}

  // ── DOOR 2: CHECK WORK ORDER STATUS (mock kept, replace when endpoint exists) ──
  async checkStatus(id) {
    // TODO: implement real endpoint /api/status/{id}
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockStatus(id)), 600);
    });
  }

  // ── DOOR 3: FETCH AGENT LOGS (mock kept) ─────────────────────────────────
  async fetchAgentLogs(reportId = 'RPT-PJ-20240812-004') {
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockAgentLogs(reportId)), 800);
    });
  }

  // ── DOOR 4: DISPATCH WORK ORDER ──────────────────────────────────────────
  async dispatchWorkOrder(workOrderId, approverNote = '') {
    return this._fetch('/api/dispatch', 'POST', {
      work_order_id: workOrderId,
      approver_note: approverNote
    });
  }

  // ── DOOR 5: WEATHER (mock) ───────────────────────────────────────────────
  async fetchWeather(lat = 3.1012, lon = 101.6530) {
    // TODO: implement real endpoint or proxy
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockWeather(lat, lon)), 900);
    });
  }

  // ── DOOR 6: FETCH REPORTS (mock) ─────────────────────────────────────────
  async fetchReports(filters = {}) {
    return new Promise((resolve) => {
      setTimeout(() => resolve({ reports: [], total: 47, page: 1 }), 700);
    });
  }

  // ── DOOR 7: METRICS (mock) ───────────────────────────────────────────────
  async fetchMetrics() {
    return new Promise((resolve) => {
      setTimeout(() => resolve({
        active_defects: 47,
        work_orders: 128,
        awaiting_dispatch: 34,
        resolved_30d: 93,
      }), 500);
    });
  }
}

// ─── Mock factories (keep for unimplemented endpoints) ───────────────────────
function _mockStatus(id) { /* ... keep existing mock ... */ }
function _mockAgentLogs(reportId) { /* ... keep ... */ }
function _mockWeather(lat, lon) { /* ... keep ... */ }
function _mockDispatch(workOrderId) { /* ... keep ... */ }