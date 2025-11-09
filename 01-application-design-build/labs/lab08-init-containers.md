# Lab 8: Init Containers

**Objective**: Master init containers for dependency management and pod initialization

**Time**: 30 minutes

**Prerequisites**: Kubernetes cluster access, understanding of pod lifecycle

---

## [Exercise 1: Basic Init Container Concepts (10 minutes](/01-application-design-build/labs/lab08-solution/exercise-01/)

Learn init container fundamentals and execution order.

### Step 1: Simple Init Container

Create `basic-init.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
  labels:
    app: init-demo
spec:
  initContainers:
  # First init container
  - name: init-setup
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Init container 1: Setting up environment..."
      echo "Creating configuration files..."
      echo "database_url=localhost:5432" > /shared-data/config.txt
      echo "debug_mode=true" >> /shared-data/config.txt
      echo "Init setup completed at $(date)"
      sleep 5
    volumeMounts:
    - name: shared-data
      mountPath: /shared-data
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  # Second init container
  - name: init-database
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Init container 2: Checking database connectivity..."
      
      # Read config from previous init container
      if [ -f /shared-data/config.txt ]; then
        echo "Configuration found:"
        cat /shared-data/config.txt
      fi
      
      echo "Simulating database connection check..."
      sleep 3
      
      # Simulate successful connection
      echo "Database connection: OK"
      echo "database_status=connected" >> /shared-data/config.txt
      echo "Database check completed at $(date)"
    volumeMounts:
    - name: shared-data
      mountPath: /shared-data
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  containers:
  # Main application container
  - name: app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Main application starting..."
      echo "Reading configuration:"
      cat /app-data/config.txt
      
      echo "Application ready!"
      
      # Keep running
      while true; do
        echo "App is running at $(date)"
        sleep 30
      done
    volumeMounts:
    - name: shared-data
      mountPath: /app-data
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  volumes:
  - name: shared-data
    emptyDir: {}
```

Deploy and monitor:
```bash
# Apply the configuration
kubectl apply -f basic-init.yaml

# Watch pod initialization
kubectl get pods init-demo -w

# Check init container logs
kubectl logs init-demo -c init-setup
kubectl logs init-demo -c init-database

# Check main container logs
kubectl logs init-demo -c app

# Describe pod to see init container details
kubectl describe pod init-demo

# Cleanup
kubectl delete -f basic-init.yaml
```

---

## [Exercise 2: Real-World Init Container Scenarios (15 minutes)](/01-application-design-build/labs/lab08-solution/exercise-02/)

Implement practical init container use cases.

### Step 1: Service Dependency Management

Create `service-dependency.yaml`:
```yaml
# Service that init containers will wait for
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
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
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
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "testuser"
        - name: POSTGRES_PASSWORD
          value: "testpass"
        ports:
        - containerPort: 5432
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - testuser
            - -d
            - testdb
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
---
# Application with init containers waiting for services
apiVersion: v1
kind: Pod
metadata:
  name: service-dependent-app
spec:
  initContainers:
  # Wait for database service
  - name: wait-for-database
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Waiting for database service to be available..."
      
      until nc -z database-service 5432; do
        echo "Database not ready, waiting..."
        sleep 2
      done
      
      echo "Database service is available!"
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  # Wait for external API
  - name: wait-for-api
    image: curlimages/curl:8.4.0
    command:
    - sh
    - -c
    - |
      echo "Waiting for external API to be available..."
      
      # Wait for external service (using httpbin as example)
      until curl -f https://httpbin.org/status/200; do
        echo "External API not ready, waiting..."
        sleep 5
      done
      
      echo "External API is available!"
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Download configuration
  - name: download-config
    image: curlimages/curl:8.4.0
    command:
    - sh
    - -c
    - |
      echo "Downloading application configuration..."
      
      # Download config from external source
      curl -s https://httpbin.org/json > /shared-config/external-config.json
      
      # Create local config
      cat > /shared-config/app-config.yaml << EOF
      app:
        name: "service-dependent-app"
        version: "1.0.0"
        database:
          host: "database-service"
          port: 5432
          database: "testdb"
        external_api:
          url: "https://httpbin.org"
      EOF
      
      echo "Configuration downloaded and created:"
      ls -la /shared-config/
    volumeMounts:
    - name: config-volume
      mountPath: /shared-config
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  containers:
  # Main application
  - name: app
    image: python:3.11-alpine
    command:
    - python
    - -c
    - |
      import time
      import json
      import os
      
      print("Application starting with all dependencies ready!")
      
      # Read downloaded config
      with open('/app-config/app-config.yaml', 'r') as f:
          config = f.read()
          print("App configuration:")
          print(config)
      
      with open('/app-config/external-config.json', 'r') as f:
          external_config = json.load(f)
          print("External configuration loaded:")
          print(json.dumps(external_config, indent=2))
      
      # Simulate application work
      counter = 0
      while True:
          counter += 1
          print(f"Application tick #{counter} at {time.ctime()}")
          time.sleep(10)
    volumeMounts:
    - name: config-volume
      mountPath: /app-config
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  volumes:
  - name: config-volume
    emptyDir: {}
```

