# Mock Scenario 3: Monitor Resource Usage

**Scenario**: You are managing a production Kubernetes cluster running multiple applications. The operations team has reported performance issues, increased latency, and occasional service outages. You need to implement comprehensive resource monitoring, identify bottlenecks, and optimize resource allocation to ensure stable application performance.

**Time Limit**: 35 minutes  
**Difficulty**: Advanced

---

## Background

Your organization runs a multi-tenant platform with the following workloads:

- **Web Application**: User-facing application with variable traffic
- **Background Workers**: Batch processing jobs for data analysis
- **Cache Layer**: Redis cluster for application caching
- **Database**: PostgreSQL with reporting workloads
- **Monitoring Stack**: Prometheus and Grafana for observability

Recent issues reported:
- Applications experiencing intermittent slowdowns
- Some pods being killed unexpectedly
- Uneven resource distribution across nodes
- Difficulty predicting resource needs for scaling

---

## Initial Setup

Deploy a multi-application environment with resource monitoring challenges:

```bash
# Create namespace
kubectl create namespace resource-monitoring
kubectl config set-context --current --namespace=resource-monitoring

# Deploy applications with various resource patterns
cat << EOF > resource-monitoring-apps.yaml
# Web application with variable load
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        tier: frontend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: web-server
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
          name: http
        # ISSUE: Resource requests/limits may not be optimal
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        env:
        - name: WORKER_THREADS
          value: "4"
        - name: CACHE_SIZE
          value: "100MB"
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import threading
          import time
          import random
          import json
          import psutil
          import os
          from urllib.parse import urlparse, parse_qs
          
          # Simulate web application with variable resource usage
          active_requests = 0
          memory_cache = {}
          
          class MetricsCollector:
              def __init__(self):
                  self.request_count = 0
                  self.error_count = 0
                  self.response_times = []
                  
              def record_request(self, duration, error=False):
                  self.request_count += 1
                  if error:
                      self.error_count += 1
                  self.response_times.append(duration)
                  if len(self.response_times) > 1000:
                      self.response_times = self.response_times[-1000:]
          
          metrics = MetricsCollector()
          
          def simulate_load():
              """Simulate varying application load"""
              global memory_cache
              while True:
                  # Simulate cache operations (memory usage)
                  if random.random() < 0.3:
                      key = f"cache_key_{random.randint(1, 1000)}"
                      value = "x" * random.randint(1024, 10240)  # 1-10KB
                      memory_cache[key] = value
                  
                  # Clean cache occasionally
                  if len(memory_cache) > 500:
                      keys_to_remove = random.sample(list(memory_cache.keys()), 100)
                      for key in keys_to_remove:
                          memory_cache.pop(key, None)
                  
                  time.sleep(random.uniform(0.1, 2.0))
          
          # Start background load simulation
          threading.Thread(target=simulate_load, daemon=True).start()
          
          class WebHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  global active_requests
                  active_requests += 1
                  start_time = time.time()
                  
                  try:
                      if self.path == '/health':
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Web app healthy')
                      
                      elif self.path == '/metrics':
                          # Prometheus metrics endpoint
                          process = psutil.Process()
                          memory_info = process.memory_info()
                          cpu_percent = process.cpu_percent()
                          
                          metrics_text = f'''# HELP http_requests_total Total HTTP requests
          # TYPE http_requests_total counter
          http_requests_total{{method="GET"}} {metrics.request_count}
          
          # HELP http_request_duration_seconds HTTP request duration
          # TYPE http_request_duration_seconds histogram
          http_request_duration_seconds_sum {sum(metrics.response_times)}
          http_request_duration_seconds_count {len(metrics.response_times)}
          
          # HELP memory_usage_bytes Memory usage in bytes
          # TYPE memory_usage_bytes gauge
          memory_usage_bytes {memory_info.rss}
          
          # HELP cpu_usage_percent CPU usage percentage
          # TYPE cpu_usage_percent gauge
          cpu_usage_percent {cpu_percent}
          
          # HELP active_requests Current active requests
          # TYPE active_requests gauge
          active_requests {active_requests}
          
          # HELP cache_size_items Cache size in items
          # TYPE cache_size_items gauge
          cache_size_items {len(memory_cache)}
          '''
                          
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(metrics_text.encode())
                      
                      elif self.path.startswith('/api/data'):
                          # Simulate CPU and memory intensive operation
                          query = parse_qs(urlparse(self.path).query)
                          complexity = int(query.get('complexity', ['1'])[0])
                          
                          # CPU intensive operation
                          result = 0
                          for i in range(complexity * 100000):
                              result += i * i
                          
                          # Memory allocation
                          temp_data = [random.random() for _ in range(complexity * 1000)]
                          
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'result': result % 1000000,
                              'complexity': complexity,
                              'data_points': len(temp_data),
                              'cache_size': len(memory_cache)
                          }
                          self.wfile.write(json.dumps(response).encode())
                      
                      else:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/html')
                          self.end_headers()
                          html = f'''
                          <html>
                          <head><title>Web Application</title></head>
                          <body>
                              <h1>Resource Monitoring Demo</h1>
                              <p>Active Requests: {active_requests}</p>
                              <p>Cache Size: {len(memory_cache)} items</p>
                              <p>Total Requests: {metrics.request_count}</p>
                              <a href="/api/data?complexity=5">Low Load Test</a><br>
                              <a href="/api/data?complexity=20">High Load Test</a><br>
                              <a href="/metrics">Metrics</a>
                          </body>
                          </html>
                          '''
                          self.wfile.write(html.encode())
                  
                  except Exception as e:
                      self.send_response(500)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(f'Error: {str(e)}'.encode())
                      metrics.record_request(time.time() - start_time, error=True)
                  finally:
                      active_requests -= 1
                      metrics.record_request(time.time() - start_time)
          
          print("Starting Web Application on port 8080...")
          with socketserver.TCPServer(("", 8080), WebHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
  labels:
    app: web-app
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080
    name: http
---
# Background worker with high resource usage
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor
  labels:
    app: data-processor
    tier: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-processor
  template:
    metadata:
      labels:
        app: data-processor
        tier: worker
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: processor
        image: python:3.11-alpine
        ports:
        - containerPort: 9090
          name: metrics
        # ISSUE: May need resource adjustment based on workload
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        env:
        - name: BATCH_SIZE
          value: "1000"
        - name: PROCESSING_INTERVAL
          value: "30"
        command:
        - python3
        - -c
        - |
          import time
          import random
          import threading
          import http.server
          import socketserver
          import json
          import psutil
          import gc
          
          # Data processing simulation
          processed_jobs = 0
          failed_jobs = 0
          current_job_size = 0
          processing_active = False
          
          def process_batch_job():
              global processed_jobs, failed_jobs, current_job_size, processing_active
              
              while True:
                  try:
                      processing_active = True
                      job_size = random.randint(500, 2000)
                      current_job_size = job_size
                      
                      print(f"Processing batch job of size {job_size}")
                      
                      # CPU intensive processing
                      data = []
                      for i in range(job_size):
                          # Simulate data processing
                          value = sum(j**2 for j in range(100))
                          data.append({
                              'id': i,
                              'result': value,
                              'timestamp': time.time(),
                              'random_data': [random.random() for _ in range(50)]
                          })
                      
                      # Memory intensive operation
                      processed_data = []
                      for item in data:
                          processed_item = {
                              **item,
                              'processed': True,
                              'extra_field': 'x' * 1024  # 1KB per item
                          }
                          processed_data.append(processed_item)
                      
                      # Simulate processing time
                      time.sleep(random.uniform(10, 30))
                      
                      # Cleanup
                      del data
                      del processed_data
                      gc.collect()
                      
                      processed_jobs += 1
                      current_job_size = 0
                      processing_active = False
                      
                      print(f"Completed job. Total processed: {processed_jobs}")
                      
                  except Exception as e:
                      print(f"Job failed: {e}")
                      failed_jobs += 1
                      processing_active = False
                      current_job_size = 0
                  
                  # Wait before next job
                  time.sleep(random.uniform(5, 15))
          
          # Start background processing
          threading.Thread(target=process_batch_job, daemon=True).start()
          
          class ProcessorHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Data processor healthy')
                  
                  elif self.path == '/metrics':
                      process = psutil.Process()
                      memory_info = process.memory_info()
                      cpu_percent = process.cpu_percent()
                      
                      metrics_text = f'''# HELP jobs_processed_total Total processed jobs
          # TYPE jobs_processed_total counter
          jobs_processed_total {processed_jobs}
          
          # HELP jobs_failed_total Total failed jobs
          # TYPE jobs_failed_total counter
          jobs_failed_total {failed_jobs}
          
          # HELP current_job_size Current job size being processed
          # TYPE current_job_size gauge
          current_job_size {current_job_size}
          
          # HELP processing_active Whether processing is active
          # TYPE processing_active gauge
          processing_active {1 if processing_active else 0}
          
          # HELP memory_usage_bytes Memory usage in bytes
          # TYPE memory_usage_bytes gauge
          memory_usage_bytes {memory_info.rss}
          
          # HELP cpu_usage_percent CPU usage percentage
          # TYPE cpu_usage_percent gauge
          cpu_usage_percent {cpu_percent}
          '''
                      
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(metrics_text.encode())
                  
                  else:
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {
                          'service': 'data-processor',
                          'processed_jobs': processed_jobs,
                          'failed_jobs': failed_jobs,
                          'current_job_size': current_job_size,
                          'processing_active': processing_active
                      }
                      self.wfile.write(json.dumps(response).encode())
          
          print("Starting Data Processor metrics server on port 9090...")
          with socketserver.TCPServer(("", 9090), ProcessorHandler) as httpd:
              httpd.serve_forever()
---
# Redis cache with memory constraints
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
  labels:
    app: redis-cache
    tier: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-cache
  template:
    metadata:
      labels:
        app: redis-cache
        tier: cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        # ISSUE: Memory limits may be too restrictive
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"  # May be too low for cache workload
        command:
        - redis-server
        - --maxmemory
        - "200mb"
        - --maxmemory-policy
        - "allkeys-lru"
        - --save
        - ""  # Disable persistence for cache
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 15
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cache-service
spec:
  selector:
    app: redis-cache
  ports:
  - port: 6379
    targetPort: 6379
---
# Database with reporting workload
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-db
  labels:
    app: postgres-db
    tier: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-db
  template:
    metadata:
      labels:
        app: postgres-db
        tier: database
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        ports:
        - containerPort: 5432
        # ISSUE: Resources may not be sufficient for workload
        resources:
          requests:
            cpu: "200m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        env:
        - name: POSTGRES_DB
          value: "monitoring_db"
        - name: POSTGRES_USER
          value: "monitoring_user"
        - name: POSTGRES_PASSWORD
          value: "monitoring_pass"
        - name: POSTGRES_SHARED_PRELOAD_LIBRARIES
          value: "pg_stat_statements"
        - name: POSTGRES_MAX_CONNECTIONS
          value: "100"
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - monitoring_user
            - -d
            - monitoring_db
          initialDelaySeconds: 15
          periodSeconds: 5
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - monitoring_user
            - -d
            - monitoring_db
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: postgres-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-db-service
spec:
  selector:
    app: postgres-db
  ports:
  - port: 5432
    targetPort: 5432
---
# Load generator to create resource pressure
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  labels:
    app: load-generator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: load-generator
  template:
    metadata:
      labels:
        app: load-generator
    spec:
      containers:
      - name: load-generator
        image: busybox:1.35
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
        command:
        - sh
        - -c
        - |
          echo "Starting load generator..."
          
          while true; do
            echo "=== Load Generation Cycle: $(date) ==="
            
            # Test web application
            echo "Testing web application..."
            for i in $(seq 1 10); do
              {
                wget -q -O- http://web-app-service/api/data?complexity=$((RANDOM % 15 + 1)) >/dev/null 2>&1 || echo "Request failed"
              } &
            done
            
            # Wait for requests to complete
            wait
            
            echo "Load generation cycle completed"
            sleep $(( RANDOM % 30 + 30 ))  # Wait 30-60 seconds
          done
EOF

kubectl apply -f resource-monitoring-apps.yaml
```

