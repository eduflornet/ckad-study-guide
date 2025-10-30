# Lab 4: Container Log Analysis

**Objective**: Master container log analysis techniques for troubleshooting and monitoring applications
**Time**: 35 minutes
**Difficulty**: Beginner to Intermediate

---

## Learning Outcomes

By the end of this lab, you will be able to:
- Use kubectl logs effectively for debugging
- Analyze logs from multi-container pods
- Stream and filter container logs
- Handle log rotation and retention
- Debug common logging issues
- Implement structured logging practices

---

## Prerequisites

- Kubernetes cluster access
- kubectl configured
- Basic understanding of pods and containers
- Familiarity with common log formats

---

## Theory: Container Logging in Kubernetes

### How Container Logging Works

1. **Container stdout/stderr** → captured by container runtime
2. **Logs stored** on node filesystem (`/var/log/pods/`)
3. **kubectl logs** → queries kubelet → retrieves logs
4. **Log rotation** → managed by container runtime
5. **Centralized logging** → optional (Fluentd, Elasticsearch, etc.)

### Log Lifecycle

- **Creation**: Container writes to stdout/stderr
- **Storage**: Stored on node with automatic rotation
- **Retention**: Based on cluster configuration
- **Access**: Via kubectl logs or log aggregation systems

---

## Exercise 1: Basic Log Operations (10 minutes)

### Step 1: Create Applications with Different Log Patterns

```yaml
cat << EOF > logging-apps.yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-logger
  labels:
    app: simple-logger
spec:
  containers:
  - name: logger
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting simple logger application..."
      counter=0
      while true; do
        counter=\$((counter + 1))
        echo "\$(date): Log message #\$counter - Application running normally"
        
        # Simulate different log levels
        if [ \$((counter % 5)) -eq 0 ]; then
          echo "\$(date): WARN - This is a warning message #\$counter" >&2
        fi
        
        if [ \$((counter % 10)) -eq 0 ]; then
          echo "\$(date): ERROR - This is an error message #\$counter" >&2
        fi
        
        sleep 2
      done
---
apiVersion: v1
kind: Pod
metadata:
  name: structured-logger
  labels:
    app: structured-logger
spec:
  containers:
  - name: app
    image: node:18-alpine
    command:
    - sh
    - -c
    - |
      cat << 'NODEAPP' > logger.js
      const winston = require('winston');
      
      // Configure structured logging
      const logger = winston.createLogger({
        level: 'info',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.errors({ stack: true }),
          winston.format.json()
        ),
        transports: [
          new winston.transports.Console()
        ]
      });
      
      let requestCount = 0;
      let errorCount = 0;
      
      function logActivity() {
        requestCount++;
        
        // Normal operations
        logger.info('Processing request', {
          requestId: \`req-\${requestCount}\`,
          method: 'GET',
          path: '/api/data',
          duration: Math.floor(Math.random() * 100),
          userAgent: 'kubectl/test'
        });
        
        // Occasional warnings
        if (requestCount % 7 === 0) {
          logger.warn('High response time detected', {
            requestId: \`req-\${requestCount}\`,
            responseTime: 850,
            threshold: 500
          });
        }
        
        // Occasional errors
        if (requestCount % 15 === 0) {
          errorCount++;
          logger.error('Database connection failed', {
            requestId: \`req-\${requestCount}\`,
            error: 'Connection timeout',
            dbHost: 'postgres.internal',
            retryCount: 3,
            errorCode: 'DB_TIMEOUT'
          });
        }
        
        // Application metrics
        if (requestCount % 20 === 0) {
          logger.info('Application metrics', {
            type: 'metrics',
            totalRequests: requestCount,
            errorRate: (errorCount / requestCount * 100).toFixed(2) + '%',
            uptime: process.uptime(),
            memoryUsage: process.memoryUsage()
          });
        }
      }
      
      // Start logging activity
      console.log('Starting structured logging application...');
      setInterval(logActivity, 1000);
      NODEAPP
      
      npm init -y
      npm install winston
      node logger.js
---
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-logger
  labels:
    app: multi-container-logger
spec:
  containers:
  - name: web
    image: nginx:1.21-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: nginx-logs
      mountPath: /var/log/nginx
  - name: log-processor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting log processor..."
      while true; do
        # Generate some web traffic simulation
        echo "\$(date): [LOG-PROCESSOR] Processing web logs..."
        echo "\$(date): [LOG-PROCESSOR] Found 5 new requests in access.log"
        echo "\$(date): [LOG-PROCESSOR] Detected 1 404 error"
        echo "\$(date): [LOG-PROCESSOR] Average response time: 125ms"
        sleep 10
      done
    volumeMounts:
    - name: nginx-logs
      mountPath: /shared-logs
  volumes:
  - name: nginx-logs
    emptyDir: {}
EOF

kubectl apply -f logging-apps.yaml
```

