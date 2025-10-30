# Lab 6: Application Metrics

**Objective**: Learn to implement and collect application metrics in Kubernetes
**Time**: 45 minutes
**Difficulty**: Intermediate

---

## Learning Outcomes

By the end of this lab, you will be able to:
- Expose application metrics in different formats
- Implement health check endpoints with metrics
- Use Prometheus metrics format
- Create custom application metrics
- Monitor application performance indicators
- Debug applications using metrics data

---

## Prerequisites

- Kubernetes cluster access
- kubectl configured
- Basic understanding of HTTP endpoints
- Completion of previous monitoring labs recommended

---

## Theory: Application Metrics in Kubernetes

### Metrics Categories

1. **Business Metrics**: User registrations, transactions, orders
2. **Application Metrics**: Response times, error rates, throughput
3. **Infrastructure Metrics**: CPU, memory, disk usage
4. **Custom Metrics**: Domain-specific measurements

### Common Metrics Formats

- **Prometheus**: Industry standard for cloud-native metrics
- **JSON**: Simple format for custom applications
- **Plain Text**: Basic key-value metrics
- **StatsD**: Network protocol for metrics collection

### Key Performance Indicators (KPIs)

- **Latency**: Request/response time
- **Traffic**: Requests per second
- **Errors**: Error rate and types
- **Saturation**: Resource utilization

---

## Exercise 1: Basic Application Metrics (15 minutes)

### Step 1: Create a Metrics-Enabled Application

```yaml
cat << EOF > metrics-app.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: metrics-app-config
data:
  app.js: |
    const express = require('express');
    const promClient = require('prom-client');
    const app = express();
    const port = 3000;
    
    // Create a Registry to register the metrics
    const register = new promClient.Registry();
    
    // Add default metrics
    promClient.collectDefaultMetrics({
      app: 'metrics-demo-app',
      prefix: 'nodejs_',
      timeout: 10000,
      gcDurationBuckets: [0.001, 0.01, 0.1, 1, 2, 5],
      register
    });
    
    // Custom metrics
    const httpRequestsTotal = new promClient.Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status_code'],
      registers: [register]
    });
    
    const httpRequestDuration = new promClient.Histogram({
      name: 'http_request_duration_seconds',
      help: 'Duration of HTTP requests in seconds',
      labelNames: ['method', 'route'],
      buckets: [0.1, 0.5, 1, 2, 5],
      registers: [register]
    });
    
    const activeConnections = new promClient.Gauge({
      name: 'active_connections',
      help: 'Number of active connections',
      registers: [register]
    });
    
    const customBusinessMetric = new promClient.Counter({
      name: 'business_transactions_total',
      help: 'Total business transactions processed',
      labelNames: ['type', 'status'],
      registers: [register]
    });
    
    // Middleware to track metrics
    app.use((req, res, next) => {
      const start = Date.now();
      activeConnections.inc();
      
      res.on('finish', () => {
        const duration = (Date.now() - start) / 1000;
        httpRequestsTotal.inc({
          method: req.method,
          route: req.route?.path || req.path,
          status_code: res.statusCode
        });
        httpRequestDuration.observe({
          method: req.method,
          route: req.route?.path || req.path
        }, duration);
        activeConnections.dec();
      });
      
      next();
    });
    
    // Routes
    app.get('/', (req, res) => {
      res.json({
        message: 'Metrics Demo Application',
        version: '1.0.0',
        timestamp: new Date().toISOString()
      });
    });
    
    app.get('/health', (req, res) => {
      const healthData = {
        status: 'healthy',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        checks: {
          memory: process.memoryUsage(),
          cpu: process.cpuUsage()
        }
      };
      res.json(healthData);
    });
    
    app.get('/metrics', async (req, res) => {
      res.set('Content-Type', register.contentType);
      const metrics = await register.metrics();
      res.end(metrics);
    });
    
    // Business logic endpoints
    app.post('/api/order', (req, res) => {
      // Simulate order processing
      const processingTime = Math.random() * 2000; // 0-2 seconds
      
      setTimeout(() => {
        const success = Math.random() > 0.1; // 90% success rate
        
        if (success) {
          customBusinessMetric.inc({ type: 'order', status: 'success' });
          res.json({ orderId: Date.now(), status: 'completed' });
        } else {
          customBusinessMetric.inc({ type: 'order', status: 'failed' });
          res.status(500).json({ error: 'Order processing failed' });
        }
      }, processingTime);
    });
    
    app.get('/api/user/:id', (req, res) => {
      const userId = req.params.id;
      
      // Simulate database lookup time
      const lookupTime = Math.random() * 500;
      
      setTimeout(() => {
        customBusinessMetric.inc({ type: 'user_lookup', status: 'success' });
        res.json({
          userId,
          name: \`User \${userId}\`,
          email: \`user\${userId}@example.com\`,
          timestamp: new Date().toISOString()
        });
      }, lookupTime);
    });
    
    // Load simulation endpoint
    app.get('/api/load/:level', (req, res) => {
      const level = parseInt(req.params.level) || 1;
      const iterations = level * 100000;
      
      // CPU intensive task
      let result = 0;
      for (let i = 0; i < iterations; i++) {
        result += Math.sqrt(i);
      }
      
      res.json({
        level,
        iterations,
        result: result.toString().slice(0, 10),
        message: \`Completed level \${level} load test\`
      });
    });
    
    app.listen(port, () => {
      console.log(\`Metrics app listening on port \${port}\`);
      console.log('Available endpoints:');
      console.log('  GET  /           - Basic info');
      console.log('  GET  /health     - Health check');
      console.log('  GET  /metrics    - Prometheus metrics');
      console.log('  POST /api/order  - Create order');
      console.log('  GET  /api/user/:id - Get user');
      console.log('  GET  /api/load/:level - Load test');
    });
  
  package.json: |
    {
      "name": "metrics-demo-app",
      "version": "1.0.0",
      "description": "Application with Prometheus metrics",
      "main": "app.js",
      "scripts": {
        "start": "node app.js"
      },
      "dependencies": {
        "express": "^4.18.2",
        "prom-client": "^14.2.0"
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
  labels:
    app: metrics-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: metrics-app
  template:
    metadata:
      labels:
        app: metrics-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: node:18-alpine
        ports:
        - containerPort: 3000
        workingDir: /app
        command:
        - sh
        - -c
        - |
          cp /config/* /app/
          npm install
          npm start
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 300m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: metrics-app-config
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-app-service
  labels:
    app: metrics-app
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
    protocol: TCP
  selector:
    app: metrics-app
EOF

kubectl apply -f metrics-app.yaml
```

### Step 2: Test Basic Metrics Collection

```bash
# Wait for deployment to be ready
kubectl wait --for=condition=available deployment/metrics-app --timeout=120s

# Test the application
kubectl port-forward service/metrics-app-service 3000:3000 &
PF_PID=$!
sleep 5

# Test basic endpoints
echo "=== Testing Basic Endpoints ==="
curl -s http://localhost:3000/ | jq '.'
echo ""

curl -s http://localhost:3000/health | jq '.'
echo ""

# Check initial metrics
echo "=== Initial Metrics ==="
curl -s http://localhost:3000/metrics | head -20
echo ""

# Clean up port forward
kill $PF_PID 2>/dev/null
```

---

## Exercise 2: Generate Application Load and Monitor Metrics (15 minutes)

### Step 1: Create Load Generation Script

```bash
cat << 'LOADGEN' > generate-load.sh
#!/bin/bash

APP_URL=${1:-http://localhost:3000}
DURATION=${2:-300}  # 5 minutes default
CONCURRENT_USERS=${3:-5}

echo "Starting load generation for $DURATION seconds"
echo "Target: $APP_URL"
echo "Concurrent users: $CONCURRENT_USERS"

# Function to simulate user behavior
simulate_user() {
    local user_id=$1
    local end_time=$(($(date +%s) + DURATION))
    
    while [ $(date +%s) -lt $end_time ]; do
        # Random user actions
        case $((RANDOM % 4)) in
            0)  # Get user info
                USER_ID=$((RANDOM % 100 + 1))
                curl -s "$APP_URL/api/user/$USER_ID" > /dev/null
                ;;
            1)  # Create order
                curl -s -X POST "$APP_URL/api/order" > /dev/null
                ;;
            2)  # Load test
                LEVEL=$((RANDOM % 5 + 1))
                curl -s "$APP_URL/api/load/$LEVEL" > /dev/null
                ;;
            3)  # Health check
                curl -s "$APP_URL/health" > /dev/null
                ;;
        esac
        
        # Random delay between requests (0.5-3 seconds)
        sleep $(echo "scale=1; $(shuf -i 5-30 -n 1)/10" | bc)
    done
    
    echo "User $user_id simulation completed"
}

# Start concurrent users
for ((i=1; i<=CONCURRENT_USERS; i++)); do
    simulate_user $i &
done

# Wait for all background jobs to complete
wait

echo "Load generation completed"
LOADGEN

chmod +x generate-load.sh
```

