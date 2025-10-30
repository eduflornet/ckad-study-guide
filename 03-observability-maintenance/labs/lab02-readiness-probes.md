# Lab 2: Readiness Probes

**Objective**: Configure and understand readiness probes to control traffic flow to pods
**Time**: 30 minutes
**Difficulty**: Intermediate

---

## Learning Objectives

By the end of this lab, you will be able to:
- Configure HTTP, TCP, and command-based readiness probes
- Understand the difference between liveness and readiness probes
- Control service endpoints based on pod readiness
- Troubleshoot readiness probe failures
- Implement best practices for readiness checks

---

## Prerequisites

- Kubernetes cluster access
- kubectl CLI configured
- Understanding of pods and services
- Basic knowledge of HTTP status codes

---

## Lab Environment Setup

Create a dedicated namespace for this lab:

```bash
kubectl create namespace readiness-lab
kubectl config set-context --current --namespace=readiness-lab
```

---

## Exercise 1: Basic HTTP Readiness Probe (10 minutes)

### Task 1.1: Create a Web Application with Readiness Endpoint

Create a simple web application that includes a readiness endpoint:

```yaml
cat << EOF > web-app-with-readiness.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-ready
  labels:
    app: web-app-ready
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app-ready
  template:
    metadata:
      labels:
        app: web-app-ready
    spec:
      containers:
      - name: web-server
        image: nginx:1.21
        ports:
        - containerPort: 80
        # Readiness probe configuration
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        # Create a custom readiness endpoint
        lifecycle:
          postStart:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                # Create a custom nginx config with readiness endpoint
                cat > /etc/nginx/conf.d/readiness.conf << 'NGINX_EOF'
                server {
                    listen 80;
                    
                    location /ready {
                        access_log off;
                        return 200 "Ready\n";
                        add_header Content-Type text/plain;
                    }
                    
                    location / {
                        root   /usr/share/nginx/html;
                        index  index.html index.htm;
                    }
                }
                NGINX_EOF
                
                # Remove default config and reload
                rm -f /etc/nginx/conf.d/default.conf
                nginx -s reload || true
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-ready-service
spec:
  selector:
    app: web-app-ready
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f web-app-with-readiness.yaml
```

### Task 1.2: Monitor Readiness Status

Observe how readiness probes affect pod status:

```bash
# Watch pod status during startup
kubectl get pods -w &
WATCH_PID=$!

# Check detailed pod information
kubectl describe pods -l app=web-app-ready

# Stop watching after 30 seconds
sleep 30
kill $WATCH_PID
```

### Task 1.3: Test Service Endpoints

Verify that only ready pods receive traffic:

```bash
# Check service endpoints
kubectl get endpoints web-app-ready-service

# Test the readiness endpoint directly
kubectl port-forward svc/web-app-ready-service 8080:80 &
PF_PID=$!
sleep 3

curl http://localhost:8080/ready
curl http://localhost:8080/

kill $PF_PID
```

---

## Exercise 2: TCP Socket Readiness Probe (8 minutes)

### Task 2.1: Create Database with TCP Readiness Check

Deploy a database service with TCP socket readiness probe:

```yaml
cat << EOF > database-tcp-ready.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-db
  labels:
    app: postgres-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-db
  template:
    metadata:
      labels:
        app: postgres-db
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
        # TCP socket readiness probe
        readinessProbe:
          tcpSocket:
            port: 5432
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        # Also add liveness probe for comparison
        livenessProbe:
          tcpSocket:
            port: 5432
          initialDelaySeconds: 30
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
  name: postgres-service
spec:
  selector:
    app: postgres-db
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

kubectl apply -f database-tcp-ready.yaml
```

### Task 2.2: Monitor Database Readiness

```bash
# Monitor the database startup
kubectl get pods -l app=postgres-db -w &
WATCH_PID=$!

# Check logs to see database initialization
kubectl logs -f deployment/postgres-db &
LOG_PID=$!

sleep 45

# Stop monitoring
kill $WATCH_PID $LOG_PID

# Check final status
kubectl describe pod -l app=postgres-db
kubectl get endpoints postgres-service
```

---

## Exercise 3: Command-Based Readiness Probe (7 minutes)

### Task 3.1: Create Application with Custom Readiness Check

Deploy an application that uses a command for readiness checking:

```yaml
cat << EOF > app-command-ready.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-command-ready
  labels:
    app: app-command-ready
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app-command-ready
  template:
    metadata:
      labels:
        app: app-command-ready
    spec:
      containers:
      - name: app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          # Simulate application startup
          echo "Starting application..."
          sleep 20
          echo "Application initialization complete"
          
          # Create readiness indicator file
          touch /tmp/ready
          
          # Keep container running and simulate work
          while true; do
            echo "Application is running..."
            sleep 30
          done
        # Command-based readiness probe
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/ready"
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 2
          successThreshold: 1
          failureThreshold: 2
        # Liveness probe to keep container alive
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "ps aux | grep -v grep | grep -q 'sleep 30'"
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: app-command-service
spec:
  selector:
    app: app-command-ready
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
EOF

kubectl apply -f app-command-ready.yaml
```

