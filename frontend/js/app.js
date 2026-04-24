/**
 * ═══════════════════════════════════════════════════════════════════
 *  app.js  —  SIRCa Main Application Controller
 *  Selangor Intelligent RoadCare Command Center
 *
 *  Responsibilities:
 *   - Bootstrap and wire all UI components on DOMContentLoaded
 *   - Run the live clock ticker
 *   - Animate metric counters
 *   - Initialise the AgentTerminal and run the reasoning script
 *   - Handle Citizen Report chat interactions
 *   - Handle Dispatch button flow (loading → success → stepper advance)
 *   - Toast notification system
 *   - Keyboard shortcut for terminal commands
 * ═══════════════════════════════════════════════════════════════════
 */

import { AgentTerminal } from './AgentTerminal.js';
import { SIRCaAPI }      from './api.js';

// ─── Singleton Instances ──────────────────────────────────────────────────────
const api      = new SIRCaAPI();
let   terminal = null;          // AgentTerminal instance
let   currentStep = 2;          // Stepper starts at "Pending Dispatch"

// ─── DOMContentLoaded ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initMetricCounters();
  initTerminal();
  initChatPanel();
  initDispatchButton();
  initNavPills();
  initTerminalControls();
  initKeyboardShortcuts();
  triggerAnalysisMock();
});

// ════════════════════════════════════════════════════════════════════════════
//  CLOCK
// ════════════════════════════════════════════════════════════════════════════

function initClock() {
  const timeEl = document.getElementById('live-time');
  const dateEl = document.getElementById('live-date');
  if (!timeEl || !dateEl) return;

  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const DAYS   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

  function tick() {
    const now = new Date();
    const h   = String(now.getHours()).padStart(2, '0');
    const m   = String(now.getMinutes()).padStart(2, '0');
    const s   = String(now.getSeconds()).padStart(2, '0');
    timeEl.textContent = `${h}:${m}:${s}`;

    const day  = DAYS[now.getDay()];
    const date = now.getDate();
    const mon  = MONTHS[now.getMonth()];
    const yr   = now.getFullYear();
    dateEl.textContent = `${day}, ${date} ${mon} ${yr}`;
  }

  tick();
  setInterval(tick, 1000);
}

// ════════════════════════════════════════════════════════════════════════════
//  ANIMATED METRIC COUNTERS
// ════════════════════════════════════════════════════════════════════════════

function initMetricCounters() {
  const metricEls = document.querySelectorAll('.metric-value[data-count]');

  const animateCount = (el, target, duration = 1200) => {
    const start     = performance.now();
    const startVal  = 0;

    const step = (now) => {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased    = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(startVal + (target - startVal) * eased);
      if (progress < 1) requestAnimationFrame(step);
    };

    requestAnimationFrame(step);
  };

  // Use IntersectionObserver so counters fire when visible
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el     = entry.target;
        const target = parseInt(el.dataset.count, 10);
        animateCount(el, target);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

  metricEls.forEach(el => observer.observe(el));
}

// ════════════════════════════════════════════════════════════════════════════
//  AGENT TERMINAL
// ════════════════════════════════════════════════════════════════════════════

function initTerminal() {
  terminal = new AgentTerminal({
    containerId: 'terminal-output',
    charDelay:   12,       // typing speed (ms per character)
    lineDelay:   320,      // gap between log lines
    batchSize:   2,        // characters per tick (higher = faster)
    onComplete:  () => {
      showToast('info', 'Agent Reasoning Complete', 'Z.AI GLM has finished analysis. Work order ready.', 4000);
    },
    onLine: (lineObj) => {
      // Example: if the DISPATCH line fires, highlight the WO card
      if (lineObj.tag === 'DISPATCH' && lineObj.text.includes('staged')) {
        document.getElementById('card-workorder')?.classList.add('ring-2', 'ring-sirca-teal/40');
      }
    },
  });

  // Start with a small delay so the page animations settle first
  setTimeout(() => {
    terminal.run(AgentTerminal.defaultScript());
  }, 900);
}

// ════════════════════════════════════════════════════════════════════════════
//  TERMINAL CONTROLS (Replay / Clear buttons)
// ════════════════════════════════════════════════════════════════════════════

