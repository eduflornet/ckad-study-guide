# Lab 1: Configure Liveness Probes

**Objective**: Learn to configure and test liveness probes to automatically restart unhealthy containers
**Time**: 30 minutes
**Difficulty**: Beginner

---

## Learning Outcomes

By the end of this lab, you will be able to:
- Understand the purpose and behavior of liveness probes
- Configure HTTP, TCP, and exec liveness probes
- Test probe functionality with failing scenarios
- Troubleshoot probe-related issues

---

## Prerequisites

- Kubernetes cluster access
- kubectl configured
- Basic understanding of pods and containers

---

## Theory: Liveness Probes

### What are Liveness Probes?

Liveness probes determine if a container is running. If a liveness probe fails, the kubelet kills the container and restarts it according to the restart policy.

### Types of Liveness Probes

1. **HTTP GET**: Performs HTTP GET request to container
2. **TCP Socket**: Attempts TCP connection to container port
3. **Exec**: Executes command inside container

### Key Configuration Parameters

- `initialDelaySeconds`: Delay before first probe
- `periodSeconds`: How often to perform probe
- `timeoutSeconds`: Timeout for probe response
- `successThreshold`: Minimum consecutive successes
- `failureThreshold`: Consecutive failures before restart

---

## Exercise 1: HTTP Liveness Probe (10 minutes)

### Step 1: Create a Web Application with Health Endpoint

```yaml
cat << EOF > webapp-with-health.yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp-liveness
  labels:
    app: webapp
spec:
  containers:
  - name: webapp
    image: node:18-alpine
    ports:
    - containerPort: 3000
    command:
    - sh
    - -c
    - |
      cat << 'NODEAPP' > app.js
      const express = require('express');
      const app = express();
      const port = 3000;
      
      let isHealthy = true;
      let requestCount = 0;
      
      app.get('/', (req, res) => {
        requestCount++;
        res.json({
          message: 'Hello from webapp!',
          requests: requestCount,
          healthy: isHealthy,
          timestamp: new Date().toISOString()
        });
      });
      
      app.get('/health', (req, res) => {
        requestCount++;
        if (isHealthy) {
          res.status(200).json({
            status: 'healthy',
            uptime: process.uptime(),
            requests: requestCount
          });
        } else {
          res.status(500).json({
            status: 'unhealthy',
            uptime: process.uptime(),
            requests: requestCount
          });
        }
      });
      
      app.post('/fail', (req, res) => {
        isHealthy = false;
        res.json({ message: 'Application marked as unhealthy' });
      });
      
      app.post('/heal', (req, res) => {
        isHealthy = true;
        res.json({ message: 'Application marked as healthy' });
      });
      
      app.listen(port, () => {
        console.log(\`App listening on port \${port}\`);
      });
      NODEAPP
      
      npm init -y
      npm install express
      node app.js
    livenessProbe:
      httpGet:
        path: /health
        port: 3000
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
      successThreshold: 1
EOF

kubectl apply -f webapp-with-health.yaml
```

### Step 2: Monitor the Pod and Probe Status

```bash
# Watch pod status
kubectl get pods webapp-liveness -w &
WATCH_PID=$!

# Check probe configuration
kubectl describe pod webapp-liveness

# View events
kubectl get events --field-selector involvedObject.name=webapp-liveness --sort-by='.lastTimestamp'

# Stop watching after observation
sleep 30
kill $WATCH_PID
```

### Step 3: Test Liveness Probe Failure

```bash
# Port forward to access the application
kubectl port-forward webapp-liveness 3000:3000 &
PF_PID=$!

# Check current health status
curl http://localhost:3000/health

# Mark application as unhealthy
curl -X POST http://localhost:3000/fail

# Check health status again
curl http://localhost:3000/health

# Stop port forwarding
kill $PF_PID

# Monitor pod restarts
kubectl get pods webapp-liveness -w
```

### Step 4: Observe Container Restart

