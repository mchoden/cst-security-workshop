# 🔧 SETUP GUIDE — Instructor Copy
## GitHub repo setup + student access + testing checklist

---

## STEP 1: Create the GitHub repo (5 min)

### On github.com:
1. Go to **github.com/new**
2. Repository name: `security-workshop` (or whatever you like)
3. Set to **Public** (students need access; Codespaces free tier requires public repos)
4. Do NOT initialize with README (we'll push our own)
5. Click **Create repository**

### On your laptop terminal:
```bash
# Unzip the workshop files
unzip security-workshop.zip
cd security-workshop

# Initialize git
git init
git add .
git commit -m "Initial workshop setup"

# Push to GitHub (replace YOUR-USERNAME)
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/security-workshop.git
git push -u origin main
```

### Add instructor-only files separately (DON'T push these):
The `.gitignore` already excludes these, but double-check:
- `INSTRUCTOR_ANSWERS.md` — all 19 flag solutions
- `PRESENTER_SCRIPT.docx` — your talking points
- `DEMO_SCRIPT.md` — college website demo script

Keep these on your laptop only. Students will see the repo source code (that's fine — they can read the vulnerable code, which is part of learning), but they shouldn't have the answer key.

---

## STEP 2: Test it yourself as a student would (15 min)

### Option A: Test via Codespaces (recommended — this is what students will use)
1. Go to your repo on GitHub
2. Click green **Code** button → **Codespaces** tab → **Create codespace on main**
3. Wait ~60 seconds for the container to build
4. Check the **Ports** tab at the bottom of VS Code:
   - Port **5000** should appear (Victim App)
   - Port **5001** should appear (Attacker App)
   - Port **5002** should appear (Internal Service)
5. **Right-click each port → Port Visibility → Public** (CRITICAL for CORS labs)
6. Click the 🌐 globe icon next to port 5000 — the workshop hub should load
7. Click through each lab, solve at least 1 flag per section

### If servers don't auto-start:
Open the Codespace terminal and run:
```bash
bash run.sh
```

### Option B: Test locally
```bash
cd security-workshop
pip install flask PyJWT
bash run.sh
# Open http://localhost:5000
```

### Testing checklist — verify at least one flag per lab:
```bash
# CORS Level 1 (should return a FLAG)
curl http://localhost:5000/cors/api/public-profile

# CSRF Level 1 (should return a FLAG in HTML)
curl -X POST http://localhost:5000/csrf/bank -d "to=attacker&amount=500"

# Auth Level 1 (should return a FLAG in HTML)
curl -X POST http://localhost:5000/auth/1 -d "username=admin&password=admin"

# API Level 1 (should return a FLAG)
curl http://localhost:5000/api-lab/api/v1/admin/users

# API Level 2 — verb tampering (should return a FLAG)
curl -X PUT http://localhost:5000/api-lab/api/v1/admin/config

# SSRF Level 1 (should return a FLAG inside the body)
curl -X POST http://localhost:5000/ssrf/preview \
  -H "Content-Type: application/json" \
  -d '{"url":"http://localhost:5002/admin"}'

# Microservices Level 3 — gateway bypass (should return a FLAG)
curl -X POST http://localhost:5000/microservices/api/gateway/payment-service/process \
  -H "Content-Type: application/json" \
  -d '{"amount":100}'

# Flag checker (should return correct:true)
curl -X POST http://localhost:5000/flags/check \
  -H "Content-Type: application/json" \
  -d '{"flag":"FLAG{cors_wildcard_is_not_a_plan}"}'
```

If any test fails, check:
- All 3 servers running? (ports 5000, 5001, 5002)
- `victim/workshop.db` exists? (auto-created on first run)
- Python version 3.8+? Flask and PyJWT installed?

---

## STEP 3: Day-of student instructions

### What to share with students (email/Slack/whiteboard before class):

```
🔓 SECURITY WORKSHOP SETUP

1. Go to: https://github.com/YOUR-USERNAME/security-workshop
2. Click the green "Code" button
3. Click "Create codespace on main"
4. Wait ~60 seconds
5. In the Ports tab (bottom of screen):
   → Right-click port 5000 → Port Visibility → Public
   → Right-click port 5001 → Port Visibility → Public
6. Click the 🌐 globe next to port 5000 to open the Workshop Hub
7. Start hacking!

If servers aren't running, open Terminal and type: bash run.sh

Need a GitHub account? Create one at github.com/signup (free, 2 min)
```

### IMPORTANT: Students do NOT fork the repo.
They create a **Codespace** directly from your repo. This is better than forking because:
- No git knowledge needed
- Isolated environment per student (their XSS/CSRF exploits don't affect others)
- Auto-starts all 3 servers
- No risk of students pushing changes to your repo
- Free tier: 60 core-hours/month per student (plenty for 2 days)

### If a student can't use Codespaces (no GitHub account, corporate restrictions):
```bash
# Clone and run locally
git clone https://github.com/YOUR-USERNAME/security-workshop.git
cd security-workshop
pip install flask PyJWT
bash run.sh      # Mac/Linux
# or: run.bat    # Windows
```

---

## STEP 4: Day-of checklist

### Night before:
- [ ] Push any last-minute fixes to the repo
- [ ] Test Codespace creation one more time (delete old one, create fresh)
- [ ] Verify all 3 servers auto-start
- [ ] Verify ports are forwarding correctly
- [ ] Print `PRESENTER_SCRIPT.docx` or have it open on your laptop
- [ ] Have `INSTRUCTOR_ANSWERS.md` accessible (not on the projector!)
- [ ] Prepare the college website URL for the live demo
- [ ] Charge laptop
- [ ] Have a backup plan if WiFi fails (USB with the zip file)

### Morning of Day 1:
- [ ] Arrive 15 min early
- [ ] Open your own Codespace on the projector — show students the Ports tab
- [ ] Write the repo URL on the whiteboard
- [ ] Have `PRESENTER_SCRIPT.docx` open on your laptop (not projected)
- [ ] Have slides open in presentation mode on projector
- [ ] Optional: play background music while students set up Codespaces

### Between labs:
- [ ] Walk the room during every hack lab
- [ ] Release hints at 15-20 minute intervals
- [ ] Celebrate first solves out loud ("Team 3 just got SSRF Level 1!")
- [ ] Help stuck pairs with nudges, not answers

### End of Day 1:
- [ ] Remind students to stop their Codespace (or it auto-stops in 30 min)
- [ ] Tease Day 2: "Tomorrow you'll chain all these attacks together"

### End of Day 2:
- [ ] Share the repo URL so they can practice at home
- [ ] Remind them about PortSwigger Web Security Academy (free)
- [ ] Collect feedback if the university requires it

---

## TROUBLESHOOTING

### "Codespace won't start"
- Check GitHub status: githubstatus.com
- Fallback: clone locally (see Step 3)

### "Servers not running in Codespace"
- Open Terminal in Codespace → `bash run.sh`
- Check for port conflicts: `lsof -i :5000`

### "CORS lab doesn't work — requests blocked"
- Both ports 5000 AND 5001 must be set to **Public** in the Ports tab
- This is the #1 setup issue. Emphasize it during setup.

### "SSRF lab can't reach internal service"
- Port 5002 must be running: check Terminal output
- The internal service should be **Private** (not Public) — students reach it via SSRF, not directly

### "Student finished all flags in 30 minutes"
- Challenge them to chain exploits: "Use SSRF to read the debug endpoint, get the JWT secret, forge an admin token, then use that token via the API gateway"
- Have them help other students
- Point them to PortSwigger labs for more challenges

### "Database got corrupted"
- Delete it and restart: `rm victim/workshop.db && bash run.sh`

---

## FILE REFERENCE

| File | Purpose | Students see? |
|------|---------|:---:|
| `victim/app.py` | Main vulnerable app (port 5000) | Yes (source is readable) |
| `attacker/app.py` | Evil attacker site (port 5001) | Yes |
| `internal/app.py` | Internal services (port 5002) | Yes (but shouldn't access directly) |
| `victim/templates/*` | All lab HTML pages | Yes |
| `victim/static/style.css` | Dark theme styling | Yes |
| `.devcontainer/` | Codespaces auto-setup | Yes |
| `run.sh` / `run.bat` | Local startup scripts | Yes |
| `scan.py` | College website scanner | Yes |
| `README.md` | Student-facing setup guide | Yes |
| `requirements.txt` | Python dependencies | Yes |
| `.gitignore` | Excludes instructor files | Yes |
| `INSTRUCTOR_ANSWERS.md` | All 19 flag solutions | **NO** (gitignored) |
| `PRESENTER_SCRIPT.docx` | Talking points + Q&A | **NO** (gitignored) |
| `DEMO_SCRIPT.md` | College website demo steps | **NO** (gitignored) |
