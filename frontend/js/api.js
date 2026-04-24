/**
 * ═══════════════════════════════════════════════════════════════════
 *  api.js  —  SIRCa Backend Integration Layer ("The Doors")
 *  Selangor Intelligent RoadCare
 *
 *  ┌─────────────────────────────────────────────────────────────┐
 *  │  BACKEND DEVELOPER GUIDE                                    │
 *  │                                                             │
 *  │  Every method in SIRCaAPI is a DOOR to a backend endpoint.  │
 *  │  Currently filled with mock Promises (setTimeout).          │
 *  │                                                             │
 *  │  TO CONNECT YOUR PYTHON BACKEND:                            │
 *  │   1. Replace BASE_URL with your server's address.           │
 *  │   2. In each method, uncomment the `return fetch(...)` call  │
 *  │      and remove the mock setTimeout block.                  │
 *  │   3. Ensure your FastAPI/Flask/Django server has CORS        │
 *  │      configured for the frontend origin.                    │
 *  │                                                             │
 *  │  Suggested Python backend: FastAPI + Uvicorn                │
 *  │  Example base: http://localhost:8000                        │
 *  └─────────────────────────────────────────────────────────────┘
 *
 * ═══════════════════════════════════════════════════════════════════
 */

// ─── Configuration ───────────────────────────────────────────────────────────

/**
 * BASE_URL
 * --------
 * BACKEND DEV: Replace with your actual backend address.
 * Production example:  'https://api.sirca.selangor.gov.my/v1'
 * Development example: 'http://localhost:8000'
 */
const BASE_URL = 'http://localhost:8000';

/**
 * DEFAULT_HEADERS
 * ---------------
 * Standard headers sent with every request.
 * BACKEND DEV: If your API requires an API key or Bearer token,
 *              add it here: 'Authorization': `Bearer ${TOKEN}`
 */
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept':       'application/json',
  // 'Authorization': 'Bearer YOUR_TOKEN_HERE',  // ← Uncomment when auth is ready
  'X-Client-App': 'SIRCa-Dashboard/1.0',
};


// ─── Mock Data Factories ─────────────────────────────────────────────────────
// These generate realistic dummy responses for development.
// Remove these once the real backend is connected.

function _mockReport(data) {
  return {
    success:    true,
    report_id:  `RPT-PJ-${Date.now()}`,
    work_order: `WO-SEL-2024-4821`,
    status:     'submitted',
    priority:   'HIGH',
    score:      87,
    authority:  'MBPJ',
    dispatch_to:'aduan@mbpj.gov.my',
    sla_hours:  48,
    created_at: new Date().toISOString(),
  };
}

function _mockStatus(id) {
  return {
    id,
    status:     'pending_dispatch',
    updated_at: new Date().toISOString(),
    steps: [
      { key: 'draft',       label: 'Draft',          done: true,  ts: '09:14 AM' },
      { key: 'submitted',   label: 'Submitted',       done: true,  ts: '09:15 AM' },
      { key: 'dispatched',  label: 'Pending Dispatch',done: false, ts: null },
      { key: 'scheduled',   label: 'Scheduled',       done: false, ts: null },
      { key: 'in_progress', label: 'In Progress',     done: false, ts: null },
      { key: 'completed',   label: 'Completed',       done: false, ts: null },
    ],
  };
}

function _mockAgentLogs(reportId) {
  return {
    report_id: reportId,
    session:   '0047',
    logs: [
      { module: 'VISION',       message: 'Image processed. Defect: Pothole (Type III). Conf: 94.2%',   ts: '09:14:02' },
      { module: 'GEO',          message: 'Coordinates: 3.1012, 101.6530 → Jalan SS7/2, Petaling Jaya', ts: '09:14:03' },
      { module: 'JURISDICTION', message: 'Road type LOCAL. Matched: MBPJ (Municipal Road)',             ts: '09:14:04' },
      { module: 'WEATHER',      message: 'Open-Meteo: 18.4mm rain (24h). Sub-base wet flag ACTIVE.',   ts: '09:14:05' },
      { module: 'PRIORITY',     message: 'Dynamic Score: 87/100 → HIGH. Near school (+20), wet (+15).', ts: '09:14:06' },
      { module: 'DISPATCH',     message: 'WO-SEL-2024-4821 generated. Awaiting approval.',              ts: '09:14:07' },
    ],
  };
}

function _mockWeather(lat, lon) {
  return {
    lat, lon,
    location:        'Petaling Jaya, Selangor',
    temperature_c:   32.1,
    precipitation_mm:18.4,
    condition:       'Partly Cloudy',
    subbase_flag:    true,
    forecast: [
      { date: 'Tomorrow', rain_mm: 4.2,  condition: 'Light Rain' },
      { date: 'Day+2',    rain_mm: 0.0,  condition: 'Sunny' },
      { date: 'Day+3',    rain_mm: 12.1, condition: 'Heavy Rain' },
    ],
  };
}

function _mockDispatch(workOrderId) {
  return {
    success:       true,
    work_order_id: workOrderId,
    dispatched_to: 'aduan@mbpj.gov.my',
    email_ref:     `MBPJ-ENF-2024-${Date.now()}`,
    dispatched_at: new Date().toISOString(),
    message:       'Work order dispatched successfully via email gateway.',
  };
}


// ─── SIRCaAPI Class ──────────────────────────────────────────────────────────

export class SIRCaAPI {

  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // ── Private HTTP Helper ─────────────────────────────────────────

  /**
   * _fetch
   * Wraps the native fetch() with standard headers and error handling.
   *
   * BACKEND DEV: This is the central HTTP method. All API calls go through here.
   * It throws on non-2xx responses, so callers can use try/catch.
   *
   * @param {string} endpoint   - e.g. '/report', '/status/123'
   * @param {string} method     - 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
   * @param {Object} [body]     - JSON body (for POST/PUT)
   * @param {Object} [headers]  - additional headers to merge
   * @returns {Promise<Object>}
   */
  async _fetch(endpoint, method = 'GET', body = null, headers = {}) {
    const options = {
      method,
      headers: { ...DEFAULT_HEADERS, ...headers },
    };
    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, options);

    if (!response.ok) {
      const errBody = await response.text();
      throw new Error(`[SIRCaAPI] HTTP ${response.status} on ${method} ${endpoint}: ${errBody}`);
    }

    return response.json();
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 1 — SUBMIT CITIZEN REPORT
  // ═══════════════════════════════════════════════════════════════
  /**
   * submitReport(data)
   * ------------------
   * Submit a new road damage report from the Citizen Input portal.
   * Triggers the YOLOv8 vision pipeline and Z.AI GLM agent on the backend.
   *
   * @param {Object} data
   * @param {File|string} data.image       - Image file or base64 string
   * @param {string}      data.description - Citizen's text description
   * @param {number}      [data.lat]       - GPS latitude (optional; fallback to EXIF)
   * @param {number}      [data.lon]       - GPS longitude
   * @param {string}      [data.reporter]  - Reporter ID or "anonymous"
   *
   * @returns {Promise<{report_id, work_order, status, priority, score, authority, ...}>}
   *
   * ─── BACKEND DEV: Replace mock below with: ───────────────────────
   *
   * PYTHON ENDPOINT (FastAPI example):
   *   POST http://localhost:8000/api/report
   *   Content-Type: multipart/form-data   ← use FormData if sending File
   *   Body: { image: File, description: str, lat?: float, lon?: float }
   *
   * REPLACEMENT CODE:
   *   const formData = new FormData();
   *   formData.append('image', data.image);
   *   formData.append('description', data.description);
   *   if (data.lat) formData.append('lat', data.lat);
   *   if (data.lon) formData.append('lon', data.lon);
   *   return fetch(`${this.baseUrl}/report`, {
   *     method: 'POST',
   *     headers: { 'X-Client-App': 'SIRCa-Dashboard/1.0' },  // NO Content-Type (multipart)
   *     body: formData,
   *   }).then(r => r.json());
   * ─────────────────────────────────────────────────────────────────
   */
  async submitReport(data) {
    // ── MOCK (remove when backend is ready) ──
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockReport(data)), 1200);
    });
    // ── END MOCK ──

    // ── REAL (uncomment when backend is ready) ──
    // return this._fetch('/report', 'POST', data);
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 2 — CHECK WORK ORDER STATUS
  // ═══════════════════════════════════════════════════════════════
  /**
   * checkStatus(id)
   * ---------------
   * Poll the status of a work order by its ID.
   * Used to update the vertical stepper (Column 3).
   *
   * @param {string} id - Work order ID (e.g., "WO-SEL-2024-4821")
   *
   * @returns {Promise<{id, status, steps: Array<{key, label, done, ts}>, ...}>}
   *
   * ─── BACKEND DEV: Replace mock below with: ───────────────────────
   *
   * PYTHON ENDPOINT (FastAPI example):
   *   GET http://localhost:8000/api/status/{id}
   *   Returns: JSON { id, status, steps: [...], updated_at }
   *
   * REPLACEMENT CODE:
   *   return this._fetch(`/status/${encodeURIComponent(id)}`, 'GET');
   * ─────────────────────────────────────────────────────────────────
   */
  async checkStatus(id) {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockStatus(id)), 600);
    });
    // ── REAL ──
    // return this._fetch(`/status/${encodeURIComponent(id)}`, 'GET');
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 3 — FETCH AGENT REASONING LOGS
  // ═══════════════════════════════════════════════════════════════
  /**
   * fetchAgentLogs(reportId)
   * ------------------------
   * Retrieve the Z.AI GLM agent's reasoning log for a report.
   * Each log line can be fed directly into AgentTerminal.run().
   *
   * @param {string} [reportId] - Report ID to retrieve logs for
   *
   * @returns {Promise<{report_id, session, logs: Array<{module, message, ts}>}>}
   *
   * ─── BACKEND DEV: Replace mock below with: ───────────────────────
   *
   * PYTHON ENDPOINT (FastAPI example):
   *   GET http://localhost:8000/api/logs/{report_id}
   *   Returns: JSON { report_id, session, logs: [...] }
   *
   * STREAMING ALTERNATIVE (Server-Sent Events):
   *   GET http://localhost:8000/api/logs/{report_id}/stream
   *   Content-Type: text/event-stream
   *   Data: each SSE event is one log line JSON object
   *
   *   Frontend SSE consumption:
   *   const es = new EventSource(`${BASE_URL}/logs/${id}/stream`);
   *   es.onmessage = (e) => terminal.appendInstant(JSON.parse(e.data));
   *
   * REPLACEMENT CODE (non-streaming):
   *   return this._fetch(`/logs/${encodeURIComponent(reportId)}`, 'GET');
   * ─────────────────────────────────────────────────────────────────
   */
  async fetchAgentLogs(reportId = 'RPT-PJ-20240812-004') {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockAgentLogs(reportId)), 800);
    });
    // ── REAL ──
    // return this._fetch(`/logs/${encodeURIComponent(reportId)}`, 'GET');
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 4 — DISPATCH WORK ORDER (Approve & Send Email)
  // ═══════════════════════════════════════════════════════════════
  /**
   * dispatchWorkOrder(workOrderId, approverNote)
   * ---------------------------------------------
   * Called when the supervisor clicks "Approve & Dispatch".
   * Triggers email dispatch to the JKR district / local council.
   *
   * @param {string} workOrderId   - e.g. "WO-SEL-2024-4821"
   * @param {string} [approverNote]- Optional supervisor annotation
   *
   * @returns {Promise<{success, dispatched_to, email_ref, dispatched_at, ...}>}
   *
   * ─── BACKEND DEV: Replace mock below with: ───────────────────────
   *
   * PYTHON ENDPOINT (FastAPI example):
   *   POST http://localhost:8000/api/dispatch
   *   Body: { work_order_id: str, approver_note?: str }
   *   Action: sends email via SMTP/SendGrid to authority contact
   *   Returns: { success, dispatched_to, email_ref, dispatched_at }
   *
   * REPLACEMENT CODE:
   *   return this._fetch('/dispatch', 'POST', { work_order_id: workOrderId, approver_note: approverNote });
   * ─────────────────────────────────────────────────────────────────
   */
  async dispatchWorkOrder(workOrderId, approverNote = '') {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockDispatch(workOrderId)), 1800);
    });
    // ── REAL ──
    // return this._fetch('/dispatch', 'POST', { work_order_id: workOrderId, approver_note: approverNote });
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 5 — FETCH WEATHER DATA (Open-Meteo proxy)
  // ═══════════════════════════════════════════════════════════════
  /**
   * fetchWeather(lat, lon)
   * ----------------------
   * Retrieve weather data for a given coordinate.
   * The backend proxies to Open-Meteo Historical API.
   *
   * @param {number} lat
   * @param {number} lon
   *
   * @returns {Promise<{temperature_c, precipitation_mm, subbase_flag, forecast, ...}>}
   *
   * ─── BACKEND DEV: Replace mock below with: ───────────────────────
   *
   * PYTHON ENDPOINT (FastAPI example):
   *   GET http://localhost:8000/api/weather?lat={lat}&lon={lon}
   *   Backend calls: https://archive-api.open-meteo.com/v1/archive?...
   *   Returns processed JSON with subbase_flag computed server-side.
   *
   * REPLACEMENT CODE:
   *   return this._fetch(`/weather?lat=${lat}&lon=${lon}`, 'GET');
   *
   * DIRECT OPEN-METEO CALL (if you skip the proxy):
   *   const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}`
   *             + `&start_date=2024-08-11&end_date=2024-08-12&hourly=precipitation`;
   *   return fetch(url).then(r => r.json());
   * ─────────────────────────────────────────────────────────────────
   */
  async fetchWeather(lat = 3.1012, lon = 101.6530) {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve(_mockWeather(lat, lon)), 900);
    });
    // ── REAL ──
    // return this._fetch(`/weather?lat=${lat}&lon=${lon}`, 'GET');
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 6 — FETCH ALL REPORTS (for table/map views)
  // ═══════════════════════════════════════════════════════════════
  /**
   * fetchReports(filters)
   * ---------------------
   * Retrieve paginated list of all reports for the Reports & Map views.
   *
   * @param {Object} [filters]
   * @param {string} [filters.status]     - 'pending' | 'dispatched' | 'completed'
   * @param {string} [filters.priority]   - 'HIGH' | 'MEDIUM' | 'LOW'
   * @param {string} [filters.authority]  - 'MBPJ' | 'MPSJ' | 'JKR' etc.
   * @param {number} [filters.page]       - Pagination page (default 1)
   * @param {number} [filters.limit]      - Items per page (default 20)
   *
   * @returns {Promise<{reports: Array, total: number, page: number}>}
   *
   * ─── BACKEND DEV: ────────────────────────────────────────────────
   * PYTHON ENDPOINT:
   *   GET http://localhost:8000/api/reports?status=pending&priority=HIGH&page=1
   *   Returns: { reports: [...], total: 47, page: 1 }
   *
   * REPLACEMENT CODE:
   *   const params = new URLSearchParams(filters).toString();
   *   return this._fetch(`/reports?${params}`, 'GET');
   * ─────────────────────────────────────────────────────────────────
   */
  async fetchReports(filters = {}) {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve({ reports: [], total: 47, page: 1 }), 700);
    });
    // ── REAL ──
    // const params = new URLSearchParams(filters).toString();
    // return this._fetch(`/reports?${params}`, 'GET');
  }


  // ═══════════════════════════════════════════════════════════════
  //  DOOR 7 — DASHBOARD METRICS
  // ═══════════════════════════════════════════════════════════════
  /**
   * fetchMetrics()
   * --------------
   * Retrieve headline KPI numbers for the metric strip.
   *
   * @returns {Promise<{active_defects, work_orders, awaiting_dispatch, resolved_30d}>}
   *
   * ─── BACKEND DEV: ────────────────────────────────────────────────
   * PYTHON ENDPOINT:
   *   GET http://localhost:8000/api/metrics
   *   Returns: { active_defects: 47, work_orders: 128, awaiting_dispatch: 34, resolved_30d: 93 }
   *
   * REPLACEMENT CODE:
   *   return this._fetch('/metrics', 'GET');
   * ─────────────────────────────────────────────────────────────────
   */
  async fetchMetrics() {
    // ── MOCK ──
    return new Promise((resolve) => {
      setTimeout(() => resolve({
        active_defects:    47,
        work_orders:       128,
        awaiting_dispatch: 34,
        resolved_30d:      93,
      }), 500);
    });
    // ── REAL ──
    // return this._fetch('/metrics', 'GET');
  }
}