function initTerminalControls() {
  const replayBtn = document.getElementById('terminal-replay');
  const clearBtn  = document.getElementById('terminal-clear');

  replayBtn?.addEventListener('click', () => {
    terminal?.replay(AgentTerminal.defaultScript());
    showToast('info', 'Terminal Replaying', 'Re-running Z.AI reasoning sequence...', 2500);
  });

  clearBtn?.addEventListener('click', () => {
    terminal?.stop();
    terminal?.clear();
    terminal?.appendInstant({ text: 'Terminal cleared. Type "run" to replay.', type: 'dim', timestamp: false, prompt: true });
  });
}

// ════════════════════════════════════════════════════════════════════════════
//  KEYBOARD SHORTCUTS (Terminal command line)
// ════════════════════════════════════════════════════════════════════════════

function initKeyboardShortcuts() {
  const input = document.getElementById('terminal-cmd');
  if (!input) return;

  input.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const cmd = input.value.trim().toLowerCase();
    input.value = '';

    // Echo the command
    terminal?.appendInstant({
      text: cmd, type: 'dim', tag: null, timestamp: false,
      prompt: false,
    });

    // Handle commands
    switch (cmd) {
      case 'run':
      case 'replay':
        terminal?.replay(AgentTerminal.defaultScript());
        break;
      case 'clear':
        terminal?.clear();
        break;
      case 'help':
        terminal?.appendInstant({ text: 'Commands: run | clear | help | status | dispatch', type: 'info', timestamp: false, prompt: false });
        break;
      case 'status':
        api.checkStatus('WO-SEL-2024-4821').then(data => {
          terminal?.appendInstant({ text: `Status: ${data.status} | Updated: ${new Date(data.updated_at).toLocaleTimeString()}`, type: 'success', tag: 'AGENT' });
        });
        break;
      case 'dispatch':
        triggerDispatch();
        break;
      default:
        terminal?.appendInstant({ text: `Unknown command: "${cmd}". Type "help" for options.`, type: 'error', tag: 'ERROR', timestamp: false, prompt: false });
    }
  });
}

// ════════════════════════════════════════════════════════════════════════════
//  CITIZEN CHAT PANEL
// ════════════════════════════════════════════════════════════════════════════

const BOT_RESPONSES = [
  "Thank you! I've logged your report. The AI is analysing the image now.",
  "Got it. Routing to the correct authority based on your location.",
  "Your report has been submitted. You'll receive an update via SMS.",
  "SIRCa has detected the damage. A work order is being generated.",
];

let botResponseIndex = 0;

function initChatPanel() {
  const sendBtn   = document.getElementById('chat-send');
  const chatInput = document.getElementById('chat-input');
  const fileInput = document.getElementById('file-upload');

  sendBtn?.addEventListener('click', sendChatMessage);
  chatInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChatMessage();
  });

  fileInput?.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    appendChatBubble('user', `📎 ${file.name} uploaded.`);
    setTimeout(() => {
      appendChatBubble('bot', `Image received! Running YOLOv8 analysis on ${file.name}...`);
      showToast('info', 'Image Uploaded', `${file.name} sent for analysis.`, 3000);
    }, 600);
  });
}

function sendChatMessage() {
  const input = document.getElementById('chat-input');
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  appendChatBubble('user', text);
  input.value = '';

  // Typing indicator then bot reply
  setTimeout(() => {
    const reply = BOT_RESPONSES[botResponseIndex % BOT_RESPONSES.length];
    botResponseIndex++;
    appendChatBubble('bot', reply);
  }, 900);
}

/**
 * Append a message bubble to the chat window.
 * @param {'user'|'bot'} sender
 * @param {string} text
 */
