# 🔓 Security Workshop — Hack Labs

Welcome to the security workshop! Your mission: find vulnerabilities, exploit them, and capture flags.

**14 flags total** across 3 labs. Can you get them all?

---

## Quick start (pick one)

### ⭐ Option A: GitHub Codespaces (recommended — zero install!)

1. Click the green **"Code"** button on this repo
2. Click **"Create codespace on main"**
3. Wait ~60 seconds for setup
4. Both apps start automatically — check the **Ports** tab at the bottom
5. Click the globe icon 🌐 next to port **5000** to open the Workshop Hub
6. Click the globe icon 🌐 next to port **5001** to open the Attacker Site

That's it. No installs, no Docker, no Python setup.

> **Important:** Make sure both ports show as **Public** in the Ports tab. Right-click a port → Port Visibility → Public. This is needed for CORS labs to work across origins.

### Option B: Docker
```bash
docker-compose up --build
```

### Option C: No Docker
```bash
# Requires Python 3.8+
pip install -r requirements.txt
bash run.sh      # Mac/Linux
run.bat          # Windows
```

### Then open:
| App | URL |
|-----|-----|
| **Workshop Hub** | http://localhost:5000 (or Codespaces port 5000) |
| **Attacker Site** | http://localhost:5001 (or Codespaces port 5001) |
| **Flag Checker** | http://localhost:5000/flags |

---

## The Labs

### 🌐 Lab 1: CORS Misconfigurations (3 flags)
Cross-Origin Resource Sharing controls which websites can read API responses. These APIs have misconfigurations that let unauthorized origins steal data.

**Tools you'll need:** Browser DevTools (Network tab), the attacker site on port 5001, `curl`

### 💉 Lab 2: Cross-Site Scripting — XSS (6 flags)
Inject JavaScript into vulnerable pages. Each level adds more defenses for you to bypass.

**Your goal:** Trigger `alert()` on each page to prove XSS. The flag is revealed when you succeed.

**Tools you'll need:** Browser, creativity

### 🔑 Lab 3: Authentication Bypass (5 flags)
Break authentication systems: default passwords, JWT forgery, IDOR, session hijacking, and privilege escalation.

**Tools you'll need:** Browser DevTools, [jwt.io](https://jwt.io), `curl`, maybe `md5sum`

---

## Rules
1. Only attack `localhost:5000` and `localhost:5001` — nowhere else
2. Flags look like `FLAG{some_text_here}`
3. Submit flags at http://localhost:5000/flags
4. Hints are available on each challenge page (use them!)
5. Work in pairs — discuss strategies, share approaches
6. **Have fun breaking things** 🔥

---

## Useful commands

```bash
# Check CORS headers on a response
curl -v -H "Origin: http://evil.com" http://localhost:5000/cors/api/public-profile

# Compute MD5 hash
echo -n "sometext" | md5sum

# Base64 encode (for JWT manipulation)
echo -n '{"alg":"none","typ":"JWT"}' | base64 | tr -d '=' | tr '+/' '-_'

# Reset the database (if you break something)
rm victim/workshop.db && python -c "from victim.app import init_db; init_db()"
```

---

## Stuck?

Every challenge page has expandable hints. Use them! Security is about persistence, not memorization.

If you're really stuck, ask the instructor — no judgment. The point is learning, not suffering.