### Step 2: Monitor Metrics During Load

```bash
# Start port forwarding
kubectl port-forward service/metrics-app-service 3000:3000 &
PF_PID=$!
sleep 5

# Start metrics monitoring
cat << 'MONITOR' > monitor-metrics.sh
#!/bin/bash

METRICS_URL=${1:-http://localhost:3000/metrics}
INTERVAL=${2:-10}

echo "Monitoring metrics from: $METRICS_URL"
echo "Interval: ${INTERVAL} seconds"
echo ""

function get_metric_value() {
    curl -s "$METRICS_URL" | grep "^$1" | grep -v "#" | tail -1 | awk '{print $2}'
}

function get_histogram_samples() {
    local metric_name=$1
    curl -s "$METRICS_URL" | grep "^${metric_name}_count" | awk '{print $2}'
}

while true; do
    echo "=== $(date) ==="
    
    # HTTP Requests
    total_requests=$(get_metric_value "http_requests_total")
    echo "Total HTTP Requests: $total_requests"
    
    # Request Duration
    request_samples=$(get_histogram_samples "http_request_duration_seconds")
    echo "Request Duration Samples: $request_samples"
    
    # Active Connections
    active_conn=$(get_metric_value "active_connections")
    echo "Active Connections: $active_conn"
    
    # Business Metrics
    business_transactions=$(get_metric_value "business_transactions_total")
    echo "Business Transactions: $business_transactions"
    
    # Node.js specific metrics
    heap_used=$(get_metric_value "nodejs_heap_size_used_bytes")
    if [ -n "$heap_used" ]; then
        heap_used_mb=$(echo "scale=2; $heap_used / 1024 / 1024" | bc)
        echo "Heap Used: ${heap_used_mb} MB"
    fi
    
    echo ""
    sleep $INTERVAL
done
MONITOR

chmod +x monitor-metrics.sh

# Start monitoring in background
./monitor-metrics.sh http://localhost:3000/metrics 15 &
MONITOR_PID=$!

# Generate load
echo "Starting load generation..."
./generate-load.sh http://localhost:3000 180 3

# Let monitoring run a bit longer
sleep 30

# Stop monitoring
kill $MONITOR_PID 2>/dev/null
kill $PF_PID 2>/dev/null
```

### Step 3: Analyze Metrics Data

```bash
# Get detailed metrics analysis
kubectl port-forward service/metrics-app-service 3000:3000 &
PF_PID=$!
sleep 5

echo "=== Detailed Metrics Analysis ==="

# Get all metrics and analyze
curl -s http://localhost:3000/metrics > current-metrics.txt

echo "--- HTTP Request Metrics ---"
grep "http_requests_total" current-metrics.txt | grep -v "#"

echo ""
echo "--- Request Duration Buckets ---"
grep "http_request_duration_seconds_bucket" current-metrics.txt | head -10

echo ""
echo "--- Business Transaction Metrics ---"
grep "business_transactions_total" current-metrics.txt | grep -v "#"

echo ""
echo "--- Memory Usage ---"
grep "nodejs_heap" current-metrics.txt | grep -v "#" | head -5

echo ""
echo "--- GC Metrics ---"
grep "nodejs_gc" current-metrics.txt | grep -v "#" | head -5

# Calculate some statistics
echo ""
echo "=== Calculated Statistics ==="

# Request rate calculation
total_requests=$(grep "http_requests_total" current-metrics.txt | grep -v "#" | head -1 | awk '{print $2}')
uptime_seconds=$(curl -s http://localhost:3000/health | jq -r '.uptime')

if [ -n "$total_requests" ] && [ -n "$uptime_seconds" ]; then
    requests_per_second=$(echo "scale=2; $total_requests / $uptime_seconds" | bc)
    echo "Average requests per second: $requests_per_second"
fi

# Success rate calculation
success_requests=$(grep 'status_code="200"' current-metrics.txt | awk '{sum += $2} END {print sum}')
error_requests=$(grep 'status_code="5' current-metrics.txt | awk '{sum += $2} END {print sum}')

if [ -n "$success_requests" ] && [ -n "$error_requests" ]; then
    total_counted=$((success_requests + error_requests))
    if [ $total_counted -gt 0 ]; then
        success_rate=$(echo "scale=2; $success_requests * 100 / $total_counted" | bc)
        echo "Success rate: ${success_rate}%"
    fi
fi

kill $PF_PID 2>/dev/null
```

