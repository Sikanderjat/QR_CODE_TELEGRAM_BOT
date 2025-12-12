# receiver_links.py
from flask import Flask, request, jsonify
import json, os, datetime

app = Flask(__name__)
LAST_FILE = "last_receiver_link.json"
SECRET = os.environ.get("OTHER_BOT_SECRET", "changeme")  # set secure value in env

@app.route("/receive_link", methods=["POST"])
def receive_link():
    # simple secret header check
    header = request.headers.get("X-Webhook-Secret", "")
    if not SECRET or header != SECRET:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}
    # Save for inspection and further processing
    payload = {
        "received_at": datetime.datetime.utcnow().isoformat(),
        "payload": data
    }
    with open(LAST_FILE, "a", encoding="utf8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    # Example processing: print & optionally forward as message (if you want)
    print("Received link payload:", data)

    # If you also want the receiver bot to post into a chat, implement Telegram API send here.
    # (Keep that separate — this endpoint just receives links.)

    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
