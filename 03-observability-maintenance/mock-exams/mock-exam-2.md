# Mock Exam 2: Advanced Observability & Maintenance

**Time Limit**: 50 minutes  
**Total Questions**: 6 questions  
**Passing Score**: 75% (4.5 out of 6 questions correct)  
**Difficulty**: Advanced CKAD Level

---

## Instructions

- You have 50 minutes to complete all 6 questions
- Questions have varying point values based on complexity
- You may use `kubectl` documentation during the exam
- Create all resources in the specified namespaces
- Verify your solutions work as expected
- Some questions build on previous questions

---

## Question 1: Complex Multi-Service Debugging (20 points)

**Time**: 12 minutes

You have inherited a microservices application that is experiencing multiple issues. The system consists of:
- Frontend service (web interface)
- API Gateway (routes requests) 
- User Service (manages users)
- Product Service (manages products)
- Database (PostgreSQL)

**Current Issues**:
- Users cannot log in
- Product listings are empty
- API Gateway returns 503 errors
- Some services keep restarting

**Setup**:
```bash
kubectl create namespace complex-debug

# Deploy the problematic system
kubectl apply -f - << EOF
# Database - Working correctly
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: complex-debug
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        env:
        - name: POSTGRES_DB
          value: "microservices"
        - name: POSTGRES_USER
          value: "dbuser"
        - name: POSTGRES_PASSWORD
          value: "dbpass"
        ports:
        - containerPort: 5432
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "dbuser", "-d", "microservices"]
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: database-service
  namespace: complex-debug
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
---
# User Service - Has configuration issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: complex-debug
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:wrongpass@database-service:5432/microservices"  # Wrong password
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
        # Missing health checks
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import psycopg2
          import os
          from urllib.parse import urlparse
          
          class UserHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      try:
                          # This will fail due to wrong password
                          db_url = os.environ.get('DATABASE_URL')
                          parsed = urlparse(db_url)
                          conn = psycopg2.connect(
                              host=parsed.hostname,
                              port=parsed.port,
                              database=parsed.path[1:],
                              user=parsed.username,
                              password=parsed.password
                          )
                          conn.close()
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'User service healthy')
                      except Exception as e:
                          print(f"Health check failed: {e}")
                          self.send_response(503)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(f'User service unhealthy: {str(e)}'.encode())
                  
                  elif self.path == '/users':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      users = [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]
                      self.wfile.write(json.dumps(users).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting User Service on port 8080...")
          with socketserver.TCPServer(("", 8080), UserHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: complex-debug
spec:
  selector:
    app: user-service
  ports:
  - port: 8080
    targetPort: 8080
---
# Product Service - Has resource and health issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
  namespace: complex-debug
spec:
  replicas: 1
  selector:
    matchLabels:
      app: product-service
  template:
    metadata:
      labels:
        app: product-service
    spec:
      containers:
      - name: product-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:dbpass@database-service:5432/microservices"
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"  # Too low
          limits:
            cpu: "100m"
            memory: "64Mi"  # Too low, will cause OOM
        # Aggressive liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 3
          timeoutSeconds: 1
          failureThreshold: 1  # Too aggressive
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import threading
          
          # Simulate memory-intensive product loading
          products_cache = []
          
          def load_products():
              global products_cache
              print("Loading products into memory...")
              # This will cause OOM with current limits
              for i in range(10000):
                  product = {
                      'id': i,
                      'name': f'Product {i}',
                      'description': 'x' * 1000,  # 1KB per product
                      'metadata': ['data'] * 100
                  }
                  products_cache.append(product)
              print(f"Loaded {len(products_cache)} products")
          
          # Start loading products in background
          threading.Thread(target=load_products, daemon=True).start()
          
          class ProductHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      # Slow health check that times out
                      time.sleep(2)  # Exceeds liveness probe timeout
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Product service healthy')
                  
                  elif self.path == '/products':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      # Return first 10 products
                      sample_products = products_cache[:10] if products_cache else []
                      self.wfile.write(json.dumps(sample_products).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Product Service on port 8080...")
          time.sleep(10)  # Startup delay
          with socketserver.TCPServer(("", 8080), ProductHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: product-service
  namespace: complex-debug
spec:
  selector:
    app: product-service
  ports:
  - port: 8080
    targetPort: 8080
---
# API Gateway - Service discovery issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: complex-debug
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: gateway
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
        lifecycle:
          postStart:
            exec:
              command:
              - sh
              - -c
              - |
                cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF'
                upstream user_service {
                    server user-api:8080;  # Wrong service name
                }
                upstream product_service {
                    server product-service:8080;
                }
                
                server {
                    listen 80;
                    
                    location /health {
                        return 200 "API Gateway healthy\n";
                        add_header Content-Type text/plain;
                    }
                    
                    # Check backend health
                    location /status {
                        proxy_pass http://user_service/health;
                        proxy_connect_timeout 2s;
                        proxy_read_timeout 2s;
                    }
                    
                    location /api/users/ {
                        proxy_pass http://user_service/;
                        proxy_set_header Host $host;
                    }
                    
                    location /api/products/ {
                        proxy_pass http://product_service/;
                        proxy_set_header Host $host;
                    }
                    
                    location / {
                        return 200 "API Gateway - Routes: /api/users/, /api/products/\n";
                        add_header Content-Type text/plain;
                    }
                }
                NGINX_EOF
                nginx -s reload
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: complex-debug
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
---
# Frontend - Depends on API Gateway
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: complex-debug
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Frontend service starting..."
          while true; do
            echo "=== Frontend Health Check: $(date) ==="
            echo "Testing API Gateway..."
            wget -q -O- http://api-gateway-service/health || echo "API Gateway unreachable"
            
            echo "Testing user service via gateway..."
            wget -q -O- http://api-gateway-service/api/users/ || echo "User service via gateway failed"
            
            echo "Testing product service via gateway..."
            wget -q -O- http://api-gateway-service/api/products/ || echo "Product service via gateway failed"
            
            sleep 30
          done
EOF
```