Test service dependencies:
```bash
# Apply the configuration
kubectl apply -f service-dependency.yaml

# Watch init containers execute
kubectl get pods service-dependent-app -w

# Check init container logs
kubectl logs service-dependent-app -c wait-for-database
kubectl logs service-dependent-app -c wait-for-api
kubectl logs service-dependent-app -c download-config

# Check main application logs
kubectl logs service-dependent-app -c app

# Verify database is running
kubectl get pods -l app=database

# Cleanup
kubectl delete -f service-dependency.yaml
```

### Step 2: Data Migration Init Container

Create `data-migration.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: migration-scripts
data:
  migrate.sql: |
    -- Database migration script
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        title VARCHAR(200) NOT NULL,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Insert sample data
    INSERT INTO users (username, email) VALUES 
        ('alice', 'alice@example.com'),
        ('bob', 'bob@example.com')
    ON CONFLICT (username) DO NOTHING;
    
    INSERT INTO posts (user_id, title, content) VALUES 
        (1, 'Hello World', 'This is my first post'),
        (2, 'Kubernetes Init Containers', 'Learning about init containers')
    ON CONFLICT DO NOTHING;
  
  seed-data.json: |
    {
      "users": [
        {"username": "charlie", "email": "charlie@example.com"},
        {"username": "diana", "email": "diana@example.com"}
      ],
      "settings": {
        "theme": "dark",
        "notifications": true,
        "max_posts_per_page": 10
      }
    }
---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-migration
spec:
  initContainers:
  # Database migration
  - name: db-migration
    image: postgres:15-alpine
    command:
    - sh
    - -c
    - |
      echo "Starting database migration..."
      
      # Wait for database to be ready
      until pg_isready -h database-service -U testuser -d testdb; do
        echo "Waiting for database..."
        sleep 2
      done
      
      echo "Running database migrations..."
      PGPASSWORD=testpass psql -h database-service -U testuser -d testdb -f /migrations/migrate.sql
      
      echo "Database migration completed successfully!"
    volumeMounts:
    - name: migration-scripts
      mountPath: /migrations
    env:
    - name: PGPASSWORD
      value: "testpass"
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  # Data seeding
  - name: data-seeder
    image: python:3.11-alpine
    command:
    - python
    - -c
    - |
      import json
      import psycopg2
      import time
      
      print("Starting data seeding...")
      
      # Wait a bit for migration to complete
      time.sleep(2)
      
      # Load seed data
      with open('/seed-data/seed-data.json', 'r') as f:
          seed_data = json.load(f)
      
      # Connect to database
      try:
          conn = psycopg2.connect(
              host="database-service",
              database="testdb",
              user="testuser",
              password="testpass"
          )
          
          cur = conn.cursor()
          
          # Seed additional users
          for user in seed_data['users']:
              cur.execute(
                  "INSERT INTO users (username, email) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING",
                  (user['username'], user['email'])
              )
          
          conn.commit()
          print("Data seeding completed successfully!")
          
      except Exception as e:
          print(f"Error during data seeding: {e}")
          exit(1)
      
      finally:
          if conn:
              conn.close()
    volumeMounts:
    - name: migration-scripts
      mountPath: /seed-data
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  # Configuration validation
  - name: config-validator
    image: python:3.11-alpine
    command:
    - python
    - -c
    - |
      import json
      import psycopg2
      
      print("Validating application configuration...")
      
      # Validate seed data format
      with open('/seed-data/seed-data.json', 'r') as f:
          config = json.load(f)
      
      # Check required fields
      required_keys = ['users', 'settings']
      for key in required_keys:
          if key not in config:
              print(f"Error: Missing required config key: {key}")
              exit(1)
      
      # Validate database connectivity and data
      try:
          conn = psycopg2.connect(
              host="database-service",
              database="testdb",
              user="testuser",
              password="testpass"
          )
          
          cur = conn.cursor()
          cur.execute("SELECT COUNT(*) FROM users")
          user_count = cur.fetchone()[0]
          
          cur.execute("SELECT COUNT(*) FROM posts")
          post_count = cur.fetchone()[0]
          
          print(f"Validation successful: {user_count} users, {post_count} posts")
          
          if user_count < 2:
              print("Warning: Expected at least 2 users")
          
          conn.close()
          
      except Exception as e:
          print(f"Database validation failed: {e}")
          exit(1)
      
      print("All validations passed!")
    volumeMounts:
    - name: migration-scripts
      mountPath: /seed-data
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  containers:
  # Main application
  - name: web-app
    image: python:3.11-alpine
    command:
    - python
    - -c
    - |
      import psycopg2
      import json
      import time
      from http.server import HTTPServer, BaseHTTPRequestHandler
      
      class AppHandler(BaseHTTPRequestHandler):
          def do_GET(self):
              if self.path == '/users':
                  self.send_response(200)
                  self.send_header('Content-type', 'application/json')
                  self.end_headers()
                  
                  try:
                      conn = psycopg2.connect(
                          host="database-service",
                          database="testdb",
                          user="testuser",
                          password="testpass"
                      )
                      
                      cur = conn.cursor()
                      cur.execute("SELECT username, email FROM users")
                      users = [{"username": row[0], "email": row[1]} for row in cur.fetchall()]
                      
                      self.wfile.write(json.dumps(users).encode())
                      conn.close()
                      
                  except Exception as e:
                      self.wfile.write(json.dumps({"error": str(e)}).encode())
              
              else:
                  self.send_response(200)
                  self.send_header('Content-type', 'text/html')
                  self.end_headers()
                  self.wfile.write(b"<h1>App with Init Containers</h1><p><a href='/users'>View Users</a></p>")
      
      print("Starting web application...")
      server = HTTPServer(('0.0.0.0', 8080), AppHandler)
      server.serve_forever()
    ports:
    - containerPort: 8080
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
  
  volumes:
  - name: migration-scripts
    configMap:
      name: migration-scripts
```

