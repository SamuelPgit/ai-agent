/* ═══════════════════════════════════════════════════════════
   AI AGENT — LÓGICA FRONTEND
   Chat simple + Agente autónomo con streaming SSE
═══════════════════════════════════════════════════════════ */

const API = "http://localhost:5000";

// ─── DOM ─────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const btnModeChat   = $("btnModeChat");
const btnModeAgent  = $("btnModeAgent");
const panelChat     = $("panelChat");
const panelAgent    = $("panelAgent");

const chatMessages  = $("chatMessages");
const chatInput     = $("chatInput");
const chatSendBtn   = $("chatSendBtn");

const taskInput     = $("taskInput");
const runBtn        = $("runBtn");
const stopBtn       = $("stopBtn");
const maxSteps      = $("maxSteps");
const stepsEmpty    = $("stepsEmpty");
const stepsList     = $("stepsList");
const liveScreen    = $("liveScreen");
const liveScreenImg = $("liveScreenImg");
const closeLiveScr  = $("closeLiveScreen");

const statusDot     = $("statusDot");
const statusText    = $("statusText");
const screenshotBtn = $("screenshotBtn");
const themeBtn      = $("themeBtn");
const clearBtn      = $("clearBtn");
const iconMoon      = $("iconMoon");
const iconSun       = $("iconSun");

const rHead   = $("rHead");
const rMouth  = $("rMouth");
const rBadge  = $("rBadge");
const rCore   = $("rCore");
const rEyeL   = $("rEyeL");
const rEyeR   = $("rEyeR");

const screenshotModal = $("screenshotModal");
const modalImg        = $("modalImg");
const closeModal      = $("closeModal");

const toasts = $("toasts");

// ─── Estado ──────────────────────────────────────────────
let currentMode   = "chat";
let agentRunning  = false;
let currentSSE    = null;
let stepCount     = 0;

// ═══════════════════════════════════════════════════════════
// CAMBIO DE MODO
// ═══════════════════════════════════════════════════════════
btnModeChat.addEventListener("click",  () => switchMode("chat"));
btnModeAgent.addEventListener("click", () => switchMode("agent"));

function switchMode(mode) {
  currentMode = mode;
  btnModeChat.classList.toggle("active",  mode === "chat");
  btnModeAgent.classList.toggle("active", mode === "agent");
  panelChat.classList.toggle("hidden",    mode !== "chat");
  panelAgent.classList.toggle("hidden",   mode !== "agent");
}

// ═══════════════════════════════════════════════════════════
// TEMA
// ═══════════════════════════════════════════════════════════
themeBtn.addEventListener("click", () => {
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  document.documentElement.setAttribute("data-theme", dark ? "light" : "dark");
  iconMoon.style.display = dark ? "none"  : "block";
  iconSun.style.display  = dark ? "block" : "none";
});

// ═══════════════════════════════════════════════════════════
// CHAT SIMPLE
// ═══════════════════════════════════════════════════════════
chatInput.addEventListener("input", autoResize.bind(null, chatInput));
chatInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
});
chatSendBtn.addEventListener("click", sendChat);

async function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = "";
  chatInput.style.height = "auto";
  appendChatMsg(text, "user");

  const typingId = appendTyping();
  chatSendBtn.disabled = true;
  setRobotState("thinking");

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    removeTyping(typingId);

    if (!res.ok) throw new Error("Error del servidor");
    const data = await res.json();

    appendChatMsg(data.message, "ai");
    speak(data.message);

    // Si el agente sugiere iniciar modo agente, cambiar automáticamente
    if (data.action === "start_agent") {
      setTimeout(() => switchMode("agent"), 600);
    }

  } catch (err) {
    removeTyping(typingId);
    appendChatMsg("No pude conectar con el servidor. ¿Está corriendo server.py?", "ai");
    setOffline();
  } finally {
    chatSendBtn.disabled = false;
    setRobotState("idle");
  }
}

function appendChatMsg(text, role) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const isAI = role === "ai";
  div.innerHTML = `
    <div class="msg-avatar ${isAI ? "ai-av" : "user-av"}">
      ${isAI
        ? `<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="10" r="1.5" fill="currentColor"/><circle cx="15" cy="10" r="1.5" fill="currentColor"/><path d="M9 15s1 1.5 3 1.5 3-1.5 3-1.5"/></svg>`
        : `<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
      }
    </div>
    <div class="msg-body">
      <div class="msg-bubble">${escHtml(text)}</div>
      <div class="msg-time">${getTime()}</div>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollBot(chatMessages);
}

