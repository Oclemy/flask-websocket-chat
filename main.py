import os
from datetime import datetime
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

connected_users = {}

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flask WebSocket Demo</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; }
  h1 { font-size: 1.6rem; margin-bottom: .3rem; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .subtitle { color: #94a3b8; font-size: .85rem; margin-bottom: 1.5rem; }
  .container { width: 100%; max-width: 520px; }
  .status { display: flex; align-items: center; gap: .5rem; font-size: .8rem; margin-bottom: 1rem; padding: .5rem .8rem; border-radius: .5rem; background: #1e293b; }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.on { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
  .dot.off { background: #ef4444; }
  #chat { background: #1e293b; border-radius: .75rem; padding: 1rem; height: 350px; overflow-y: auto; margin-bottom: 1rem; display: flex; flex-direction: column; gap: .4rem; scrollbar-width: thin; scrollbar-color: #334155 transparent; }
  .msg { padding: .45rem .75rem; border-radius: .5rem; font-size: .85rem; max-width: 85%; word-wrap: break-word; animation: fadeIn .2s ease; }
  .msg.sent { background: #3b82f6; align-self: flex-end; color: #fff; }
  .msg.received { background: #334155; align-self: flex-start; }
  .msg.system { background: transparent; align-self: center; color: #64748b; font-size: .75rem; font-style: italic; }
  .msg .time { font-size: .65rem; opacity: .6; margin-top: .15rem; }
  .input-row { display: flex; gap: .5rem; }
  input { flex: 1; padding: .65rem .9rem; border-radius: .5rem; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; font-size: .9rem; outline: none; transition: border-color .2s; }
  input:focus { border-color: #3b82f6; }
  button { padding: .65rem 1.3rem; border-radius: .5rem; border: none; background: #3b82f6; color: #fff; font-size: .9rem; cursor: pointer; transition: background .2s; }
  button:hover { background: #2563eb; }
  button:disabled { opacity: .5; cursor: not-allowed; }
  .info { margin-top: 1.2rem; background: #1e293b; border-radius: .75rem; padding: 1rem; font-size: .78rem; color: #94a3b8; line-height: 1.6; }
  .info h3 { color: #e2e8f0; font-size: .85rem; margin-bottom: .4rem; }
  .info code { background: #334155; padding: .1rem .35rem; border-radius: .25rem; font-size: .75rem; color: #38bdf8; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>
  <h1>WebSocket Chat</h1>
  <p class="subtitle">Real-time messaging with Flask-SocketIO</p>
  <div class="container">
    <div class="status">
      <span class="dot off" id="dot"></span>
      <span id="statusText">Disconnected</span>
      <span style="margin-left:auto; color:#64748b;" id="clients"></span>
    </div>
    <div id="chat"></div>
    <div class="input-row">
      <input id="msg" placeholder="Type a message..." autocomplete="off" disabled />
      <button id="send" onclick="sendMsg()" disabled>Send</button>
    </div>
    <div class="info">
      <h3>How it works</h3>
      <p>This app uses <code>Flask-SocketIO</code> with <code>eventlet</code> for real-time WebSocket connections. Messages are broadcast to all connected clients instantly. Open multiple tabs to test it out!</p>
    </div>
  </div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
<script>
  const chat = document.getElementById('chat');
  const msgInput = document.getElementById('msg');
  const sendBtn = document.getElementById('send');
  const dot = document.getElementById('dot');
  const statusText = document.getElementById('statusText');
  const clientsSpan = document.getElementById('clients');
  const username = 'User_' + Math.random().toString(36).slice(2, 6);

  const socket = io({ transports: ['websocket', 'polling'] });

  socket.on('connect', () => {
    dot.className = 'dot on';
    statusText.textContent = 'Connected as ' + username;
    msgInput.disabled = false; sendBtn.disabled = false; msgInput.focus();
    socket.emit('join', { user: username });
  });

  socket.on('disconnect', () => {
    dot.className = 'dot off';
    statusText.textContent = 'Disconnected — reconnecting...';
    msgInput.disabled = true; sendBtn.disabled = true;
  });

  socket.on('chat_message', (data) => {
    const div = document.createElement('div');
    div.className = 'msg ' + (data.user === username ? 'sent' : 'received');
    div.innerHTML = '<strong>' + data.user + '</strong> ' + data.text + '<div class="time">' + data.time + '</div>';
    chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
  });

  socket.on('system_message', (data) => {
    const div = document.createElement('div');
    div.className = 'msg system';
    div.textContent = data.text;
    chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
  });

  socket.on('client_count', (data) => {
    clientsSpan.textContent = data.count + ' online';
  });

  function sendMsg() {
    const text = msgInput.value.trim();
    if (!text) return;
    socket.emit('chat_message', { user: username, text: text });
    msgInput.value = ''; msgInput.focus();
  }

  msgInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMsg(); });
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@socketio.on("join")
def handle_join(data):
    connected_users[data["user"]] = True
    emit("system_message", {"text": f"{data['user']} joined the chat"}, broadcast=True)
    emit("client_count", {"count": len(connected_users)}, broadcast=True)


@socketio.on("chat_message")
def handle_message(data):
    now = datetime.now().strftime("%H:%M")
    emit("chat_message", {
        "user": data["user"],
        "text": data["text"],
        "time": now,
    }, broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    emit("client_count", {"count": max(0, len(connected_users) - 1)}, broadcast=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port)
