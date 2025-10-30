# Lab 3: Startup Probes

**Objective**: Configure startup probes to handle applications with long initialization times
**Time**: 25 minutes
**Difficulty**: Intermediate

---

## Learning Objectives

By the end of this lab, you will be able to:
- Configure startup probes for applications with long startup times
- Understand how startup probes interact with liveness and readiness probes
- Implement startup probes for different application types
- Troubleshoot startup probe failures
- Apply best practices for startup probe configuration

---

## Prerequisites

- Kubernetes cluster access
- kubectl CLI configured
- Understanding of liveness and readiness probes
- Basic knowledge of container lifecycle

---

## Lab Environment Setup

Create a dedicated namespace for this lab:

```bash
kubectl create namespace startup-lab
kubectl config set-context --current --namespace=startup-lab
```

---

## Exercise 1: Basic Startup Probe Configuration (8 minutes)

### Task 1.1: Create Application with Long Startup Time

Deploy an application that takes a long time to start and would normally fail liveness probes:

```yaml
cat << EOF > slow-startup-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slow-startup-app
  labels:
    app: slow-startup-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: slow-startup-app
  template:
    metadata:
      labels:
        app: slow-startup-app
    spec:
      containers:
      - name: slow-app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting slow application initialization..."
          
          # Simulate very slow startup (2 minutes)
          for i in {1..120}; do
            echo "Initialization step $i/120"
            sleep 1
          done
          
          echo "Application startup complete!"
          touch /tmp/app-started
          
          # Start the application
          while true; do
            echo "Application is running..."
            date > /tmp/last-heartbeat
            sleep 10
          done
        # Startup probe - allows long initialization
        startupProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/app-started"
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 15  # Allow up to 150 seconds (15 * 10s)
        # Liveness probe - takes over after startup
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/last-heartbeat && test $(( $(date +%s) - $(stat -c %Y /tmp/last-heartbeat) )) -lt 30"
          initialDelaySeconds: 0    # Not used when startup probe exists
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        # Readiness probe - controls traffic
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/app-started"
          initialDelaySeconds: 0    # Not used when startup probe exists
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: slow-startup-service
spec:
  selector:
    app: slow-startup-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
EOF

kubectl apply -f slow-startup-app.yaml
```

### Task 1.2: Monitor Startup Process

Observe how startup probes protect the container during initialization:

```bash
# Monitor pod status during startup
kubectl get pods -l app=slow-startup-app -w &
WATCH_PID=$!

# In another terminal, monitor the logs
kubectl logs -f deployment/slow-startup-app &
LOG_PID=$!

# Wait for startup to complete
sleep 180

# Stop monitoring
kill $WATCH_PID $LOG_PID

# Check final status
kubectl describe pods -l app=slow-startup-app | grep -A 5 "Startup\|Liveness\|Readiness"
```

---

## Exercise 2: Database with Startup Probe (7 minutes)

### Task 2.1: Deploy Database with Migration Simulation

Create a database deployment that simulates long startup due to migrations:

```yaml
cat << EOF > database-startup.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-with-migration
  labels:
    app: postgres-migration
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-migration
  template:
    metadata:
      labels:
        app: postgres-migration
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        env:
        - name: POSTGRES_DB
          value: "appdb"
        - name: POSTGRES_USER
          value: "appuser"
        - name: POSTGRES_PASSWORD
          value: "apppass"
        ports:
        - containerPort: 5432
        # Custom entrypoint to simulate migrations
        command:
        - sh
        - -c
        - |
          echo "Starting PostgreSQL with migrations..."
          
          # Start PostgreSQL in background
          docker-entrypoint.sh postgres &
          PG_PID=$!
          
          # Wait for PostgreSQL to be ready for connections
          echo "Waiting for PostgreSQL to start..."
          until pg_isready -h localhost -p 5432; do
            echo "PostgreSQL not ready yet..."
            sleep 2
          done
          
          echo "PostgreSQL started, running migrations..."
          
          # Simulate long-running migrations
          for i in {1..60}; do
            echo "Running migration $i/60..."
            sleep 2
          done
          
          echo "Migrations complete!"
          touch /tmp/migrations-done
          
          # Wait for PostgreSQL process
          wait $PG_PID
        # Startup probe - wait for migrations
        startupProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/migrations-done"
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 18  # Allow up to 3 minutes
        # Liveness probe - check PostgreSQL process
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "pg_isready -h localhost -p 5432"
          initialDelaySeconds: 0
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        # Readiness probe - check if ready for connections
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "pg_isready -h localhost -p 5432 && test -f /tmp/migrations-done"
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-migration-service
spec:
  selector:
    app: postgres-migration
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

kubectl apply -f database-startup.yaml
```

