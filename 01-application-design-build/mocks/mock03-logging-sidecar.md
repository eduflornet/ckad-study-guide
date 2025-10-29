# Mock Scenario 3: Implement a Logging Sidecar Pattern

**Objective**: Design and implement a comprehensive logging solution using sidecar containers
**Time**: 45 minutes
**Difficulty**: Advanced

---

## Scenario Overview

You work for a microservices company that needs a centralized logging solution. The current application generates logs in multiple formats and locations, making debugging and monitoring difficult. You need to implement a logging sidecar pattern that:

- Collects logs from multiple sources within a pod
- Processes and formats logs consistently
- Forwards logs to centralized logging systems
- Handles log rotation and storage management
- Provides real-time log streaming capabilities
- Supports different log levels and filtering
- Maintains high availability and performance

## Application Architecture

The logging solution must support:

1. **Main Application**: Web API that generates access logs and error logs
2. **Database Client**: Service that generates query logs and performance metrics
3. **Background Worker**: Task processor that generates job execution logs
4. **Log Collector**: Sidecar that aggregates all logs
5. **Log Processor**: Sidecar that formats and enriches logs
6. **Log Forwarder**: Sidecar that sends logs to external systems

## Implementation Tasks

### Task 1: Create Application Components (15 minutes)

Create the main application that generates various types of logs:

```bash
mkdir /tmp/logging-demo
cd /tmp/logging-demo
mkdir app configs
```

Create `app/web-api.py`:
```python
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
```

Create `app/database-client.py`:
```python
#!/usr/bin/env python3
import json
import time
import random
import logging
import threading
from datetime import datetime
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('database-client')

# Configure database query log
query_logger = logging.getLogger('database.queries')
query_handler = logging.FileHandler('/logs/database-queries.log')
query_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
query_logger.addHandler(query_handler)
query_logger.setLevel(logging.INFO)

# Configure performance log
perf_logger = logging.getLogger('database.performance')
perf_handler = logging.FileHandler('/logs/database-performance.log')
perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
perf_logger.addHandler(perf_handler)
perf_logger.setLevel(logging.INFO)

class DatabaseClient:
    def __init__(self):
        self.connection_pool_size = 10
        self.active_connections = 0
        self.query_count = 0
        self.running = True
    
    def simulate_query(self, query_type, table, conditions=None):
        """Simulate database query execution"""
        start_time = time.time()
        query_id = f"q_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Log query start
        query_log_entry = {
            "query_id": query_id,
            "type": query_type,
            "table": table,
            "conditions": conditions or {},
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        query_logger.info(json.dumps(query_log_entry))
        
        # Simulate query execution time
        execution_time = random.uniform(0.05, 2.0)  # 50ms to 2 seconds
        time.sleep(execution_time)
        
        # Simulate occasional slow queries
        if random.random() < 0.1:  # 10% chance of slow query
            execution_time += random.uniform(2.0, 5.0)
            time.sleep(2.0)
        
        # Simulate query failures
        success = random.random() > 0.05  # 95% success rate
        
        end_time = time.time()
        actual_execution_time = end_time - start_time
        
        # Log query completion
        query_log_entry.update({
            "status": "completed" if success else "failed",
            "execution_time_ms": round(actual_execution_time * 1000, 2),
            "rows_affected": random.randint(0, 1000) if success else 0,
            "error": None if success else "Connection timeout"
        })
        query_logger.info(json.dumps(query_log_entry))
        
        # Log performance metrics
        perf_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "execution_time_ms": round(actual_execution_time * 1000, 2),
            "cpu_usage_percent": random.uniform(10, 80),
            "memory_usage_mb": random.uniform(50, 200),
            "disk_io_kb": random.randint(100, 5000),
            "network_io_kb": random.randint(10, 1000)
        }
        perf_logger.info(json.dumps(perf_log_entry))
        
        self.query_count += 1
        return success
    
    def connection_monitor(self):
        """Monitor database connections"""
        while self.running:
            try:
                # Simulate connection pool monitoring
                self.active_connections = random.randint(0, self.connection_pool_size)
                
                connection_log = {
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": self.active_connections,
                    "pool_size": self.connection_pool_size,
                    "utilization_percent": (self.active_connections / self.connection_pool_size) * 100,
                    "total_queries": self.query_count
                }
                perf_logger.info(json.dumps(connection_log))
                
                # Log warnings for high connection usage
                if self.active_connections > (self.connection_pool_size * 0.8):
                    logger.warning(f"High connection pool usage: {self.active_connections}/{self.connection_pool_size}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Connection monitor error: {str(e)}")
                time.sleep(30)
    
    def query_simulator(self):
        """Simulate various database queries"""
        tables = ['users', 'orders', 'products', 'transactions', 'logs']
        query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        
        while self.running:
            try:
                # Generate random queries
                query_type = random.choice(query_types)
                table = random.choice(tables)
                
                conditions = {}
                if query_type == 'SELECT':
                    conditions = {"limit": random.randint(1, 100)}
                elif query_type == 'UPDATE':
                    conditions = {"where": f"id = {random.randint(1, 1000)}"}
                
                self.simulate_query(query_type, table, conditions)
                
                # Variable delay between queries
                time.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                logger.error(f"Query simulator error: {str(e)}")
                time.sleep(10)
    
    def run(self):
        """Start the database client simulation"""
        logger.info("Database client starting up")
        
        # Start monitoring threads
        connection_thread = threading.Thread(target=self.connection_monitor, daemon=True)
        query_thread = threading.Thread(target=self.query_simulator, daemon=True)
        
        connection_thread.start()
        query_thread.start()
        
        logger.info("Database client simulation started")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Database client shutting down")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure log directory exists
    os.makedirs('/logs', exist_ok=True)
    
    # Start database client
    client = DatabaseClient()
    client.run()
```

