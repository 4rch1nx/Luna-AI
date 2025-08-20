from flask import Flask, render_template_string
import os

app = Flask(__name__)
LOG_FILE = "web_logs.txt"


@app.route("/")
def show_logs():
    if not os.path.exists(LOG_FILE):
        return "<h3>No logs found yet.</h3>"

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        raw_logs = f.read()

    entries = raw_logs.strip().split("---")

    html = """
    <html>
    <head>
        <title>Luna Web Logs</title>
        <style>
            body { font-family: monospace; background: #1e1e1e; color: #f5f5f5; padding: 20px; }
            h2 { color: #ff6ec7; }
            pre { white-space: pre-wrap; word-wrap: break-word; background: #2d2d2d; padding: 10px; border-radius: 5px; }
            hr { border: 1px solid #444; }
        </style>
    </head>
    <body>
        <h2>Luna Web Logs</h2>
        {% for entry in entries %}
            <pre>{{ entry }}</pre><hr>
        {% endfor %}
    </body>
    </html>
    """

    return render_template_string(html, entries=entries)


if __name__ == "__main__":
    print("Starting Flask server at http://localhost:5000")
    app.run(debug=True)