---

## Your Mission

### Task 1: Establish Resource Monitoring Baseline (8 minutes)

Set up monitoring to understand current resource usage patterns:

```bash
# TODO: Analyze current resource usage across all applications
# Use kubectl top, describe commands, and application metrics
```

**Monitoring Tasks**:
1. Check current CPU and memory usage for all pods
2. Identify resource requests vs actual usage
3. Look for resource pressure indicators
4. Monitor application-specific metrics

**Questions to answer**:
- Which applications are using the most CPU/memory?
- Are any applications hitting resource limits?
- What is the variance in resource usage over time?

### Task 2: Identify Resource Bottlenecks (7 minutes)

Analyze the system for resource constraints and performance issues:

```bash
# TODO: Identify specific resource bottlenecks
# Look for OOM kills, CPU throttling, and resource starvation
```

**Investigation Areas**:
1. Pod evictions and OOM kills
2. CPU throttling events
3. Memory pressure on nodes
4. Resource allocation inefficiencies

**Questions to answer**:
- Are any pods being killed due to resource constraints?
- Which services are experiencing performance degradation?
- How is resource usage distributed across nodes?

### Task 3: Implement Resource Monitoring Tools (8 minutes)

Deploy monitoring tools to get better visibility into resource usage:

```bash
# TODO: Set up monitoring infrastructure
# Deploy metrics collection and visualization tools
```

**Monitoring Tools to Deploy**:
1. Metrics server (if not available)
2. Custom monitoring dashboard
3. Resource usage collection scripts
4. Application metrics aggregation

**Requirements**:
- Real-time resource usage monitoring
- Historical usage tracking
- Alert capability for resource issues
- Application-level metrics collection

### Task 4: Optimize Resource Allocation (8 minutes)

Based on monitoring data, optimize resource requests and limits:

```yaml
# TODO: Adjust resource requests and limits based on observed usage
# Consider:
# - Right-sizing based on actual usage
# - Quality of Service classes
# - Resource guarantees vs limits
```

**Optimization Tasks**:
1. Adjust resource requests to match actual usage
2. Set appropriate resource limits to prevent resource hogging
3. Implement resource quotas if needed
4. Configure appropriate QoS classes

**Questions to consider**:
- Which applications need more/less resources?
- How can you balance resource efficiency with performance?
- What safety margins should be maintained?

### Task 5: Validate and Monitor Improvements (4 minutes)

Test the optimized configuration and monitor for improvements:

```bash
# TODO: Validate resource optimizations
# Monitor performance improvements and resource efficiency
```

**Validation Steps**:
1. Deploy optimized configurations
2. Run load tests to verify performance
3. Monitor resource utilization patterns
4. Check for any new issues or regressions