```bash
# Check restart count
kubectl get pod webapp-liveness -o jsonpath='{.status.containerStatuses[0].restartCount}'

# View detailed events
kubectl describe pod webapp-liveness

# Check logs from previous container (after restart)
kubectl logs webapp-liveness --previous
```

---

## Exercise 2: TCP Liveness Probe (5 minutes)

### Step 1: Create a TCP Server with Liveness Probe

```yaml
cat << EOF > tcp-liveness.yaml
apiVersion: v1
kind: Pod
metadata:
  name: tcp-server-liveness
  labels:
    app: tcp-server
spec:
  containers:
  - name: tcp-server
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      # Create a simple TCP server that can be controlled
      echo "Starting TCP server on port 8080"
      while true; do
        if [ -f /tmp/stop ]; then
          echo "Server stopped"
          sleep 60  # Keep container alive but don't listen
        else
          echo "Server listening..." | nc -l -p 8080
        fi
      done
    ports:
    - containerPort: 8080
    livenessProbe:
      tcpSocket:
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 2
EOF

kubectl apply -f tcp-liveness.yaml
```

### Step 2: Test TCP Probe

```bash
# Check initial status
kubectl get pod tcp-server-liveness

# Test TCP connection
kubectl exec tcp-server-liveness -- nc -z localhost 8080

# Stop the TCP server to trigger probe failure
kubectl exec tcp-server-liveness -- touch /tmp/stop

# Monitor pod for restart
kubectl get pod tcp-server-liveness -w
```

---

## Exercise 3: Exec Liveness Probe (10 minutes)

### Step 1: Create a Pod with Command-Based Health Check

```yaml
cat << EOF > exec-liveness.yaml
apiVersion: v1
kind: Pod
metadata:
  name: exec-liveness
  labels:
    app: exec-probe
spec:
  containers:
  - name: app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      # Create a health file initially
      touch /tmp/healthy
      echo "Application started, health file created"
      
      # Simulate application work
      while true; do
        if [ -f /tmp/healthy ]; then
          echo "Application running normally..."
          sleep 30
        else
          echo "Application in unhealthy state..."
          sleep 30
        fi
      done
    livenessProbe:
      exec:
        command:
        - test
        - -f
        - /tmp/healthy
      initialDelaySeconds: 10
      periodSeconds: 15
      timeoutSeconds: 5
      failureThreshold: 2
EOF

kubectl apply -f exec-liveness.yaml
```

### Step 2: Test Exec Probe Functionality

```bash
# Check initial pod status
kubectl get pod exec-liveness

# Verify health file exists
kubectl exec exec-liveness -- ls -la /tmp/healthy

# Test the probe command manually
kubectl exec exec-liveness -- test -f /tmp/healthy && echo "Health check passed" || echo "Health check failed"

# Remove health file to trigger failure
kubectl exec exec-liveness -- rm /tmp/healthy

# Monitor for restart
kubectl get pod exec-liveness -w
```

---

## Exercise 4: Advanced Liveness Probe Configuration (5 minutes)

### Step 1: Create a Pod with Complex Probe Logic

```yaml
cat << EOF > advanced-liveness.yaml
apiVersion: v1
kind: Pod
metadata:
  name: advanced-liveness
  labels:
    app: advanced-app
spec:
  containers:
  - name: app
    image: alpine:3.18
    command:
    - sh
    - -c
    - |
      # Install curl for HTTP checks
      apk add --no-cache curl
      
      # Start a simple HTTP server in background
      cat << 'SERVER' > server.py
      import http.server
      import socketserver
      import threading
      import time
      import os
      
      class HealthHandler(http.server.BaseHTTPRequestHandler):
          def do_GET(self):
              if self.path == '/health':
                  # Check multiple health indicators
                  cpu_ok = os.path.exists('/tmp/cpu_ok')
                  memory_ok = os.path.exists('/tmp/memory_ok')
                  disk_ok = os.path.exists('/tmp/disk_ok')
                  
                  if cpu_ok and memory_ok and disk_ok:
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      self.wfile.write(b'{"status":"healthy","checks":{"cpu":true,"memory":true,"disk":true}}')
                  else:
                      self.send_response(500)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      self.wfile.write(b'{"status":"unhealthy","checks":{"cpu":' + str(cpu_ok).lower().encode() + b',"memory":' + str(memory_ok).lower().encode() + b',"disk":' + str(disk_ok).lower().encode() + b'}}')
              else:
                  self.send_response(404)
                  self.end_headers()
      
      # Create initial health indicators
      os.system('touch /tmp/cpu_ok /tmp/memory_ok /tmp/disk_ok')
      
      # Start server
      httpd = socketserver.TCPServer(("", 8080), HealthHandler)
      httpd.serve_forever()
      SERVER
      
      python3 server.py
    ports:
    - containerPort: 8080
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
        httpHeaders:
        - name: User-Agent
          value: Kubernetes-Liveness-Probe
      initialDelaySeconds: 20
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
      successThreshold: 1
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
EOF

kubectl apply -f advanced-liveness.yaml
```

