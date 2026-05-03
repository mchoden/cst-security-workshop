"""
Security Workshop — Vulnerable Target Application
===================================================
INTENTIONALLY VULNERABLE. Do NOT deploy to production.
Labs: CORS (3), CSRF (2), Auth Bypass (5), API Security (3), SSRF (3), Microservices (3)
"""

import os, re, json, hashlib, sqlite3, datetime, secrets
import urllib.request, urllib.error
from functools import wraps
from flask import (Flask, request, jsonify, render_template, redirect,
                   url_for, make_response, session, g)
import jwt

app = Flask(__name__)
app.secret_key = "super-secret-key-do-not-use-in-production"
JWT_SECRET = "workshop-jwt-secret-123"
DATABASE = os.path.join(os.path.dirname(__file__), "workshop.db")
INTERNAL_URL = os.environ.get("INTERNAL_URL", "http://localhost:5002")

# ─── All Flags ───────────────────────────────────────────────────
FLAGS = {
    "cors_1": "FLAG{cors_wildcard_is_not_a_plan}",
    "cors_2": "FLAG{regex_origin_check_fail}",
    "cors_3": "FLAG{reflected_origin_with_creds}",
    "csrf_1": "FLAG{csrf_no_token_no_problem}",
    "csrf_2": "FLAG{csrf_token_check_is_a_joke}",
    "auth_1": "FLAG{default_creds_strike_again}",
    "auth_2": "FLAG{jwt_none_algorithm_lol}",
    "auth_3": "FLAG{idor_your_data_is_my_data}",
    "auth_4": "FLAG{predictable_tokens_are_yikes}",
    "auth_5": "FLAG{role_escalation_to_the_moon}",
    "api_1":  "FLAG{hidden_endpoint_not_so_hidden}",
    "api_2":  "FLAG{verb_tampering_method_to_madness}",
    "api_3":  "FLAG{mass_assignment_role_play}",
    "ssrf_1": "FLAG{ssrf_internal_access_granted}",
    "ssrf_2": "FLAG{port_scan_found_the_secret}",
    "ssrf_3": "FLAG{cloud_metadata_keys_leaked}",
    "micro_1":"FLAG{no_service_auth_free_access}",
    "micro_2":"FLAG{debug_endpoint_in_production}",
    "micro_3":"FLAG{lateral_movement_game_over}",
}

# ─── DB ──────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
            role TEXT DEFAULT 'user', email TEXT, secret_note TEXT, balance INTEGER DEFAULT 1000
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, from_user TEXT, to_user TEXT,
            amount INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    users = [
        (1,"admin","admin","admin","admin@workshop.lab",f"Admin note: {FLAGS['auth_1']}",50000),
        (2,"alice","password123","user","alice@workshop.lab",f"Alice diary: {FLAGS['auth_3']}",1000),
        (3,"bob","bobsecure!","user","bob@workshop.lab","Bob: I like cats.",1000),
        (4,"charlie","charlie456","user","charlie@workshop.lab","Charlie: Nothing here.",1000),
    ]
    for u in users:
        try: db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", u)
        except sqlite3.IntegrityError: pass
    db.commit(); db.close()

# ═══════════════════════════════════════════════════════════════════
# HUB
# ═══════════════════════════════════════════════════════════════════
@app.route("/")
def hub():
    return render_template("hub.html")

# ═══════════════════════════════════════════════════════════════════
# LAB 1: CORS (3 flags) — kept from original
# ═══════════════════════════════════════════════════════════════════
@app.route("/cors")
def cors_hub():
    return render_template("cors_hub.html")

@app.route("/cors/api/public-profile")
def cors_l1():
    resp = jsonify({"username":"admin","email":"admin@workshop.lab","internal_note":FLAGS["cors_1"]})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.route("/cors/api/trusted-profile")
def cors_l2():
    origin = request.headers.get("Origin","")
    if origin.endswith("trusted-app.com"):
        resp = jsonify({"username":"admin","salary":"$420,000","flag":FLAGS["cors_2"]})
        resp.headers["Access-Control-Allow-Origin"] = origin
        return resp
    return jsonify({"error":"Origin not allowed"}), 403

@app.route("/cors/api/secret-profile")
def cors_l3():
    origin = request.headers.get("Origin","")
    if request.cookies.get("session_id") == "valid-session-token":
        data = {"username":"admin","ssn":"123-45-6789","flag":FLAGS["cors_3"]}
    else:
        data = {"message":"Need cookie session_id=valid-session-token on victim domain first"}
    resp = jsonify(data)
    if origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp

@app.route("/cors/api/<path:p>", methods=["OPTIONS"])
def cors_preflight(p):
    origin = request.headers.get("Origin","")
    resp = make_response("", 204)
    resp.headers["Access-Control-Allow-Origin"] = origin or "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp

# ═══════════════════════════════════════════════════════════════════
# LAB 2: CSRF (2 flags)
# ═══════════════════════════════════════════════════════════════════
@app.route("/csrf")
def csrf_hub():
    return render_template("csrf_hub.html")

# Level 1: No CSRF protection at all
@app.route("/csrf/bank", methods=["GET","POST"])
def csrf_bank():
    session["csrf_user"] = "alice"
    if request.method == "POST":
        to_user = request.form.get("to","")
        amount = int(request.form.get("amount", 0))
        referer = request.headers.get("Referer", "")
        if to_user == "attacker" and amount >= 500:
            if "csrf/bank" in referer:
                return render_template("csrf_bank.html", 
                    msg=f"Transferred ${amount} to {to_user} — but that's just normal usage. "
                        f"The flag requires the request to come from OUTSIDE this page. "
                        f"Try: curl -X POST http://localhost:5000/csrf/bank -d \"to=attacker&amount=500\"")
            return render_template("csrf_success.html", flag=FLAGS["csrf_1"], amount=amount)
        return render_template("csrf_bank.html", msg=f"Transferred ${amount} to {to_user}")
    return render_template("csrf_bank.html", msg=None)

# Level 2: CSRF token present but not validated properly
@app.route("/csrf/bank2", methods=["GET","POST"])
def csrf_bank2():
    session["csrf_user"] = "alice"
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)

    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        if not token:
            return render_template("csrf_bank2.html", error="CSRF token missing!", token=session["csrf_token"])
        to_user = request.form.get("to","")
        amount = int(request.form.get("amount", 0))
        referer = request.headers.get("Referer", "")
        if to_user == "attacker" and amount >= 500:
            if "csrf/bank2" in referer:
                return render_template("csrf_bank2.html",
                    msg=f"Transferred ${amount} to {to_user} — but that's normal usage. "
                        f"The flag requires the request from OUTSIDE. "
                        f"Hint: the server checks if csrf_token EXISTS but not if it's CORRECT. "
                        f"Try: curl -X POST http://localhost:5000/csrf/bank2 -d \"csrf_token=fake&to=attacker&amount=500\"",
                    token=session["csrf_token"], error=None)
            return render_template("csrf_success.html", flag=FLAGS["csrf_2"], amount=amount)
        return render_template("csrf_bank2.html", msg=f"Transferred ${amount} to {to_user}", token=session["csrf_token"], error=None)
    return render_template("csrf_bank2.html", msg=None, token=session["csrf_token"], error=None)

# ═══════════════════════════════════════════════════════════════════
# LAB 3: AUTH BYPASS (5 flags) — kept from original
# ═══════════════════════════════════════════════════════════════════
@app.route("/auth")
def auth_hub():
    return render_template("auth_hub.html")

@app.route("/auth/1", methods=["GET","POST"])
def auth_l1():
    error = None
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                          (request.form.get("username",""), request.form.get("password",""))).fetchone()
        if user and user["role"] == "admin":
            return render_template("auth_1_success.html", flag=FLAGS["auth_1"], user=user)
        error = "Invalid credentials or not admin."
    return render_template("auth_1.html", error=error)

@app.route("/auth/2")
def auth_l2():
    return render_template("auth_2.html")

@app.route("/auth/2/login", methods=["POST"])
def auth_2_login():
    data = request.get_json(); db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (data.get("username",""), data.get("password",""))).fetchone()
    if not user: return jsonify({"error":"Invalid"}), 401
    token = jwt.encode({"sub":user["username"],"role":user["role"],
                        "exp":datetime.datetime.utcnow()+datetime.timedelta(hours=1)},
                       JWT_SECRET, algorithm="HS256")
    return jsonify({"token":token})

