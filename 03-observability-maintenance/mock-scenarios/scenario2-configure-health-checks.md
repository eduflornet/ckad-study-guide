# Mock Scenario 2: Configure Health Checks

**Scenario**: You are deploying a new microservices application to production. The application consists of multiple services with different startup characteristics and dependencies. You need to implement proper health checks to ensure reliable deployments and prevent service disruptions.

**Time Limit**: 25 minutes  
**Difficulty**: Intermediate

---

## Background

Your team is deploying a new financial services application with the following components:

- **API Gateway**: Routes requests to backend services (fast startup)
- **Authentication Service**: Handles user authentication (medium startup, depends on database)
- **Payment Service**: Processes payments (slow startup, high availability requirements)
- **Notification Service**: Sends notifications (fast startup, external dependencies)
- **Database**: PostgreSQL database (slow startup, critical for other services)

Each service has different requirements for health checks based on their startup times, dependencies, and criticality.

---

## Initial Setup

Deploy the base application without health checks:

```bash
# Create namespace
kubectl create namespace fintech-app
kubectl config set-context --current --namespace=fintech-app

# Deploy the application without proper health checks
cat << EOF > fintech-base-app.yaml
# Database - Critical foundation service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  labels:
    app: database
    tier: data
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
        tier: data
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "fintech"
        - name: POSTGRES_USER
          value: "fintech_user"
        - name: POSTGRES_PASSWORD
          value: "secure_password"
        - name: POSTGRES_INITDB_ARGS
          value: "--data-checksums"
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        # TODO: Add appropriate health checks for database
        command:
        - docker-entrypoint.sh
        - postgres
        - -c
        - shared_preload_libraries=pg_stat_statements
        - -c
        - pg_stat_statements.track=all
      volumes:
      - name: postgres-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: database-service
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
---
# API Gateway - Fast startup, traffic router
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
    tier: gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        tier: gateway
    spec:
      containers:
      - name: gateway
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        # TODO: Add health checks for API gateway
        lifecycle:
          postStart:
            exec:
              command:
              - sh
              - -c
              - |
                cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF'
                upstream auth_service {
                    server auth-service:8080;
                }
                upstream payment_service {
                    server payment-service:8080;
                }
                upstream notification_service {
                    server notification-service:8080;
                }
                
                server {
                    listen 80;
                    
                    # Health check endpoint
                    location /health {
                        access_log off;
                        return 200 "API Gateway healthy\n";
                        add_header Content-Type text/plain;
                    }
                    
                    # Gateway status with dependency checks
                    location /status {
                        access_log off;
                        proxy_pass http://auth_service/health;
                        proxy_connect_timeout 2s;
                        proxy_read_timeout 2s;
                        error_page 502 503 504 = @fallback;
                    }
                    
                    location @fallback {
                        return 503 "Dependencies not ready\n";
                        add_header Content-Type text/plain;
                    }
                    
                    # Route authentication requests
                    location /api/auth/ {
                        proxy_pass http://auth_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 30s;
                    }
                    
                    # Route payment requests
                    location /api/payments/ {
                        proxy_pass http://payment_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 30s;
                    }
                    
                    # Route notification requests
                    location /api/notifications/ {
                        proxy_pass http://notification_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 30s;
                    }
                    
                    # Default route
                    location / {
                        return 200 "FinTech API Gateway - Ready\n";
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
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
---
# Authentication Service - Medium startup, database dependent
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  labels:
    app: auth-service
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
        tier: api
    spec:
      containers:
      - name: auth-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://fintech_user:secure_password@database-service:5432/fintech"
        - name: JWT_SECRET
          value: "your-secret-key"
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "300m"
            memory: "256Mi"
        # TODO: Add health checks for auth service
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import threading
          import psycopg2
          import os
          from urllib.parse import urlparse
          
          # Simulate database initialization time
          DB_READY = False
          
          def initialize_database():
              global DB_READY
              print("Initializing database connection...")
              time.sleep(20)  # Simulate database connection setup
              
              # Try to connect to database
              try:
                  db_url = os.environ.get('DATABASE_URL')
                  parsed = urlparse(db_url)
                  
                  # This will fail initially until database is ready
                  conn = psycopg2.connect(
                      host=parsed.hostname,
                      port=parsed.port,
                      database=parsed.path[1:],
                      user=parsed.username,
                      password=parsed.password
                  )
                  conn.close()
                  DB_READY = True
                  print("Database connection established")
              except Exception as e:
                  print(f"Database connection failed: {e}")
                  # Keep trying
                  threading.Timer(10, initialize_database).start()
          
          # Start database initialization in background
          threading.Thread(target=initialize_database, daemon=True).start()
          
          class AuthHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      if DB_READY:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'healthy',
                              'service': 'auth-service',
                              'database': 'connected',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'starting',
                              'service': 'auth-service',
                              'database': 'connecting',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                  
                  elif self.path == '/ready':
                      if DB_READY:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Auth service ready')
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Auth service not ready - database initializing')
                  
                  elif self.path == '/':
                      if DB_READY:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'service': 'auth-service',
                              'endpoints': ['/login', '/logout', '/verify'],
                              'status': 'operational'
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {'error': 'Service initializing'}
                          self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Auth Service on port 8080...")
          with socketserver.TCPServer(("", 8080), AuthHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - port: 8080
    targetPort: 8080
---
# Payment Service - Slow startup, high availability requirements
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  labels:
    app: payment-service
    tier: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
        tier: api
    spec:
      containers:
      - name: payment-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://fintech_user:secure_password@database-service:5432/fintech"
        - name: PAYMENT_GATEWAY_URL
          value: "https://api.stripe.com"
        - name: ENCRYPTION_KEY
          value: "payment-encryption-key"
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        # TODO: Add health checks for payment service
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import threading
          import random
          
          # Simulate complex payment service initialization
          STARTUP_COMPLETE = False
          PAYMENT_GATEWAY_READY = False
          
          def initialize_payment_service():
              global STARTUP_COMPLETE, PAYMENT_GATEWAY_READY
              
              print("Initializing payment service...")
              print("Loading encryption modules...")
              time.sleep(30)  # Encryption module loading
              
              print("Connecting to payment gateway...")
              time.sleep(20)  # Payment gateway connection
              PAYMENT_GATEWAY_READY = True
              
              print("Validating security certificates...")
              time.sleep(25)  # Security validation
              
              print("Loading fraud detection models...")
              time.sleep(15)  # ML model loading
              
              STARTUP_COMPLETE = True
              print("Payment service fully initialized")
          
          # Start initialization in background
          threading.Thread(target=initialize_payment_service, daemon=True).start()
          
          class PaymentHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      # Basic health check - should be fast
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {
                          'status': 'healthy',
                          'service': 'payment-service',
                          'timestamp': time.time()
                      }
                      self.wfile.write(json.dumps(response).encode())
                  
                  elif self.path == '/ready':
                      # Readiness check - depends on full initialization
                      if STARTUP_COMPLETE:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'ready',
                              'service': 'payment-service',
                              'payment_gateway': 'connected' if PAYMENT_GATEWAY_READY else 'connecting',
                              'fraud_detection': 'loaded',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'initializing',
                              'service': 'payment-service',
                              'payment_gateway': 'connected' if PAYMENT_GATEWAY_READY else 'connecting',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                  
                  elif self.path == '/startup':
                      # Startup health check - used during initialization
                      if PAYMENT_GATEWAY_READY:
                          self.send_response(200)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Payment gateway connected')
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Payment gateway initializing')
                  
                  elif self.path == '/':
                      if STARTUP_COMPLETE:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'service': 'payment-service',
                              'endpoints': ['/process', '/refund', '/status'],
                              'status': 'operational'
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {'error': 'Service initializing'}
                          self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Payment Service on port 8080...")
          with socketserver.TCPServer(("", 8080), PaymentHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
spec:
  selector:
    app: payment-service
  ports:
  - port: 8080
    targetPort: 8080
---
# Notification Service - Fast startup, external dependencies
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
  labels:
    app: notification-service
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: notification-service
  template:
    metadata:
      labels:
        app: notification-service
        tier: api
    spec:
      containers:
      - name: notification-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        env:
        - name: SMTP_HOST
          value: "smtp.mailgun.com"
        - name: SMTP_PORT
          value: "587"
        - name: SMS_GATEWAY_URL
          value: "https://api.twilio.com"
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        # TODO: Add health checks for notification service
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import random
          
          # Fast startup service
          print("Notification Service starting...")
          time.sleep(5)  # Quick startup
          
          class NotificationHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      # Check external dependencies
                      external_healthy = random.random() > 0.2  # 80% success rate
                      
                      if external_healthy:
                          self.send_response(200)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'healthy',
                              'service': 'notification-service',
                              'smtp': 'connected',
                              'sms_gateway': 'connected',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                      else:
                          self.send_response(503)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          response = {
                              'status': 'degraded',
                              'service': 'notification-service',
                              'smtp': 'timeout',
                              'sms_gateway': 'connected',
                              'timestamp': time.time()
                          }
                          self.wfile.write(json.dumps(response).encode())
                  
                  elif self.path == '/ready':
                      # Simple readiness check
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Notification service ready')
                  
                  elif self.path == '/' :
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {
                          'service': 'notification-service',
                          'endpoints': ['/send-email', '/send-sms', '/send-push'],
                          'status': 'operational'
                      }
                      self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Notification Service on port 8080...")
          with socketserver.TCPServer(("", 8080), NotificationHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: notification-service
spec:
  selector:
    app: notification-service
  ports:
  - port: 8080
    targetPort: 8080
EOF

kubectl apply -f fintech-base-app.yaml
```