### Step 2: Test Advanced Health Checks

```bash
# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/advanced-liveness --timeout=60s

# Test health endpoint
kubectl port-forward advanced-liveness 8080:8080 &
PF_PID=$!
sleep 3

# Check healthy status
curl http://localhost:8080/health

# Simulate component failure
kubectl exec advanced-liveness -- rm /tmp/cpu_ok

# Check health status again
curl http://localhost:8080/health

# Clean up
kill $PF_PID
```

---

## Troubleshooting Common Issues

### Issue 1: Probe Timing Problems

```bash
# Check probe configuration
kubectl describe pod webapp-liveness | grep -A 10 "Liveness:"

# Common timing issues:
# - initialDelaySeconds too short (container not ready)
# - periodSeconds too frequent (unnecessary load)
# - timeoutSeconds too short (network delays)
# - failureThreshold too low (false positives)
```

### Issue 2: Application Not Ready for Probes

```yaml
# Example fix: Increase initial delay
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 30  # Increased from 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Issue 3: Debugging Probe Failures

```bash
# Check probe logs in events
kubectl get events --field-selector reason=Unhealthy

# Check container logs for health endpoint errors
kubectl logs webapp-liveness

# Test health endpoint manually
kubectl exec webapp-liveness -- curl -f http://localhost:3000/health

# Check port accessibility
kubectl exec webapp-liveness -- netstat -tlnp | grep 3000
```

---

## Validation and Testing

### Test Your Understanding

1. **Create a pod with an HTTP liveness probe** that checks `/api/health` every 30 seconds
2. **Configure timeouts** appropriately for a slow-starting application
3. **Simulate probe failures** and observe restart behavior
4. **Debug a failing liveness probe** using kubectl commands

### Verification Commands

```bash
# Check all pods with liveness probes
kubectl get pods -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,STATUS:.status.phase

# View probe configurations
kubectl get pod webapp-liveness -o yaml | grep -A 10 livenessProbe

# Monitor probe events
kubectl get events --field-selector reason=Unhealthy,reason=Started --sort-by='.lastTimestamp'

# Check probe success/failure rates
kubectl describe pod webapp-liveness | grep -A 5 "Events:"
```

---

## Cleanup

```bash
# Delete all lab resources
kubectl delete pod webapp-liveness tcp-server-liveness exec-liveness advanced-liveness

# Remove YAML files
rm -f webapp-with-health.yaml tcp-liveness.yaml exec-liveness.yaml advanced-liveness.yaml
```

---

## Key Takeaways

1. **Liveness probes restart containers** when health checks fail
2. **Proper timing configuration** prevents false restarts
3. **Different probe types** suit different application architectures
4. **Health endpoints should be lightweight** and quick to respond
5. **Monitor restart counts** to identify probe issues
6. **Use events and logs** for troubleshooting probe failures

---

## Next Steps

- Proceed to [Lab 2: Readiness Probes](lab02-readiness-probes.md)
- Learn about [Startup Probes](lab03-startup-probes.md)
- Practice [Combined Health Checks](../mocks/mock02-health-checks.md)

---

## Additional Resources

- [Kubernetes Probes Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Container Restart Policy](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy)