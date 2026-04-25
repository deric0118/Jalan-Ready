/**
 * ═══════════════════════════════════════════════════════════════════
 *  AgentTerminal.js  —  Jalan-Ready Agentic Core Log Renderer
 *  Selangor Intelligent RoadCare · Z.AI GLM Reasoning Terminal
 *
 *  This class manages the dark-mode terminal display in Column 2.
 *  It handles:
 *   - Typed-character animation for realistic "AI reasoning" feel
 *   - Colour-coded module tags: [VISION], [GEO], [WEATHER], etc.
 *   - Sequential log queue playback with configurable timing
 *   - External event callbacks (onComplete, onLine)
 *   - Public replay() and clear() APIs
 * ═══════════════════════════════════════════════════════════════════
 */

export class AgentTerminal {
  /**
   * @param {Object} config
   * @param {string}   config.containerId  - ID of the <div> to render into
   * @param {number}  [config.charDelay]   - ms between each character (typing speed)
   * @param {number}  [config.lineDelay]   - ms gap between log lines
   * @param {number}  [config.batchSize]   - chars to print per tick (increase = faster)
   * @param {Function}[config.onComplete]  - callback when all lines finish
   * @param {Function}[config.onLine]      - callback(lineObj) after each line renders
   */
  constructor(config = {}) {
    this.containerId = config.containerId || 'terminal-output';
    this.charDelay   = config.charDelay  ?? 18;
    this.lineDelay   = config.lineDelay  ?? 380;
    this.batchSize   = config.batchSize  ?? 1;
    this.onComplete  = config.onComplete || null;
    this.onLine      = config.onLine     || null;

    this._container  = document.getElementById(this.containerId);
    this._queue      = [];
    this._isRunning  = false;
    this._timers     = [];
    this._lineCount  = 0;

    // Module tag → CSS class mapping
    this._tagClasses = {
      VISION:    't-vision',
      GEO:       't-geo',
      JURISDICTION: 't-juri',
      JURI:      't-juri',
      WEATHER:   't-weather',
      PRIORITY:  't-priority',
      AGENT:     't-agent',
      DISPATCH:  't-dispatch',
      ERROR:     't-error',
      SYSTEM:    't-agent',
    };

    // Line type → text colour class mapping
    this._typeClasses = {
      info:    'info',
      success: 'success',
      warn:    'warn',
      error:   'error',
      dim:     'dim',
      default: '',
    };
  }

  // ─── Public API ────────────────────────────────────────────────

  /**
   * Load a sequence of log objects and begin playback.
   * Each log object: { tag, text, type, delay, instant }
   *
   * @param {Array<Object>} lines
   */
  load(lines) {
    this._queue = [...lines];
    this._isRunning = false;
    this._clearTimers();
  }

  /** Start (or resume) playback of the loaded queue. */
  play() {
    if (this._isRunning || this._queue.length === 0) return;
    this._isRunning = true;
    this._printNext(0);
  }

  /** Load and immediately play a sequence. */
  run(lines) {
    this.load(lines);
    this.play();
  }

  /** Stop playback and clear all pending timers. */
  stop() {
    this._isRunning = false;
    this._clearTimers();
  }

  /** Clear the terminal output (but keep the queue). */
  clear() {
    if (this._container) this._container.innerHTML = '';
    this._lineCount = 0;
  }

  /**
   * Clear and replay from the beginning.
   * @param {Array<Object>} [lines] - optional new sequence; otherwise reuses last loaded queue
   */
  replay(lines) {
    this.stop();
    this.clear();
    if (lines) this._queue = [...lines];
    this._isRunning = true;
    this._printNext(0);
  }

  /**
   * Append a single line instantly (no typing animation).
   * Useful for injecting user commands or system messages on-demand.
   *
   * @param {Object} lineObj
   */
  appendInstant(lineObj) {
    const el = this._buildLineElement(lineObj, lineObj.text || '');
    this._container.appendChild(el);
    this._scrollToBottom();
    this._lineCount++;
  }

  /**
   * Print a separator line.
   */
  appendDivider(char = '─', count = 56) {
    this.appendInstant({ text: char.repeat(count), type: 'dim' });
  }

  // ─── Private: Playback Engine ───────────────────────────────────

  _printNext(index) {
    if (!this._isRunning || index >= this._queue.length) {
      this._isRunning = false;
      if (typeof this.onComplete === 'function') this.onComplete();
      return;
    }

    const lineObj   = this._queue[index];
    const extraDelay = lineObj.delay ?? this.lineDelay;
    const isInstant  = lineObj.instant === true;

    const timer = setTimeout(() => {
      if (!this._isRunning) return;

      if (isInstant) {
        // Print all text at once
        this._printLine(lineObj, lineObj.text || '', () => {
          this._printNext(index + 1);
        });
      } else {
        // Type character by character
        this._typeLine(lineObj, () => {
          if (typeof this.onLine === 'function') this.onLine(lineObj);
          this._printNext(index + 1);
        });
      }
    }, extraDelay);

    this._timers.push(timer);
  }