### Step 2: Basic Log Viewing Commands

```bash
# Wait for pods to start
kubectl wait --for=condition=Ready pod/simple-logger pod/structured-logger pod/multi-container-logger --timeout=60s

# View logs from simple logger
echo "=== Simple Logger Logs ==="
kubectl logs simple-logger

# View last 10 lines
echo "=== Last 10 Lines ==="
kubectl logs simple-logger --tail=10

# View logs from specific time
echo "=== Logs from last 2 minutes ==="
kubectl logs simple-logger --since=2m

# View structured logs
echo "=== Structured Logger Logs ==="
kubectl logs structured-logger --tail=5
```

### Step 3: Multi-Container Log Access

```bash
# List containers in multi-container pod
kubectl get pod multi-container-logger -o jsonpath='{.spec.containers[*].name}'

# View logs from specific container
echo "=== Web Container Logs ==="
kubectl logs multi-container-logger -c web --tail=5

echo "=== Log Processor Container Logs ==="
kubectl logs multi-container-logger -c log-processor --tail=5

# View logs from all containers
echo "=== All Container Logs ==="
kubectl logs multi-container-logger --all-containers=true --tail=3
```

---

## Exercise 2: Advanced Log Operations (10 minutes)

### Step 1: Log Streaming and Following

```bash
# Follow logs in real-time
echo "Following simple logger (Ctrl+C to stop)..."
timeout 15 kubectl logs simple-logger -f || true

# Follow logs with timestamps
echo "Following with timestamps..."
timeout 10 kubectl logs structured-logger -f --timestamps || true

# Follow logs from multiple containers
echo "Following multi-container logs..."
timeout 10 kubectl logs multi-container-logger --all-containers=true -f || true
```

### Step 2: Log Filtering and Processing

```bash
# Save logs to file for processing
kubectl logs structured-logger --tail=50 > structured-logs.json

# Process JSON logs with jq
echo "=== Error Logs Only ==="
cat structured-logs.json | jq 'select(.level == "error")'

echo "=== High Response Time Warnings ==="
cat structured-logs.json | jq 'select(.level == "warn" and .message | contains("response time"))'

echo "=== Request IDs from Errors ==="
cat structured-logs.json | jq -r 'select(.level == "error") | .requestId'

# Filter logs using grep
echo "=== Error Messages from Simple Logger ==="
kubectl logs simple-logger | grep "ERROR"

echo "=== Warning and Error Messages ==="
kubectl logs simple-logger 2>&1 | grep -E "(WARN|ERROR)"
```

### Step 3: Log Aggregation and Analysis

```bash
# Create a log analysis script
cat << 'SCRIPT' > analyze-logs.sh
#!/bin/bash

echo "=== Log Analysis Report ==="
echo "Generated at: $(date)"
echo ""

# Analyze simple logger
echo "--- Simple Logger Analysis ---"
SIMPLE_LOGS=$(kubectl logs simple-logger 2>&1)
TOTAL_LINES=$(echo "$SIMPLE_LOGS" | wc -l)
ERROR_COUNT=$(echo "$SIMPLE_LOGS" | grep -c "ERROR" || echo "0")
WARN_COUNT=$(echo "$SIMPLE_LOGS" | grep -c "WARN" || echo "0")

echo "Total log lines: $TOTAL_LINES"
echo "Error count: $ERROR_COUNT"
echo "Warning count: $WARN_COUNT"
echo ""

# Analyze structured logger
echo "--- Structured Logger Analysis ---"
kubectl logs structured-logger --tail=100 > temp-structured.json
TOTAL_REQUESTS=$(cat temp-structured.json | jq -r 'select(.requestId) | .requestId' | wc -l)
ERRORS=$(cat temp-structured.json | jq -r 'select(.level == "error")' | wc -l)
WARNINGS=$(cat temp-structured.json | jq -r 'select(.level == "warn")' | wc -l)

echo "Total requests logged: $TOTAL_REQUESTS"
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ $TOTAL_REQUESTS -gt 0 ]; then
    ERROR_RATE=$(echo "scale=2; $ERRORS * 100 / $TOTAL_REQUESTS" | bc -l 2>/dev/null || echo "N/A")
    echo "Error rate: ${ERROR_RATE}%"
fi

echo ""
echo "--- Recent Error Details ---"
cat temp-structured.json | jq -r 'select(.level == "error") | "\(.timestamp): \(.message) (\(.errorCode))"' | tail -3

rm -f temp-structured.json
SCRIPT

chmod +x analyze-logs.sh
./analyze-logs.sh
```

