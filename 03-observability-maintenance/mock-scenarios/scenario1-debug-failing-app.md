# Mock Scenario 1: Debug Failing Application

**Scenario**: You are a DevOps engineer supporting a production e-commerce application. The application has been experiencing intermittent failures, and customer complaints are increasing. You need to investigate and resolve the issues quickly.

**Time Limit**: 30 minutes  
**Difficulty**: Intermediate to Advanced

---

## Background

Your company runs a microservices-based e-commerce platform with the following components:
- **Frontend**: Web application serving customer requests
- **Product Service**: Manages product catalog
- **User Service**: Handles user authentication and profiles
- **Order Service**: Processes customer orders
- **Database**: PostgreSQL database for data storage

Recent issues reported:
- Intermittent 500 errors on the website
- Users unable to complete purchases
- Slow page load times
- Some services appear to be restarting frequently

---

## Initial Setup

Deploy the problematic application to your cluster:

```bash
# Create namespace for the scenario
kubectl create namespace ecommerce-debug
kubectl config set-context --current --namespace=ecommerce-debug

# Deploy the problematic application
cat << EOF > failing-ecommerce-app.yaml
# Frontend deployment with issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
    tier: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: web
    spec:
      containers:
      - name: frontend
        image: nginx:1.21
        ports:
        - containerPort: 80
        # ISSUE: Missing health checks
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        env:
        - name: PRODUCT_SERVICE_URL
          value: "http://product-service:8080"
        - name: USER_SERVICE_URL
          value: "http://user-service:8080"
        - name: ORDER_SERVICE_URL
          value: "http://order-service:8080"
        lifecycle:
          postStart:
            exec:
              command:
              - sh
              - -c
              - |
                # Simulate application initialization
                cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF'
                upstream product_service {
                    server product-service:8080;
                }
                upstream user_service {
                    server user-service:8080;
                }
                upstream order_service {
                    server order-service:8080;
                }
                
                server {
                    listen 80;
                    
                    location / {
                        root /usr/share/nginx/html;
                        index index.html;
                        try_files $uri $uri/ /index.html;
                    }
                    
                    location /api/products/ {
                        proxy_pass http://product_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 10s;
                    }
                    
                    location /api/users/ {
                        proxy_pass http://user_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 10s;
                    }
                    
                    location /api/orders/ {
                        proxy_pass http://order_service/;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_connect_timeout 5s;
                        proxy_read_timeout 10s;
                    }
                    
                    location /health {
                        access_log off;
                        return 200 "Frontend healthy\n";
                        add_header Content-Type text/plain;
                    }
                }
                NGINX_EOF
                
                # Create a simple frontend page
                cat > /usr/share/nginx/html/index.html << 'HTML_EOF'
                <!DOCTYPE html>
                <html>
                <head><title>E-Commerce App</title></head>
                <body>
                    <h1>Welcome to E-Commerce</h1>
                    <p>Application Status: <span id="status">Loading...</span></p>
                    <script>
                        fetch('/api/products/health')
                            .then(r => r.text())
                            .then(data => document.getElementById('status').innerText = 'Running')
                            .catch(e => document.getElementById('status').innerText = 'Error: ' + e.message);
                    </script>
                </body>
                </html>
                HTML_EOF
                
                nginx -s reload
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
---
# Product service with memory issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
  labels:
    app: product-service
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: product-service
  template:
    metadata:
      labels:
        app: product-service
        tier: api
    spec:
      containers:
      - name: product-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        # ISSUE: Memory limits too low, will cause OOM
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "96Mi"  # Too low - will cause OOM
        # ISSUE: No health checks
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:dbpass@database-service:5432/ecommerce"
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import threading
          import time
          import random
          
          # ISSUE: Memory leak simulation
          memory_hog = []
          
          class ProductHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Product service healthy')
                  elif self.path == '/':
                      # ISSUE: Simulate memory leak
                      global memory_hog
                      memory_hog.extend([{'data': 'x' * 1024} for _ in range(100)])
                      
                      # Simulate occasional failures
                      if random.random() < 0.1:  # 10% failure rate
                          self.send_response(500)
                          self.send_header('Content-type', 'application/json')
                          self.end_headers()
                          self.wfile.write(json.dumps({'error': 'Internal server error'}).encode())
                          return
                      
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      
                      products = [
                          {'id': 1, 'name': 'Laptop', 'price': 999.99},
                          {'id': 2, 'name': 'Mouse', 'price': 29.99},
                          {'id': 3, 'name': 'Keyboard', 'price': 79.99}
                      ]
                      self.wfile.write(json.dumps(products).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Product Service on port 8080...")
          with socketserver.TCPServer(("", 8080), ProductHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: product-service
spec:
  selector:
    app: product-service
  ports:
  - port: 8080
    targetPort: 8080
---
# User service with startup issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        tier: api
    spec:
      containers:
      - name: user-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        # ISSUE: Readiness probe pointing to wrong endpoint
        readinessProbe:
          httpGet:
            path: /wrong-health-endpoint  # Wrong endpoint
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:dbpass@database-service:5432/ecommerce"
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import random
          
          class UserHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  # ISSUE: Long startup time without proper startup probe
                  if hasattr(self.server, 'startup_complete'):
                      startup_complete = self.server.startup_complete
                  else:
                      # Simulate 60 second startup time
                      self.server.startup_complete = time.time() + 60
                      startup_complete = self.server.startup_complete
                  
                  if time.time() < startup_complete:
                      self.send_response(503)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Service starting up...')
                      return
                  
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'User service healthy')
                  elif self.path == '/':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      
                      users = [
                          {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                          {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
                      ]
                      self.wfile.write(json.dumps(users).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting User Service on port 8080 (with slow startup)...")
          with socketserver.TCPServer(("", 8080), UserHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 8080
    targetPort: 8080
---
# Order service with database connectivity issues
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        tier: api
    spec:
      containers:
      - name: order-service
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        # ISSUE: Liveness probe is too aggressive
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 2  # Too short
          failureThreshold: 1  # Too aggressive
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:dbpass@wrong-database-service:5432/ecommerce"  # Wrong service name
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import json
          import time
          import random
          
          class OrderHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      # ISSUE: Health check depends on database
                      # Simulate database connectivity check that fails
                      if random.random() < 0.3:  # 30% failure rate
                          time.sleep(5)  # Slow response
                          self.send_response(500)
                          self.send_header('Content-type', 'text/plain')
                          self.end_headers()
                          self.wfile.write(b'Database connection failed')
                          return
                      
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Order service healthy')
                  elif self.path == '/':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      
                      orders = [
                          {'id': 1, 'user_id': 1, 'product_id': 1, 'quantity': 2},
                          {'id': 2, 'user_id': 2, 'product_id': 2, 'quantity': 1}
                      ]
                      self.wfile.write(json.dumps(orders).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          print("Starting Order Service on port 8080...")
          with socketserver.TCPServer(("", 8080), OrderHandler) as httpd:
              httpd.serve_forever()
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
  ports:
  - port: 8080
    targetPort: 8080
---
# Database (working correctly)
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
          value: "ecommerce"
        - name: POSTGRES_USER
          value: "dbuser"
        - name: POSTGRES_PASSWORD
          value: "dbpass"
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "200m"
            memory: "512Mi"
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - dbuser
            - -d
            - ecommerce
          initialDelaySeconds: 15
          periodSeconds: 5
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - dbuser
            - -d
            - ecommerce
          initialDelaySeconds: 30
          periodSeconds: 10
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
EOF

kubectl apply -f failing-ecommerce-app.yaml
```

