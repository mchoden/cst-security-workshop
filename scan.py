#!/usr/bin/env python3
"""
🔍 Security Header Scanner
===========================
Scans a website's publicly visible security posture.
Only reads what the server sends to every visitor — no active testing.

Usage:
    python scan.py https://your-college-website.edu
"""

import sys
import json
import urllib.request
import urllib.error
import ssl
import http.cookiejar


# ─── Colors ──────────────────────────────────────────────────────
class C:
    PASS  = "\033[92m✓\033[0m"
    FAIL  = "\033[91m✗\033[0m"
    WARN  = "\033[93m⚠\033[0m"
    INFO  = "\033[94mℹ\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    RST   = "\033[0m"
    RED   = "\033[91m"
    GRN   = "\033[92m"
    YEL   = "\033[93m"
    BLU   = "\033[94m"


def header(text):
    print(f"\n{C.BOLD}{'─'*60}{C.RST}")
    print(f"{C.BOLD}  {text}{C.RST}")
    print(f"{C.BOLD}{'─'*60}{C.RST}")


def grade(score, total):
    pct = (score / total) * 100 if total else 0
    if pct >= 80:
        return f"{C.GRN}A ({pct:.0f}%){C.RST}"
    elif pct >= 60:
        return f"{C.YEL}B ({pct:.0f}%){C.RST}"
    elif pct >= 40:
        return f"{C.YEL}C ({pct:.0f}%){C.RST}"
    elif pct >= 20:
        return f"{C.RED}D ({pct:.0f}%){C.RST}"
    else:
        return f"{C.RED}F ({pct:.0f}%){C.RST}"


def scan(url):
    if not url.startswith("http"):
        url = "https://" + url

    print(f"\n{C.BOLD}🔍 Scanning: {C.BLU}{url}{C.RST}")
    print(f"{C.DIM}   Reading publicly visible headers only — no active testing.{C.RST}")

    score = 0
    total = 0
    findings = []

    # ─── Fetch ───────────────────────────────────────────────
    try:
        ctx = ssl.create_default_context()
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=ctx)
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "SecurityWorkshop-HeaderScanner/1.0"
        })
        resp = opener.open(req, timeout=10)
        headers = {k.lower(): v for k, v in resp.getheaders()}
        status = resp.status
        body_start = resp.read(2048).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        headers = {k.lower(): v for k, v in e.headers.items()}
        status = e.code
        body_start = ""
    except Exception as e:
        print(f"\n{C.FAIL} Could not connect: {e}")
        return

    print(f"{C.DIM}   HTTP {status} — {len(headers)} headers received{C.RST}")

    # ═══════════════════════════════════════════════════════════
    # 1. SECURITY HEADERS
    # ═══════════════════════════════════════════════════════════
    header("1. Security headers")

    sec_headers = {
        "strict-transport-security": {
            "name": "Strict-Transport-Security (HSTS)",
            "good": "Forces HTTPS. Prevents downgrade attacks.",
            "bad":  "Missing — site can be downgraded to HTTP.",
            "weight": 2,
        },
        "content-security-policy": {
            "name": "Content-Security-Policy (CSP)",
            "good": "Restricts which scripts/resources can load. Strong XSS defense.",
            "bad":  "Missing — no restriction on inline scripts or external resources.",
            "weight": 2,
        },
        "x-content-type-options": {
            "name": "X-Content-Type-Options",
            "good": "Prevents MIME-type sniffing.",
            "bad":  "Missing — browser may interpret files as wrong type.",
            "weight": 1,
        },
        "x-frame-options": {
            "name": "X-Frame-Options",
            "good": "Prevents clickjacking (embedding in iframes).",
            "bad":  "Missing — page can be framed by malicious sites.",
            "weight": 1,
        },
        "x-xss-protection": {
            "name": "X-XSS-Protection",
            "good": "Legacy XSS filter enabled.",
            "bad":  "Missing (less important if CSP is present).",
            "weight": 0,  # deprecated
        },
        "referrer-policy": {
            "name": "Referrer-Policy",
            "good": "Controls how much referrer info leaks.",
            "bad":  "Missing — full URL may leak in Referer header.",
            "weight": 1,
        },
        "permissions-policy": {
            "name": "Permissions-Policy",
            "good": "Restricts browser features (camera, mic, geolocation).",
            "bad":  "Missing — all browser features available by default.",
            "weight": 1,
        },
    }

    for key, info in sec_headers.items():
        total += info["weight"]
        val = headers.get(key)
        if val:
            score += info["weight"]
            print(f"  {C.PASS} {C.BOLD}{info['name']}{C.RST}")
            print(f"      {C.DIM}{val[:80]}{C.RST}")
            print(f"      {C.GRN}{info['good']}{C.RST}")
        else:
            icon = C.FAIL if info["weight"] > 0 else C.WARN
            print(f"  {icon} {C.BOLD}{info['name']}{C.RST}")
            print(f"      {C.RED}{info['bad']}{C.RST}")

    # ═══════════════════════════════════════════════════════════
    # 2. CORS POLICY
    # ═══════════════════════════════════════════════════════════
    header("2. CORS policy")
    total += 2

    acao = headers.get("access-control-allow-origin")
    acac = headers.get("access-control-allow-credentials")

    if acao is None:
        score += 2
        print(f"  {C.PASS} No Access-Control-Allow-Origin header")
        print(f"      {C.GRN}Good — default same-origin policy applies.{C.RST}")
    elif acao == "*":
        score += 0
        if acac and "true" in acac.lower():
            print(f"  {C.FAIL} {C.BOLD}Access-Control-Allow-Origin: *{C.RST}")
            print(f"  {C.FAIL} {C.BOLD}Access-Control-Allow-Credentials: true{C.RST}")
            print(f"      {C.RED}CRITICAL — wildcard with credentials! Any site can read authenticated data.{C.RST}")
            findings.append("CRITICAL: CORS wildcard + credentials")
        else:
            print(f"  {C.WARN} {C.BOLD}Access-Control-Allow-Origin: *{C.RST}")
            print(f"      {C.YEL}Wildcard origin — any site can read responses. Check if sensitive data is exposed.{C.RST}")
            score += 1
    else:
        score += 2
        print(f"  {C.PASS} Access-Control-Allow-Origin: {acao}")
        print(f"      {C.GRN}Restricted to specific origin.{C.RST}")

    # Also test with a fake origin
    try:
        req2 = urllib.request.Request(url, headers={
            "User-Agent": "SecurityWorkshop-HeaderScanner/1.0",
            "Origin": "https://evil-attacker-site.com"
        })
        resp2 = opener.open(req2, timeout=10)
        h2 = {k.lower(): v for k, v in resp2.getheaders()}
        reflected = h2.get("access-control-allow-origin", "")
        if "evil-attacker-site.com" in reflected:
            print(f"  {C.FAIL} {C.BOLD}Origin reflection detected!{C.RST}")
            print(f"      Sent Origin: https://evil-attacker-site.com")
            print(f"      Got back: Access-Control-Allow-Origin: {reflected}")
            print(f"      {C.RED}Server reflects any origin — CORS bypass possible.{C.RST}")
            findings.append("CRITICAL: CORS reflects arbitrary origins")
            score -= 2  # penalty
    except Exception:
        pass

    # ═══════════════════════════════════════════════════════════
    # 3. COOKIE SECURITY
    # ═══════════════════════════════════════════════════════════
    header("3. Cookie security")

    if not cj:
        print(f"  {C.INFO} No cookies set on this page.")
    else:
        for cookie in cj:
            total += 3
            cookie_score = 0
            print(f"\n  {C.BOLD}Cookie: {cookie.name}{C.RST}")
            print(f"      {C.DIM}Value: {cookie.value[:30]}{'...' if len(cookie.value)>30 else ''}{C.RST}")

            if cookie.secure:
                cookie_score += 1
                print(f"  {C.PASS} Secure flag — only sent over HTTPS")
            else:
                print(f"  {C.FAIL} No Secure flag — sent over HTTP too")
                findings.append(f"Cookie '{cookie.name}' missing Secure flag")

            # Check HttpOnly from Set-Cookie header
            set_cookie = headers.get("set-cookie", "")
            is_httponly = "httponly" in set_cookie.lower()
            if is_httponly:
                cookie_score += 1
                print(f"  {C.PASS} HttpOnly — not accessible via JavaScript")
            else:
                print(f"  {C.FAIL} No HttpOnly — JavaScript can read this cookie (XSS risk)")
                findings.append(f"Cookie '{cookie.name}' missing HttpOnly flag")

            if "samesite" in set_cookie.lower():
                cookie_score += 1
                if "samesite=strict" in set_cookie.lower():
                    print(f"  {C.PASS} SameSite=Strict — strong CSRF protection")
                elif "samesite=lax" in set_cookie.lower():
                    print(f"  {C.PASS} SameSite=Lax — basic CSRF protection")
                elif "samesite=none" in set_cookie.lower():
                    print(f"  {C.WARN} SameSite=None — cookies sent cross-origin (needed for some features)")
                    cookie_score -= 1
            else:
                print(f"  {C.FAIL} No SameSite attribute — vulnerable to CSRF")
                findings.append(f"Cookie '{cookie.name}' missing SameSite attribute")

            score += cookie_score

    # ═══════════════════════════════════════════════════════════
    # 4. CSRF INDICATORS
    # ═══════════════════════════════════════════════════════════
    header("4. CSRF protection indicators")

    csrf_found = False
    csrf_terms = ["csrf", "_token", "authenticity_token", "__requestverificationtoken", "csrfmiddlewaretoken"]
    for term in csrf_terms:
        if term in body_start.lower():
            csrf_found = True
            print(f"  {C.PASS} Found CSRF-like token in page: '{term}'")
            break

    if not csrf_found:
        print(f"  {C.INFO} No CSRF token found in first 2KB of page body")
        print(f"      {C.DIM}(May use SameSite cookies or header-based CSRF protection instead){C.RST}")

    # ═══════════════════════════════════════════════════════════
    # 5. OTHER OBSERVATIONS
    # ═══════════════════════════════════════════════════════════
    header("5. Other observations")

    server = headers.get("server")
    if server:
        print(f"  {C.WARN} Server header exposed: {C.BOLD}{server}{C.RST}")
        print(f"      {C.DIM}Reveals server software. Helps attackers target known CVEs.{C.RST}")
    else:
        print(f"  {C.PASS} Server header hidden or absent")

    powered = headers.get("x-powered-by")
    if powered:
        print(f"  {C.WARN} X-Powered-By: {C.BOLD}{powered}{C.RST}")
        print(f"      {C.DIM}Reveals framework/language. Free info for attackers.{C.RST}")
    else:
        print(f"  {C.PASS} X-Powered-By hidden or absent")

    # HTTPS check
    if url.startswith("https"):
        print(f"  {C.PASS} Using HTTPS")
    else:
        print(f"  {C.FAIL} Not using HTTPS!")
        findings.append("Site not using HTTPS")

    # ═══════════════════════════════════════════════════════════
    # SCORE
    # ═══════════════════════════════════════════════════════════
    header("REPORT CARD")

    g = grade(score, total)
    print(f"\n  {C.BOLD}Overall grade: {g}{C.RST}")
    print(f"  {C.DIM}Score: {score}/{total} points{C.RST}\n")

    if findings:
        print(f"  {C.BOLD}{C.RED}Key findings:{C.RST}")
        for f in findings:
            print(f"    {C.FAIL} {f}")
        print()

    print(f"  {C.DIM}This scan only reads publicly visible headers.{C.RST}")
    print(f"  {C.DIM}No active testing was performed.{C.RST}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan.py <url>")
        print("Example: python scan.py https://your-college.edu")
        sys.exit(1)
    scan(sys.argv[1])