Create `app/background-worker.py`:
```python
#!/usr/bin/env python3
import json
import time
import random
import logging
import threading
from datetime import datetime, timedelta
import os
import signal
import sys
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('background-worker')

# Configure job execution log
job_logger = logging.getLogger('jobs.execution')
job_handler = logging.FileHandler('/logs/job-execution.log')
job_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
job_logger.addHandler(job_handler)
job_logger.setLevel(logging.INFO)

# Configure job metrics log
metrics_logger = logging.getLogger('jobs.metrics')
metrics_handler = logging.FileHandler('/logs/job-metrics.log')
metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
metrics_logger.addHandler(metrics_handler)
metrics_logger.setLevel(logging.INFO)

class BackgroundWorker:
    def __init__(self):
        self.job_queue = Queue()
        self.running = True
        self.processed_jobs = 0
        self.failed_jobs = 0
        self.worker_threads = 3
    
    def create_sample_jobs(self):
        """Create sample jobs for processing"""
        job_types = [
            'email_notification',
            'data_backup',
            'report_generation',
            'image_processing',
            'data_sync',
            'cache_cleanup',
            'log_rotation'
        ]
        
        while self.running:
            try:
                # Create random jobs
                for _ in range(random.randint(1, 5)):
                    job = {
                        'id': f"job_{int(time.time())}_{random.randint(1000, 9999)}",
                        'type': random.choice(job_types),
                        'priority': random.choice(['low', 'normal', 'high']),
                        'created_at': datetime.now().isoformat(),
                        'params': {
                            'target': f"target_{random.randint(1, 100)}",
                            'batch_size': random.randint(10, 1000)
                        }
                    }
                    self.job_queue.put(job)
                    
                    job_log_entry = {
                        'job_id': job['id'],
                        'type': job['type'],
                        'priority': job['priority'],
                        'status': 'queued',
                        'timestamp': datetime.now().isoformat()
                    }
                    job_logger.info(json.dumps(job_log_entry))
                
                # Wait before creating more jobs
                time.sleep(random.uniform(5.0, 15.0))
                
            except Exception as e:
                logger.error(f"Job creation error: {str(e)}")
                time.sleep(10)
    
    def process_job(self, job):
        """Process a single job"""
        job_id = job['id']
        job_type = job['type']
        
        start_time = time.time()
        
        # Log job start
        job_log_entry = {
            'job_id': job_id,
            'type': job_type,
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'worker_thread': threading.current_thread().name
        }
        job_logger.info(json.dumps(job_log_entry))
        
        try:
            # Simulate job processing
            processing_time = random.uniform(1.0, 10.0)
            
            # Simulate different job types with different processing characteristics
            if job_type == 'email_notification':
                processing_time = random.uniform(0.5, 2.0)
            elif job_type == 'data_backup':
                processing_time = random.uniform(30.0, 120.0)
            elif job_type == 'report_generation':
                processing_time = random.uniform(10.0, 60.0)
            elif job_type == 'image_processing':
                processing_time = random.uniform(5.0, 30.0)
            
            # Simulate processing steps
            steps = ['initializing', 'processing', 'validating', 'finalizing']
            for i, step in enumerate(steps):
                step_log = {
                    'job_id': job_id,
                    'step': step,
                    'progress_percent': ((i + 1) / len(steps)) * 100,
                    'timestamp': datetime.now().isoformat()
                }
                job_logger.info(json.dumps(step_log))
                
                time.sleep(processing_time / len(steps))
            
            # Simulate job failures
            success = random.random() > 0.1  # 90% success rate
            
            end_time = time.time()
            actual_processing_time = end_time - start_time
            
            # Log job completion
            completion_log = {
                'job_id': job_id,
                'type': job_type,
                'status': 'completed' if success else 'failed',
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': None if success else 'Processing timeout'
            }
            job_logger.info(json.dumps(completion_log))
            
            # Log metrics
            metrics_log = {
                'timestamp': datetime.now().isoformat(),
                'job_id': job_id,
                'job_type': job_type,
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'cpu_usage_percent': random.uniform(20, 90),
                'memory_usage_mb': random.uniform(100, 500),
                'disk_usage_mb': random.uniform(10, 100),
                'success': success
            }
            metrics_logger.info(json.dumps(metrics_log))
            
            if success:
                self.processed_jobs += 1
                logger.info(f"Job {job_id} completed successfully")
            else:
                self.failed_jobs += 1
                logger.error(f"Job {job_id} failed")
            
            return success
            
        except Exception as e:
            end_time = time.time()
            actual_processing_time = end_time - start_time
            
            error_log = {
                'job_id': job_id,
                'type': job_type,
                'status': 'error',
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            job_logger.info(json.dumps(error_log))
            
            self.failed_jobs += 1
            logger.error(f"Job {job_id} error: {str(e)}")
            return False
    
    def worker_thread(self):
        """Worker thread that processes jobs from the queue"""
        thread_name = threading.current_thread().name
        logger.info(f"Worker thread {thread_name} started")
        
        while self.running:
            try:
                # Get job from queue (with timeout)
                job = self.job_queue.get(timeout=5.0)
                self.process_job(job)
                self.job_queue.task_done()
                
            except Exception as e:
                if self.running:  # Only log errors if we're still running
                    logger.error(f"Worker thread {thread_name} error: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker thread {thread_name} stopped")
    
    def metrics_reporter(self):
        """Report worker metrics periodically"""
        while self.running:
            try:
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'queue_size': self.job_queue.qsize(),
                    'processed_jobs': self.processed_jobs,
                    'failed_jobs': self.failed_jobs,
                    'success_rate': (self.processed_jobs / max(1, self.processed_jobs + self.failed_jobs)) * 100,
                    'worker_threads': self.worker_threads
                }
                metrics_logger.info(json.dumps(metrics))
                
                # Log warnings for queue buildup
                if self.job_queue.qsize() > 20:
                    logger.warning(f"Job queue buildup detected: {self.job_queue.qsize()} jobs pending")
                
                time.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics reporter error: {str(e)}")
                time.sleep(60)
    
    def run(self):
        """Start the background worker"""
        logger.info("Background worker starting up")
        
        # Start worker threads
        threads = []
        
        # Job creation thread
        job_creator = threading.Thread(target=self.create_sample_jobs, daemon=True)
        job_creator.start()
        threads.append(job_creator)
        
        # Worker threads
        for i in range(self.worker_threads):
            worker = threading.Thread(target=self.worker_thread, daemon=True, name=f"worker-{i+1}")
            worker.start()
            threads.append(worker)
        
        # Metrics reporter thread
        metrics_thread = threading.Thread(target=self.metrics_reporter, daemon=True)
        metrics_thread.start()
        threads.append(metrics_thread)
        
        logger.info(f"Background worker started with {self.worker_threads} worker threads")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Background worker shutting down")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure log directory exists
    os.makedirs('/logs', exist_ok=True)
    
    # Start background worker
    worker = BackgroundWorker()
    worker.run()
```