---

## Exercise 3: Custom Metrics Implementation (10 minutes)

### Step 1: Create Advanced Metrics Application

```yaml
cat << EOF > advanced-metrics-app.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: advanced-metrics-config
data:
  advanced-app.py: |
    from flask import Flask, jsonify, request
    from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
    import time
    import random
    import threading
    import json
    from datetime import datetime

    app = Flask(__name__)

    # Define custom metrics
    REQUEST_COUNT = Counter(
        'flask_requests_total', 
        'Total Flask HTTP requests', 
        ['method', 'endpoint', 'status']
    )

    REQUEST_LATENCY = Histogram(
        'flask_request_duration_seconds',
        'Flask HTTP request latency',
        ['endpoint']
    )

    ACTIVE_SESSIONS = Gauge(
        'active_user_sessions',
        'Number of active user sessions'
    )

    QUEUE_SIZE = Gauge(
        'background_queue_size',
        'Size of background processing queue'
    )

    BUSINESS_OPERATIONS = Counter(
        'business_operations_total',
        'Total business operations',
        ['operation', 'status', 'customer_tier']
    )

    RESPONSE_SIZE = Summary(
        'response_size_bytes',
        'Size of HTTP responses',
        ['endpoint']
    )

    DATABASE_CONNECTIONS = Gauge(
        'database_connections_active',
        'Active database connections'
    )

    # Simulate some background metrics
    processing_queue = []
    active_sessions = set()
    db_connections = 0

    def background_metrics_updater():
        """Background thread to update various metrics"""
        global db_connections
        while True:
            # Simulate queue processing
            if processing_queue:
                processing_queue.pop(0)
            
            # Simulate database connection changes
            db_connections += random.randint(-2, 3)
            db_connections = max(0, min(db_connections, 50))  # Keep between 0-50
            DATABASE_CONNECTIONS.set(db_connections)
            
            # Update queue size
            QUEUE_SIZE.set(len(processing_queue))
            
            # Update active sessions
            ACTIVE_SESSIONS.set(len(active_sessions))
            
            time.sleep(5)

    # Start background thread
    threading.Thread(target=background_metrics_updater, daemon=True).start()

    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        # Record request metrics
        request_latency = time.time() - request.start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            endpoint=request.endpoint or 'unknown'
        ).observe(request_latency)
        
        # Record response size
        if hasattr(response, 'content_length') and response.content_length:
            RESPONSE_SIZE.labels(
                endpoint=request.endpoint or 'unknown'
            ).observe(response.content_length)
        
        return response

    @app.route('/')
    def home():
        return jsonify({
            'service': 'Advanced Metrics Demo',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'features': ['custom_metrics', 'business_intelligence', 'real_time_monitoring']
        })

    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'active_sessions': len(active_sessions),
                'queue_size': len(processing_queue),
                'db_connections': db_connections
            }
        })

    @app.route('/metrics')
    def metrics():
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

    @app.route('/api/login', methods=['POST'])
    def login():
        # Simulate login processing
        user_id = f"user_{random.randint(1000, 9999)}"
        tier = random.choice(['basic', 'premium', 'enterprise'])
        
        # Add some processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Success rate based on tier
        success_rates = {'basic': 0.95, 'premium': 0.98, 'enterprise': 0.99}
        success = random.random() < success_rates[tier]
        
        if success:
            active_sessions.add(user_id)
            BUSINESS_OPERATIONS.labels(
                operation='login',
                status='success',
                customer_tier=tier
            ).inc()
            
            return jsonify({
                'user_id': user_id,
                'session_token': f"token_{int(time.time())}",
                'tier': tier,
                'message': 'Login successful'
            })
        else:
            BUSINESS_OPERATIONS.labels(
                operation='login',
                status='failure',
                customer_tier=tier
            ).inc()
            return jsonify({'error': 'Login failed'}), 401

    @app.route('/api/logout', methods=['POST'])
    def logout():
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        if user_id in active_sessions:
            active_sessions.remove(user_id)
            
        BUSINESS_OPERATIONS.labels(
            operation='logout',
            status='success',
            customer_tier='unknown'
        ).inc()
        
        return jsonify({'message': 'Logout successful'})

    @app.route('/api/process', methods=['POST'])
    def process_request():
        data = request.get_json() or {}
        task_type = data.get('type', 'standard')
        priority = data.get('priority', 'normal')
        
        # Add to processing queue
        task = {
            'id': f"task_{int(time.time())}_{random.randint(100, 999)}",
            'type': task_type,
            'priority': priority,
            'created_at': datetime.now().isoformat()
        }
        processing_queue.append(task)
        
        # Simulate processing time based on type
        processing_times = {
            'standard': (0.1, 0.5),
            'premium': (0.05, 0.2),
            'bulk': (1.0, 3.0)
        }
        
        min_time, max_time = processing_times.get(task_type, (0.1, 0.5))
        time.sleep(random.uniform(min_time, max_time))
        
        BUSINESS_OPERATIONS.labels(
            operation='process_request',
            status='completed',
            customer_tier=task_type
        ).inc()
        
        return jsonify(task)

    @app.route('/api/stats')
    def stats():
        return jsonify({
            'current_stats': {
                'active_sessions': len(active_sessions),
                'queue_size': len(processing_queue),
                'db_connections': db_connections,
                'timestamp': datetime.now().isoformat()
            },
            'queue_preview': processing_queue[:5] if processing_queue else []
        })

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=False)

  requirements.txt: |
    Flask==2.3.3
    prometheus_client==0.17.1
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: advanced-metrics-app
  labels:
    app: advanced-metrics-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: advanced-metrics-app
  template:
    metadata:
      labels:
        app: advanced-metrics-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "5000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: python:3.9-alpine
        ports:
        - containerPort: 5000
        workingDir: /app
        command:
        - sh
        - -c
        - |
          cp /config/* /app/
          pip install -r requirements.txt
          python advanced-app.py
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 300m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: advanced-metrics-config
---
apiVersion: v1
kind: Service
metadata:
  name: advanced-metrics-service
  labels:
    app: advanced-metrics-app
spec:
  type: ClusterIP
  ports:
  - port: 5000
    targetPort: 5000
    protocol: TCP
  selector:
    app: advanced-metrics-app
EOF

kubectl apply -f advanced-metrics-app.yaml
```

