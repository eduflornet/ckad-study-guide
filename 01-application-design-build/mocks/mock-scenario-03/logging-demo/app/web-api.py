#!/usr/bin/env python3
import json
import time
import random
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
logger = logging.getLogger('web-api')

# Configure access log
access_logger = logging.getLogger('access')
access_handler = logging.FileHandler('/logs/access.log')
access_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
access_logger.addHandler(access_handler)
access_logger.setLevel(logging.INFO)

# Configure error log
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler('/logs/error.log')
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

# Configure application log
app_logger = logging.getLogger('application')
app_handler = logging.FileHandler('/logs/application.log')
app_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app_logger.addHandler(app_handler)
app_logger.setLevel(logging.DEBUG)

# Simulate some application state
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]

@app.before_request
def log_request():
    """Log all incoming requests"""
    access_log_entry = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string.decode(),
        "remote_addr": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', ''),
        "content_length": request.content_length or 0
    }
    access_logger.info(json.dumps(access_log_entry))

@app.after_request
def log_response(response):
    """Log response details"""
    response_log_entry = {
        "timestamp": datetime.now().isoformat(),
        "status_code": response.status_code,
        "content_length": response.content_length or 0,
        "processing_time_ms": random.randint(10, 500)  # Simulated processing time
    }
    access_logger.info(json.dumps(response_log_entry))
    return response

@app.route('/health')
def health_check():
    """Health check endpoint"""
    app_logger.info("Health check requested")
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/users')
def get_users():
    """Get all users"""
    app_logger.info(f"Fetching {len(users_db)} users")
    
    # Simulate occasional errors
    if random.random() < 0.1:  # 10% chance of error
        error_msg = "Database connection timeout"
        error_logger.error(f"Failed to fetch users: {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    return jsonify({"users": users_db, "count": len(users_db)})

@app.route('/users/<int:user_id>')
def get_user(user_id):
    """Get specific user"""
    app_logger.info(f"Fetching user with ID: {user_id}")
    
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        app_logger.warning(f"User not found: {user_id}")
        return jsonify({"error": "User not found"}), 404
    
    app_logger.info(f"User found: {user['name']}")
    return jsonify({"user": user})

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    app_logger.info(f"Creating new user: {data}")
    
    # Validate input
    if not data or 'name' not in data or 'email' not in data:
        error_msg = "Missing required fields: name, email"
        error_logger.error(f"User creation failed: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    # Simulate validation errors
    if random.random() < 0.15:  # 15% chance of validation error
        error_msg = "Email already exists"
        error_logger.error(f"User creation failed: {error_msg}")
        return jsonify({"error": error_msg}), 409
    
    new_user = {
        "id": len(users_db) + 1,
        "name": data["name"],
        "email": data["email"]
    }
    users_db.append(new_user)
    
    app_logger.info(f"User created successfully: {new_user}")
    return jsonify({"user": new_user}), 201

@app.route('/simulate-load')
def simulate_load():
    """Simulate application load for testing"""
    app_logger.info("Starting load simulation")
    
    # Generate multiple log entries
    for i in range(random.randint(5, 15)):
        app_logger.info(f"Processing simulated request {i+1}")
        
        # Simulate some errors
        if random.random() < 0.2:
            error_logger.error(f"Simulated error in request {i+1}")
        
        time.sleep(0.1)  # Small delay
    
    app_logger.info("Load simulation completed")
    return jsonify({"message": "Load simulation completed"})

def background_logger():
    """Background thread that generates periodic logs"""
    while True:
        try:
            # Generate background activity logs
            app_logger.debug("Background task: Checking system health")
            
            # Simulate periodic maintenance tasks
            if random.random() < 0.3:
                app_logger.info("Background task: Cache cleanup performed")
            
            if random.random() < 0.1:
                app_logger.warning("Background task: High memory usage detected")
            
            time.sleep(30)  # Run every 30 seconds
            
        except Exception as e:
            error_logger.error(f"Background task error: {str(e)}")
            time.sleep(60)  # Wait longer on error

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    app_logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start background logging thread
    bg_thread = threading.Thread(target=background_logger, daemon=True)
    bg_thread.start()
    
    # Ensure log directory exists
    os.makedirs('/logs', exist_ok=True)
    
    app_logger.info("Web API starting up")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)