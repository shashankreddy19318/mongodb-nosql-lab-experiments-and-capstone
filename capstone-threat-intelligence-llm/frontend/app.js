// frontend/app.js - Threat Intelligence & SecOps Bot Controller

let selectedPlatform = "All";
let selectedStatus = "All";
let sessionId = "session-" + Math.random().toString(36).substring(2, 10);
let pendingVulnId = null;

document.addEventListener("DOMContentLoaded", () => {
  initMetrics();
  setupFilters();
  setupChat();
  setupBot();
  setupExercises();
});

// 1. Initial Metrics & Health Fetch
async function initMetrics() {
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();
    document.getElementById("status-db").textContent = data.db_mode.includes("live") ? "Live MongoDB rs0" : "MongoDB Engine";
    document.getElementById("metric-threats").textContent = data.total_threats;
    document.getElementById("metric-chunks").textContent = data.vector_chunks;
    document.getElementById("metric-llm").textContent = data.llm_backend.toUpperCase();
  } catch (e) {
    document.getElementById("status-db").textContent = "Local Active";
  }

  // Check bot status for pending mitigations
  try {
    const bRes = await fetch("/bot/status");
    const bData = await bRes.json();
    if (bData.pending_count > 0) {
      showBotAlert(bData.pending_mitigations[0]);
    }
  } catch (e) {
    console.warn("Bot status check failed:", e);
  }
}

// 2. Setup Platform and Status Filters
function setupFilters() {
  const platButtons = document.querySelectorAll("#platform-filters .pill");
  platButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      platButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedPlatform = btn.getAttribute("data-platform");
      updateSubtitle();
    });
  });

  const statusButtons = document.querySelectorAll("#lifecycle-filters .lifecycle-btn");
  statusButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      statusButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedStatus = btn.getAttribute("data-status");
      updateSubtitle();
    });
  });
}

function updateSubtitle() {
  document.getElementById("chat-subtitle").textContent = `Filtering: ${selectedPlatform} Platform | ${selectedStatus} Lifecycles`;
}

// 3. Conversational RAG Chat
function setupChat() {
  const sendBtn = document.getElementById("btn-send-chat");
  const inputEl = document.getElementById("chat-input");
  const clearBtn = document.getElementById("btn-clear-chat");
  const quickBtns = document.querySelectorAll(".quick-btn");

  sendBtn.addEventListener("click", () => sendMessage());
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  clearBtn.addEventListener("click", () => {
    document.getElementById("chat-messages").innerHTML = `
      <div class="message assistant-msg">
        <div class="msg-avatar">🛡️</div>
        <div class="msg-content">
          <p><strong>Chat session cleared.</strong></p>
          <p>Ready to query platform threats and execute mitigations.</p>
        </div>
      </div>
    `;
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
  });

  quickBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const q = btn.getAttribute("data-query");
      inputEl.value = q;
      sendMessage();
    });
  });
}

async function sendMessage(overrideText = null) {
  const inputEl = document.getElementById("chat-input");
  const msgText = overrideText || inputEl.value.trim();
  if (!msgText) return;

  appendMessage("user", msgText);
  if (!overrideText) inputEl.value = "";

  const chatContainer = document.getElementById("chat-messages");
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message assistant-msg";
  loadingDiv.innerHTML = `
    <div class="msg-avatar">🛡️</div>
    <div class="msg-content"><p><em>Analyzing threat vector & retrieving mitigation playbooks...</em></p></div>
  `;
  chatContainer.appendChild(loadingDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: msgText,
        platform: selectedPlatform,
        top_k: 3
      })
    });
    const data = await res.json();
    loadingDiv.remove();

    appendAssistantResponse(data.response, data.sources, data.latency_ms);

    // If this was a confirmation that resolved a pending vuln, hide the alert box
    if (msgText.toLowerCase().includes("yes") || msgText.toLowerCase().includes("approve") || msgText.toLowerCase().includes("confirm")) {
      document.getElementById("bot-alert-box").classList.add("hidden");
    }
  } catch (err) {
    loadingDiv.remove();
    appendMessage("assistant", `⚠️ Error communicating with Threat Intelligence backend: ${err.message}`);
  }
}