---

## Your Mission

### Task 1: Initial Assessment (5 minutes)

Quickly assess the current state of the application and identify obvious issues:

```bash
# TODO: Check the overall health of the application
# Examine pod status, service endpoints, and recent events
```

**Questions to answer:**
1. How many pods are running vs expected?
2. Are there any pods in CrashLoopBackOff or pending state?
3. What do the recent events tell you about system health?

### Task 2: Debug Service Availability (8 minutes)

Investigate service connectivity and endpoint availability:

```bash
# TODO: Test service connectivity and endpoint resolution
# Check if services can communicate with each other
```

**Questions to answer:**
1. Are all services accessible from within the cluster?
2. Which services are failing to respond?
3. What are the specific error messages or timeouts?

### Task 3: Analyze Resource Issues (7 minutes)

Examine resource utilization and constraints:

```bash
# TODO: Check resource usage, limits, and any resource-related failures
# Look for OOM kills, CPU throttling, and resource constraints
```

**Questions to answer:**
1. Are any pods being killed due to resource constraints?
2. Which services are consuming the most resources?
3. Are resource limits appropriate for the workload?

### Task 4: Fix Health Check Configuration (5 minutes)

Identify and fix health check issues:

```bash
# TODO: Examine and fix liveness, readiness, and startup probes
# Address any health check misconfigurations
```

