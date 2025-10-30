# Mock Exam 1: Observability & Maintenance

**Time Limit**: 45 minutes  
**Total Questions**: 8 questions  
**Passing Score**: 75% (6 out of 8 questions correct)  
**Difficulty**: CKAD Exam Level

---

## Instructions

- You have 45 minutes to complete all 8 questions
- Each question has equal weight (12.5 points each)
- You may use `kubectl` documentation during the exam
- Create all resources in the specified namespaces
- Verify your solutions work as expected

---

## Question 1: Health Probes Configuration (12.5 points)

**Time**: 5 minutes

You need to deploy a web application with proper health checks. The application:
- Takes 30 seconds to start up completely
- Has a health endpoint at `/health` on port 8080
- Should be restarted if health checks fail 3 consecutive times
- Should not receive traffic until it passes readiness checks

**Task**:
Create a deployment called `web-app` in the `exam-q1` namespace with the following specifications:

```yaml
# Base deployment - add health probes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: exam-q1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-server
        image: nginx:1.21-alpine
        ports:
        - containerPort: 8080
        # TODO: Add appropriate health probes
```

**Requirements**:
1. Create the namespace `exam-q1`
2. Add appropriate startup, liveness, and readiness probes
3. Ensure probes check the `/health` endpoint on port 8080
4. Configure appropriate timing and failure thresholds

---

## Question 2: Debug Application Startup Issues (12.5 points)

**Time**: 6 minutes

A deployment called `problematic-app` in namespace `exam-q2` is failing to start. The application should connect to a database service, but pods keep restarting.

**Setup**:
```bash
kubectl create namespace exam-q2

# Deploy the problematic application
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: problematic-app
  namespace: exam-q2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: problematic-app
  template:
    metadata:
      labels:
        app: problematic-app
    spec:
      containers:
      - name: app
        image: busybox:1.35
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@db-service:5432/appdb"
        command:
        - sh
        - -c
        - |
          echo "Connecting to database..."
          # This will fail because db-service doesn't exist
          nc -z db-service 5432 || exit 1
          echo "App started successfully"
          while true; do sleep 30; done
---
apiVersion: v1
kind: Service
metadata:
  name: app-service
  namespace: exam-q2
spec:
  selector:
    app: problematic-app
  ports:
  - port: 80
    targetPort: 8080
EOF
```

**Tasks**:
1. Identify why the application is failing to start
2. Create the missing database service that the app requires
3. Ensure the application pod starts successfully
4. Verify the application can connect to the database service

**Acceptance Criteria**:
- Pod `problematic-app` is in Running state
- No restarts due to connection failures
- Application logs show successful database connection

---

## Question 3: Resource Monitoring and Optimization (12.5 points)

**Time**: 6 minutes

Deploy an application and optimize its resource allocation based on usage patterns.

**Task**:
1. Create namespace `exam-q3`
2. Deploy the following application:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-app
  namespace: exam-q3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resource-app
  template:
    metadata:
      labels:
        app: resource-app
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        command:
        - python3
        - -c
        - |
          import time
          import psutil
          print("Starting resource monitoring app...")
          while True:
              cpu_percent = psutil.cpu_percent(interval=1)
              memory_info = psutil.virtual_memory()
              print(f"CPU: {cpu_percent}%, Memory: {memory_info.percent}%")
              time.sleep(10)
        # TODO: Add appropriate resource requests and limits
```

3. Monitor the application's actual resource usage
4. Set appropriate resource requests and limits based on observed usage
5. Ensure the application has adequate resources but is not over-provisioned

**Requirements**:
- Application should have reasonable resource requests (CPU: ~50m, Memory: ~64Mi)
- Resource limits should prevent resource hogging (CPU: ~200m, Memory: ~128Mi)
- Verify resource usage with `kubectl top pod`

---

## Question 4: Network Connectivity Debugging (12.5 points)

**Time**: 6 minutes

You have two services that need to communicate, but the connection is failing. Debug and fix the connectivity issue.

**Setup**:
```bash
kubectl create namespace exam-q4