Test data migration:
```bash
# Make sure database is still running from previous exercise
kubectl get pods -l app=database

# Apply migration configuration
kubectl apply -f data-migration.yaml

# Watch init containers execute in sequence
kubectl get pods app-with-migration -w

# Check init container logs
kubectl logs app-with-migration -c db-migration
kubectl logs app-with-migration -c data-seeder
kubectl logs app-with-migration -c config-validator

# Check main application
kubectl logs app-with-migration -c web-app

# Test the application
kubectl port-forward pod/app-with-migration 8080:8080 &
curl http://localhost:8080/users

# Cleanup
kubectl delete -f data-migration.yaml
pkill -f "kubectl port-forward"
```

---

## [Exercise 3: Init Container Failure Handling (5 minutes)](/01-application-design-build/labs/lab08-solution/exercise-03/)

Learn how init container failures are handled.

### Step 1: Init Container with Failure

Create `init-failure.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-failure-demo
spec:
  initContainers:
  # This init container will succeed
  - name: init-success
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Successful init container"
      echo "setup_complete=true" > /shared/status.txt
      exit 0
    volumeMounts:
    - name: shared
      mountPath: /shared
  
  # This init container will fail
  - name: init-failure
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "This init container will fail after checking previous step"
      
      if [ -f /shared/status.txt ]; then
        echo "Previous init container completed:"
        cat /shared/status.txt
      fi
      
      echo "Simulating failure..."
      exit 1
    volumeMounts:
    - name: shared
      mountPath: /shared
  
  # This init container will never run due to previous failure
  - name: init-never-runs
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "This should never be printed"
      exit 0
  
  containers:
  # Main container will never start
  - name: main-app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Main application starting..."
      while true; do
        echo "App running..."
        sleep 30
      done
  
  volumes:
  - name: shared
    emptyDir: {}
  
  restartPolicy: Never
```