**Questions to answer:**
1. Which health checks are failing and why?
2. Are probe configurations appropriate for service startup times?
3. How can health checks be improved for reliability?

### Task 5: Resolve Application Issues (5 minutes)

Fix the remaining application-specific problems:

```bash
# TODO: Address configuration errors, service dependencies, and other issues
# Ensure all services can communicate and function properly
```

**Questions to answer:**
1. Are there any configuration errors in service connections?
2. What application-level fixes are needed?
3. How can you verify the fixes are working?

---

## Issues Summary

The application has multiple intentional issues:

1. **Frontend**: Missing health checks
2. **Product Service**: Memory limits too low causing OOM, memory leak simulation
3. **User Service**: Wrong readiness probe endpoint, long startup time without startup probe
4. **Order Service**: Aggressive liveness probe, wrong database service name in configuration
5. **Database**: Working correctly (control group)

---

## Solution Guidelines

### Expected Debugging Process:

1. **Initial Assessment**:
   ```bash
   kubectl get pods,services,endpoints
   kubectl describe pods
   kubectl get events --sort-by='.lastTimestamp'
   kubectl top pods (if metrics available)
   ```

2. **Service Connectivity Testing**:
   ```bash
   kubectl run debug --image=busybox:1.35 --rm -it -- sh
   # Test service DNS resolution and connectivity
   nslookup product-service
   wget -qO- http://product-service:8080/health
   ```

3. **Resource Analysis**:
   ```bash
   kubectl describe pods | grep -A 5 -B 5 "Limits\|Requests"
   kubectl get events | grep -i "oom\|kill\|fail"
   kubectl logs <pod-name>
   ```

4. **Health Check Fixes**:
   ```bash
   # Fix user-service readiness probe
   kubectl patch deployment user-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"user-service","readinessProbe":{"httpGet":{"path":"/health","port":8080}}}]}}}}'
   
   # Add startup probe for user-service
   kubectl patch deployment user-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"user-service","startupProbe":{"httpGet":{"path":"/health","port":8080},"initialDelaySeconds":10,"periodSeconds":10,"failureThreshold":10}}]}}}}'
   
   # Fix order-service liveness probe
   kubectl patch deployment order-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"order-service","livenessProbe":{"timeoutSeconds":10,"failureThreshold":3}}]}}}}'
   ```

5. **Application Fixes**:
   ```bash
   # Fix order-service database connection
   kubectl patch deployment order-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"order-service","env":[{"name":"DATABASE_URL","value":"postgresql://dbuser:dbpass@database-service:5432/ecommerce"}]}]}}}}'
   
   # Increase product-service memory limit
   kubectl patch deployment product-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"product-service","resources":{"limits":{"memory":"256Mi"}}}]}}}}'
   ```

### Validation:

```bash
# Wait for deployments to stabilize
kubectl wait --for=condition=available deployment/frontend deployment/product-service deployment/user-service deployment/order-service --timeout=300s

# Test application functionality
kubectl run test-client --image=busybox:1.35 --rm -it -- sh
wget -qO- http://frontend-service/
wget -qO- http://frontend-service/api/products/
wget -qO- http://frontend-service/api/users/
wget -qO- http://frontend-service/api/orders/
```

---

## Success Criteria

✅ **All pods are running and ready**  
✅ **All services respond to health checks**  
✅ **No OOM kills or resource constraint failures**  
✅ **Frontend can successfully proxy to all backend services**  
✅ **Application responds correctly to user requests**  
✅ **Health checks are properly configured for all services**

---

## Cleanup

```bash
kubectl delete namespace ecommerce-debug
kubectl config set-context --current --namespace=default
rm -f failing-ecommerce-app.yaml
```

---

## Learning Outcomes

After completing this scenario, you should understand:

- How to systematically debug multi-service application failures
- The importance of proper health check configuration
- How resource constraints affect application reliability
- Service discovery and connectivity troubleshooting
- The impact of configuration errors on application behavior
- How to validate fixes and ensure system stability