### Task 2.2: Monitor Database Startup and Migration

```bash
# Monitor the database startup process
kubectl get pods -l app=postgres-migration -w &
WATCH_PID=$!

# Monitor logs to see migration progress
kubectl logs -f deployment/postgres-with-migration &
LOG_PID=$!

# Wait for completion
sleep 200

# Stop monitoring
kill $WATCH_PID $LOG_PID

# Check final probe status
kubectl describe pod -l app=postgres-migration | grep -A 5 "Startup\|Liveness\|Readiness"

# Verify service endpoints
kubectl get endpoints postgres-migration-service
```

---

## Exercise 3: Java Application Startup Probe (5 minutes)

### Task 3.1: Simulate Java Application with JVM Warm-up

Create a simulation of a Java application that needs JVM warm-up time:

```yaml
cat << EOF > java-app-startup.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: java-app
  labels:
    app: java-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: java-app
  template:
    metadata:
      labels:
        app: java-app
    spec:
      containers:
      - name: java-app
        image: openjdk:11-jre-slim
        command:
        - sh
        - -c
        - |
          echo "Starting Java application..."
          echo "JVM Options: -Xmx512m -Xms256m"
          
          # Simulate JVM startup and class loading
          echo "Loading JVM..."
          sleep 30
          
          echo "Loading application classes..."
          sleep 20
          
          echo "Initializing frameworks..."
          sleep 25
          
          echo "Connecting to external services..."
          sleep 15
          
          echo "Application ready!"
          echo "ready" > /tmp/app-ready
          
          # Simulate running application
          while true; do
            echo "Processing requests..."
            date > /tmp/last-activity
            sleep 5
          done
        ports:
        - containerPort: 8080
        # Startup probe for Java app
        startupProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 12  # Allow up to 2 minutes
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 30
          timeoutSeconds: 3
          failureThreshold: 3
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        # Add simple HTTP server for health checks
        lifecycle:
          postStart:
            exec:
              command:
              - sh
              - -c
              - |
                # Start simple HTTP server in background
                (
                  while [ ! -f /tmp/app-ready ]; do
                    sleep 1
                  done
                  
                  # Simple HTTP server simulation
                  while true; do
                    if [ -f /tmp/app-ready ]; then
                      echo "HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 25

{\"status\":\"UP\"}" | nc -l -p 8080
                    else
                      echo "HTTP/1.1 503 Service Unavailable
Content-Type: application/json
Content-Length: 27

{\"status\":\"DOWN\"}" | nc -l -p 8080
                    fi
                  done
                ) &
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
EOF

# Note: This example simulates Java app behavior with shell commands
# In real scenarios, you would use actual Java applications
kubectl apply -f java-app-startup.yaml
```

---

## Exercise 4: Startup Probe Failure Scenarios (10 minutes)

### Task 4.1: Create App with Startup Probe Issues

Create an application with problematic startup probe configuration:

```yaml
cat << EOF > problematic-startup.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: problematic-startup
  labels:
    app: problematic-startup
spec:
  replicas: 1
  selector:
    matchLabels:
      app: problematic-startup
  template:
    metadata:
      labels:
        app: problematic-startup
    spec:
      containers:
      - name: problematic-app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting application with issues..."
          
          # Simulate startup that takes 3 minutes
          sleep 180
          
          echo "App started!"
          touch /tmp/started
          
          while true; do
            echo "Running..."
            sleep 10
          done
        # Problematic startup probe - times out too early
        startupProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/started"
          initialDelaySeconds: 10
          periodSeconds: 15
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5  # Only allows 75 seconds (5 * 15s)
        # This liveness probe would kill the container without startup probe
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/started"
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
EOF

kubectl apply -f problematic-startup.yaml
```

### Task 4.2: Observe and Fix the Issue

```bash
# Monitor the problematic deployment
kubectl get pods -l app=problematic-startup -w &
WATCH_PID=$!

# Check events for startup probe failures
kubectl get events --sort-by=.metadata.creationTimestamp | grep -i startup &
EVENT_PID=$!

sleep 120

kill $WATCH_PID $EVENT_PID

# Check pod status and events
kubectl describe pod -l app=problematic-startup

# Create fixed version
cat << EOF > fixed-startup.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fixed-startup
  labels:
    app: fixed-startup
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fixed-startup
  template:
    metadata:
      labels:
        app: fixed-startup
    spec:
      containers:
      - name: fixed-app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting application..."
          
          # Same 3-minute startup
          sleep 180
          
          echo "App started!"
          touch /tmp/started
          
          while true; do
            echo "Running..."
            sleep 10
          done
        # Fixed startup probe - allows enough time
        startupProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/started"
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 15  # Allows 225 seconds (15 * 15s)
        # Same liveness probe
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/started"
          initialDelaySeconds: 0  # Disabled until startup succeeds
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
EOF

kubectl apply -f fixed-startup.yaml

# Monitor the fixed version
kubectl get pods -l app=fixed-startup -w &
WATCH_PID=$!

sleep 240  # Wait for full startup

kill $WATCH_PID

# Compare results
echo "=== Problematic Startup ==="
kubectl get pods -l app=problematic-startup
kubectl describe pod -l app=problematic-startup | grep -A 3 "Restart Count"

echo -e "\n=== Fixed Startup ==="
kubectl get pods -l app=fixed-startup
kubectl describe pod -l app=fixed-startup | grep -A 3 "Restart Count"
```