### Step 2: Test Advanced Metrics

```bash
# Wait for deployment
kubectl wait --for=condition=available deployment/advanced-metrics-app --timeout=120s

# Test advanced metrics
kubectl port-forward service/advanced-metrics-service 5000:5000 &
PF_PID=$!
sleep 5

echo "=== Testing Advanced Metrics Application ==="

# Test basic endpoints
curl -s http://localhost:5000/ | jq '.'
echo ""

curl -s http://localhost:5000/health | jq '.'
echo ""

# Generate some business activity
echo "=== Generating Business Activity ==="

# Simulate logins
for i in {1..10}; do
    curl -s -X POST http://localhost:5000/api/login \
         -H "Content-Type: application/json" \
         -d '{}' | jq '.user_id // .error'
done

echo ""

# Simulate processing requests
for type in standard premium bulk; do
    for priority in normal high; do
        curl -s -X POST http://localhost:5000/api/process \
             -H "Content-Type: application/json" \
             -d "{\"type\":\"$type\",\"priority\":\"$priority\"}" | jq '.id'
    done
done

echo ""

# Check application stats
echo "=== Application Stats ==="
curl -s http://localhost:5000/api/stats | jq '.'

echo ""

# Check metrics
echo "=== Business Metrics Sample ==="
curl -s http://localhost:5000/metrics | grep "business_operations_total"

echo ""
echo "=== Session Metrics ==="
curl -s http://localhost:5000/metrics | grep "active_user_sessions"

kill $PF_PID 2>/dev/null
```

---

## Exercise 4: Metrics Collection and Analysis (5 minutes)

### Step 1: Comprehensive Metrics Dashboard

