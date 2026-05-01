"""
Internal Service — Port 5002
==============================
Simulates internal microservices not exposed to the internet.
SSRF and Microservices labs target this service.
"""
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

FLAGS = {
    "ssrf_1": "FLAG{ssrf_internal_access_granted}",
    "ssrf_2": "FLAG{port_scan_found_the_secret}",
    "ssrf_3": "FLAG{cloud_metadata_keys_leaked}",
    "micro_1":"FLAG{no_service_auth_free_access}",
    "micro_2":"FLAG{debug_endpoint_in_production}",
    "micro_3":"FLAG{lateral_movement_game_over}",
}

# ─── SSRF Level 1: Internal admin panel ──────────────
@app.route("/admin")
def admin():
    return jsonify({
        "service": "Internal Admin Panel",
        "message": "This endpoint should NOT be reachable from outside!",
        "flag": FLAGS["ssrf_1"],
        "users": ["admin","alice","bob","charlie"],
    })

# ─── SSRF Level 2: Secret service on unusual path ────
@app.route("/secret-service-7890")
def secret_svc():
    return jsonify({
        "service": "Secret Analytics Service",
        "message": "You found me by port/path scanning!",
        "flag": FLAGS["ssrf_2"],
    })

# ─── SSRF Level 3: Fake cloud metadata endpoint ──────
@app.route("/latest/meta-data/")
def metadata_root():
    return "ami-id\nhostname\niam/", 200, {"Content-Type":"text/plain"}

@app.route("/latest/meta-data/iam/")
def metadata_iam():
    return "security-credentials/", 200, {"Content-Type":"text/plain"}

@app.route("/latest/meta-data/iam/security-credentials/")
def metadata_creds_list():
    return "workshop-ec2-role", 200, {"Content-Type":"text/plain"}

@app.route("/latest/meta-data/iam/security-credentials/workshop-ec2-role")
def metadata_creds():
    return jsonify({
        "Code": "Success",
        "AccessKeyId": "AKIA" + FLAGS["ssrf_3"],
        "SecretAccessKey": "wJalrXUtnFEMI/FAKE/SECRET+KEY",
        "Token": "FwoGZXIvY...fake-session-token...",
        "Expiration": "2026-12-31T23:59:59Z",
        "message": "You reached the cloud metadata service via SSRF!",
        "flag": FLAGS["ssrf_3"],
    })

# ─── Microservice Level 1: User service (no auth between services) ──
@app.route("/user-service/users")
def user_svc():
    # No service-to-service authentication!
    return jsonify({
        "service": "Internal User Service",
        "warning": "No authentication required — any service (or attacker) can call this!",
        "flag": FLAGS["micro_1"],
        "users": [
            {"id":1,"username":"admin","email":"admin@workshop.lab","role":"admin"},
            {"id":2,"username":"alice","email":"alice@workshop.lab","role":"user"},
        ]
    })

# ─── Microservice Level 2: Debug endpoint left in production ──
@app.route("/debug")
def debug_endpoint():
    return jsonify({
        "service": "Debug Endpoint",
        "warning": "This should have been removed before deployment!",
        "flag": FLAGS["micro_2"],
        "environment": {
            "DB_HOST": "internal-db.prod.cluster",
            "DB_PASSWORD": "super-secret-db-pass-123",
            "JWT_SECRET": "workshop-jwt-secret-123",
            "AWS_ACCESS_KEY": "AKIAIOSFODNN7EXAMPLE",
        }
    })

# ─── Microservice Level 3: Payment service — shared DB creds ──
@app.route("/payment-service/process", methods=["POST","PUT","PATCH"])
def payment_svc():
    data = json.loads(request.get_data() or "{}")
    return jsonify({
        "service": "Payment Service",
        "message": "Payment processed via unauthenticated gateway bypass!",
        "flag": FLAGS["micro_3"],
        "processed": data,
        "warning": "The API gateway only checks auth on GET requests!"
    })

@app.route("/")
def index():
    return jsonify({
        "service": "Internal Service Mesh",
        "message": "You reached an internal service. This should not be accessible from outside.",
        "paths": ["/admin", "/user-service/users", "/debug", "/payment-service/process",
                  "/latest/meta-data/", "/secret-service-7890"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