---

## Monitoring Tools and Scripts

### Resource Monitoring Dashboard

```bash
# Create a comprehensive resource monitoring script
cat << 'EOF' > resource-monitoring-dashboard.sh
#!/bin/bash

echo "=== Kubernetes Resource Monitoring Dashboard ==="

# Function to display resource usage
display_resource_usage() {
    echo "========================================================"
    echo "Resource Usage Dashboard - $(date)"
    echo "========================================================"
    
    echo -e "\n📊 NODE RESOURCE USAGE"
    echo "--------------------------------------------------------"
    kubectl top nodes 2>/dev/null || echo "Node metrics not available"
    
    echo -e "\n🔧 POD RESOURCE USAGE"
    echo "--------------------------------------------------------"
    kubectl top pods --all-namespaces 2>/dev/null || echo "Pod metrics not available"
    
    echo -e "\n📈 RESOURCE REQUESTS vs LIMITS"
    echo "--------------------------------------------------------"
    kubectl describe nodes | grep -A 20 "Allocated resources" | head -40
    
    echo -e "\n⚠️  RESOURCE PRESSURE EVENTS"
    echo "--------------------------------------------------------"
    kubectl get events --all-namespaces | grep -i -E "oom|evict|insuffic|pressu" | tail -10
    
    echo -e "\n🎯 APPLICATION METRICS"
    echo "--------------------------------------------------------"
    echo "Web App Service Metrics:"
    kubectl exec -n resource-monitoring deployment/web-app -- wget -q -O- http://localhost:8080/metrics | head -20 2>/dev/null || echo "Metrics not available"
    
    echo -e "\n💾 STORAGE USAGE"
    echo "--------------------------------------------------------"
    kubectl get pv,pvc --all-namespaces 2>/dev/null || echo "No persistent volumes"
    
    echo "========================================================"
}

# Check if running in interactive mode
if [ "$1" = "--watch" ]; then
    while true; do
        clear
        display_resource_usage
        echo -e "\nPress Ctrl+C to exit..."
        sleep 10
    done
else
    display_resource_usage
fi
EOF

chmod +x resource-monitoring-dashboard.sh
```