# Deploy frontend and backend
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: exam-q4
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
          while true; do
            echo "Testing backend connection..."
            wget -q --timeout=5 -O- http://backend-service:8080/api || echo "Connection failed"
            sleep 10
          done
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: exam-q4
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: exam-q4
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend-api  # Wrong label!
  template:
    metadata:
      labels:
        app: backend  # Different from selector!
    spec:
      containers:
      - name: backend
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: exam-q4
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 80
EOF
```

**Tasks**:
1. Identify why the frontend cannot connect to the backend
2. Fix the connectivity issue
3. Verify that the frontend can successfully connect to the backend
4. Ensure service discovery is working correctly

**Acceptance Criteria**:
- Frontend pod logs show successful connections to backend
- `kubectl get endpoints` shows the backend service has endpoints
- Service-to-service communication works properly

---

## Question 5: Performance Debugging (12.5 points)

**Time**: 6 minutes

An application is experiencing performance issues. Debug and optimize its configuration.

**Setup**:
```bash
kubectl create namespace exam-q5

# Deploy performance problematic app
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slow-app
  namespace: exam-q5
spec:
  replicas: 1
  selector:
    matchLabels:
      app: slow-app
  template:
    metadata:
      labels:
        app: slow-app
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        resources:
          requests:
            cpu: "10m"     # Too low
            memory: "16Mi" # Too low
          limits:
            cpu: "50m"     # Too restrictive
            memory: "32Mi" # Too restrictive
        command:
        - python3
        - -c
        - |
          import time
          import random
          print("Starting performance-intensive application...")
          data = []
          while True:
              # CPU intensive operation
              for i in range(100000):
                  result = i ** 2
              
              # Memory allocation
              data.extend([random.random() for _ in range(1000)])
              if len(data) > 10000:
                  data = data[-5000:]  # Keep last 5000 items
              
              print(f"Processed batch, data size: {len(data)}")
              time.sleep(5)
EOF
```

**Tasks**:
1. Monitor the application's performance and resource usage
2. Identify resource constraints causing performance issues
3. Optimize resource requests and limits
4. Verify improved performance after optimization

**Requirements**:
- Application should not be CPU throttled
- Memory limits should be adequate for the workload
- Resource requests should reflect actual usage
- Application performance should improve after optimization

---

## Question 6: Logging and Troubleshooting (12.5 points)

**Time**: 5 minutes

A multi-container pod is having issues. Use logs to identify and fix the problem.

**Setup**:
```bash
kubectl create namespace exam-q6

# Deploy multi-container pod with issues
kubectl apply -f - << EOF
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
  namespace: exam-q6
spec:
  containers:
  - name: main-app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Main app starting..."
      sleep 10
      echo "Checking for config file..."
      cat /shared/config.txt || echo "Config file not found!"
      while true; do
        echo "Main app running... $(date)"
        sleep 30
      done
    volumeMounts:
    - name: shared-volume
      mountPath: /shared
  - name: config-provider
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Config provider starting..."
      sleep 20  # Takes longer than main app expects
      echo "Creating config file..."
      echo "app_mode=production" > /shared/config.txt
      echo "database_url=postgresql://localhost:5432/app" >> /shared/config.txt
      echo "Config file created"
      while true; do
        echo "Config provider running... $(date)"
        sleep 60
      done
    volumeMounts:
    - name: shared-volume
      mountPath: /shared
  volumes:
  - name: shared-volume
    emptyDir: {}