### Task 2: Create Logging Sidecar Containers (15 minutes)

Create `app/log-collector.py`:
```python
#!/usr/bin/env python3
import json
import time
import os
import logging
import threading
from datetime import datetime
import glob
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('log-collector')

class LogCollector:
    def __init__(self):
        self.log_directory = '/logs'
        self.output_directory = '/collected-logs'
        self.running = True
        self.file_positions = {}
        self.collected_logs = defaultdict(list)
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
    
    def read_log_file(self, file_path):
        """Read new lines from a log file"""
        try:
            # Get current position for this file
            current_position = self.file_positions.get(file_path, 0)
            
            with open(file_path, 'r') as f:
                f.seek(current_position)
                new_lines = f.readlines()
                self.file_positions[file_path] = f.tell()
            
            return new_lines
            
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {str(e)}")
            return []
    
    def process_log_line(self, line, source_file):
        """Process a single log line and extract metadata"""
        try:
            # Try to parse as JSON first
            if line.strip().startswith('{'):
                log_entry = json.loads(line.strip())
                log_entry['source_file'] = source_file
                log_entry['collected_at'] = datetime.now().isoformat()
                return log_entry
            else:
                # Handle plain text logs
                return {
                    'message': line.strip(),
                    'source_file': source_file,
                    'collected_at': datetime.now().isoformat(),
                    'log_level': 'INFO'  # Default level
                }
                
        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            return {
                'message': line.strip(),
                'source_file': source_file,
                'collected_at': datetime.now().isoformat(),
                'log_level': 'INFO'
            }
        except Exception as e:
            logger.error(f"Error processing log line: {str(e)}")
            return None
    
    def collect_logs(self):
        """Collect logs from all log files"""
        while self.running:
            try:
                # Find all log files
                log_files = glob.glob(os.path.join(self.log_directory, '*.log'))
                
                for log_file in log_files:
                    if not os.path.exists(log_file):
                        continue
                    
                    # Read new lines from the file
                    new_lines = self.read_log_file(log_file)
                    
                    for line in new_lines:
                        if line.strip():  # Skip empty lines
                            processed_log = self.process_log_line(line, os.path.basename(log_file))
                            if processed_log:
                                # Categorize logs by source
                                source = processed_log.get('source_file', 'unknown')
                                self.collected_logs[source].append(processed_log)
                
                time.sleep(1)  # Check for new logs every second
                
            except Exception as e:
                logger.error(f"Log collection error: {str(e)}")
                time.sleep(5)
    
    def write_collected_logs(self):
        """Write collected logs to output files"""
        while self.running:
            try:
                for source, logs in self.collected_logs.items():
                    if logs:
                        # Write logs to source-specific file
                        output_file = os.path.join(self.output_directory, f"collected_{source}")
                        
                        with open(output_file, 'a') as f:
                            for log_entry in logs:
                                f.write(json.dumps(log_entry) + '\n')
                        
                        # Clear processed logs
                        self.collected_logs[source] = []
                        
                        logger.debug(f"Wrote {len(logs)} logs to {output_file}")
                
                time.sleep(5)  # Write collected logs every 5 seconds
                
            except Exception as e:
                logger.error(f"Log writing error: {str(e)}")
                time.sleep(10)
    
    def generate_collection_stats(self):
        """Generate statistics about log collection"""
        while self.running:
            try:
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'monitored_files': len(self.file_positions),
                    'file_positions': self.file_positions.copy(),
                    'pending_logs': {source: len(logs) for source, logs in self.collected_logs.items()},
                    'total_pending': sum(len(logs) for logs in self.collected_logs.values())
                }
                
                stats_file = os.path.join(self.output_directory, 'collection_stats.json')
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                
                logger.info(f"Collection stats: {stats['total_pending']} pending logs from {stats['monitored_files']} files")
                
                time.sleep(30)  # Update stats every 30 seconds
                
            except Exception as e:
                logger.error(f"Stats generation error: {str(e)}")
                time.sleep(60)
    
    def run(self):
        """Start the log collector"""
        logger.info("Log collector starting up")
        
        # Start collection threads
        threads = []
        
        collection_thread = threading.Thread(target=self.collect_logs, daemon=True)
        collection_thread.start()
        threads.append(collection_thread)
        
        writing_thread = threading.Thread(target=self.write_collected_logs, daemon=True)
        writing_thread.start()
        threads.append(writing_thread)
        
        stats_thread = threading.Thread(target=self.generate_collection_stats, daemon=True)
        stats_thread.start()
        threads.append(stats_thread)
        
        logger.info("Log collector started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Log collector shutting down")

if __name__ == '__main__':
    collector = LogCollector()
    collector.run()
```