---

## Your Mission

### Task 1: Analyze Service Requirements (5 minutes)

Study each service and determine appropriate health check strategies:

**Service Analysis**:

1. **Database**: 
   - Startup time: Slow (PostgreSQL initialization)
   - Criticality: High (foundation for other services)
   - Health check requirements: ?

2. **API Gateway**:
   - Startup time: Fast (Nginx)
   - Criticality: High (entry point)
   - Health check requirements: ?

3. **Auth Service**:
   - Startup time: Medium (database dependency)
   - Criticality: High (security)
   - Health check requirements: ?

4. **Payment Service**:
   - Startup time: Very slow (complex initialization)
   - Criticality: Critical (financial transactions)
   - Health check requirements: ?

5. **Notification Service**:
   - Startup time: Fast
   - Criticality: Medium (external dependencies)
   - Health check requirements: ?

```bash
# TODO: Observe current deployment behavior without health checks
# Note startup times, failure patterns, and service dependencies
```

### Task 2: Configure Database Health Checks (5 minutes)

Implement appropriate health checks for the PostgreSQL database:

```yaml
# TODO: Add liveness and readiness probes for database
# Consider: 
# - What command should be used to check PostgreSQL health?
# - How long does PostgreSQL take to start?
# - What are appropriate timeout and failure thresholds?
```