EOF
```

**Tasks**:
1. Check the logs of both containers in the pod
2. Identify the timing issue between containers
3. Fix the startup sequence so the main app waits for config
4. Verify both containers are working correctly

**Acceptance Criteria**:
- Main app successfully reads the config file
- No error messages in the logs about missing config
- Both containers remain running

---

## Question 7: Monitoring Application Metrics (12.5 points)

**Time**: 6 minutes

Create an application that exposes metrics and configure monitoring.

**Task**:
Deploy an application in namespace `exam-q7` that:
1. Exposes Prometheus-style metrics on `/metrics` endpoint
2. Has proper labels for monitoring
3. Is configured with a service that can be scraped by monitoring tools

```yaml
# Complete this deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
  namespace: exam-q7
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-app
  template:
    metadata:
      labels:
        app: metrics-app
      # TODO: Add monitoring annotations
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        ports:
        - containerPort: 8080
          name: http
        command:
        - python3
        - -c
        - |
          import http.server
          import socketserver
          import time
          import random
          
          request_count = 0
          
          class MetricsHandler(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  global request_count
                  request_count += 1
                  
                  if self.path == '/metrics':
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      
                      metrics = f"""# HELP http_requests_total Total HTTP requests
          # TYPE http_requests_total counter
          http_requests_total {request_count}
          
          # HELP app_uptime_seconds Application uptime
          # TYPE app_uptime_seconds gauge
          app_uptime_seconds {time.time()}
          
          # HELP random_value Random test value
          # TYPE random_value gauge
          random_value {random.random()}
          """
                      self.wfile.write(metrics.encode())
                  else:
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      self.wfile.write(b'Metrics app running')
          
          print("Starting metrics app on port 8080...")
          with socketserver.TCPServer(("", 8080), MetricsHandler) as httpd:
              httpd.serve_forever()
```

**Requirements**:
1. Create namespace `exam-q7`
2. Add appropriate monitoring annotations to the pod template
3. Create a service that exposes the metrics endpoint
4. Verify that metrics are accessible via the service

---

## Question 8: Health Check Optimization (12.5 points)

**Time**: 5 minutes

Optimize health checks for an application with specific requirements.

**Scenario**: You have a database application that:
- Takes 45 seconds to initialize on startup
- Responds to health checks on port 5432 using `pg_isready` command
- Should be considered unhealthy if it fails health checks 2 times in a row
- Should check health every 10 seconds once running
- Is critical and should have a liveness check every 30 seconds

**Task**:
Create a deployment called `database-app` in namespace `exam-q8` with optimized health checks:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-app
  namespace: exam-q8
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database-app
  template:
    metadata:
      labels:
        app: database-app
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "testuser"
        - name: POSTGRES_PASSWORD
          value: "testpass"
        # TODO: Add optimized health probes based on requirements
```

**Requirements**:
1. Configure startup probe for 45-second initialization
2. Set readiness probe with 10-second intervals
3. Configure liveness probe with 30-second intervals  
4. Set failure threshold to 2 for health checks
5. Ensure appropriate timeouts and delays

---

## Answer Key and Scoring

### Question 1: Health Probes Configuration

**Solution**:
```bash
kubectl create namespace exam-q1

kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: exam-q1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-server
        image: nginx:1.21-alpine
        ports:
        - containerPort: 8080
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 6  # 30 seconds total
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 35
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 2
EOF
```

**Scoring**: 2 points each for startup, liveness, readiness probes, 2 points for correct configuration, 4.5 points for namespace creation and working deployment

---

### Question 2: Debug Application Startup Issues

**Solution**:
```bash
# Create the missing database service
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: exam-q2
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
          value: "appdb"
        - name: POSTGRES_USER
          value: "user"
        - name: POSTGRES_PASSWORD
          value: "pass"
        ports:
        - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: db-service
  namespace: exam-q2
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
EOF
```

**Scoring**: 5 points for identifying the issue, 5 points for creating database deployment, 2.5 points for creating service with correct name

---

### Question 3: Resource Monitoring and Optimization

**Solution**:
```bash
kubectl create namespace exam-q3

kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-app
  namespace: exam-q3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resource-app
  template:
    metadata:
      labels:
        app: resource-app
    spec:
      containers:
      - name: app
        image: python:3.11-alpine
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        command:
        - python3
        - -c
        - |
          import time
          import psutil
          print("Starting resource monitoring app...")
          while True:
              cpu_percent = psutil.cpu_percent(interval=1)
              memory_info = psutil.virtual_memory()
              print(f"CPU: {cpu_percent}%, Memory: {memory_info.percent}%")
              time.sleep(10)
EOF
```

**Scoring**: 3 points for namespace, 4.5 points for appropriate resource requests, 4.5 points for appropriate limits, 0.5 points for working deployment

---

### Question 4: Network Connectivity Debugging

**Solution**:
```bash
# Fix the backend deployment selector
kubectl patch deployment backend -n exam-q4 -p '{"spec":{"selector":{"matchLabels":{"app":"backend"}}}}'
```

**Scoring**: 6 points for identifying the label mismatch issue, 6.5 points for fixing the deployment selector or pod labels

---

### Question 5: Performance Debugging

**Solution**:
```bash
# Update resource allocation
kubectl patch deployment slow-app -n exam-q5 -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "requests": {"cpu": "100m", "memory": "64Mi"},
            "limits": {"cpu": "300m", "memory": "128Mi"}
          }
        }]
      }
    }
  }
}'
```

**Scoring**: 4 points for identifying resource constraints, 4 points for increasing requests, 4.5 points for increasing limits appropriately

---

### Question 6: Logging and Troubleshooting

**Solution**:
```bash
# Update the main-app to wait for config
kubectl patch pod multi-container-pod -n exam-q6 -p '{
  "spec": {
    "containers": [{
      "name": "main-app",
      "command": ["sh", "-c", "echo \"Main app starting...\"; sleep 30; echo \"Checking for config file...\"; cat /shared/config.txt; while true; do echo \"Main app running... $(date)\"; sleep 30; done"]
    }]
  }
}'
```

**Scoring**: 4 points for identifying timing issue, 4 points for analyzing logs, 4.5 points for fixing the startup sequence

---

### Question 7: Monitoring Application Metrics

**Solution**:
```bash
kubectl create namespace exam-q7

kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
  namespace: exam-q7
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-app
  template:
    metadata:
      labels:
        app: metrics-app
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
        # [same command as provided]
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-app-service
  namespace: exam-q7
spec:
  selector:
    app: metrics-app
  ports:
  - port: 8080
    targetPort: 8080
    name: http
EOF
```

**Scoring**: 3 points for namespace, 4 points for monitoring annotations, 5.5 points for service configuration

---

### Question 8: Health Check Optimization

**Solution**:
```bash
kubectl create namespace exam-q8

kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-app
  namespace: exam-q8
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database-app
  template:
    metadata:
      labels:
        app: database-app
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "testuser"
        - name: POSTGRES_PASSWORD
          value: "testpass"
        startupProbe:
          exec:
            command:
            - pg_isready
            - -U
            - testuser
            - -d
            - testdb
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 9  # 45 seconds total
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - testuser
            - -d
            - testdb
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 2
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - testuser
            - -d
            - testdb
          initialDelaySeconds: 50
          periodSeconds: 30
          failureThreshold: 2
EOF
```

**Scoring**: 2.5 points each for startup, readiness, liveness probes, 5 points for correct timing configuration

---

## Exam Summary

**Total Time**: 45 minutes  
**Total Points**: 100 points (8 questions × 12.5 points each)  
**Passing Score**: 75 points

**Key Areas Tested**:
- Health probe configuration and optimization
- Application debugging and troubleshooting
- Resource monitoring and optimization
- Network connectivity debugging
- Performance analysis and tuning
- Logging and multi-container pod troubleshooting
- Metrics and monitoring setup
- Advanced health check scenarios

**Tips for Success**:
- Read each question carefully and understand requirements
- Test your solutions before moving to the next question
- Use `kubectl describe` and `kubectl logs` for debugging
- Monitor time and allocate appropriately per question
- Verify your solutions work as expected