function appendTyping() {
  const id = "t" + Date.now();
  const div = document.createElement("div");
  div.className = "msg ai"; div.id = id;
  div.innerHTML = `
    <div class="msg-avatar ai-av">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="10" r="1.5" fill="currentColor"/><circle cx="15" cy="10" r="1.5" fill="currentColor"/><path d="M9 15s1 1.5 3 1.5 3-1.5 3-1.5"/></svg>
    </div>
    <div class="msg-body"><div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div></div>
  `;
  chatMessages.appendChild(div);
  scrollBot(chatMessages);
  return id;
}
function removeTyping(id) { const el = $(id); if (el) el.remove(); }

// ═══════════════════════════════════════════════════════════
// AGENTE AUTÓNOMO — SSE
// ═══════════════════════════════════════════════════════════
runBtn.addEventListener("click", startTask);
stopBtn.addEventListener("click", stopTask);
closeLiveScr.addEventListener("click", () => liveScreen.style.display = "none");

// Ejemplos rápidos
document.querySelectorAll(".ex-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    taskInput.value = btn.dataset.task;
    autoResize(taskInput);
  });
});

taskInput.addEventListener("input", autoResize.bind(null, taskInput));
taskInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); startTask(); }
});

async function startTask() {
  const task = taskInput.value.trim();
  if (!task || agentRunning) return;

  // Limpiar pasos anteriores
  stepsList.innerHTML = "";
  stepsEmpty.style.display = "none";
  stepCount = 0;
  liveScreen.style.display = "none";

  agentRunning = true;
  runBtn.classList.add("hidden");
  stopBtn.classList.remove("hidden");
  runBtn.disabled = true;

  setAgentBusy(task);
  setRobotState("thinking");

  // Abrir SSE
  const body = JSON.stringify({ task, max_steps: parseInt(maxSteps.value) || 25 });

  try {
    const response = await fetch(`${API}/task`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    });

    if (!response.ok) {
      const err = await response.json();
      addStepError(err.error || "Error al iniciar la tarea");
      resetAgentUI();
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // Guardar línea incompleta

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event = JSON.parse(line.slice(6));
            handleStepEvent(event);
          } catch (e) { /* ignorar líneas malformadas */ }
        }
      }
    }

  } catch (err) {
    addStepError("No se pudo conectar con el servidor. ¿Está corriendo server.py?");
    setOffline();
  } finally {
    resetAgentUI();
  }
}

function handleStepEvent(event) {
  const type = event.type;

  if (type === "start") {
    addStepInfo(`Iniciando: "${event.task}"`);
    return;
  }

  if (type === "error") {
    addStepError(event.message);
    return;
  }

  if (type === "stopped") {
    addStepInfo("Tarea detenida por el usuario");
    return;
  }

  // Paso normal
  stepCount++;
  const step = event;
  renderStep(step);

  // Actualizar pantalla en vivo si hay screenshot
  if (step.screenshot) {
    liveScreen.style.display = "block";
    liveScreenImg.src = "data:image/png;base64," + step.screenshot;
  }

  // Estado del robot
  if (step.done) {
    setRobotState("idle");
    speak(step.result || "Tarea completada");
  } else {
    const actionMap = {
      screenshot: "thinking",
      mouse_click: "acting", mouse_move: "acting", mouse_drag: "acting",
      type_text: "acting", key_press: "acting", hotkey: "acting",
      open_app: "acting", open_url: "acting", web_search: "acting",
      chat: "speaking"
    };
    setRobotState(actionMap[step.action] || "thinking");
  }
}

