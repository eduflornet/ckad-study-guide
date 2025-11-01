from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h1>Mixed Stack Application</h1>
            <script src="/static/app.js"></script>
        </body>
    </html>
    '''

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('/app/static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