### Task 3.2: Observe Readiness Transition

```bash
# Monitor readiness transition
kubectl get pods -l app=app-command-ready -w &
WATCH_PID=$!

# Check logs to see application startup
kubectl logs -f deployment/app-command-ready &
LOG_PID=$!

sleep 40

kill $WATCH_PID $LOG_PID

# Check final readiness status
kubectl describe pods -l app=app-command-ready | grep -A 10 "Readiness"
```

---

## Exercise 4: Readiness vs Liveness Comparison (10 minutes)

### Task 4.1: Create Pod with Both Probes

Create a deployment that demonstrates the difference between liveness and readiness:

```yaml
cat << EOF > probe-comparison.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: probe-demo
  labels:
    app: probe-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: probe-demo
  template:
    metadata:
      labels:
        app: probe-demo
    spec:
      containers:
      - name: demo-app
        image: nginx:1.21
        ports:
        - containerPort: 80
        # Readiness probe - controls traffic
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 2
        # Liveness probe - controls restarts
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        lifecycle:
          postStart:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                # Setup custom endpoints
                cat > /etc/nginx/conf.d/probes.conf << 'NGINX_EOF'
                server {
                    listen 80;
                    
                    location /ready {
                        access_log off;
                        # Check if ready file exists
                        try_files /tmp/ready =503;
                    }
                    
                    location /health {
                        access_log off;
                        return 200 "Healthy\n";
                        add_header Content-Type text/plain;
                    }
                    
                    location / {
                        root   /usr/share/nginx/html;
                        index  index.html index.htm;
                    }
                }
                NGINX_EOF
                
                rm -f /etc/nginx/conf.d/default.conf
                nginx -s reload
                
                # Initially not ready
                sleep 10
                echo "ready" > /tmp/ready
---
apiVersion: v1
kind: Service
metadata:
  name: probe-demo-service
spec:
  selector:
    app: probe-demo
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f probe-comparison.yaml
```

### Task 4.2: Simulate Readiness Failure

```bash
# Monitor initial startup
kubectl get pods -l app=probe-demo -w &
WATCH_PID=$!

sleep 20
kill $WATCH_PID

# Check endpoints - should show ready pod
kubectl get endpoints probe-demo-service

# Simulate readiness failure (remove ready file)
POD_NAME=$(kubectl get pods -l app=probe-demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD_NAME -- rm -f /tmp/ready

# Monitor for readiness failure
kubectl get pods -l app=probe-demo -w &
WATCH_PID=$!

sleep 30
kill $WATCH_PID

# Check endpoints - should be empty now
kubectl get endpoints probe-demo-service

# Restore readiness
kubectl exec $POD_NAME -- sh -c 'echo "ready" > /tmp/ready'

sleep 15

# Check endpoints - should show pod again
kubectl get endpoints probe-demo-service
```

---

## Exercise 5: Troubleshooting Readiness Issues (15 minutes)

### Task 5.1: Create Problematic Deployment

Create a deployment with readiness probe issues:

```yaml
cat << EOF > problematic-readiness.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: problematic-app
  labels:
    app: problematic-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: problematic-app
  template:
    metadata:
      labels:
        app: problematic-app
    spec:
      containers:
      - name: slow-app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting slow application..."
          # Simulate very slow startup (90 seconds)
          sleep 90
          echo "App ready!"
          
          # Start a simple HTTP server simulation
          while true; do
            echo "Server running..."
            sleep 10
          done
        ports:
        - containerPort: 8080
        # Problematic readiness probe - too aggressive
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "wget -q --spider http://localhost:8080/health || exit 1"
          initialDelaySeconds: 5  # Too short
          periodSeconds: 2        # Too frequent
          timeoutSeconds: 1       # Too short
          successThreshold: 1
          failureThreshold: 2     # Too low
---
apiVersion: v1
kind: Service
metadata:
  name: problematic-service
spec:
  selector:
    app: problematic-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
EOF

kubectl apply -f problematic-readiness.yaml
```

### Task 5.2: Diagnose and Fix Issues

```bash
# Monitor the problematic deployment
kubectl get pods -l app=problematic-app -w &
WATCH_PID=$!

sleep 30
kill $WATCH_PID

# Diagnose the issues
echo "=== Pod Status ==="
kubectl get pods -l app=problematic-app

echo -e "\n=== Pod Describe ==="
kubectl describe pods -l app=problematic-app | grep -A 10 "Readiness"

echo -e "\n=== Events ==="
kubectl get events --sort-by=.metadata.creationTimestamp | tail -10

echo -e "\n=== Endpoints ==="
kubectl get endpoints problematic-service
```

### Task 5.3: Create Fixed Version

```yaml
cat << EOF > fixed-readiness.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fixed-app
  labels:
    app: fixed-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fixed-app
  template:
    metadata:
      labels:
        app: fixed-app
    spec:
      containers:
      - name: fixed-app
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting application..."
          # Simulate startup
          sleep 30
          echo "App ready!"
          
          # Create readiness indicator
          touch /tmp/app-ready
          
          # Keep running
          while true; do
            echo "Server running..."
            sleep 10
          done
        ports:
        - containerPort: 8080
        # Fixed readiness probe
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "test -f /tmp/app-ready"
          initialDelaySeconds: 35  # Allow for startup time
          periodSeconds: 10        # Reasonable frequency
          timeoutSeconds: 5        # Sufficient timeout
          successThreshold: 1
          failureThreshold: 3      # Allow some failures
---
apiVersion: v1
kind: Service
metadata:
  name: fixed-service
spec:
  selector:
    app: fixed-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
EOF

kubectl apply -f fixed-readiness.yaml
```

### Task 5.4: Compare Results

```bash
# Monitor the fixed deployment
kubectl get pods -l app=fixed-app -w &
WATCH_PID=$!

sleep 60
kill $WATCH_PID

# Compare with problematic version
echo "=== Problematic App Status ==="
kubectl get pods -l app=problematic-app
kubectl get endpoints problematic-service

echo -e "\n=== Fixed App Status ==="
kubectl get pods -l app=fixed-app
kubectl get endpoints fixed-service
```

---

## Best Practices and Troubleshooting

### Readiness Probe Best Practices

1. **Appropriate Timing**:
   ```yaml
   readinessProbe:
     initialDelaySeconds: 30  # Allow reasonable startup time
     periodSeconds: 10        # Don't check too frequently
     timeoutSeconds: 5        # Allow reasonable response time
     failureThreshold: 3      # Allow some transient failures
   ```

2. **Lightweight Checks**: Keep readiness checks simple and fast

3. **Different from Liveness**: Readiness should check application-specific readiness

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Pod never ready | `0/1 Ready` status | Check probe configuration and endpoint |
| Intermittent readiness | Flapping ready status | Increase `failureThreshold` |
| Slow startup | Probe fails initially | Increase `initialDelaySeconds` |
| No traffic to pods | Service has no endpoints | Check readiness probe success |

### Debugging Commands

```bash
# Check pod readiness status
kubectl get pods -o wide

# Detailed probe information
kubectl describe pod <pod-name>

# Check service endpoints
kubectl get endpoints <service-name>

# Test probe manually
kubectl exec <pod-name> -- <probe-command>

# View probe failures in events
kubectl get events --field-selector reason=Unhealthy
```

---

## Validation and Testing

### Test Your Understanding

1. **Create a web application** with an HTTP readiness probe that checks `/api/health`
2. **Configure a database** with TCP readiness probe and verify endpoint behavior
3. **Implement a command-based probe** that checks for a specific file
4. **Troubleshoot a failing readiness probe** and fix the configuration

### Verification Commands

```bash
# Verify all deployments are ready
kubectl get deployments

# Check all services have endpoints
kubectl get endpoints

# Validate probe configurations
kubectl get pods -o yaml | grep -A 10 readinessProbe

# Test service connectivity
kubectl run test-pod --image=busybox:1.35 --rm -it --restart=Never -- wget -O- http://<service-name>/
```

---

## Cleanup

```bash
# Delete all resources created in this lab
kubectl delete deployment web-app-ready postgres-db app-command-ready probe-demo problematic-app fixed-app
kubectl delete service web-app-ready-service postgres-service app-command-service probe-demo-service problematic-service fixed-service
kubectl delete namespace readiness-lab

# Reset context
kubectl config set-context --current --namespace=default
```

---

## Summary

In this lab, you learned how to:

- ✅ Configure HTTP, TCP, and command-based readiness probes
- ✅ Understand the relationship between readiness probes and service endpoints
- ✅ Distinguish between liveness and readiness probe purposes
- ✅ Troubleshoot common readiness probe issues
- ✅ Apply best practices for readiness probe configuration
- ✅ Monitor and debug probe failures effectively

**Key Takeaways**:
- Readiness probes control traffic flow, not container restarts
- Failed readiness probes remove pods from service endpoints
- Proper timing configuration is crucial for reliable readiness checks
- Readiness probes should check application-specific readiness, not just process health

**Next Steps**: Proceed to [Lab 3: Startup Probes](lab03-startup-probes.md) to learn about startup probes for applications with long initialization times.