function renderStep(step) {
  const div = document.createElement("div");
  div.className = "step-item";

  const numClass = step.done ? "done" : (step.ok ? "ok" : "err");
  const tag = getActionTag(step.action);
  const screenshotHtml = step.screenshot
    ? `<div class="step-screenshot" onclick="openModal('${step.screenshot}')">
         <img src="data:image/png;base64,${step.screenshot}" alt="Pantalla" loading="lazy"/>
         <div class="step-screenshot-label">Clic para ampliar · Paso ${step.step}</div>
       </div>`
    : "";

  div.innerHTML = `
    <div class="step-num ${numClass}">${step.step === 0 ? "📷" : step.step}</div>
    <div class="step-body">
      <div class="step-header">
        <span class="step-action-tag ${tag.cls}">${tag.label}</span>
        <span class="step-reason">${escHtml(step.reason || "")}</span>
      </div>
      <div class="step-result">${escHtml(step.result || "")}</div>
      ${screenshotHtml}
    </div>
  `;
  stepsList.appendChild(div);
  scrollBot(stepsList.parentElement);
}

function addStepInfo(msg) {
  const div = document.createElement("div");
  div.style.cssText = "font-size:12.5px;color:var(--sub);padding:6px 0;border-bottom:1px solid var(--border);margin-bottom:6px";
  div.textContent = "ℹ️ " + msg;
  stepsList.appendChild(div);
}

function addStepError(msg) {
  const div = document.createElement("div");
  div.style.cssText = "font-size:13px;color:#E74C3C;padding:10px 14px;background:rgba(192,57,43,.1);border:1px solid rgba(192,57,43,.25);border-radius:8px;margin-top:6px";
  div.textContent = "❌ " + msg;
  stepsList.appendChild(div);
  scrollBot(stepsList.parentElement);
}

async function stopTask() {
  try { await fetch(`${API}/task/stop`, { method: "POST" }); } catch {}
  showToast("Deteniendo tarea...", "info");
}

function resetAgentUI() {
  agentRunning = false;
  runBtn.classList.remove("hidden");
  stopBtn.classList.add("hidden");
  runBtn.disabled = false;
  setAgentReady();
  setRobotState("idle");
}

// ═══════════════════════════════════════════════════════════
// SCREENSHOT MANUAL
// ═══════════════════════════════════════════════════════════
screenshotBtn.addEventListener("click", async () => {
  showToast("Tomando captura...", "info");
  try {
    const res = await fetch(`${API}/screenshot`);
    const data = await res.json();
    if (data.screenshot) openModal(data.screenshot);
    else showToast("Error al tomar captura", "error");
  } catch { showToast("Sin conexión", "error"); }
});

// ═══════════════════════════════════════════════════════════
// MODAL SCREENSHOT
// ═══════════════════════════════════════════════════════════
closeModal.addEventListener("click", () => screenshotModal.classList.add("hidden"));
screenshotModal.addEventListener("click", e => {
  if (e.target === screenshotModal) screenshotModal.classList.add("hidden");
});

function openModal(b64) {
  modalImg.src = "data:image/png;base64," + b64;
  screenshotModal.classList.remove("hidden");
}
window.openModal = openModal;

// ═══════════════════════════════════════════════════════════
// LIMPIAR HISTORIAL
// ═══════════════════════════════════════════════════════════
clearBtn.addEventListener("click", async () => {
  if (!confirm("¿Limpiar todo el historial?")) return;
  try {
    await fetch(`${API}/clear`, { method: "POST" });
    chatMessages.innerHTML = "";
    stepsList.innerHTML = "";
    stepsEmpty.style.display = "flex";
    showToast("Historial limpiado", "success");
  } catch { showToast("Error al limpiar", "error"); }
});