**Tasks** (20 points total):

1. **System Analysis** (4 points): Identify all issues in the system by examining pods, services, logs, and events
2. **Database Connectivity Fix** (4 points): Fix the user service database connection issue
3. **Resource Optimization** (4 points): Fix the product service memory issues and optimize resources
4. **Health Check Optimization** (4 points): Fix the aggressive liveness probe in product service
5. **Service Discovery Fix** (4 points): Fix the API Gateway service discovery issues

**Acceptance Criteria**:
- All pods are running and ready
- API Gateway can route to all backend services
- No OOM kills or restart loops
- All services pass health checks
- Frontend logs show successful connectivity to all services

---

## Question 2: Advanced Performance Monitoring (18 points)

**Time**: 10 minutes

Create a comprehensive performance monitoring setup for a high-traffic application.

**Requirements**:
Deploy in namespace `perf-monitoring` an application that:

1. **Application with Metrics** (6 points):
   - Exposes Prometheus metrics on `/metrics`
   - Includes custom business metrics (requests, errors, response time)
   - Has configurable resource limits based on load

2. **Resource Monitoring** (6 points):
   - Configure HPA based on CPU and memory
   - Set up resource quotas for the namespace
   - Implement resource requests that scale with replicas

3. **Health Monitoring** (6 points):
   - Multiple health endpoints for different purposes
   - Startup probe for slow initialization
   - Dependency health checking

