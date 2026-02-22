import os
import json
from datetime import datetime
from flask import Flask, render_template_string
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

connected_clients = set()

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
  <p class="subtitle">Real-time messaging with Flask-Sock</p>
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
      <p>This app uses <code>flask-sock</code> for WebSocket connections. Messages are broadcast to all connected clients in real time. The server tracks active connections and relays every message as JSON. Open multiple tabs to test it out!</p>
    </div>
  </div>
<script>
  const chat = document.getElementById('chat');
  const msgInput = document.getElementById('msg');
  const sendBtn = document.getElementById('send');
  const dot = document.getElementById('dot');
  const statusText = document.getElementById('statusText');
  const clientsSpan = document.getElementById('clients');
  let ws, username = 'User_' + Math.random().toString(36).slice(2, 6);

  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => {
      dot.className = 'dot on'; statusText.textContent = 'Connected as ' + username;
      msgInput.disabled = false; sendBtn.disabled = false; msgInput.focus();
      ws.send(JSON.stringify({ type: 'join', user: username }));
    };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'clients') { clientsSpan.textContent = data.count + ' online'; return; }
      const div = document.createElement('div');
      div.className = 'msg ' + (data.type === 'system' ? 'system' : data.user === username ? 'sent' : 'received');
      if (data.type === 'system') { div.textContent = data.text; }
      else { div.innerHTML = `<strong>${data.user}</strong> ${data.text}<div class="time">${data.time}</div>`; }
      chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
    };
    ws.onclose = () => {
      dot.className = 'dot off'; statusText.textContent = 'Disconnected — reconnecting...';
      msgInput.disabled = true; sendBtn.disabled = true;
      setTimeout(connect, 2000);
    };
  }

  function sendMsg() {
    const text = msgInput.value.trim();
    if (!text || !ws || ws.readyState !== 1) return;
    ws.send(JSON.stringify({ type: 'message', user: username, text }));
    msgInput.value = ''; msgInput.focus();
  }

  msgInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMsg(); });
  connect();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


def broadcast(message):
    dead = set()
    data = json.dumps(message)
    for client in connected_clients:
        try:
            client.send(data)
        except Exception:
            dead.add(client)
    connected_clients -= dead


def send_client_count():
    broadcast({"type": "clients", "count": len(connected_clients)})


@sock.route("/ws")
def websocket(ws):
    connected_clients.add(ws)
    send_client_count()
    try:
        while True:
            raw = ws.receive()
            if raw is None:
                break
            data = json.loads(raw)
            now = datetime.now().strftime("%H:%M")

            if data.get("type") == "join":
                broadcast({"type": "system", "text": f"{data['user']} joined the chat"})
                send_client_count()

            elif data.get("type") == "message":
                broadcast({
                    "type": "message",
                    "user": data["user"],
                    "text": data["text"],
                    "time": now,
                })
    except Exception:
        pass
    finally:
        connected_clients.discard(ws)
        send_client_count()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