---

## Best Practices and Configuration Guidelines

### Startup Probe Best Practices

1. **Calculate Appropriate Failure Threshold**:
   ```yaml
   startupProbe:
     periodSeconds: 10
     failureThreshold: 30  # Allows 5 minutes (30 * 10s)
   ```

2. **Use Same Check as Liveness Probe**:
   ```yaml
   startupProbe:
     httpGet:
       path: /health
       port: 8080
   livenessProbe:
     httpGet:
       path: /health  # Same endpoint
       port: 8080
   ```

3. **Conservative Timing**:
   ```yaml
   startupProbe:
     initialDelaySeconds: 30    # Allow some initial time
     periodSeconds: 10          # Reasonable frequency
     timeoutSeconds: 5          # Sufficient timeout
     failureThreshold: 18       # Allow 3+ minutes total
   ```

### Probe Interaction Rules

- **Startup probe active**: Liveness and readiness probes are disabled
- **Startup probe succeeds**: Liveness and readiness probes take over
- **Startup probe fails**: Container is restarted
- **No startup probe**: Liveness and readiness probes start immediately

### Common Configuration Patterns

```yaml
# Long-running application (e.g., Java)
startupProbe:
  httpGet:
    path: /actuator/health
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 20  # 5+ minutes

# Database with migrations
startupProbe:
  tcpSocket:
    port: 5432
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 18  # 3+ minutes

# Application with custom readiness
startupProbe:
  exec:
    command: ["sh", "-c", "test -f /tmp/ready"]
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 24  # 2+ minutes
```

---

## Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Container keeps restarting | Startup probe timeout too short | Increase `failureThreshold` |
| App takes too long to start | Inefficient startup probe | Optimize `periodSeconds` |
| Probe never succeeds | Wrong probe configuration | Verify probe command/endpoint |
| Intermittent failures | Network/resource issues | Increase `timeoutSeconds` |

### Debugging Commands

```bash
# Check startup probe status
kubectl describe pod <pod-name> | grep -A 10 "Startup"

# Monitor startup probe events
kubectl get events --field-selector reason=ProbeWarning

# Test probe manually
kubectl exec <pod-name> -- <probe-command>

# Check probe timings
kubectl get pod <pod-name> -o yaml | grep -A 15 startupProbe
```

---

## Validation and Testing

### Test Your Knowledge

1. **Configure a startup probe** for a web application that takes 2 minutes to start
2. **Create a database deployment** with startup probe that waits for migrations
3. **Fix a failing startup probe** by adjusting timing parameters
4. **Compare behavior** with and without startup probes

### Verification Commands

```bash
# Check all deployments have started successfully
kubectl get deployments

# Verify no restart loops
kubectl get pods | grep -v "0/"

# Check probe configurations
kubectl get pods -o yaml | grep -A 10 startupProbe

# Monitor for startup-related events
kubectl get events | grep -i startup
```

---

## Cleanup

```bash
# Delete all resources created in this lab
kubectl delete deployment slow-startup-app postgres-with-migration java-app problematic-startup fixed-startup
kubectl delete service slow-startup-service postgres-migration-service
kubectl delete namespace startup-lab

# Reset context
kubectl config set-context --current --namespace=default
```

---

## Summary

In this lab, you learned how to:

- ✅ Configure startup probes for applications with long initialization times
- ✅ Understand how startup probes protect containers during startup
- ✅ Use startup probes with databases and complex applications
- ✅ Troubleshoot and fix startup probe timing issues
- ✅ Apply best practices for startup probe configuration
- ✅ Understand the interaction between startup, liveness, and readiness probes

**Key Takeaways**:
- Startup probes prevent premature liveness probe failures during long startups
- Once startup probe succeeds, liveness and readiness probes take over
- Calculate failure threshold to allow sufficient startup time
- Use the same health check for startup and liveness probes
- Startup probes are essential for applications with variable or long startup times

**Next Steps**: Proceed to [Lab 4: Log Analysis](lab04-log-analysis.md) to learn about analyzing container logs for debugging and monitoring.