**Base Application Template**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-traffic-app
  namespace: perf-monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: high-traffic-app
  template:
    metadata:
      labels:
        app: high-traffic-app
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        # TODO: Add comprehensive resource configuration
        # TODO: Add comprehensive health checks
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
          
          # Metrics storage
          metrics = {
              'requests_total': 0,
              'errors_total': 0,
              'response_times': [],
              'active_connections': 0
          }
          
          # Simulate startup time
          startup_complete = False
          
          def initialize_app():
              global startup_complete
              print("Starting application initialization...")
              time.sleep(20)  # 20 second startup
              startup_complete = True
              print("Application initialization complete")
          
          threading.Thread(target=initialize_app, daemon=True).start()
          
          class AppHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  global metrics
                  start_time = time.time()
                  metrics['active_connections'] += 1
                  
                  try:
                      if self.path == '/health':
                          if startup_complete:
                              self.send_response(200)
                              self.send_header('Content-type', 'application/json')
                              self.end_headers()
                              health_data = {
                                  'status': 'healthy',
                                  'uptime': time.time(),
                                  'startup_complete': startup_complete
                              }
                              self.wfile.write(json.dumps(health_data).encode())
                          else:
                              self.send_response(503)
                              self.send_header('Content-type', 'text/plain')
                              self.end_headers()
                              self.wfile.write(b'Application starting up...')
                      
                      elif self.path == '/ready':
                          if startup_complete:
                              self.send_response(200)
                              self.send_header('Content-type', 'text/plain')
                              self.end_headers()
                              self.wfile.write(b'Ready')
                          else:
                              self.send_response(503)
                              self.send_header('Content-type', 'text/plain')
                              self.end_headers()
                              self.wfile.write(b'Not ready')
                      
                      elif self.path == '/metrics':
                          process = psutil.Process()
                          memory_info = process.memory_info()
                          cpu_percent = process.cpu_percent()
                          
                          avg_response_time = sum(metrics['response_times'][-1000:]) / max(len(metrics['response_times'][-1000:]), 1)
                          
                          metrics_text = f'''# HELP http_requests_total Total HTTP requests
          # TYPE http_requests_total counter
          http_requests_total {metrics['requests_total']}
          
          # HELP http_errors_total Total HTTP errors
          # TYPE http_errors_total counter
          http_errors_total {metrics['errors_total']}
          
          # HELP http_request_duration_seconds Average response time
          # TYPE http_request_duration_seconds gauge
          http_request_duration_seconds {avg_response_time}
          
          # HELP active_connections Current active connections
          # TYPE active_connections gauge
          active_connections {metrics['active_connections']}
          
          # HELP memory_usage_bytes Memory usage
          # TYPE memory_usage_bytes gauge
          memory_usage_bytes {memory_info.rss}
          
          # HELP cpu_usage_percent CPU usage
          # TYPE cpu_usage_percent gauge
          cpu_usage_percent {cpu_percent}
          '''
                          
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(metrics_text.encode())
                      
                      elif self.path.startswith('/api/'):
                          # Simulate API work with variable response time
                          work_time = random.uniform(0.1, 2.0)
                          time.sleep(work_time)
                          
                          # 5% error rate
                          if random.random() < 0.05:
                              metrics['errors_total'] += 1
                              self.send_response(500)
                              self.send_header('Content-type', 'application/json')
                              self.end_headers()
                              self.wfile.write(json.dumps({'error': 'Internal server error'}).encode())
                          else:
                              self.send_response(200)
                              self.send_header('Content-type', 'application/json')
                              self.end_headers()
                              self.wfile.write(json.dumps({'message': 'API response', 'processing_time': work_time}).encode())
                      
                      else:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/html')
                          self.end_headers()
                          html = f'''
                          <h1>High Traffic Application</h1>
                          <p>Requests: {metrics['requests_total']}</p>
                          <p>Errors: {metrics['errors_total']}</p>
                          <p>Active Connections: {metrics['active_connections']}</p>
                          <a href="/api/test">Test API</a> | <a href="/metrics">Metrics</a>
                          '''
                          self.wfile.write(html.encode())
                      
                      metrics['requests_total'] += 1
                      
                  except Exception as e:
                      metrics['errors_total'] += 1
                      self.send_response(500)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(f'Error: {str(e)}'.encode())
                  
                  finally:
                      response_time = time.time() - start_time
                      metrics['response_times'].append(response_time)
                      metrics['active_connections'] -= 1
          
          print("Starting High Traffic Application on port 8080...")
          with socketserver.TCPServer(("", 8080), AppHandler) as httpd:
              httpd.serve_forever()
```

**Deliverables**:
1. Complete deployment with optimized resource configuration
2. HPA configuration targeting 70% CPU and 80% memory
3. Resource quota limiting namespace to 4 CPU cores and 8Gi memory
4. Service exposing both application and metrics ports
5. Comprehensive health checks for all scenarios

---

## Question 3: Log Analysis and Troubleshooting (16 points)

**Time**: 8 minutes

You have a complex application with multiple components that is generating errors. Use log analysis to identify and fix issues.

**Setup**:
```bash
kubectl create namespace log-analysis

# Deploy application with logging issues
kubectl apply -f - << EOF
# Application with multiple log sources
apiVersion: v1
kind: Pod
metadata:
  name: complex-app
  namespace: log-analysis
spec:
  containers:
  # Main application container
  - name: main-app
    image: python:3.11-alpine
    command:
    - python3
    - -c
    - |
      import logging
      import time
      import random
      import json
      import sys
      
      # Configure logging
      logging.basicConfig(
          level=logging.INFO,
          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )
      
      logger = logging.getLogger('main-app')
      
      # Application state
      errors_count = 0
      
      logger.info("Main application starting...")
      
      while True:
          try:
              # Simulate different operations
              operation = random.choice(['user_login', 'data_process', 'api_call', 'database_query'])
              
              if operation == 'user_login':
                  user_id = random.randint(1, 1000)
                  if random.random() < 0.1:  # 10% login failures
                      logger.error(f"Login failed for user {user_id}: Invalid credentials")
                      errors_count += 1
                  else:
                      logger.info(f"User {user_id} logged in successfully")
              
              elif operation == 'data_process':
                  batch_size = random.randint(100, 1000)
                  processing_time = random.uniform(1, 5)
                  
                  if random.random() < 0.05:  # 5% processing failures
                      logger.error(f"Data processing failed for batch size {batch_size}: Memory allocation error")
                      errors_count += 1
                  else:
                      logger.info(f"Processed {batch_size} records in {processing_time:.2f}s")
              
              elif operation == 'api_call':
                  endpoint = random.choice(['/users', '/products', '/orders'])
                  response_time = random.uniform(0.1, 3.0)
                  
                  if random.random() < 0.15:  # 15% API failures
                      error_code = random.choice([500, 503, 504])
                      logger.error(f"API call to {endpoint} failed: HTTP {error_code}")
                      errors_count += 1
                  else:
                      logger.info(f"API call to {endpoint} completed in {response_time:.2f}s")
              
              elif operation == 'database_query':
                  query_type = random.choice(['SELECT', 'INSERT', 'UPDATE'])
                  
                  if random.random() < 0.08:  # 8% database failures
                      logger.error(f"Database {query_type} failed: Connection timeout")
                      errors_count += 1
                  else:
                      logger.info(f"Database {query_type} executed successfully")
              
              # Log periodic stats
              if random.random() < 0.1:
                  logger.info(f"Application stats - Total errors: {errors_count}")
              
              time.sleep(random.uniform(1, 3))
              
          except Exception as e:
              logger.error(f"Unexpected error: {str(e)}")
              errors_count += 1
              time.sleep(5)
  
  # Sidecar logging container
  - name: log-processor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Log processor starting..."
      
      while true; do
        echo "[LOG-PROCESSOR] $(date): Processing application logs..."
        
        # Simulate log processing
        if [ $((RANDOM % 10)) -eq 0 ]; then
          echo "[LOG-PROCESSOR] ERROR: Log processing queue full"
        else
          echo "[LOG-PROCESSOR] INFO: Processed logs successfully"
        fi
        
        sleep 10
      done
  
  # Metrics collector container
  - name: metrics-collector
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Metrics collector starting..."
      
      counter=0
      while true; do
        counter=$((counter + 1))
        
        echo "[METRICS] $(date): Collecting metrics batch $counter"
        
        # Simulate metrics collection issues
        if [ $((counter % 20)) -eq 0 ]; then
          echo "[METRICS] ERROR: Failed to connect to metrics endpoint"
        elif [ $((counter % 15)) -eq 0 ]; then
          echo "[METRICS] WARN: High memory usage detected"
        else
          echo "[METRICS] INFO: Metrics collected successfully"
        fi
        
        sleep 5
      done
  
  # Init container that may have issues
  initContainers:
  - name: init-setup
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Init container starting setup..."
      
      # Simulate setup tasks
      echo "Checking configuration..."
      sleep 5
      
      echo "Downloading dependencies..."
      sleep 10
      
      echo "Setting up database schema..."
      if [ $((RANDOM % 5)) -eq 0 ]; then
        echo "ERROR: Database schema setup failed - connection refused"
        exit 1
      fi
      
      echo "Setup completed successfully"