---

## Exercise 3: Debugging with Logs (10 minutes)

### Step 1: Create a Problematic Application

```yaml
cat << EOF > problematic-app.yaml
apiVersion: v1
kind: Pod
metadata:
  name: problematic-app
  labels:
    app: problematic-app
spec:
  containers:
  - name: app
    image: python:3.9-alpine
    command:
    - python
    - -c
    - |
      import time
      import random
      import sys
      import traceback
      
      print("Starting problematic application...")
      print("Application initialized successfully")
      
      # Simulate various issues
      issues = [
          "database_connection_failed",
          "memory_leak_detected", 
          "api_timeout",
          "config_file_missing",
          "permission_denied"
      ]
      
      counter = 0
      while True:
          counter += 1
          
          # Normal operation
          if counter % 3 == 0:
              print(f"INFO: Processing request #{counter}")
          
          # Random issues
          if random.random() < 0.3:  # 30% chance of issue
              issue = random.choice(issues)
              if issue == "database_connection_failed":
                  print(f"ERROR: Database connection failed on request #{counter}", file=sys.stderr)
                  print(f"ERROR: Connection string: postgresql://user:pass@db:5432/app", file=sys.stderr)
              elif issue == "memory_leak_detected":
                  print(f"WARN: Memory usage high: {random.randint(80, 95)}%", file=sys.stderr)
              elif issue == "api_timeout":
                  print(f"ERROR: API call timeout after 30s on request #{counter}", file=sys.stderr)
              elif issue == "config_file_missing":
                  print(f"ERROR: Configuration file not found: /app/config.yaml", file=sys.stderr)
              elif issue == "permission_denied":
                  print(f"ERROR: Permission denied accessing /var/data/", file=sys.stderr)
          
          # Catastrophic failure simulation
          if counter == 25:
              print("FATAL: Unhandled exception occurred!", file=sys.stderr)
              try:
                  raise Exception("Critical system failure")
              except Exception as e:
                  traceback.print_exc()
              sys.exit(1)
          
          time.sleep(2)
  restartPolicy: Always
EOF

kubectl apply -f problematic-app.yaml
```

### Step 2: Debug Using Log Analysis

```bash
# Wait for the app to start and run for a bit
sleep 10

# Check current status
kubectl get pod problematic-app

# Analyze recent logs
echo "=== Recent Application Logs ==="
kubectl logs problematic-app --tail=20

# Check for errors specifically
echo "=== Error Analysis ==="
kubectl logs problematic-app 2>&1 | grep -E "(ERROR|FATAL|WARN)"

# Wait for the pod to crash and restart
echo "Waiting for pod to crash and restart..."
kubectl wait --for=condition=Ready pod/problematic-app --timeout=60s || echo "Pod might have crashed"

# Check restart count
RESTART_COUNT=$(kubectl get pod problematic-app -o jsonpath='{.status.containerStatuses[0].restartCount}')
echo "Restart count: $RESTART_COUNT"

# Analyze logs from previous container instance
if [ "$RESTART_COUNT" -gt 0 ]; then
    echo "=== Logs from Previous Container (before crash) ==="
    kubectl logs problematic-app --previous
    
    echo "=== Last few lines before crash ==="
    kubectl logs problematic-app --previous --tail=10
fi
```

### Step 3: Log Pattern Analysis

```bash
# Create comprehensive log analysis
cat << 'ANALYSIS' > log-analysis.sh
#!/bin/bash

POD_NAME="problematic-app"
echo "=== Comprehensive Log Analysis for $POD_NAME ==="
echo ""

# Check pod status
echo "--- Pod Status ---"
kubectl get pod $POD_NAME -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,READY:.status.conditions[1].status

echo ""
echo "--- Current Logs Analysis ---"
CURRENT_LOGS=$(kubectl logs $POD_NAME 2>&1)

if [ -n "$CURRENT_LOGS" ]; then
    echo "Total log lines: $(echo "$CURRENT_LOGS" | wc -l)"
    echo "Error count: $(echo "$CURRENT_LOGS" | grep -c "ERROR" || echo "0")"
    echo "Warning count: $(echo "$CURRENT_LOGS" | grep -c "WARN" || echo "0")"
    echo "Fatal count: $(echo "$CURRENT_LOGS" | grep -c "FATAL" || echo "0")"
    
    echo ""
    echo "--- Error Breakdown ---"
    echo "$CURRENT_LOGS" | grep "ERROR" | cut -d':' -f3- | sort | uniq -c | sort -nr
    
    echo ""
    echo "--- Warning Breakdown ---"
    echo "$CURRENT_LOGS" | grep "WARN" | cut -d':' -f3- | sort | uniq -c | sort -nr
fi

# Check previous logs if container restarted
RESTART_COUNT=$(kubectl get pod $POD_NAME -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
if [ "$RESTART_COUNT" -gt 0 ]; then
    echo ""
    echo "--- Previous Container Logs (Crash Analysis) ---"
    PREV_LOGS=$(kubectl logs $POD_NAME --previous 2>&1)
    
    if [ -n "$PREV_LOGS" ]; then
        echo "Previous container log lines: $(echo "$PREV_LOGS" | wc -l)"
        echo ""
        echo "--- Last 5 lines before crash ---"
        echo "$PREV_LOGS" | tail -5
        
        echo ""
        echo "--- Fatal errors in previous run ---"
        echo "$PREV_LOGS" | grep -E "(FATAL|Exception|Traceback)"
    fi
fi

echo ""
echo "--- Recent Events ---"
kubectl get events --field-selector involvedObject.name=$POD_NAME --sort-by='.lastTimestamp' | tail -5
ANALYSIS

chmod +x log-analysis.sh
./log-analysis.sh
```

---

## Exercise 4: Log Troubleshooting Scenarios (5 minutes)

### Step 1: Application Not Producing Logs

```yaml
cat << EOF > silent-app.yaml
apiVersion: v1
kind: Pod
metadata:
  name: silent-app
  labels:
    app: silent-app
spec:
  containers:
  - name: app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      # Application that writes to files instead of stdout/stderr
      mkdir -p /app/logs
      while true; do
        echo "$(date): Application running" >> /app/logs/app.log
        echo "$(date): Debug info" >> /app/logs/debug.log
        sleep 5
      done
EOF

kubectl apply -f silent-app.yaml
```

### Step 2: Debug Silent Application

```bash
# Try to get logs - will be empty
echo "=== Silent App Logs (should be empty) ==="
kubectl logs silent-app

# Check where logs are actually being written
echo "=== Checking application log files ==="
kubectl exec silent-app -- ls -la /app/logs/

# Read actual log files
echo "=== Application Log Content ==="
kubectl exec silent-app -- cat /app/logs/app.log

echo "=== Debug Log Content ==="
kubectl exec silent-app -- cat /app/logs/debug.log

# Demonstrate how to fix - redirect to stdout
kubectl exec silent-app -- sh -c 'tail -f /app/logs/app.log &'
```

### Step 3: Log Permission Issues

```yaml
cat << EOF > permission-issue.yaml
apiVersion: v1
kind: Pod
metadata:
  name: permission-issue
  labels:
    app: permission-issue
spec:
  securityContext:
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
  containers:
  - name: app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting application with user $(id)"
      
      # Try to write to a restricted location
      if ! echo "Test log" > /var/log/app.log 2>/dev/null; then
        echo "ERROR: Cannot write to /var/log/app.log - permission denied" >&2
        echo "INFO: Falling back to user directory" 
        echo "$(date): Application started successfully" > /tmp/app.log
      fi
      
      while true; do
        echo "$(date): Application running normally"
        echo "$(date): User: $(id)" >> /tmp/app.log 2>/dev/null || echo "Log write failed" >&2
        sleep 10
      done
EOF

kubectl apply -f permission-issue.yaml
```

