/* BazaarBot — chat widget JS */
function initChatWidget(tenantSlug) {
  var messages = document.getElementById('cwMessages');
  var input = document.getElementById('cwInput');
  var sendBtn = document.getElementById('cwSend');
  if (!messages || !input || !sendBtn) return;

  function addMsg(text, role) {
    var div = document.createElement('div');
    div.className = role === 'user' ? 'cw-msg-user' : 'cw-msg-bot';
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function send() {
    var text = input.value.trim();
    if (!text) return;
    addMsg(text, 'user');
    input.value = '';
    sendBtn.disabled = true;
    fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, phone: 'dashboard-user', tenant: tenantSlug})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) { addMsg(d.response || 'Error', 'bot'); })
    .catch(function() { addMsg('Network error. Reload karein.', 'bot'); })
    .finally(function() { sendBtn.disabled = false; input.focus(); });
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', function(e) { if (e.key === 'Enter') send(); });

  // Auto greet
  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'hi', phone: 'dashboard-user', tenant: tenantSlug})
  })
  .then(function(r) { return r.json(); })
  .then(function(d) { addMsg(d.response || '', 'bot'); })
  .catch(function() {});
}