Create `app/log-processor.py`:
```python
#!/usr/bin/env python3
import json
import time
import os
import logging
import threading
import re
from datetime import datetime
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('log-processor')

class LogProcessor:
    def __init__(self):
        self.input_directory = '/collected-logs'
        self.output_directory = '/processed-logs'
        self.running = True
        self.processed_count = 0
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Log processing rules
        self.processing_rules = {
            'access.log': self.process_access_logs,
            'error.log': self.process_error_logs,
            'application.log': self.process_application_logs,
            'database-queries.log': self.process_database_logs,
            'job-execution.log': self.process_job_logs
        }
        
        # Log level mapping
        self.log_levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
    
    def extract_log_level(self, message):
        """Extract log level from message"""
        level_patterns = {
            'ERROR': r'\b(error|exception|failed|failure)\b',
            'WARNING': r'\b(warn|warning|deprecated)\b',
            'DEBUG': r'\b(debug|trace)\b',
            'INFO': r'\b(info|started|completed|success)\b'
        }
        
        message_lower = message.lower()
        
        for level, pattern in level_patterns.items():
            if re.search(pattern, message_lower):
                return level
        
        return 'INFO'  # Default level
    
    def process_access_logs(self, log_entry):
        """Process access log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse the message if it's JSON
            if 'message' in processed and processed['message'].startswith('{'):
                access_data = json.loads(processed['message'])
                processed.update(access_data)
                del processed['message']
            
            # Add processing metadata
            processed.update({
                'log_category': 'access',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Extract additional fields
            if 'path' in processed:
                processed['endpoint'] = processed['path'].split('?')[0]
            
            if 'status_code' in processed:
                if 200 <= processed['status_code'] < 300:
                    processed['status_category'] = 'success'
                elif 300 <= processed['status_code'] < 400:
                    processed['status_category'] = 'redirect'
                elif 400 <= processed['status_code'] < 500:
                    processed['status_category'] = 'client_error'
                else:
                    processed['status_category'] = 'server_error'
            
        except Exception as e:
            logger.warning(f"Failed to process access log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_error_logs(self, log_entry):
        """Process error log entries"""
        processed = log_entry.copy()
        
        try:
            processed.update({
                'log_category': 'error',
                'log_level': 'ERROR',
                'processed_at': datetime.now().isoformat(),
                'severity': 'high'
            })
            
            # Extract error patterns
            message = processed.get('message', '')
            if 'timeout' in message.lower():
                processed['error_type'] = 'timeout'
            elif 'connection' in message.lower():
                processed['error_type'] = 'connection'
            elif 'validation' in message.lower():
                processed['error_type'] = 'validation'
            else:
                processed['error_type'] = 'unknown'
            
        except Exception as e:
            logger.warning(f"Failed to process error log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_application_logs(self, log_entry):
        """Process application log entries"""
        processed = log_entry.copy()
        
        try:
            message = processed.get('message', '')
            
            # Extract log level from message
            log_level = self.extract_log_level(message)
            
            processed.update({
                'log_category': 'application',
                'log_level': log_level,
                'processed_at': datetime.now().isoformat()
            })
            
            # Extract component name if present
            if 'web-api' in message:
                processed['component'] = 'web-api'
            elif 'background' in message:
                processed['component'] = 'background-task'
            else:
                processed['component'] = 'unknown'
            
        except Exception as e:
            logger.warning(f"Failed to process application log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_database_logs(self, log_entry):
        """Process database log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse JSON message if present
            if 'message' in processed and processed['message'].startswith('{'):
                db_data = json.loads(processed['message'])
                processed.update(db_data)
                del processed['message']
            
            processed.update({
                'log_category': 'database',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Classify query performance
            if 'execution_time_ms' in processed:
                exec_time = processed['execution_time_ms']
                if exec_time > 5000:  # 5 seconds
                    processed['performance_category'] = 'very_slow'
                    processed['log_level'] = 'WARNING'
                elif exec_time > 1000:  # 1 second
                    processed['performance_category'] = 'slow'
                elif exec_time > 100:  # 100ms
                    processed['performance_category'] = 'normal'
                else:
                    processed['performance_category'] = 'fast'
            
        except Exception as e:
            logger.warning(f"Failed to process database log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_job_logs(self, log_entry):
        """Process job execution log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse JSON message if present
            if 'message' in processed and processed['message'].startswith('{'):
                job_data = json.loads(processed['message'])
                processed.update(job_data)
                del processed['message']
            
            processed.update({
                'log_category': 'job',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Set log level based on job status
            status = processed.get('status', 'unknown')
            if status in ['failed', 'error']:
                processed['log_level'] = 'ERROR'
            elif status == 'started':
                processed['log_level'] = 'INFO'
            elif status == 'completed':
                processed['log_level'] = 'INFO'
            
        except Exception as e:
            logger.warning(f"Failed to process job log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_log_file(self, file_path):
        """Process a collected log file"""
        filename = os.path.basename(file_path)
        logger.info(f"Processing log file: {filename}")
        
        try:
            processed_logs = []
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Find appropriate processor
                            processor = None
                            for log_type, proc_func in self.processing_rules.items():
                                if log_type in filename:
                                    processor = proc_func
                                    break
                            
                            if processor:
                                processed_log = processor(log_entry)
                            else:
                                # Default processing
                                processed_log = log_entry.copy()
                                processed_log.update({
                                    'log_category': 'unknown',
                                    'log_level': 'INFO',
                                    'processed_at': datetime.now().isoformat()
                                })
                            
                            processed_logs.append(processed_log)
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON on line {line_num} in {filename}")
                        except Exception as e:
                            logger.error(f"Error processing line {line_num} in {filename}: {str(e)}")
            
            # Write processed logs
            output_file = os.path.join(self.output_directory, f"processed_{filename}")
            with open(output_file, 'w') as f:
                for log_entry in processed_logs:
                    f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"Processed {len(processed_logs)} log entries from {filename}")
            self.processed_count += len(processed_logs)
            
            # Remove processed file
            os.remove(file_path)
            
            return len(processed_logs)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return 0
    
    def process_logs(self):
        """Process collected log files"""
        while self.running:
            try:
                # Find collected log files
                collected_files = glob.glob(os.path.join(self.input_directory, 'collected_*.log'))
                
                if collected_files:
                    for file_path in collected_files:
                        self.process_log_file(file_path)
                else:
                    time.sleep(5)  # Wait if no files to process
                
            except Exception as e:
                logger.error(f"Log processing error: {str(e)}")
                time.sleep(10)
    
    def generate_processing_stats(self):
        """Generate processing statistics"""
        while self.running:
            try:
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'total_processed': self.processed_count,
                    'processing_rate_per_minute': 0,  # Could be calculated
                    'active_processors': len(self.processing_rules)
                }
                
                stats_file = os.path.join(self.output_directory, 'processing_stats.json')
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                
                logger.info(f"Processing stats: {self.processed_count} total logs processed")
                
                time.sleep(60)  # Update stats every minute
                
            except Exception as e:
                logger.error(f"Stats generation error: {str(e)}")
                time.sleep(120)
    
    def run(self):
        """Start the log processor"""
        logger.info("Log processor starting up")
        
        # Start processing threads
        processing_thread = threading.Thread(target=self.process_logs, daemon=True)
        processing_thread.start()
        
        stats_thread = threading.Thread(target=self.generate_processing_stats, daemon=True)
        stats_thread.start()
        
        logger.info("Log processor started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Log processor shutting down")

if __name__ == '__main__':
    processor = LogProcessor()
    processor.run()
```

