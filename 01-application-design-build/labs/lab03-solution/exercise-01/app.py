from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return f"Secure App Running! User: {os.getenv('USER', 'unknown')}"

@app.route('/whoami')
def whoami():
    import subprocess
    try:
        result = subprocess.run(['whoami'], capture_output=True, text=True)
        return f"Current user: {result.stdout.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