### Resource Analysis Script

```bash
# Create resource analysis script
cat << 'EOF' > resource-analysis.sh
#!/bin/bash

echo "=== Resource Usage Analysis ==="

# Function to analyze resource efficiency
analyze_resource_efficiency() {
    echo "--- Resource Efficiency Analysis ---"
    
    echo "Pods with high resource requests but low usage:"
    kubectl top pods --all-namespaces 2>/dev/null | awk 'NR>1 {
        split($3, cpu, "m"); split($4, mem, "Mi");
        if (cpu[1] < 50 && mem[1] < 100) 
            print $1, $2, "Low usage - CPU:", $3, "Memory:", $4
    }'
    
    echo -e "\nPods potentially hitting resource limits:"
    for pod in $(kubectl get pods -o jsonpath='{.items[*].metadata.name}'); do
        requests=$(kubectl describe pod $pod | grep -A 5 "Requests" | grep -E "cpu|memory")
        limits=$(kubectl describe pod $pod | grep -A 5 "Limits" | grep -E "cpu|memory")
        echo "Pod: $pod"
        echo "  Requests: $requests"
        echo "  Limits: $limits"
        echo ""
    done
}

# Function to check for resource problems
check_resource_problems() {
    echo "--- Resource Problem Detection ---"
    
    echo "Recent OOM kills:"
    kubectl get events --all-namespaces | grep -i "oom" | tail -5
    
    echo -e "\nPods in resource pressure:"
    kubectl describe nodes | grep -A 10 -B 10 "pressure" || echo "No pressure detected"
    
    echo -e "\nFailed pod deployments due to resources:"
    kubectl get events --all-namespaces | grep -i "insuffic" | tail -5
}

# Function to suggest optimizations
suggest_optimizations() {
    echo "--- Optimization Suggestions ---"
    
    # Analyze current vs requested resources
    echo "Resource optimization opportunities:"
    
    kubectl top pods 2>/dev/null | awk 'NR>1 {
        split($2, cpu, "m"); split($3, mem, "Mi");
        cpu_val = cpu[1]; mem_val = mem[1];
        
        if (cpu_val < 10) print "Consider reducing CPU request for", $1;
        if (mem_val < 50) print "Consider reducing memory request for", $1;
        if (cpu_val > 400) print "Consider increasing CPU limit for", $1;
        if (mem_val > 800) print "Consider increasing memory limit for", $1;
    }'
}

# Run analysis
analyze_resource_efficiency
check_resource_problems
suggest_optimizations
EOF

chmod +x resource-analysis.sh
```

### Load Testing Script

```bash
# Create load testing script for resource monitoring
cat << 'EOF' > load-test-resources.sh
#!/bin/bash

echo "=== Resource Load Testing ==="

# Function to generate application load
generate_app_load() {
    local duration=${1:-60}
    echo "Generating application load for $duration seconds..."
    
    # Generate concurrent requests to web app
    for i in $(seq 1 20); do
        {
            for j in $(seq 1 10); do
                kubectl exec -n resource-monitoring deployment/load-generator -- \
                    wget -q -O- http://web-app-service/api/data?complexity=10 >/dev/null 2>&1
                sleep 1
            done
        } &
    done
    
    echo "Load generation started with 20 concurrent workers"
    echo "Monitoring resource usage during load..."
    
    # Monitor resources during load
    for i in $(seq 1 $((duration/10))); do
        echo "=== Load Test Status - $(date) ==="
        kubectl top pods -n resource-monitoring 2>/dev/null || echo "Metrics not available"
        sleep 10
    done
    
    # Stop load generation
    kubectl exec -n resource-monitoring deployment/load-generator -- pkill wget 2>/dev/null || true
    echo "Load test completed"
}

# Function to test resource limits
test_resource_limits() {
    echo "--- Testing Resource Limits ---"
    
    # Create a pod that will hit CPU limits
    kubectl run cpu-stress --image=busybox:1.35 --rm -it --restart=Never \
        --requests='cpu=100m,memory=64Mi' \
        --limits='cpu=200m,memory=128Mi' \
        -- sh -c 'while true; do :; done' &
    
    local stress_pid=$!
    sleep 30
    
    echo "CPU stress test running, checking resource usage:"
    kubectl top pod cpu-stress 2>/dev/null || echo "Metrics not available"
    
    # Clean up
    kill $stress_pid 2>/dev/null || true
    kubectl delete pod cpu-stress --force --grace-period=0 2>/dev/null || true
}

# Run load tests
generate_app_load 60
test_resource_limits
EOF

chmod +x load-test-resources.sh
```