### Task 3: Create Kubernetes Manifests (15 minutes)

Create `logging-sidecar-app.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-scripts
data:
  web-api.py: |
    # (Include the web-api.py script content here)
  database-client.py: |
    # (Include the database-client.py script content here)
  background-worker.py: |
    # (Include the background-worker.py script content here)
  log-collector.py: |
    # (Include the log-collector.py script content here)
  log-processor.py: |
    # (Include the log-processor.py script content here)
---
apiVersion: v1
kind: Service
metadata:
  name: logging-demo-app
spec:
  selector:
    app: logging-demo
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logging-demo
  labels:
    app: logging-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: logging-demo
  template:
    metadata:
      labels:
        app: logging-demo
    spec:
      containers:
      # Main application containers
      - name: web-api
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install flask requests
          python /app/web-api.py
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: app-scripts
          mountPath: /app
        - name: shared-logs
          mountPath: /logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
      
      - name: database-client
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install pandas
          python /app/database-client.py
        volumeMounts:
        - name: app-scripts
          mountPath: /app
        - name: shared-logs
          mountPath: /logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
      
      - name: background-worker
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          python /app/background-worker.py
        volumeMounts:
        - name: app-scripts
          mountPath: /app
        - name: shared-logs
          mountPath: /logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
      
      # Logging sidecar containers
      - name: log-collector
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          python /app/log-collector.py
        volumeMounts:
        - name: app-scripts
          mountPath: /app
        - name: shared-logs
          mountPath: /logs
        - name: collected-logs
          mountPath: /collected-logs
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      
      - name: log-processor
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install pandas
          python /app/log-processor.py
        volumeMounts:
        - name: app-scripts
          mountPath: /app
        - name: collected-logs
          mountPath: /collected-logs
        - name: processed-logs
          mountPath: /processed-logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
      
      - name: log-forwarder
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          # Simple log forwarder that outputs processed logs
          while true; do
            echo "=== Log Forward Report $(date) ==="
            if [ -d /processed-logs ]; then
              find /processed-logs -name "*.log" -exec wc -l {} \; 2>/dev/null || true
              echo "Latest processed logs:"
              find /processed-logs -name "processed_*" -type f -exec tail -5 {} \; 2>/dev/null || true
            fi
            echo "=== End Report ==="
            sleep 60
          done
        volumeMounts:
        - name: processed-logs
          mountPath: /processed-logs
        resources:
          requests:
            memory: "64Mi"
            cpu: "25m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      
      volumes:
      - name: app-scripts
        configMap:
          name: app-scripts
          defaultMode: 0755
      - name: shared-logs
        emptyDir: {}
      - name: collected-logs
        emptyDir: {}
      - name: processed-logs
        emptyDir: {}
---
# Optional: Create a monitoring pod to observe logs
apiVersion: v1
kind: Pod
metadata:
  name: log-monitor
  labels:
    app: log-monitor
spec:
  containers:
  - name: monitor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Log monitoring started..."
      while true; do
        echo "=== Log Monitor Report $(date) ==="
        echo "Checking application logs..."
        kubectl logs deployment/logging-demo -c web-api --tail=5 2>/dev/null || echo "Could not fetch web-api logs"
        kubectl logs deployment/logging-demo -c log-collector --tail=5 2>/dev/null || echo "Could not fetch log-collector logs"
        kubectl logs deployment/logging-demo -c log-processor --tail=5 2>/dev/null || echo "Could not fetch log-processor logs"
        echo "=== End Monitor Report ==="
        sleep 120
      done
    resources:
      requests:
        memory: "64Mi"
        cpu: "25m"
      limits:
        memory: "128Mi"
        cpu: "100m"
  restartPolicy: Always
```