function appendChatBubble(sender, text) {
  const chatWindow = document.getElementById('chat-window');
  if (!chatWindow) return;

  const isUser = sender === 'user';

  const wrapper = document.createElement('div');
  wrapper.className = `chat-msg ${sender}`;
  wrapper.style.cssText = 'opacity:0; transform:translateY(8px); transition: opacity 0.3s ease, transform 0.3s ease;';

  const avatar = document.createElement('div');
  avatar.className = `chat-avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`;
  avatar.innerHTML = `<i class="fa-solid fa-${isUser ? 'user' : 'robot'} text-xs"></i>`;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`;
  bubble.textContent = text;

  if (isUser) {
    wrapper.appendChild(bubble);
    wrapper.appendChild(avatar);
  } else {
    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
  }

  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Animate in
  requestAnimationFrame(() => {
    wrapper.style.opacity = '1';
    wrapper.style.transform = 'translateY(0)';
  });
}

// ════════════════════════════════════════════════════════════════════════════
//  VISION ANALYSIS MOCK TRIGGER
// ════════════════════════════════════════════════════════════════════════════

/**
 * Simulates the async pipeline: progress bar fills → "analysis done" label appears.
 */
function triggerAnalysisMock() {
  const doneMsgEl = document.getElementById('analysis-done');
  if (!doneMsgEl) return;

  // The CSS animation runs for 2.5s (analysis-progress class).
  // After it finishes, reveal the "done" message.
  setTimeout(() => {
    doneMsgEl.classList.remove('hidden');
    doneMsgEl.style.cssText = 'opacity:0; transition: opacity 0.5s ease;';
    requestAnimationFrame(() => { doneMsgEl.style.opacity = '1'; });
  }, 3600);  // 0.8s delay + 2.5s animation + buffer
}

// ════════════════════════════════════════════════════════════════════════════
//  STEPPER — advance to next step
// ════════════════════════════════════════════════════════════════════════════

function advanceStepper() {
  const steps = document.querySelectorAll('#status-stepper .step');
  if (!steps.length) return;

  // Move current "active" → "completed"
  const activeStep = document.querySelector('#status-stepper .step.active');
  if (activeStep) {
    activeStep.classList.remove('active');
    activeStep.classList.add('completed');
    const ind = activeStep.querySelector('.step-indicator');
    if (ind) ind.innerHTML = '<i class="fa-solid fa-check text-[10px]"></i>';
  }

  // Make next "pending" → "active"
  currentStep++;
  const nextStep = document.querySelector(`#status-stepper .step[data-step="${currentStep}"]`);
  if (nextStep) {
    nextStep.classList.remove('pending');
    nextStep.classList.add('active');
    const ind = nextStep.querySelector('.step-indicator');
    if (ind) ind.innerHTML = '<span class="step-pulse"></span>';
    const meta = nextStep.querySelector('.step-meta');
    if (meta) meta.innerHTML = 'Scheduled for repair · <span class="text-sirca-accent">Within 48h</span>';
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  DISPATCH BUTTON
// ════════════════════════════════════════════════════════════════════════════

function initDispatchButton() {
  const btn = document.getElementById('dispatch-btn');
  btn?.addEventListener('click', triggerDispatch);
}

async function triggerDispatch() {
  const btn        = document.getElementById('dispatch-btn');
  const content    = document.getElementById('dispatch-btn-content');
  const successEl  = document.getElementById('dispatch-success');
  if (!btn) return;

  // ── Loading State ──
  btn.disabled = true;
  btn.classList.add('loading');
  if (content) content.innerHTML = `
    <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
    </svg>
    <span>Dispatching Work Order...</span>
  `;

  // ── Terminal log ──
  terminal?.appendInstant({ tag: 'DISPATCH', text: 'Supervisor approval received. Initiating email dispatch...', type: 'warn' });

  try {
    const result = await api.dispatchWorkOrder('WO-SEL-2024-4821', 'Approved via dashboard');

    // ── Success State ──
    btn.classList.add('hidden');
    document.getElementById('edit-btn')?.classList.add('hidden');
    document.getElementById('reject-btn')?.classList.add('hidden');

    if (successEl) {
      successEl.classList.remove('hidden');
      successEl.style.cssText = 'opacity:0; transform:scale(0.95); transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);';
      requestAnimationFrame(() => {
        successEl.style.opacity = '1';
        successEl.style.transform = 'scale(1)';
      });
    }

    // ── Advance Stepper ──
    setTimeout(() => advanceStepper(), 400);

    // ── Terminal success log ──
    terminal?.appendInstant({ tag: 'DISPATCH', text: `Email sent to ${result.dispatched_to}. Ref: ${result.email_ref}`, type: 'success' });
    terminal?.appendInstant({ tag: 'DISPATCH', text: 'Work order status updated to: SCHEDULED.', type: 'success' });
    terminal?.appendDivider();

    showToast('success', 'Work Order Dispatched!', `Email sent to aduan@mbpj.gov.my · Ref: ${result.email_ref}`, 6000);

  } catch (err) {
    // ── Error State ──
    btn.disabled = false;
    btn.classList.remove('loading');
    if (content) content.innerHTML = `
      <i class="fa-solid fa-paper-plane"></i>
      <span>Approve &amp; Dispatch Work Order</span>
      <i class="fa-solid fa-arrow-right text-sm opacity-70"></i>
    `;
    terminal?.appendInstant({ tag: 'ERROR', text: `Dispatch failed: ${err.message}`, type: 'error' });
    showToast('error', 'Dispatch Failed', err.message, 5000);
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  EDIT & REJECT BUTTONS
// ════════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('edit-btn')?.addEventListener('click', () => {
    showToast('info', 'Edit Mode', 'Work order editing panel coming soon.', 3000);
    terminal?.appendInstant({ tag: 'AGENT', text: 'Supervisor initiated edit mode on WO-SEL-2024-4821.', type: 'warn' });
  });

  document.getElementById('reject-btn')?.addEventListener('click', () => {
    showToast('warn', 'Work Order Rejected', 'WO-SEL-2024-4821 sent back for review.', 4000);
    terminal?.appendInstant({ tag: 'AGENT', text: 'Work order WO-SEL-2024-4821 rejected by supervisor. Re-queuing.', type: 'error' });
    // Reset stepper to step 1 (submitted)
    currentStep = 1;
    document.querySelectorAll('#status-stepper .step').forEach((step, i) => {
      step.classList.remove('active', 'completed', 'pending');
      const ind = step.querySelector('.step-indicator');
      if (i < 2) {
        step.classList.add('completed');
        if (ind) ind.innerHTML = '<i class="fa-solid fa-check text-[10px]"></i>';
      } else if (i === 2) {
        step.classList.add('active');
        if (ind) ind.innerHTML = '<span class="step-pulse"></span>';
      } else {
        step.classList.add('pending');
        if (ind) ind.innerHTML = `<span class="step-num">${i + 1}</span>`;
      }
    });
  });
});