// ═══════════════════════════════════════════════════════════
// SÍNTESIS DE VOZ
// ═══════════════════════════════════════════════════════════
function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const clean = text.replace(/[*_`#[\]]/g, "").substring(0, 250);
  const utt = new SpeechSynthesisUtterance(clean);
  utt.lang = "es-ES"; utt.rate = 1.05; utt.pitch = 1.1;
  const voices = window.speechSynthesis.getVoices();
  const esVoice = voices.find(v => v.lang.startsWith("es"));
  if (esVoice) utt.voice = esVoice;
  utt.onstart = () => { rMouth.classList.add("speaking"); rHead.classList.add("talking"); setRobotState("speaking"); };
  utt.onend   = () => { rMouth.classList.remove("speaking"); rHead.classList.remove("talking"); setRobotState("idle"); };
  utt.onerror = () => { rMouth.classList.remove("speaking"); rHead.classList.remove("talking"); };
  window.speechSynthesis.speak(utt);
}
if (window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.addEventListener("voiceschanged", () => window.speechSynthesis.getVoices());
}

// ═══════════════════════════════════════════════════════════
// ROBOT — ESTADOS Y ANIMACIONES
// ═══════════════════════════════════════════════════════════
function setRobotState(state) {
  rBadge.className = "r-badge";
  rCore.className  = "r-core";
  switch (state) {
    case "thinking": rBadge.classList.add("thinking"); rBadge.textContent = "Pensando..."; rCore.classList.add("thinking"); break;
    case "acting":   rBadge.classList.add("acting");   rBadge.textContent = "Actuando";    rCore.classList.add("active");   break;
    case "speaking": rBadge.classList.add("speaking"); rBadge.textContent = "Hablando";    break;
    default:         rBadge.textContent = "En espera";
  }
}

// Parpadeo aleatorio
function randomBlink() {
  setTimeout(() => {
    rEyeL.classList.add("blink"); rEyeR.classList.add("blink");
    setTimeout(() => { rEyeL.classList.remove("blink"); rEyeR.classList.remove("blink"); }, 180);
    randomBlink();
  }, 2200 + Math.random() * 4000);
}
randomBlink();

// Ojos siguen el mouse
document.addEventListener("mousemove", e => {
  document.querySelectorAll(".r-pupil").forEach(p => {
    const eye = p.parentElement;
    const r = eye.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const angle = Math.atan2(e.clientY - cy, e.clientX - cx);
    p.style.transform = `translate(${Math.cos(angle)*3}px,${Math.sin(angle)*3}px)`;
  });
});

// ═══════════════════════════════════════════════════════════
// ESTADO DEL SERVIDOR
// ═══════════════════════════════════════════════════════════
function setAgentBusy(task) {
  statusDot.className = "status-dot busy";
  statusText.textContent = "Ejecutando...";
}
function setAgentReady() {
  statusDot.className = "status-dot";
  statusText.textContent = "Listo";
}
function setOffline() {
  statusDot.className = "status-dot offline";
  statusText.textContent = "Sin conexión";
}

async function checkServer() {
  try {
    const res = await fetch(`${API}/status`);
    if (res.ok) {
      const data = await res.json();
      if (data.running) setAgentBusy(data.current_task);
      else setAgentReady();
    } else setOffline();
  } catch { setOffline(); }
}
checkServer();

// ═══════════════════════════════════════════════════════════
// UTILIDADES
// ═══════════════════════════════════════════════════════════
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

function scrollBot(el) {
  setTimeout(() => { if (el) el.scrollTop = el.scrollHeight; }, 60);
}

function getTime() {
  return new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/\n/g,"<br>");
}

function showToast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  toasts.appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .35s"; setTimeout(() => t.remove(), 350); }, 3000);
}

// Etiquetas de acciones
function getActionTag(action) {
  const map = {
    screenshot:    { label: "📷 Screenshot",  cls: "tag-screenshot" },
    mouse_click:   { label: "🖱️ Clic",         cls: "tag-click" },
    mouse_move:    { label: "🖱️ Mover mouse",  cls: "tag-click" },
    mouse_drag:    { label: "🖱️ Arrastrar",    cls: "tag-click" },
    mouse_scroll:  { label: "🖱️ Scroll",       cls: "tag-click" },
    type_text:     { label: "⌨️ Escribir",     cls: "tag-type" },
    key_press:     { label: "⌨️ Tecla",        cls: "tag-key" },
    hotkey:        { label: "⚡ Atajo",         cls: "tag-hotkey" },
    open_app:      { label: "📂 Abrir app",    cls: "tag-open" },
    open_url:      { label: "🌐 Abrir URL",    cls: "tag-open" },
    web_search:    { label: "🔍 Buscar",       cls: "tag-search" },
    run_command:   { label: "💻 Comando",      cls: "tag-open" },
    clipboard_copy:  { label: "📋 Copiar",     cls: "tag-type" },
    clipboard_paste: { label: "📋 Pegar",      cls: "tag-type" },
    wait:          { label: "⏳ Esperar",      cls: "tag-wait" },
    chat:          { label: "💬 Chat",         cls: "tag-chat" },
    task_done:     { label: "✅ Completado",   cls: "tag-done" },
    start:         { label: "🚀 Inicio",       cls: "tag-done" },
    error:         { label: "❌ Error",        cls: "tag-default" },
  };
  return map[action] || { label: action, cls: "tag-default" };
}