---
# Service to expose the application
apiVersion: v1
kind: Service
metadata:
  name: complex-app-service
  namespace: log-analysis
spec:
  selector:
    app: complex-app  # This won't match - missing app label on pod
  ports:
  - port: 8080
    targetPort: 8080
EOF
```

**Tasks** (16 points total):

1. **Log Analysis** (4 points): 
   - Analyze logs from all containers and identify error patterns
   - Count and categorize different types of errors
   - Identify the most frequent error sources

2. **Init Container Debugging** (4 points):
   - Check if init container issues are affecting pod startup
   - Fix any init container failures
   - Ensure reliable pod initialization

3. **Service Configuration Fix** (4 points):
   - Identify why the service cannot find the pod
   - Fix service selector issues
   - Verify service endpoint configuration

4. **Log Monitoring Setup** (4 points):
   - Create a monitoring solution to track error rates
   - Set up log aggregation for the multi-container pod
   - Implement error alerting based on log patterns

**Deliverables**:
- Error analysis report showing error types and frequencies
- Fixed service configuration
- Working log monitoring setup
- Documentation of troubleshooting steps taken

---

## Question 4: Resource Quota and Limits Management (14 points)

**Time**: 8 minutes

Implement comprehensive resource management for a multi-tenant environment.

**Scenario**: You need to set up resource management for three teams sharing a cluster:
- **Team A (Development)**: Needs moderate resources, can tolerate some resource pressure
- **Team B (Staging)**: Needs guaranteed resources, performance-sensitive
- **Team C (Production)**: Needs priority access and guaranteed high-quality resources

**Tasks** (14 points total):

1. **Create Resource Quotas** (5 points):
   ```bash
   # Create namespaces for three teams
   kubectl create namespace team-a-dev
   kubectl create namespace team-b-staging  
   kubectl create namespace team-c-prod
   
   # TODO: Create appropriate resource quotas for each namespace
   # Team A: 2 CPU cores, 4Gi memory, 10 pods max
   # Team B: 4 CPU cores, 8Gi memory, 20 pods max
   # Team C: 8 CPU cores, 16Gi memory, 50 pods max
   ```

2. **Configure LimitRanges** (4 points):
   ```yaml
   # TODO: Create LimitRanges for each namespace with:
   # - Default CPU/memory requests and limits
   # - Minimum and maximum resource constraints
   # - Different QoS policies per environment
   ```

3. **Deploy Test Applications** (3 points):
   Deploy applications in each namespace that test the resource constraints:
   ```yaml
   # TODO: Create deployments that:
   # - Respect the resource quotas
   # - Have appropriate QoS classes
   # - Test resource limit enforcement
   ```

4. **Validation and Testing** (2 points):
   ```bash
   # TODO: Test resource quota enforcement
   # - Try to exceed quotas
   # - Verify LimitRange defaults are applied
   # - Check QoS class assignments
   ```

**Requirements**:
- All resource quotas must be enforced
- LimitRanges should provide appropriate defaults
- Applications should have proper QoS classes
- Resource limits should prevent resource abuse

---

## Question 5: Advanced Network Debugging (16 points)

**Time**: 8 minutes

Debug a complex network issue in a microservices application.

**Setup**:
```bash
kubectl create namespace network-issues