---

## Expected Issues to Discover

### Common Resource Problems:

1. **Over-provisioned Resources**: Web app may have too high resource requests
2. **Under-provisioned Resources**: Redis cache may hit memory limits
3. **Resource Imbalance**: Background workers may need more CPU during processing
4. **Missing Resource Limits**: Some applications may not have appropriate limits
5. **Inefficient Resource Distribution**: Uneven resource allocation across nodes

### Monitoring Insights to Gather:

1. **Peak vs Average Usage**: Understanding usage patterns
2. **Resource Utilization Trends**: Identifying growth patterns
3. **Performance Correlation**: Linking resource usage to application performance
4. **Scaling Triggers**: Determining when to scale applications

---

## Solution Guidelines

### Expected Resource Optimizations:

1. **Web Application**:
```yaml
resources:
  requests:
    cpu: "50m"      # Reduced from 100m
    memory: "96Mi"  # Reduced from 128Mi
  limits:
    cpu: "300m"     # Increased from 200m
    memory: "256Mi" # Unchanged
```

2. **Data Processor**:
```yaml
resources:
  requests:
    cpu: "300m"     # Increased from 200m
    memory: "384Mi" # Increased from 256Mi
  limits:
    cpu: "800m"     # Increased from 500m
    memory: "768Mi" # Increased from 512Mi
```

3. **Redis Cache**:
```yaml
resources:
  requests:
    cpu: "100m"     # Unchanged
    memory: "256Mi" # Increased from 128Mi
  limits:
    cpu: "200m"     # Unchanged
    memory: "512Mi" # Increased from 256Mi
```

### Monitoring Implementation:

```bash
# Apply resource optimizations
kubectl patch deployment web-app -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "web-server",
          "resources": {
            "requests": {"cpu": "50m", "memory": "96Mi"},
            "limits": {"cpu": "300m", "memory": "256Mi"}
          }
        }]
      }
    }
  }
}'

# Enable HPA for web application
kubectl autoscale deployment web-app --cpu-percent=70 --min=2 --max=10

# Create resource quotas
kubectl create quota compute-quota \
  --hard=requests.cpu=2,requests.memory=4Gi,limits.cpu=4,limits.memory=8Gi
```

---

## Success Criteria

✅ **Comprehensive resource monitoring is in place**  
✅ **Resource bottlenecks are identified and documented**  
✅ **Resource requests and limits are optimized based on actual usage**  
✅ **Application performance is maintained or improved**  
✅ **Resource utilization efficiency is increased**  
✅ **Monitoring tools provide actionable insights**  
✅ **Resource scaling triggers are properly configured**

---

## Advanced Monitoring (Optional)

If you complete the basic scenario, try these advanced monitoring techniques:

1. **Custom Metrics**: Implement application-specific metrics collection
2. **Prometheus Integration**: Set up Prometheus scraping for all applications
3. **Grafana Dashboard**: Create visual dashboards for resource monitoring
4. **Alerting Rules**: Configure alerts for resource threshold breaches
5. **Cost Analysis**: Calculate resource costs and optimization savings

---

## Cleanup

```bash
# Stop monitoring scripts
pkill -f "resource-monitoring" 2>/dev/null || true

# Delete applications
kubectl delete -f resource-monitoring-apps.yaml

# Delete namespace
kubectl delete namespace resource-monitoring

# Clean up scripts
rm -f resource-monitoring-apps.yaml
rm -f resource-monitoring-dashboard.sh resource-analysis.sh load-test-resources.sh

# Reset context
kubectl config set-context --current --namespace=default
```

---

## Learning Outcomes

After completing this scenario, you should understand:

- How to establish comprehensive resource monitoring for Kubernetes applications
- Techniques for identifying resource bottlenecks and performance issues
- Methods for optimizing resource requests and limits based on actual usage
- The relationship between resource allocation and application performance
- How to implement monitoring tools that provide actionable insights
- Best practices for resource efficiency and cost optimization
- The importance of continuous monitoring and adjustment of resource allocations