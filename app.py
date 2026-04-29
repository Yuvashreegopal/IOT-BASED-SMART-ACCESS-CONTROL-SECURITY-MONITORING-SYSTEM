from flask import Flask, request, jsonify, render_template, redirect, url_for
import mysql.connector
from datetime import datetime, time
from flask_mail import Mail, Message
from face_auth import recognize_face_from_camera
from time import time as current_time

app = Flask(__name__)

# -------------------------------------------------
# 🛡️ DoS / RATE LIMITING CONFIG
# -------------------------------------------------
request_log = {}
blocked_users = {}

MAX_REQUESTS = 3
TIME_WINDOW = 20
BLOCK_TIME = 10

def is_rate_limited(uid):
    now = current_time()

    if uid in blocked_users:
        if now < blocked_users[uid]:
            print(f"🚫 UID BLOCKED: {uid}")
            return True
        else:
            del blocked_users[uid]

    if uid not in request_log:
        request_log[uid] = []

    request_log[uid] = [t for t in request_log[uid] if now - t < TIME_WINDOW]
    request_log[uid].append(now)

    if len(request_log[uid]) >= MAX_REQUESTS:
        print(f"🚨 DoS Attack Detected for UID: {uid}")

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO alerts (uid, message, alert_time)
                VALUES (%s, %s, NOW())
            """, (uid, "DoS Attack Detected"))

            cursor.close()
            db.close()

            print("🚨 Alert saved to DB")

        except Exception as e:
            print("❌ Alert DB Error:", e)

        blocked_users[uid] = now + BLOCK_TIME
        return True

    return False

# -------------------------------------------------
# 📧 Mail Config
# -------------------------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sachinshobi56@gmail.com'
app.config['MAIL_PASSWORD'] = 'oncdblsjsqhwtptm'
app.config['MAIL_DEFAULT_SENDER'] = 'sachinvenkatesan19@gmail.com'

mail = Mail(app)

# -------------------------------------------------
# ✅ DB CONNECTION (FIXED)
# -------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sa@19102004",
        database="iot_access_control",
        autocommit=True
    )

# -------------------------------------------------
# TIME CHECK
# -------------------------------------------------
def within_allowed_time(role, batch=None):
    now = datetime.now().time()

    # ✅ STUDENT RULES (CUSTOM)
    if role == "student":

        if batch == "morning":
            return time(9, 0) <= now <= time(13, 0)

        elif batch == "evening":
            return time(14, 0) <= now <= time(20, 0)

        else:
            return False

    # ✅ ALWAYS ALLOWED USERS
    elif role in ["lab_technician", "admin"]:
        return True

    # ✅ FACULTY (optional)
    elif role == "faculty":
        return True

    return False

# -------------------------------------------------
# MAIL
# -------------------------------------------------
def send_warning_email(to_email, name, role):
    try:
        msg = Message(
            subject="⚠️ Access Denied Alert",
            recipients=[to_email]
        )

        msg.body = f"""
Hello {name},

Your lab access attempt was DENIED.

Role: {role}
Reason: Outside allowed access time

Regards,
IoT Access Control System
"""
        mail.send(msg)
        print("✅ Warning email sent")

    except Exception as e:
        print("❌ Mail Error:", e)

# -------------------------------------------------
# DOOR STATUS
# -------------------------------------------------
@app.route('/api/door-status')
def door_status():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT uid, access_status, access_time 
            FROM access_logs 
            ORDER BY access_time DESC 
            LIMIT 1
        """)
        log = cursor.fetchone()

        if log:
            uid, status, access_time = log

            cursor.execute("SELECT name, role, batch FROM users WHERE uid=%s", (uid,))
            user = cursor.fetchone()

            name, role, batch = user if user else ("Unknown", "Unknown", None)

            cursor.close()
            db.close()

            return jsonify({
                "status": status,
                "last_uid": uid,
                "user": name,
                "role": role,
                "batch": batch,
                "time": access_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        cursor.close()
        db.close()
        return jsonify({"status": "LOCKED"})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "ERROR"}), 500

# -------------------------------------------------
# MAIN API
# -------------------------------------------------
@app.route('/api/access-request', methods=['POST'])
def access_request():

    try:
        data = request.json
        uid = data.get('uid')

        print("UID Received:", uid)

        # 🛡️ DoS Protection
        if is_rate_limited(uid):
            return jsonify({"access": "denied", "reason": "too_many_requests"}), 429

        # ✅ STEP 1 → FETCH USER
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT name, role, email, batch FROM users WHERE uid=%s",
            (uid,)
        )
        user = cursor.fetchone()

        cursor.close()
        db.close()

        # ❌ INVALID RFID
        if not user:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO access_logs (uid, access_status) VALUES (%s, %s)",
                (uid, "DENIED")
            )

            cursor.close()
            db.close()

            return jsonify({"access": "denied", "reason": "unauthorized_uid"}), 403

        name, role, email, batch = user

        # 👨‍🔧 LAB TECHNICIAN
        if role == "lab_technician":
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO access_logs (uid, access_status) VALUES (%s, %s)",
                (uid, "GRANTED")
            )

            cursor.close()
            db.close()

            return jsonify({
                "access": "granted",
                "user": name,
                "role": role
            }), 200

        # ⏰ TIME CHECK
        if not within_allowed_time(role, batch):
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO access_logs (uid, access_status) VALUES (%s, %s)",
                (uid, "DENIED")
            )

            cursor.close()
            db.close()

            if email:
                send_warning_email(email, name, role)

            return jsonify({
                "access": "denied",
                "reason": "outside_allowed_time"
            }), 403

        # 📸 FACE VERIFICATION
        print("📸 Starting Face Verification...")
        detected_name = recognize_face_from_camera()
        print("Detected Face:", detected_name)

        if not detected_name or detected_name.lower() != name.lower():
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO access_logs (uid, access_status) VALUES (%s, %s)",
                (uid, "DENIED")
            )

            cursor.close()
            db.close()

            return jsonify({
                "access": "denied",
                "reason": "face_not_matched"
            }), 403

        # ✅ FINAL SUCCESS
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO access_logs (uid, access_status) VALUES (%s, %s)",
            (uid, "GRANTED")
        )

        cursor.close()
        db.close()

        return jsonify({
            "access": "granted",
            "user": name,
            "role": role,
            "batch": batch,
            "reason": "rfid+face_verified"
        }), 200

    except Exception as e:
        print("❌ SERVER ERROR:", e)
        return jsonify({
            "access": "denied",
            "reason": "server_error"
        }), 500

# -------------------------------------------------
# UI ROUTES (UNCHANGED)
# -------------------------------------------------
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logs')
def view_logs():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT u.name, l.uid, l.access_status, l.access_time
        FROM access_logs l
        LEFT JOIN users u ON l.uid = u.uid
        ORDER BY l.access_time DESC
    """)
    logs = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('logs.html', logs=logs)

@app.route('/users')
def view_users():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT id, name, uid, role, email, batch FROM users")
    users = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('users.html', users=users)

@app.route('/alerts')
def view_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT uid, message, alert_time
            FROM alerts
            ORDER BY alert_time DESC
        """)

        data = cursor.fetchall()

        alerts_data = []

        for row in data:
            alerts_data.append((
                "Unknown",   # name not in DB
                row[0],      # uid
                row[1],      # message
                row[2]       # time
            ))

        cursor.close()
        conn.close()

        return render_template('alerts.html', alerts=alerts_data)

    except Exception as e:
        print("❌ ALERT FETCH ERROR:", e)
        return "Error loading alerts"

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)