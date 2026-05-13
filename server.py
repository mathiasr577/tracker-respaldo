import threading
import os
import time
import datetime
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import config
import tracker
import paper_trader

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app, origins="*", supports_credentials=False)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/trades")
def get_trades():
    return jsonify(tracker.detected_trades)

@app.route("/api/paper")
def get_paper():
    return jsonify(paper_trader.get_summary())

@app.route("/api/portfolio")
def get_portfolio():
    return jsonify(paper_trader.get_portfolio())

@app.route("/api/wallets")
def get_wallets():
    return jsonify([{
        "address": w,
        "short": w[:6] + "..." + w[-4:],
        "status": "active" if w in tracker.last_seen else "initializing"
    } for w in config.WATCHLIST])

@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    return jsonify({"addresses": config.WATCHLIST, "total": len(config.WATCHLIST)})

@app.route("/api/watchlist/add", methods=["POST", "OPTIONS"])
def add_wallet():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "no body"}), 400
    address = data.get("address", "").strip()
    if not address:
        return jsonify({"ok": False, "error": "no address"}), 400
    ok, msg = config.add_to_watchlist(address)
    return jsonify({"ok": ok, "message": msg, "total": len(config.WATCHLIST)})

@app.route("/api/watchlist/remove", methods=["POST", "OPTIONS"])
def remove_wallet():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "no body"}), 400
    address = data.get("address", "").strip()
    ok, msg = config.remove_from_watchlist(address)
    return jsonify({"ok": ok, "message": msg, "total": len(config.WATCHLIST)})

t1 = threading.Thread(target=tracker.run_loop, daemon=True)
t1.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("[server] Tracker Respaldo iniciando...")
    app.run(host="0.0.0.0", port=port, debug=False)