Deploy and test the logging solution:

```bash
# Apply the logging sidecar application
kubectl apply -f logging-sidecar-app.yaml

# Wait for deployment to be ready
kubectl rollout status deployment/logging-demo

# Check pod status
kubectl get pods -l app=logging-demo

# Test the web API to generate logs
kubectl port-forward service/logging-demo-app 8080:8080 &

# Generate some test traffic
curl http://localhost:8080/health
curl http://localhost:8080/users
curl http://localhost:8080/users/1
curl http://localhost:8080/users/999  # 404 error
curl http://localhost:8080/simulate-load

# Check logs from different containers
kubectl logs deployment/logging-demo -c web-api --tail=20
kubectl logs deployment/logging-demo -c database-client --tail=20
kubectl logs deployment/logging-demo -c background-worker --tail=20
kubectl logs deployment/logging-demo -c log-collector --tail=20
kubectl logs deployment/logging-demo -c log-processor --tail=20
kubectl logs deployment/logging-demo -c log-forwarder --tail=20

# Check log monitor
kubectl logs pod/log-monitor --tail=50

# Exec into containers to check log files
kubectl exec deployment/logging-demo -c web-api -- find /logs -name "*.log" -ls
kubectl exec deployment/logging-demo -c log-collector -- find /collected-logs -name "*" -ls
kubectl exec deployment/logging-demo -c log-processor -- find /processed-logs -name "*" -ls

# Check specific log contents
kubectl exec deployment/logging-demo -c log-collector -- head -10 /collected-logs/collected_access.log
kubectl exec deployment/logging-demo -c log-processor -- head -10 /processed-logs/processed_collected_access.log

# Cleanup
kubectl delete -f logging-sidecar-app.yaml
```

## Success Criteria

- [ ] All containers start successfully without errors
- [ ] Main application generates logs in multiple formats
- [ ] Log collector successfully reads and aggregates logs
- [ ] Log processor formats and enriches logs consistently
- [ ] Log forwarder outputs processed logs
- [ ] Logs are properly shared between containers using volumes
- [ ] Different log types are processed with appropriate rules
- [ ] Log collection and processing statistics are generated
- [ ] Web API responds correctly and generates access logs
- [ ] Background services generate periodic logs
- [ ] Error scenarios produce appropriate error logs

## Advanced Extensions

1. **Log Shipping**: Forward logs to external systems (ELK, Splunk)
2. **Log Filtering**: Implement dynamic log filtering based on levels
3. **Log Compression**: Compress older logs to save space
4. **Alerting**: Add alerting for critical log patterns
5. **Performance Metrics**: Monitor sidecar resource usage

## Learning Objectives

- Multi-container pod design and coordination
- Shared volume configuration for log sharing
- Sidecar pattern implementation
- Log processing and enrichment techniques
- Container resource management
- Inter-container communication patterns