**Requirements**:
- Readiness probe to ensure database accepts connections
- Liveness probe to detect database failures
- Appropriate timeouts for database operations

### Task 3: Configure API Gateway Health Checks (4 minutes)

Implement health checks for the Nginx API Gateway:

```yaml
# TODO: Add health checks for API gateway
# Consider:
# - Simple health endpoint vs dependency checking
# - Fast startup means minimal delay needed
# - Gateway should check backend availability?
```

**Requirements**:
- Basic liveness probe for Nginx process
- Readiness probe for routing capability
- Consider dependency health checking

### Task 4: Configure Backend Services Health Checks (8 minutes)

Implement health checks for Auth, Payment, and Notification services:

```yaml
# TODO: Configure health checks for each backend service
# 
# Auth Service considerations:
# - Database dependency
# - Medium startup time
#
# Payment Service considerations:
# - Very slow startup (90+ seconds)
# - Multiple initialization phases
# - High availability requirements
#
# Notification Service considerations:
# - Fast startup
# - External dependency health varies
```

**Requirements**:
- Startup probes for services with long initialization
- Readiness probes that check dependencies
- Liveness probes with appropriate thresholds
- Different probe configurations based on service characteristics

### Task 5: Test and Validate Health Checks (3 minutes)

Verify that health checks work correctly:

```bash
# TODO: Test health check behavior
# - Deploy with health checks
# - Simulate failures
# - Verify proper startup sequencing
# - Check readiness during rolling updates
```

**Validation Steps**:
1. All services start in correct order
2. Services aren't marked ready until dependencies are available
3. Failing services are properly detected and restarted
4. Rolling updates don't cause service disruption

---

## Solution Guidelines

### Expected Health Check Implementation:

1. **Database Health Checks**:
```yaml
readinessProbe:
  exec:
    command:
    - pg_isready
    - -U
    - fintech_user
    - -d
    - fintech
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
livenessProbe:
  exec:
    command:
    - pg_isready
    - -U
    - fintech_user
    - -d
    - fintech
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

2. **API Gateway Health Checks**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 2
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 2
```

3. **Auth Service Health Checks**:
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 12  # Allow 60 seconds for startup
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3
```

4. **Payment Service Health Checks**:
```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 15  # Allow 150 seconds for startup
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 2
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 120
  periodSeconds: 20
  timeoutSeconds: 10
  failureThreshold: 3
```

5. **Notification Service Health Checks**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Complete Configuration Example:

```bash
# Apply health checks to each deployment
kubectl patch deployment database -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "postgres",
          "readinessProbe": {
            "exec": {
              "command": ["pg_isready", "-U", "fintech_user", "-d", "fintech"]
            },
            "initialDelaySeconds": 15,
            "periodSeconds": 5,
            "timeoutSeconds": 3,
            "failureThreshold": 3
          },
          "livenessProbe": {
            "exec": {
              "command": ["pg_isready", "-U", "fintech_user", "-d", "fintech"]
            },
            "initialDelaySeconds": 30,
            "periodSeconds": 10,
            "timeoutSeconds": 5,
            "failureThreshold": 3
          }
        }]
      }
    }
  }
}'

# Similar patches for other services...
```

---

## Success Criteria

✅ **Database starts up properly with health checks**  
✅ **API Gateway health checks work without dependency issues**  
✅ **Auth Service waits for database before marking ready**  
✅ **Payment Service uses startup probes for long initialization**  
✅ **Notification Service handles external dependency health gracefully**  
✅ **Rolling updates work smoothly with proper readiness checking**  
✅ **Failed services are detected and restarted appropriately**

---

## Advanced Challenge (Optional)

If you complete the basic scenario early, try these additional challenges:

1. **Dependency-Aware Health Checks**: Configure the API Gateway to check backend service health in its readiness probe
2. **Circuit Breaker Pattern**: Implement health checks that consider external service availability
3. **Custom Health Endpoints**: Create more sophisticated health endpoints that provide detailed service status
4. **Monitoring Integration**: Add prometheus-style metrics endpoints to health checks

---

## Cleanup

```bash
kubectl delete namespace fintech-app
kubectl config set-context --current --namespace=default
rm -f fintech-base-app.yaml
```

---

## Learning Outcomes

After completing this scenario, you should understand:

- How to choose appropriate health check types for different services
- The importance of startup probes for services with long initialization times
- How readiness probes affect service discovery and load balancing
- The relationship between liveness probes and restart policies
- How to configure health checks for services with external dependencies
- Best practices for timeout and threshold configuration
- The impact of health checks on rolling updates and service availability