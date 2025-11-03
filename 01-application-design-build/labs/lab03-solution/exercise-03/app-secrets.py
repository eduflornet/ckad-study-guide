from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Read secrets from environment or mounted files
    db_password = os.getenv('DB_PASSWORD', 'not_set')
    api_key_file = '/run/secrets/api_key'
    
    api_key = 'not_set'
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()
    
    return f"""
    <h1>Secrets Demo</h1>
    <p>DB Password: {'***' if db_password != 'not_set' else 'not_set'}</p>
    <p>API Key: {'***' if api_key != 'not_set' else 'not_set'}</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