### Step 4: Analyze Permission Issues

```bash
# Check logs for permission errors
echo "=== Permission Issue Logs ==="
kubectl logs permission-issue

# Check user context
echo "=== User Context Check ==="
kubectl exec permission-issue -- id

# Check file permissions
echo "=== File Permissions ==="
kubectl exec permission-issue -- ls -la /var/log/ || echo "Cannot list /var/log/"
kubectl exec permission-issue -- ls -la /tmp/
```

---

## Troubleshooting Common Log Issues

### Issue 1: No Logs Appearing

```bash
# Check if container is running
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].state}'

# Check if application writes to stdout/stderr
kubectl exec <pod-name> -- ps aux

# Verify log path
kubectl describe pod <pod-name> | grep -A 5 "Mounts:"
```

### Issue 2: Logs Truncated or Missing

```bash
# Check log rotation settings
kubectl exec <pod-name> -- df -h
kubectl describe node <node-name> | grep -A 10 "System Info:"

# Check container runtime logs
kubectl get events --field-selector involvedObject.name=<pod-name>
```

### Issue 3: Performance Impact from Logging

```bash
# Monitor resource usage
kubectl top pod <pod-name>

# Check log volume
kubectl logs <pod-name> --tail=1000 | wc -l

# Analyze log patterns for optimization
kubectl logs <pod-name> --tail=100 | head -20
```

---

## Best Practices for Container Logging

### 1. Application Logging Guidelines

```yaml
# Good: Write to stdout/stderr
containers:
- name: app
  image: myapp:latest
  command: ["myapp"]  # App writes to stdout/stderr directly

# Avoid: Writing to files inside container
# Unless using proper volume mounts and log collection
```

### 2. Structured Logging Example

```javascript
// Good: Structured JSON logging
console.log(JSON.stringify({
  timestamp: new Date().toISOString(),
  level: 'info',
  message: 'User authenticated',
  userId: 12345,
  requestId: 'req-abc123'
}));

// Avoid: Unstructured text
console.log('User 12345 authenticated at ' + new Date());
```

### 3. Log Level Management

```yaml
containers:
- name: app
  env:
  - name: LOG_LEVEL
    value: "info"  # Configurable log level
  - name: LOG_FORMAT
    value: "json"  # Structured format
```

---

## Validation and Testing

### Test Your Understanding

1. **Retrieve logs** from a multi-container pod for specific containers
2. **Filter logs** to find error messages and warnings
3. **Analyze log patterns** to identify application issues
4. **Debug a crashing application** using previous container logs

### Verification Commands

```bash
# Test log retrieval skills
kubectl logs <pod-name> --tail=20 --timestamps
kubectl logs <pod-name> -c <container-name> --since=5m
kubectl logs <pod-name> --previous --tail=10

# Test log analysis
kubectl logs <pod-name> | grep -E "(ERROR|WARN|FATAL)"
kubectl logs <pod-name> --tail=100 | jq 'select(.level == "error")'

# Test troubleshooting
kubectl describe pod <pod-name> | grep -A 10 "Events:"
kubectl get events --field-selector involvedObject.name=<pod-name>
```

---

## Cleanup

```bash
# Delete all lab resources
kubectl delete pod simple-logger structured-logger multi-container-logger problematic-app silent-app permission-issue

# Remove files
rm -f logging-apps.yaml problematic-app.yaml silent-app.yaml permission-issue.yaml
rm -f structured-logs.json analyze-logs.sh log-analysis.sh
```

---

## Key Takeaways

1. **kubectl logs** is the primary tool for accessing container logs
2. **Multi-container pods** require specifying container names
3. **Structured logging** enables better analysis and filtering
4. **Previous container logs** are crucial for debugging crashes
5. **Log streaming** helps with real-time troubleshooting
6. **Applications should write to stdout/stderr** for Kubernetes log collection

---

## Next Steps

- Proceed to [Lab 5: Resource Monitoring](lab05-resource-monitoring.md)
- Learn about [Application Metrics](lab06-metrics.md)
- Practice [Pod Debugging](lab07-pod-debugging.md)

---

## Additional Resources

- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [kubectl logs Command Reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#logs)
- [Container Runtime Logging](https://kubernetes.io/docs/concepts/cluster-administration/logging/#logging-at-the-node-level)