```bash
cat << 'METRICS_DASHBOARD' > comprehensive-metrics-dashboard.sh
#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NODEJS_APP_URL="http://localhost:3000"
PYTHON_APP_URL="http://localhost:5000"

function print_header() {
    clear
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Application Metrics Dashboard${NC}"
    echo -e "${BLUE}  $(date)${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

function get_metric_value() {
    local url=$1
    local metric=$2
    curl -s "$url/metrics" | grep "^$metric" | grep -v "#" | head -1 | awk '{print $2}'
}

function show_nodejs_metrics() {
    echo -e "${GREEN}--- Node.js Application Metrics ---${NC}"
    
    local total_requests=$(get_metric_value "$NODEJS_APP_URL" "http_requests_total")
    local active_conn=$(get_metric_value "$NODEJS_APP_URL" "active_connections")
    local business_trans=$(get_metric_value "$NODEJS_APP_URL" "business_transactions_total")
    
    echo "Total HTTP Requests: ${total_requests:-N/A}"
    echo "Active Connections: ${active_conn:-N/A}"
    echo "Business Transactions: ${business_trans:-N/A}"
    
    # Memory usage
    local heap_used=$(get_metric_value "$NODEJS_APP_URL" "nodejs_heap_size_used_bytes")
    if [ -n "$heap_used" ]; then
        local heap_mb=$(echo "scale=2; $heap_used / 1024 / 1024" | bc 2>/dev/null || echo "0")
        echo "Heap Used: ${heap_mb} MB"
    fi
    
    echo ""
}

function show_python_metrics() {
    echo -e "${GREEN}--- Python Application Metrics ---${NC}"
    
    local flask_requests=$(get_metric_value "$PYTHON_APP_URL" "flask_requests_total")
    local active_sessions=$(get_metric_value "$PYTHON_APP_URL" "active_user_sessions")
    local queue_size=$(get_metric_value "$PYTHON_APP_URL" "background_queue_size")
    local db_connections=$(get_metric_value "$PYTHON_APP_URL" "database_connections_active")
    
    echo "Flask Requests: ${flask_requests:-N/A}"
    echo "Active Sessions: ${active_sessions:-N/A}"
    echo "Queue Size: ${queue_size:-N/A}"
    echo "DB Connections: ${db_connections:-N/A}"
    
    # Business operations
    local business_ops=$(curl -s "$PYTHON_APP_URL/metrics" | grep "business_operations_total" | wc -l)
    echo "Business Operation Types: ${business_ops}"
    
    echo ""
}

function show_comparative_analysis() {
    echo -e "${GREEN}--- Comparative Analysis ---${NC}"
    
    # Compare response times if available
    local nodejs_health=$(curl -s -w "%{time_total}" "$NODEJS_APP_URL/health" -o /dev/null 2>/dev/null)
    local python_health=$(curl -s -w "%{time_total}" "$PYTHON_APP_URL/health" -o /dev/null 2>/dev/null)
    
    if [ -n "$nodejs_health" ] && [ -n "$python_health" ]; then
        echo "Health Endpoint Response Times:"
        echo "  Node.js: ${nodejs_health}s"
        echo "  Python: ${python_health}s"
    fi
    
    echo ""
}

# Check if apps are accessible
kubectl port-forward service/metrics-app-service 3000:3000 >/dev/null 2>&1 &
NODEJS_PF=$!

kubectl port-forward service/advanced-metrics-service 5000:5000 >/dev/null 2>&1 &
PYTHON_PF=$!

sleep 5

# Display dashboard
print_header
show_nodejs_metrics
show_python_metrics
show_comparative_analysis

echo -e "${YELLOW}Raw Metrics Samples:${NC}"
echo "--- Node.js Metrics Sample ---"
curl -s "$NODEJS_APP_URL/metrics" | grep -E "(http_requests_total|nodejs_heap)" | head -5

echo ""
echo "--- Python Metrics Sample ---"
curl -s "$PYTHON_APP_URL/metrics" | grep -E "(flask_requests_total|business_operations)" | head -5

# Cleanup
kill $NODEJS_PF $PYTHON_PF 2>/dev/null
METRICS_DASHBOARD

chmod +x comprehensive-metrics-dashboard.sh
./comprehensive-metrics-dashboard.sh
```

### Step 2: Export Metrics for Analysis

```bash
# Export current metrics for analysis
echo "=== Exporting Metrics Data ==="

# Create metrics export directory
mkdir -p metrics-export

# Export Node.js metrics
kubectl port-forward service/metrics-app-service 3000:3000 >/dev/null 2>&1 &
NODEJS_PF=$!
sleep 3

curl -s http://localhost:3000/metrics > metrics-export/nodejs-metrics.txt
curl -s http://localhost:3000/health > metrics-export/nodejs-health.json

kill $NODEJS_PF 2>/dev/null

# Export Python metrics
kubectl port-forward service/advanced-metrics-service 5000:5000 >/dev/null 2>&1 &
PYTHON_PF=$!
sleep 3

curl -s http://localhost:5000/metrics > metrics-export/python-metrics.txt
curl -s http://localhost:5000/health > metrics-export/python-health.json
curl -s http://localhost:5000/api/stats > metrics-export/python-stats.json

kill $PYTHON_PF 2>/dev/null

# Analyze metrics
echo "=== Metrics Analysis Summary ==="

echo "Node.js Metrics:"
echo "  Total metrics: $(grep -c "^[a-zA-Z]" metrics-export/nodejs-metrics.txt)"
echo "  HTTP request metrics: $(grep -c "http_requests_total" metrics-export/nodejs-metrics.txt)"
echo "  Custom business metrics: $(grep -c "business_transactions_total" metrics-export/nodejs-metrics.txt)"

echo ""
echo "Python Metrics:"
echo "  Total metrics: $(grep -c "^[a-zA-Z]" metrics-export/python-metrics.txt)"
echo "  Flask request metrics: $(grep -c "flask_requests_total" metrics-export/python-metrics.txt)"
echo "  Business operation metrics: $(grep -c "business_operations_total" metrics-export/python-metrics.txt)"

echo ""
echo "Exported files:"
ls -la metrics-export/
```

---

## Troubleshooting Metrics Issues

### Common Metrics Problems

#### Issue 1: Metrics Endpoint Not Accessible

```bash
# Check if metrics endpoint is responding
kubectl get pods -l app=metrics-app
kubectl logs -l app=metrics-app --tail=20

# Test metrics endpoint
kubectl port-forward service/metrics-app-service 3000:3000 &
sleep 3
curl -I http://localhost:3000/metrics
kill %1
```

#### Issue 2: Metrics Not Updating

```bash
# Check application logs for errors
kubectl logs deployment/metrics-app

# Verify metrics are being generated
kubectl exec deployment/metrics-app -- curl -s localhost:3000/metrics | grep -c "^[a-zA-Z]"
```

#### Issue 3: High Cardinality Metrics

```bash
# Check for high cardinality metrics (too many labels)
curl -s http://localhost:3000/metrics | grep "http_requests_total" | wc -l

# Analyze label combinations
curl -s http://localhost:3000/metrics | grep "http_requests_total" | head -10
```

---

## Validation and Testing

### Test Your Understanding

1. **Implement custom application metrics** using Prometheus format
2. **Generate and collect business metrics** from application endpoints
3. **Monitor application performance** using various metric types
4. **Analyze metrics data** to identify patterns and issues

### Verification Commands

```bash
# Metrics accessibility
kubectl port-forward service/metrics-app-service 3000:3000 &
curl -s http://localhost:3000/metrics | grep -E "(http_requests_total|business_transactions_total)"
kill %1

# Custom metrics verification
kubectl port-forward service/advanced-metrics-service 5000:5000 &
curl -s http://localhost:5000/metrics | grep -E "(flask_requests_total|business_operations_total)"
kill %1

# Health metrics
kubectl get pods -l app=metrics-app -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,READY:.status.conditions[1].status
```

---

## Cleanup

```bash
# Delete all lab resources
kubectl delete -f metrics-app.yaml
kubectl delete -f advanced-metrics-app.yaml

# Remove generated files
rm -f metrics-app.yaml advanced-metrics-app.yaml
rm -f generate-load.sh monitor-metrics.sh comprehensive-metrics-dashboard.sh
rm -f current-metrics.txt
rm -rf metrics-export/
```

---

## Key Takeaways

1. **Prometheus format** is the standard for cloud-native metrics
2. **Custom metrics** should align with business objectives
3. **Metric types** (Counter, Gauge, Histogram, Summary) serve different purposes
4. **Label cardinality** must be controlled to avoid performance issues
5. **Regular monitoring** of metrics helps identify application issues
6. **Business metrics** provide insights beyond technical performance

---

## Next Steps

- Proceed to [Lab 7: Pod Debugging](lab07-pod-debugging.md)
- Practice [Network Debugging](lab08-network-debug.md)
- Explore [Performance Debugging](lab09-performance-debug.md)

---

## Additional Resources

- [Prometheus Metrics Best Practices](https://prometheus.io/docs/practices/naming/)
- [Application Metrics with Prometheus](https://prometheus.io/docs/guides/go-application/)
- [Kubernetes Monitoring Architecture](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)