function appendMessage(role, text) {
  const chatContainer = document.getElementById("chat-messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}-msg`;
  const avatar = role === "user" ? "👤" : "🛡️";

  msgDiv.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content">${formatMarkdown(text)}</div>
  `;
  chatContainer.appendChild(msgDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendAssistantResponse(text, sources, latencyMs) {
  const chatContainer = document.getElementById("chat-messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = "message assistant-msg";

  let sourcesHtml = "";
  if (sources && sources.length > 0) {
    sourcesHtml = `
      <details class="sources-box">
        <summary>Retrieved Sources (${sources.length}) • ${latencyMs}ms</summary>
        <ul>
          ${sources.map(s => `<li><strong>[${s.platform}] ${s.title}</strong> (Score: ${s.score})<br><small>${s.text.substring(0, 150)}...</small></li>`).join("")}
        </ul>
      </details>
    `;
  }

  msgDiv.innerHTML = `
    <div class="msg-avatar">🛡️</div>
    <div class="msg-content">
      ${formatMarkdown(text)}
      ${sourcesHtml}
    </div>
  `;
  chatContainer.appendChild(msgDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatMarkdown(text) {
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/```([\s\S]*?)```/gim, '<pre class="code-snippet">$1</pre>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n\n/gim, '<br><br>')
    .replace(/\n/gim, '<br>');
  return html;
}

// 4. Vulnerability Scanner Bot
function setupBot() {
  const scanBtn = document.getElementById("btn-trigger-scan");
  const confirmBtn = document.getElementById("btn-confirm-mitigation");

  scanBtn.addEventListener("click", async () => {
    const platform = document.getElementById("bot-scan-platform").value;
    scanBtn.disabled = true;
    scanBtn.textContent = "Scanning...";

    try {
      const res = await fetch("/bot/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform: platform, scope: "system" })
      });
      const data = await res.json();
      scanBtn.disabled = false;
      scanBtn.textContent = "🔍 Run Vulnerability Scan";

      if (data.detected_count > 0) {
        showBotAlert(data.vulnerabilities[0]);
        // Also post the alert conversationally in the chat!
        appendMessage("assistant", data.conversational_alert);
      } else {
        alert("System audit complete: No new vulnerabilities detected.");
      }
    } catch (e) {
      scanBtn.disabled = false;
      scanBtn.textContent = "🔍 Run Vulnerability Scan";
      alert("Scan failed: " + e.message);
    }
  });

  confirmBtn.addEventListener("click", () => {
    // Trigger conversational approval directly through the chat input
    sendMessage("Yes, approve and execute mitigation for " + (pendingVulnId || "detected vulnerability"));
  });
}

function showBotAlert(vuln) {
  pendingVulnId = vuln.vuln_id;
  document.getElementById("alert-vuln-id").textContent = vuln.vuln_id;
  document.getElementById("alert-vuln-title").textContent = vuln.title;
  document.getElementById("alert-vuln-desc").textContent = vuln.description;
  document.getElementById("alert-vuln-cmd").textContent = vuln.mitigation_command;
  document.getElementById("bot-alert-box").classList.remove("hidden");
}

// 5. Exercises 1 - 18 Demonstration Studio
function setupExercises() {
  const runAllBtn = document.getElementById("btn-run-all-exercises");
  const exButtons = document.querySelectorAll(".ex-btn");
  const outBox = document.getElementById("exercise-output");
  const outTitle = document.getElementById("output-title");
  const outBadge = document.getElementById("output-status");

  runAllBtn.addEventListener("click", async () => {
    outTitle.textContent = "Executing All 18 Exercises...";
    outBadge.textContent = "RUNNING";
    outBadge.className = "badge yellow";
    outBox.textContent = "Starting automated pipeline execution for Exercises 1 to 18...\n";

    try {
      const res = await fetch("/exercises/run-all");
      const data = await res.json();
      outTitle.textContent = "All 18 Exercises Completed";
      outBadge.textContent = `${data.passed}/${data.total_exercises} PASSED`;
      outBadge.className = "badge green";

      outBox.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      outBadge.textContent = "ERROR";
      outBadge.className = "badge red";
      outBox.textContent = "Execution failed: " + e.message;
    }
  });

  exButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const exNum = btn.getAttribute("data-ex");
      outTitle.textContent = `Running Exercise ${exNum}...`;
      outBadge.textContent = "RUNNING";
      outBadge.className = "badge yellow";
      outBox.textContent = `Executing Exercise ${exNum} over Threat Intelligence MongoDB collection...\n`;

      try {
        const res = await fetch(`/exercises/run/${exNum}`, { method: "POST" });
        const data = await res.json();
        outTitle.textContent = data.exercise || `Exercise ${exNum} Output`;
        outBadge.textContent = data.status || "PASS";
        outBadge.className = data.status === "PASS" ? "badge green" : "badge red";
        outBox.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        outBadge.textContent = "ERROR";
        outBadge.className = "badge red";
        outBox.textContent = `Error: ${e.message}`;
      }
    });
  });
}