@app.route("/auth/2/admin")
def auth_2_admin():
    token = request.headers.get("Authorization","").replace("Bearer ","")
    if not token: return jsonify({"error":"No token"}), 401
    try:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256","none"])
        except (jwt.exceptions.DecodeError, jwt.exceptions.InvalidKeyError):
            payload = jwt.decode(token, None, algorithms=["none"], options={"verify_signature":False})
        if payload.get("role") == "admin":
            return jsonify({"message":"Welcome admin!","flag":FLAGS["auth_2"]})
        return jsonify({"error":"Not admin","your_role":payload.get("role")}), 403
    except Exception as e:
        return jsonify({"error":str(e)}), 401

@app.route("/auth/3")
def auth_l3():
    return render_template("auth_3.html")

@app.route("/auth/3/api/users/<int:uid>")
def auth_3_profile(uid):
    db = get_db()
    user = db.execute("SELECT id,username,email,secret_note FROM users WHERE id=?", (uid,)).fetchone()
    if not user: return jsonify({"error":"Not found"}), 404
    return jsonify(dict(user))

@app.route("/auth/4")
def auth_l4():
    return render_template("auth_4.html")

@app.route("/auth/4/login", methods=["POST"])
def auth_4_login():
    data = request.get_json(); db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (data.get("username",""), data.get("password",""))).fetchone()
    if not user: return jsonify({"error":"Invalid"}), 401
    token = hashlib.md5(data["username"].encode()).hexdigest()
    db.execute("INSERT OR REPLACE INTO sessions (token,user_id) VALUES (?,?)", (token,user["id"]))
    db.commit()
    return jsonify({"token":token,"message":f"Welcome {data['username']}!"})

@app.route("/auth/4/dashboard")
def auth_4_dash():
    token = request.headers.get("X-Session-Token","")
    if not token: return jsonify({"error":"No token"}), 401
    db = get_db()
    sess = db.execute("SELECT u.username,u.role,u.secret_note FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?", (token,)).fetchone()
    if not sess: return jsonify({"error":"Invalid session"}), 401
    result = dict(sess)
    if result["role"] == "admin": result["flag"] = FLAGS["auth_4"]
    return jsonify(result)

@app.route("/auth/5")
def auth_l5():
    return render_template("auth_5.html")

@app.route("/auth/5/login", methods=["POST"])
def auth_5_login():
    data = request.get_json(); db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (data.get("username",""), data.get("password",""))).fetchone()
    if not user: return jsonify({"error":"Invalid"}), 401
    token = jwt.encode({"sub":user["username"],"role":user["role"],"uid":user["id"],
                        "exp":datetime.datetime.utcnow()+datetime.timedelta(hours=1)},
                       "secret", algorithm="HS256")
    return jsonify({"token":token})

@app.route("/auth/5/admin-panel")
def auth_5_panel():
    token = request.headers.get("Authorization","").replace("Bearer ","")
    if not token: return jsonify({"error":"No token"}), 401
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        if payload.get("role") == "admin":
            return jsonify({"message":"Full admin access!","flag":FLAGS["auth_5"]})
        return jsonify({"error":"Admin required","your_claims":payload,"hint":"JWT has your role. Can you change it?"}), 403
    except Exception as e:
        return jsonify({"error":str(e)}), 401

# ═══════════════════════════════════════════════════════════════════
# LAB 4: API SECURITY (3 flags)
# ═══════════════════════════════════════════════════════════════════
@app.route("/api-lab")
def api_hub():
    return render_template("api_hub.html")

# Public API docs page — doesn't mention admin endpoints
@app.route("/api-lab/docs")
def api_docs():
    return jsonify({
        "endpoints": [
            {"method":"GET", "path":"/api-lab/api/v1/products", "description":"List products"},
            {"method":"GET", "path":"/api-lab/api/v1/products/<id>", "description":"Get product"},
            {"method":"GET", "path":"/api-lab/api/v1/profile", "description":"Your profile"},
        ],
        "auth": "Bearer token in Authorization header"
    })

@app.route("/api-lab/api/v1/products")
def api_products():
    return jsonify({"products":[
        {"id":1,"name":"Widget","price":9.99},
        {"id":2,"name":"Gadget","price":19.99},
    ]})

# Hidden admin endpoint — not in docs!
@app.route("/api-lab/api/v1/admin/users")
def api_admin_users():
    return jsonify({"users":["admin","alice","bob","charlie"],"flag":FLAGS["api_1"],
                    "message":"You found the hidden admin endpoint!"})

# Level 2: Verb tampering — GET blocked, but PUT isn't
@app.route("/api-lab/api/v1/admin/config", methods=["GET","POST"])
def api_config_blocked():
    return jsonify({"error":"Forbidden — admin access required"}), 403

