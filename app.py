from flask import Flask, request, jsonify
import re, os, psycopg2

app = Flask(__name__)

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS recipients (
            phone TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def clean_phone(raw, country="1"):
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        digits = country + digits
    return "+" + digits

@app.route("/new-member", methods=["POST"])
def new_member():
    data = request.json or {}
    member = data.get("member", {})
    raw_phone = member.get("phone", "")
    if not raw_phone:
        return jsonify({"error": "no phone"}), 400
    offer = data.get("offer", {}).get("title", "")
    allowed_offers = ["Monthly Membership. KBK Dinner Club", "Yearly Membership - KBK Dinner Club"]
    if not any(o in offer for o in allowed_offers):
        return jsonify({"status": "skipped", "reason": "wrong offer"}), 200
    phone = clean_phone(raw_phone)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO recipients (phone) VALUES (%s) ON CONFLICT DO NOTHING", (phone,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "added", "phone": phone}), 200

@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    from_number = request.form.get("From", "")
    if not from_number:
        return "", 200
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipients WHERE phone = %s", (from_number,))
    conn.commit()
    cur.close()
    conn.close()
    return "", 200

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