# Deploy application with network problems
kubectl apply -f - << EOF
# Frontend service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: network-issues
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Frontend starting..."
          while true; do
            echo "=== Frontend Network Test: $(date) ==="
            
            # Test backend connectivity
            echo "Testing backend service..."
            nc -z backend-service 8080 && echo "Backend reachable" || echo "Backend unreachable"
            
            # Test API service
            echo "Testing API service..."
            nc -z api-service 9090 && echo "API reachable" || echo "API unreachable"
            
            # Test external connectivity
            echo "Testing external connectivity..."
            nc -z google.com 80 && echo "External connectivity OK" || echo "External connectivity failed"
            
            sleep 20
          done
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: network-issues
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
---
# Backend service with wrong port configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: network-issues
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: python:3.11-alpine
        ports:
        - containerPort: 7070  # Different from service port
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          
          class BackendHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  self.send_response(200)
                  self.send_header('Content-type', 'text/plain')
                  self.end_headers()
                  self.wfile.write(b'Backend service response')
          
          print("Starting backend on port 7070...")
          with socketserver.TCPServer(("", 7070), BackendHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: network-issues
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080  # Wrong target port
---
# API service with DNS issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: network-issues
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-server  # Different from service selector
  template:
    metadata:
      labels:
        app: api-service  # Different label
    spec:
      containers:
      - name: api
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: network-issues
spec:
  selector:
    app: api-service
  ports:
  - port: 9090
    targetPort: 80
---
# Network policy that blocks traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrictive-policy
  namespace: network-issues
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # Block all ingress
  egress: []   # Block all egress
EOF
```

**Tasks** (16 points total):

1. **Network Connectivity Analysis** (4 points):
   - Test and document all network connectivity issues
   - Identify service endpoint problems
   - Check DNS resolution issues

2. **Port Configuration Fix** (4 points):
   - Fix backend service port mismatch
   - Ensure services point to correct container ports
   - Verify port connectivity

3. **Service Discovery Fix** (4 points):
   - Fix API service label mismatch
   - Ensure service selectors match pod labels
   - Verify service endpoints are populated

4. **Network Policy Resolution** (4 points):
   - Identify restrictive network policies
   - Fix or remove policies blocking legitimate traffic
   - Test connectivity after policy changes

**Acceptance Criteria**:
- All services can communicate with each other
- Service endpoints show proper pod targets
- Network policies allow necessary traffic
- Frontend connectivity tests pass

---

## Question 6: Comprehensive Health and Performance Optimization (16 points)

**Time**: 8 minutes

Optimize a production application for reliability and performance.

**Current Application** (has multiple issues):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-app
  namespace: optimization
spec:
  replicas: 5
  selector:
    matchLabels:
      app: production-app
  template:
    metadata:
      labels:
        app: production-app
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        # Current configuration has issues:
        resources:
          requests:
            cpu: "1000m"    # Over-provisioned
            memory: "2Gi"   # Over-provisioned
          limits:
            cpu: "2000m"    # Too high
            memory: "4Gi"   # Too high
        # Problematic health checks:
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5   # Too short
          periodSeconds: 5         # Too frequent
          timeoutSeconds: 1        # Too short
          failureThreshold: 1      # Too aggressive
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 1
          failureThreshold: 1
        # Missing startup probe for slow app
        env:
        - name: APP_MODE
          value: "production"
        - name: WORKERS
          value: "4"
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import time
          import threading
          import random
          import json
          
          # Simulate slow application startup
          startup_time = 60  # 60 seconds to start
          startup_complete = False
          health_check_count = 0
          
          def startup_sequence():
              global startup_complete
              print("Starting application initialization...")
              time.sleep(startup_time)
              startup_complete = True
              print("Application startup complete")
          
          threading.Thread(target=startup_sequence, daemon=True).start()
          
          class AppHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  global health_check_count
                  
                  if self.path == '/health':
                      health_check_count += 1
                      
                      # Simulate slow health checks occasionally
                      if random.random() < 0.1:
                          time.sleep(3)  # Sometimes slow
                      
                      if startup_complete:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'healthy',
                              'startup_complete': True,
                              'health_checks': health_check_count
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'starting',
                              'startup_complete': False
                          }
                          self.wfile.write(json.dumps(response).encode())
                  
                  elif self.path == '/startup':
                      # Faster startup check
                      if startup_complete:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Startup complete')
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Starting up...')
                  
                  elif self.path == '/ready':
                      # Ready check - stricter than health
                      if startup_complete and health_check_count > 5:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Ready')
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Not ready')
                  
                  else:
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {
                          'service': 'production-app',
                          'startup_complete': startup_complete,
                          'health_checks': health_check_count
                      }
                      self.wfile.write(json.dumps(response).encode())
          
          print("Starting production application on port 8080...")
          with socketserver.TCPServer(("", 8080), AppHandler) as httpd:
              httpd.serve_forever()
```

**Tasks** (16 points total):

1. **Resource Optimization** (4 points):
   - Analyze actual resource usage patterns
   - Right-size CPU and memory requests/limits
   - Implement appropriate QoS class

2. **Health Check Optimization** (6 points):
   - Add appropriate startup probe for 60-second initialization
   - Fix liveness probe timing and thresholds
   - Optimize readiness probe for proper traffic routing

3. **Scalability Configuration** (3 points):
   - Configure HPA for automatic scaling
   - Set appropriate scaling metrics and thresholds
   - Test scaling behavior

4. **Performance Monitoring** (3 points):
   - Add metrics endpoint
   - Configure monitoring annotations
   - Set up performance tracking

**Acceptance Criteria**:
- Application starts reliably without premature restarts
- Health checks are optimized for the application's behavior
- Resources are right-sized for efficiency
- Application can scale automatically based on load
- Performance metrics are available for monitoring

---

## Answer Key and Scoring

### Question 1: Complex Multi-Service Debugging (20 points)

**Issues Identified**:
1. User service has wrong database password (4 points)
2. Product service has insufficient memory limits causing OOM (4 points)  
3. Product service has aggressive liveness probe (4 points)
4. API Gateway has wrong service name for user service (4 points)
5. Multiple service configuration issues (4 points)

**Solutions**:
```bash
# Fix user service database password
kubectl patch deployment user-service -n complex-debug -p '{"spec":{"template":{"spec":{"containers":[{"name":"user-service","env":[{"name":"DATABASE_URL","value":"postgresql://dbuser:dbpass@database-service:5432/microservices"}]}]}}}}'

# Fix product service memory limits
kubectl patch deployment product-service -n complex-debug -p '{"spec":{"template":{"spec":{"containers":[{"name":"product-service","resources":{"limits":{"memory":"512Mi"},"requests":{"memory":"256Mi"}}}]}}}}'

# Fix product service liveness probe
kubectl patch deployment product-service -n complex-debug -p '{"spec":{"template":{"spec":{"containers":[{"name":"product-service","livenessProbe":{"timeoutSeconds":5,"failureThreshold":3,"periodSeconds":10}}]}}}}'

# Fix API Gateway upstream name
kubectl exec -n complex-debug deployment/api-gateway -- sed -i 's/user-api:8080/user-service:8080/' /etc/nginx/conf.d/default.conf
kubectl exec -n complex-debug deployment/api-gateway -- nginx -s reload
```

### Question 2: Advanced Performance Monitoring (18 points)

**Complete Solution**:
```bash
kubectl create namespace perf-monitoring

# Resource quota (6 points)
kubectl apply -f - << EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: perf-monitoring
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
EOF

# HPA configuration (6 points)
kubectl apply -f - << EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: high-traffic-app-hpa
  namespace: perf-monitoring
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: high-traffic-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

# Optimized deployment with health checks (6 points)
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-traffic-app
  namespace: perf-monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: high-traffic-app
  template:
    metadata:
      labels:
        app: high-traffic-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        startupProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 8  # 40 seconds for startup
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 25
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 2
        # [application command from template]
EOF
```

### Additional Questions Solutions Available Upon Request

**Total Exam Time**: 50 minutes  
**Total Points**: 100 points  
**Passing Score**: 75 points

This advanced exam tests comprehensive CKAD Observability & Maintenance skills including complex debugging scenarios, performance optimization, resource management, and production-ready configurations.