  /** Type a single line character by character. */
  _typeLine(lineObj, callback) {
    const text      = lineObj.text || '';
    const el        = this._buildLineElement(lineObj, '');
    const cursor    = this._buildCursor();

    el.appendChild(cursor);
    this._container.appendChild(el);
    this._lineCount++;
    this._scrollToBottom();

    let charIndex = 0;

    const tick = () => {
      if (!this._isRunning) return;

      const end = Math.min(charIndex + this.batchSize, text.length);
      const chunk = text.slice(charIndex, end);
      charIndex = end;

      // Insert chunk before cursor
      el.insertBefore(document.createTextNode(chunk), cursor);
      this._scrollToBottom();

      if (charIndex < text.length) {
        const t = setTimeout(tick, this.charDelay);
        this._timers.push(t);
      } else {
        cursor.remove();
        if (typeof callback === 'function') callback();
      }
    };

    const t = setTimeout(tick, this.charDelay);
    this._timers.push(t);
  }

  /** Print a line instantly (no per-char delay). */
  _printLine(lineObj, text, callback) {
    const el = this._buildLineElement(lineObj, text);
    this._container.appendChild(el);
    this._lineCount++;
    this._scrollToBottom();
    if (typeof callback === 'function') callback();
  }

  // ─── Private: DOM Builders ──────────────────────────────────────

  /**
   * Build a <span class="term-line ..."> element.
   * Injects a coloured [TAG] badge at the start if lineObj.tag is set.
   */
  _buildLineElement(lineObj, textContent) {
    const span = document.createElement('span');
    span.classList.add('term-line');

    const typeClass = this._typeClasses[lineObj.type] || this._typeClasses.default;
    if (typeClass) span.classList.add(typeClass);

    // Timestamp prefix
    if (lineObj.timestamp !== false) {
      const ts = document.createElement('span');
      ts.classList.add('timestamp');
      ts.textContent = this._timestamp() + ' ';
      span.appendChild(ts);
    }

    // Prompt character
    if (lineObj.prompt !== false && lineObj.type !== 'dim') {
      const prompt = document.createElement('span');
      prompt.style.color = '#334155';
      prompt.textContent = '> ';
      span.appendChild(prompt);
    }

    // Module tag badge
    if (lineObj.tag) {
      const badge = document.createElement('span');
      badge.classList.add('t-tag', this._tagClasses[lineObj.tag] || 't-agent');
      badge.textContent = lineObj.tag;
      span.appendChild(badge);
      span.appendChild(document.createTextNode(' '));
    }

    // Main text content
    span.appendChild(document.createTextNode(textContent));

    return span;
  }

  _buildCursor() {
    const cursor = document.createElement('span');
    cursor.classList.add('cursor-blink');
    return cursor;
  }

  _timestamp() {
    const now = new Date();
    return `[${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}]`;
  }

  _scrollToBottom() {
    if (this._container) {
      this._container.scrollTop = this._container.scrollHeight;
    }
  }

  _clearTimers() {
    this._timers.forEach(t => clearTimeout(t));
    this._timers = [];
  }


  // ─── Static Factory: Default SIRCa Reasoning Script ────────────

  /**
   * Returns the canonical SIRCa agent reasoning log sequence.
   * This is the "script" for the Z.AI GLM agent's thought process.
   * Backend devs: you can replace these with REAL log lines fetched
   * from the Z.AI agent via api.js → SIRCaAPI.fetchAgentLogs().
   *
   * @returns {Array<Object>}
   */
  static defaultScript() {
    return [
      // ── Bootstrap
      { tag: null,       text: '═'.repeat(54), type: 'dim', instant: true, delay: 0, timestamp: false, prompt: false },
      { tag: 'AGENT',    text: 'SIRCa Autonomous Governance Engine starting...', type: 'info', delay: 100 },
      { tag: 'AGENT',    text: 'Loading Z.AI GLM-4 reasoning model...', type: 'info', delay: 300 },
      { tag: 'AGENT',    text: 'Model loaded. Session ID: 0047. Report ID: RPT-PJ-20240812-004.', type: 'success', delay: 250 },
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 120, timestamp: false, prompt: false },

      // ── Vision Stage
      { tag: 'VISION',   text: 'Receiving image payload... (640×480, JPEG, 78KB)', type: 'info', delay: 400 },
      { tag: 'VISION',   text: 'Running YOLOv8m-seg inference on input frame...', type: 'info', delay: 200 },
      { tag: 'VISION',   text: 'Defects detected: 2 objects above confidence threshold.', type: 'success', delay: 250 },
      { tag: 'VISION',   text: 'Primary: Pothole (Type III) — Conf: 94.2% — BBox: [142,144,302,267]', type: 'success', delay: 180 },
      { tag: 'VISION',   text: 'Secondary: Longitudinal Crack — Conf: 76.1% — BBox: [210,112,390,155]', type: 'warn', delay: 180 },
      { tag: 'VISION',   text: 'Estimated pothole diameter: ~42cm × 38cm. Depth: moderate.', type: 'info', delay: 220 },

      // ── Geo Stage
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 200, timestamp: false, prompt: false },
      { tag: 'GEO',      text: 'Extracting EXIF geotag from image metadata...', type: 'info', delay: 350 },
      { tag: 'GEO',      text: 'Coordinates resolved: 3.1012° N, 101.6530° E', type: 'success', delay: 200 },
      { tag: 'GEO',      text: 'Reverse geocoding via Nominatim... → Jalan SS7/2, Petaling Jaya', type: 'success', delay: 280 },
      { tag: 'GEO',      text: 'District: Petaling Jaya | State: Selangor | Postcode: 47301', type: 'info', delay: 180 },