// ════════════════════════════════════════════════════════════════════════════
//  NAV PILLS
// ════════════════════════════════════════════════════════════════════════════

function initNavPills() {
  const pills = document.querySelectorAll('.nav-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      const view = pill.dataset.view;
      if (view !== 'dashboard') {
        showToast('info', 'Coming Soon', `The "${pill.textContent.trim()}" view is under construction.`, 3000);
      }
    });
  });
}

// ════════════════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATION SYSTEM
// ════════════════════════════════════════════════════════════════════════════

/**
 * Show a toast notification.
 *
 * @param {'success'|'error'|'info'|'warn'} type
 * @param {string} title
 * @param {string} message
 * @param {number} [duration=4000] - auto-dismiss delay in ms
 */
function showToast(type, title, message, duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const ICONS = {
    success: '<i class="fa-solid fa-circle-check text-emerald-500"></i>',
    error:   '<i class="fa-solid fa-circle-xmark text-red-500"></i>',
    info:    '<i class="fa-solid fa-circle-info text-sky-500"></i>',
    warn:    '<i class="fa-solid fa-triangle-exclamation text-amber-500"></i>',
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${ICONS[type] || ICONS.info}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-msg">${message}</div>` : ''}
    </div>
    <button class="ml-2 text-slate-400 hover:text-slate-600 transition-colors text-sm shrink-0 self-start mt-0.5" onclick="this.parentElement.remove()">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  container.appendChild(toast);

  // Auto-dismiss
  const timer = setTimeout(() => {
    toast.classList.add('out');
    setTimeout(() => toast.remove(), 280);
  }, duration);

  // Click to dismiss early
  toast.addEventListener('click', () => {
    clearTimeout(timer);
    toast.classList.add('out');
    setTimeout(() => toast.remove(), 280);
  });
}

// ── Expose showToast globally so inline HTML handlers can call it ──
window.showToast = showToast;