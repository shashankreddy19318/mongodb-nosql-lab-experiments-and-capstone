/**
 * Sentinel AI Copilot: Interactive Chatbot Module for CTI Digest Platform
 */

let isChatOpen = false;

function toggleChat() {
  const windowEl = document.getElementById('chat-window');
  const triggerEl = document.getElementById('chat-trigger-btn');
  isChatOpen = !isChatOpen;

  if (isChatOpen) {
    windowEl.classList.add('open');
    triggerEl.classList.add('active');
    document.getElementById('chat-input-field').focus();
    // Clear notification badge
    const badge = document.getElementById('chat-badge');
    if (badge) badge.style.display = 'none';
  } else {
    windowEl.classList.remove('open');
    triggerEl.classList.remove('active');
  }
}

function formatMarkdown(text) {
  if (!text) return '';
  // Basic markdown formatting for chat
  return text
    .replace(/^### (.*$)/gim, '<h5 style="color:var(--primary-cyan); margin:0.3rem 0;">$1</h5>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n/g, '<br>');
}

function appendMessage(sender, text, suggestions = []) {
  const messagesContainer = document.getElementById('chat-messages');

  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-bubble ${sender}`;

  const avatar = sender === 'bot' ? '🤖' : '👤';

  msgDiv.innerHTML = `
    <div class="bubble-avatar">${avatar}</div>
    <div class="bubble-content">
      <div class="bubble-text">${formatMarkdown(text)}</div>
      ${suggestions && suggestions.length > 0 ? `
        <div class="chat-suggestions">
          ${suggestions.map(s => `<button class="suggestion-pill" onclick="sendSuggestion('${s.replace(/'/g, "\\'")}')">${s}</button>`).join('')}
        </div>
      ` : ''}
    </div>
  `;

  messagesContainer.appendChild(msgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
  const messagesContainer = document.getElementById('chat-messages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-bubble bot typing-bubble';
  typingDiv.id = 'typing-indicator';
  typingDiv.innerHTML = `
    <div class="bubble-avatar">🤖</div>
    <div class="bubble-content">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messagesContainer.appendChild(typingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input-field');
  const text = input.value.trim();
  if (!text) return;

  // Append user message
  appendMessage('user', text);
  input.value = '';

  // Show typing
  showTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    removeTypingIndicator();

    if (data.status === 'success') {
      appendMessage('bot', data.reply, data.suggested_actions);
    } else {
      appendMessage('bot', `⚠️ *Error:* ${data.message || 'Unable to process query.'}`);
    }
  } catch (err) {
    removeTypingIndicator();
    appendMessage('bot', `⚠️ *Connection Error:* Could not communicate with backend assistant.`);
  }
}

function sendSuggestion(text) {
  document.getElementById('chat-input-field').value = text;
  sendChatMessage();
}

function clearChat() {
  const messagesContainer = document.getElementById('chat-messages');
  messagesContainer.innerHTML = '';
  appendMessage('bot', "Conversation reset. I am connected to your laptop hardware and database. Ask me anything to get a **YES / NO** verdict!", [
    "Is my laptop charging?",
    "Is my battery low?",
    "Is my RAM full?",
    "Do I have enough disk space?",
    "What is the current cache hit ratio?"
  ]);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input-field');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }

  // Initial welcome message if chat container exists
  setTimeout(() => {
    const container = document.getElementById('chat-messages');
    if (container && container.children.length === 0) {
      appendMessage('bot', "👋 **Welcome to Sentinel Copilot!**\n\nI am **connected directly to your laptop hardware** and can answer queries with a definitive **YES or NO** verdict (battery, charging, RAM, disk space, OS, processes), plus CTI threats and WiredTiger cache metrics!", [
        "Is my laptop charging?",
        "Is my battery low?",
        "Is my RAM full?",
        "Do I have enough disk space?",
        "Is Docker running?"
      ]);
    }
  }, 1000);
});