      // ── Jurisdiction Stage
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 200, timestamp: false, prompt: false },
      { tag: 'JURISDICTION', text: 'Querying Selangor Road Ownership Registry...', type: 'info', delay: 380 },
      { tag: 'JURISDICTION', text: 'Road type: LOCAL (Municipal jurisdiction confirmed).', type: 'success', delay: 220 },
      { tag: 'JURISDICTION', text: 'Matched authority: MBPJ (Majlis Bandaraya Petaling Jaya)', type: 'success', delay: 200 },
      { tag: 'JURISDICTION', text: 'Contact: aduan@mbpj.gov.my | Ref: MBPJ-ENF-2024', type: 'info', delay: 150 },

      // ── Weather Stage
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 200, timestamp: false, prompt: false },
      { tag: 'WEATHER',  text: 'Calling Open-Meteo Historical API... lat=3.1012&lon=101.6530', type: 'info', delay: 420 },
      { tag: 'WEATHER',  text: 'HTTP 200 OK. Parsing precipitation data...', type: 'success', delay: 280 },
      { tag: 'WEATHER',  text: 'Rainfall (past 24h): 18.4mm — classified as HEAVY RAIN.', type: 'warn', delay: 220 },
      { tag: 'WEATHER',  text: '⚠ Sub-base saturation risk detected. Wet sub-base flag: ACTIVE.', type: 'warn', delay: 200 },
      { tag: 'WEATHER',  text: 'Priority score adjustment: +15 points applied.', type: 'warn', delay: 180 },

      // ── Priority Scoring Stage
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 200, timestamp: false, prompt: false },
      { tag: 'PRIORITY', text: 'Computing dynamic priority score...', type: 'info', delay: 380 },
      { tag: 'PRIORITY', text: 'Base score (severity HIGH):        52 pts', type: 'info', delay: 160 },
      { tag: 'PRIORITY', text: 'Proximity modifier (school 80m):   +20 pts', type: 'info', delay: 120 },
      { tag: 'PRIORITY', text: 'Weather modifier (wet sub-base):   +15 pts', type: 'info', delay: 120 },
      { tag: 'PRIORITY', text: 'Traffic volume (arterial road):    +10 pts / 10', type: 'info', delay: 120 },
      { tag: 'PRIORITY', text: 'Days since report:                 +0 pts (new)', type: 'dim',  delay: 100 },
      { tag: 'PRIORITY', text: '──────────────────────────────────', type: 'dim', instant: true, delay: 80, timestamp: false, prompt: false },
      { tag: 'PRIORITY', text: 'TOTAL DYNAMIC SCORE: 87/100 → PRIORITY: HIGH ✓', type: 'success', delay: 250 },

      // ── SLA & Dispatch
      { tag: null,       text: '─'.repeat(54), type: 'dim', instant: true, delay: 200, timestamp: false, prompt: false },
      { tag: 'DISPATCH', text: 'SLA classification: HIGH → repair within 48 hours.', type: 'success', delay: 350 },
      { tag: 'DISPATCH', text: 'Work Order WO-SEL-2024-4821 generated and staged.', type: 'success', delay: 200 },
      { tag: 'DISPATCH', text: 'Awaiting supervisor approval to dispatch...', type: 'warn', delay: 300 },
      { tag: null,       text: '═'.repeat(54), type: 'dim', instant: true, delay: 150, timestamp: false, prompt: false },
      { tag: 'AGENT',    text: 'Reasoning complete. Returning control to dashboard.', type: 'success', delay: 200 },
    ];
  }
}