@app.route("/api-lab/api/v1/admin/config", methods=["PUT","PATCH","DELETE"])
def api_config_open():
    return jsonify({"config":{"debug":True,"db_host":"internal-db.prod"},"flag":FLAGS["api_2"],
                    "message":"Verb tampering worked! GET/POST blocked but PUT/PATCH/DELETE forgotten."})

# Level 3: Mass assignment — profile update accepts role field
@app.route("/api-lab/api/v1/profile", methods=["GET"])
def api_profile_get():
    return jsonify({"username":"bob","email":"bob@workshop.lab","role":"user",
                    "hint":"Try updating your profile with PUT and adding extra fields..."})

@app.route("/api-lab/api/v1/profile", methods=["PUT"])
def api_profile_update():
    data = request.get_json() or {}
    # BUG: blindly accepts ALL fields including role!
    updated = {"username":"bob","email":"bob@workshop.lab","role":"user"}
    updated.update(data)
    if updated.get("role") == "admin":
        updated["flag"] = FLAGS["api_3"]
        updated["message"] = "Mass assignment! You set your own role to admin."
    return jsonify(updated)

# ═══════════════════════════════════════════════════════════════════
# LAB 5: SSRF (3 flags)
# ═══════════════════════════════════════════════════════════════════
@app.route("/ssrf")
def ssrf_hub():
    return render_template("ssrf_hub.html")

@app.route("/ssrf/preview", methods=["GET","POST"])
def ssrf_preview():
    if request.method == "GET":
        return render_template("ssrf_preview.html")
    url = (request.get_json() or {}).get("url") or request.form.get("url","")
    if not url:
        return jsonify({"error":"No URL provided"}), 400
    # BUG: no validation on URL — fetches anything!
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Workshop-Preview/1.0"})
        resp = urllib.request.urlopen(req, timeout=3)
        body = resp.read(4096).decode("utf-8", errors="replace")
        return jsonify({"url":url,"status":resp.status,"body":body})
    except urllib.error.HTTPError as e:
        body = e.read(4096).decode("utf-8", errors="replace")
        return jsonify({"url":url,"status":e.code,"body":body})
    except Exception as e:
        return jsonify({"url":url,"error":str(e)})

# ═══════════════════════════════════════════════════════════════════
# LAB 6: MICROSERVICES (3 flags)
# ═══════════════════════════════════════════════════════════════════
@app.route("/microservices")
def micro_hub():
    return render_template("micro_hub.html")

# Gateway that's supposed to enforce auth — but only checks GET
@app.route("/microservices/api/gateway/<path:p>", methods=["GET"])
def micro_gateway_get(p):
    auth = request.headers.get("Authorization","")
    if auth != "Bearer admin-gateway-token":
        return jsonify({"error":"Unauthorized — need admin gateway token"}), 401
    # proxy to internal
    try:
        resp = urllib.request.urlopen(f"{INTERNAL_URL}/{p}", timeout=3)
        return jsonify(json.loads(resp.read()))
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# BUG: POST/PUT bypass the auth check entirely!
@app.route("/microservices/api/gateway/<path:p>", methods=["POST","PUT","PATCH","DELETE"])
def micro_gateway_noauth(p):
    try:
        data = request.get_data()
        req = urllib.request.Request(f"{INTERNAL_URL}/{p}", data=data, method=request.method,
                                     headers={"Content-Type":"application/json"})
        resp = urllib.request.urlopen(req, timeout=3)
        return jsonify(json.loads(resp.read()))
    except urllib.error.HTTPError as e:
        return jsonify(json.loads(e.read())), e.code
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# ═══════════════════════════════════════════════════════════════════
# FLAG CHECKER
# ═══════════════════════════════════════════════════════════════════
@app.route("/flags")
def flag_checker():
    return render_template("flags.html", total=len(FLAGS))

@app.route("/flags/check", methods=["POST"])
def check_flag():
    submitted = (request.get_json() or {}).get("flag","").strip()
    for lab, flag in FLAGS.items():
        if submitted == flag:
            return jsonify({"correct":True,"challenge":lab,"message":f"Correct! Solved {lab}!"})
    return jsonify({"correct":False,"message":"Incorrect flag. Keep trying!"})

# ═══════════════════════════════════════════════════════════════════
init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