Test failure handling:
```bash
# Apply the failing configuration
kubectl apply -f init-failure.yaml

# Watch the pod fail
kubectl get pods init-failure-demo -w

# Check which init containers ran
kubectl describe pod init-failure-demo

# Check logs from successful init container
kubectl logs init-failure-demo -c init-success

# Check logs from failed init container
kubectl logs init-failure-demo -c init-failure

# Try to check logs from container that never ran (should fail)
kubectl logs init-failure-demo -c init-never-runs

# Check pod events
kubectl get events --field-selector involvedObject.name=init-failure-demo

# Cleanup
kubectl delete -f init-failure.yaml
```

---

## 🎯 Init Container Patterns

### 1. Service Dependencies
```yaml
initContainers:
- name: wait-for-service
  image: busybox
  command: ['sh', '-c', 'until nc -z service-name 80; do sleep 1; done']
```

### 2. Data Download/Setup
```yaml
initContainers:
- name: download-data
  image: curlimages/curl
  command: ['curl', '-o', '/shared/data.json', 'https://api.example.com/data']
  volumeMounts:
  - name: shared-data
    mountPath: /shared
```

### 3. Configuration Generation
```yaml
initContainers:
- name: generate-config
  image: busybox
  command:
  - sh
  - -c
  - |
    cat > /config/app.conf << EOF
    server_name=$HOSTNAME
    port=8080
    EOF
```

### 4. Database Migration
```yaml
initContainers:
- name: db-migrate
  image: migrate/migrate
  command:
  - migrate
  - -database
  - postgres://user:pass@db:5432/dbname?sslmode=disable
  - -path
  - /migrations
  - up
```

## 🔍 Troubleshooting Commands

```bash
# Check init container status
kubectl describe pod <pod-name>

# View init container logs
kubectl logs <pod-name> -c <init-container-name>

# Get pod events
kubectl get events --field-selector involvedObject.name=<pod-name>

# Check init container restart count
kubectl get pod <pod-name> -o jsonpath='{.status.initContainerStatuses[*].restartCount}'

# Check which init container failed
kubectl get pod <pod-name> -o jsonpath='{.status.initContainerStatuses[?(@.ready==false)].name}'
```

## 📝 Best Practices

1. **Keep init containers lightweight** - They run sequentially
2. **Handle failures gracefully** - Failed init containers prevent pod startup
3. **Use appropriate restart policies** - Consider OnFailure for retryable operations
4. **Share data via volumes** - Use emptyDir or persistent volumes
5. **Set resource limits** - Prevent init containers from consuming too many resources
6. **Order matters** - Init containers run in the order they're defined

## 🎯 Key Takeaways

- Init containers run before main application containers
- They run sequentially and must complete successfully
- Use for setup tasks, dependency checks, and data preparation
- Failed init containers prevent main containers from starting
- Share data with main containers via volumes

## 📚 Additional Resources

- [Init Containers Documentation](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Container Probes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)