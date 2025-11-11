# Lab 3: Deployment Strategies

**Objective**: Master different deployment strategies and patterns
**Time**: 45 minutes
**Difficulty**: Advanced

## Learning Goals

- Implement Blue-Green deployments
- Configure Canary releases
- Use A/B testing patterns
- Implement rolling updates with validation
- Configure automated rollbacks
- Monitor deployment health

## [Exercise 1: Blue-Green Deployment Strategy (15 minutes)](/02-application-deployment/labs/lab03-solution/exercise-01/)

### Task 1.1: Setup Blue Environment

```yaml
cat << EOF > blue-green-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: blue-green-demo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  namespace: blue-green-demo
  labels:
    app: web-app
    version: blue
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
      version: blue
  template:
    metadata:
      labels:
        app: web-app
        version: blue
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "blue-v1.20"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
  namespace: blue-green-demo
  labels:
    app: web-app
spec:
  selector:
    app: web-app
    version: blue  # Initially pointing to blue
  ports:
  - port: 80
    targetPort: 80
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-public
  namespace: blue-green-demo
  labels:
    app: web-app
spec:
  selector:
    app: web-app
    version: blue
  ports:
  - port: 80
    targetPort: 80
    name: http
  type: LoadBalancer
EOF

kubectl apply -f blue-green-namespace.yaml
```

### Task 1.2: Verify Blue Environment

```bash
# Check blue deployment
kubectl get deployments -n blue-green-demo
kubectl get pods -n blue-green-demo -l version=blue

# Test blue environment
kubectl get svc -n blue-green-demo

# Test connectivity (if LoadBalancer is available)
kubectl port-forward -n blue-green-demo svc/web-app-service 8080:80 &

# Test the blue environment
curl http://localhost:8080
```

### Task 1.3: Deploy Green Environment

```yaml
cat << EOF > green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  namespace: blue-green-demo
  labels:
    app: web-app
    version: green
    environment: staging
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
      version: green
  template:
    metadata:
      labels:
        app: web-app
        version: green
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "green-v1.21"
        - name: ENVIRONMENT
          value: "staging"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-green-service
  namespace: blue-green-demo
  labels:
    app: web-app
    version: green
spec:
  selector:
    app: web-app
    version: green
  ports:
  - port: 80
    targetPort: 80
    name: http
  type: ClusterIP
EOF

kubectl apply -f green-deployment.yaml
```

### Task 1.4: Test Green Environment

```bash
# Wait for green deployment
kubectl rollout status deployment/app-green -n blue-green-demo

# Test green environment separately
kubectl port-forward -n blue-green-demo svc/web-app-green-service 8081:80 &

# Test green environment
curl http://localhost:8081
```

### Task 1.5: Switch Traffic (Blue to Green)

```bash
# Switch the main service to green
kubectl patch service web-app-service -n blue-green-demo -p '{"spec":{"selector":{"version":"green"}}}'

# Also switch public service
kubectl patch service web-app-public -n blue-green-demo -p '{"spec":{"selector":{"version":"green"}}}'

# Verify the switch
kubectl describe service web-app-service -n blue-green-demo

# Test that traffic now goes to green
curl http://localhost:8080
```

### Task 1.6: Rollback Capability

```bash
# If issues are found, quickly rollback to blue
kubectl patch service web-app-service -n blue-green-demo -p '{"spec":{"selector":{"version":"blue"}}}'
kubectl patch service web-app-public -n blue-green-demo -p '{"spec":{"selector":{"version":"blue"}}}'

# Verify rollback
curl http://localhost:8080

# Switch back to green for next exercise
kubectl patch service web-app-service -n blue-green-demo -p '{"spec":{"selector":{"version":"green"}}}'
```

## Exercise 2: Canary Deployment Strategy (15 minutes)

### Task 2.1: Setup Canary Environment

```yaml
cat << EOF > canary-setup.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: canary-demo
---
# Stable version (v1)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
  namespace: canary-demo
  labels:
    app: canary-app
    version: stable
spec:
  replicas: 9  # 90% of traffic
  selector:
    matchLabels:
      app: canary-app
      version: stable
  template:
    metadata:
      labels:
        app: canary-app
        version: stable
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "stable-v1.20"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
---
# Canary version (v2)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
  namespace: canary-demo
  labels:
    app: canary-app
    version: canary
spec:
  replicas: 1  # 10% of traffic
  selector:
    matchLabels:
      app: canary-app
      version: canary
  template:
    metadata:
      labels:
        app: canary-app
        version: canary
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "canary-v1.21"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
---
# Service that includes both stable and canary
apiVersion: v1
kind: Service
metadata:
  name: canary-service
  namespace: canary-demo
spec:
  selector:
    app: canary-app  # Selects both stable and canary
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f canary-setup.yaml
```

### Task 2.2: Test Canary Distribution

```bash
# Wait for deployments
kubectl rollout status deployment/app-stable -n canary-demo
kubectl rollout status deployment/app-canary -n canary-demo

# Check pod distribution
kubectl get pods -n canary-demo -l app=canary-app --show-labels

# Test traffic distribution
kubectl port-forward -n canary-demo svc/canary-service 8082:80 &

# Test multiple requests to see distribution
for i in {1..20}; do
  echo "Request $i:"
  curl -s http://localhost:8082 | grep -o "nginx/[0-9.]*" || echo "No version info"
  sleep 1
done
```

### Task 2.3: Gradual Canary Rollout

```bash
# Increase canary traffic to 20% (2 out of 10 total pods)
kubectl scale deployment app-canary -n canary-demo --replicas=2
kubectl scale deployment app-stable -n canary-demo --replicas=8

# Wait for scaling
kubectl get pods -n canary-demo -l app=canary-app

# Test new distribution
for i in {1..20}; do
  echo "Request $i:"
  curl -s http://localhost:8082 | grep -o "nginx/[0-9.]*" || echo "No version info"
  sleep 1
done
```

### Task 2.4: Complete Canary Rollout

```bash
# If canary is successful, migrate all traffic
kubectl scale deployment app-canary -n canary-demo --replicas=10
kubectl scale deployment app-stable -n canary-demo --replicas=0

# Verify full migration
kubectl get pods -n canary-demo -l app=canary-app

# Test that all traffic goes to canary
for i in {1..10}; do
  curl -s http://localhost:8082 | grep -o "nginx/[0-9.]*" || echo "No version info"
done
```

### Task 2.5: Canary Rollback Scenario

```bash
# Simulate canary failure - rollback quickly
kubectl scale deployment app-stable -n canary-demo --replicas=10
kubectl scale deployment app-canary -n canary-demo --replicas=0

# Verify rollback
kubectl get pods -n canary-demo -l app=canary-app

# Test rollback
for i in {1..5}; do
  curl -s http://localhost:8082 | grep -o "nginx/[0-9.]*" || echo "No version info"
done
```

## Exercise 3: A/B Testing Pattern (10 minutes)

### Task 3.1: Setup A/B Testing

```yaml
cat << EOF > ab-testing.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ab-testing-demo
---
# Version A
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-version-a
  namespace: ab-testing-demo
  labels:
    app: ab-test-app
    version: a
spec:
  replicas: 5
  selector:
    matchLabels:
      app: ab-test-app
      version: a
  template:
    metadata:
      labels:
        app: ab-test-app
        version: a
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "version-a"
        - name: FEATURE_FLAG
          value: "old-ui"
---
# Version B
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-version-b
  namespace: ab-testing-demo
  labels:
    app: ab-test-app
    version: b
spec:
  replicas: 5
  selector:
    matchLabels:
      app: ab-test-app
      version: b
  template:
    metadata:
      labels:
        app: ab-test-app
        version: b
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "version-b"
        - name: FEATURE_FLAG
          value: "new-ui"
---
# Service for A/B testing
apiVersion: v1
kind: Service
metadata:
  name: ab-test-service
  namespace: ab-testing-demo
spec:
  selector:
    app: ab-test-app  # Routes to both versions
  ports:
  - port: 80
    targetPort: 80
---
# Dedicated services for each version
apiVersion: v1
kind: Service
metadata:
  name: version-a-service
  namespace: ab-testing-demo
spec:
  selector:
    app: ab-test-app
    version: a
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: version-b-service
  namespace: ab-testing-demo
spec:
  selector:
    app: ab-test-app
    version: b
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f ab-testing.yaml
```

### Task 3.2: Test A/B Distribution

```bash
# Wait for deployments
kubectl rollout status deployment/app-version-a -n ab-testing-demo
kubectl rollout status deployment/app-version-b -n ab-testing-demo

# Test combined service (50/50 split)
kubectl port-forward -n ab-testing-demo svc/ab-test-service 8083:80 &

# Test A/B distribution
for i in {1..20}; do
  echo "Request $i:"
  curl -s http://localhost:8083 | grep -o "nginx/[0-9.]*" || echo "No version info"
done
```

### Task 3.3: Adjust A/B Ratios

```bash
# Change to 80/20 split (A/B)
kubectl scale deployment app-version-a -n ab-testing-demo --replicas=8
kubectl scale deployment app-version-b -n ab-testing-demo --replicas=2

# Test new distribution
kubectl get pods -n ab-testing-demo -l app=ab-test-app

# Verify new ratio
for i in {1..20}; do
  curl -s http://localhost:8083 | grep -o "nginx/[0-9.]*" || echo "Request $i"
done
```

## Exercise 4: Automated Deployment with Validation (5 minutes)

### Task 4.1: Deployment with Automated Checks

```yaml
cat << EOF > validated-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: validated-demo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: validated-app
  namespace: validated-demo
  annotations:
    deployment.kubernetes.io/revision: "1"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Ensure no downtime
  selector:
    matchLabels:
      app: validated-app
  template:
    metadata:
      labels:
        app: validated-app
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
          timeoutSeconds: 2
          successThreshold: 2
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: validated-service
  namespace: validated-demo
spec:
  selector:
    app: validated-app
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f validated-deployment.yaml
```

### Task 4.2: Test Automated Validation

```bash
# Perform update with validation
kubectl set image deployment/validated-app -n validated-demo web=nginx:1.21

# Monitor the rolling update
kubectl rollout status deployment/validated-app -n validated-demo

# Check that readiness probes validate new pods
kubectl describe deployment validated-app -n validated-demo
```

## Lab Validation

### Comprehensive Testing

```bash
# Test all deployment strategies
echo "=== Blue-Green Test ==="
kubectl get deployments -n blue-green-demo
curl http://localhost:8080

echo "=== Canary Test ==="
kubectl get deployments -n canary-demo
curl http://localhost:8082

echo "=== A/B Test ==="
kubectl get deployments -n ab-testing-demo
curl http://localhost:8083

echo "=== Validated Deployment Test ==="
kubectl get deployments -n validated-demo
```

### Performance Comparison

```bash
# Create a simple load test
kubectl run load-test --image=busybox:1.35 --rm -it --restart=Never -- sh

# Inside the pod, test each strategy:
# while true; do wget -qO- http://web-app-service.blue-green-demo.svc.cluster.local && sleep 0.1; done
```

## Cleanup

```bash
# Stop port forwards
pkill -f "kubectl port-forward"

# Clean up all namespaces and resources
kubectl delete namespace blue-green-demo
kubectl delete namespace canary-demo
kubectl delete namespace ab-testing-demo
kubectl delete namespace validated-demo

# Verify cleanup
kubectl get namespaces | grep -E "(blue-green|canary|ab-testing|validated)"
```

## Key Takeaways

1. **Blue-Green** provides instant rollback but requires 2x resources
2. **Canary** allows gradual rollout with risk mitigation
3. **A/B Testing** enables feature comparison with user traffic
4. **Readiness probes** are critical for all strategies
5. **Service selectors** control traffic routing
6. **Resource planning** is essential for deployment strategies

## Best Practices

1. Always use readiness and liveness probes
2. Plan for resource requirements (especially Blue-Green)
3. Monitor metrics during deployments
4. Have clear rollback procedures
5. Test deployment strategies in staging first
6. Use labels consistently for traffic routing

## Common CKAD Scenarios

```bash
# 1. Blue-Green deployment
kubectl create deployment blue --image=nginx:1.20
kubectl create deployment green --image=nginx:1.21
kubectl patch service app -p '{"spec":{"selector":{"version":"green"}}}'

# 2. Canary release (10% traffic)
kubectl scale deployment stable --replicas=9
kubectl scale deployment canary --replicas=1

# 3. Rollback strategy
kubectl rollout undo deployment/app
kubectl rollout status deployment/app

# 4. Traffic splitting
kubectl patch service app -p '{"spec":{"selector":{"app":"myapp"}}}'
```

## Advanced Patterns

- **Progressive Delivery**: Combine canary with automated promotion
- **Feature Flags**: Use environment variables for A/B testing
- **Circuit Breakers**: Implement automatic rollbacks on failure
- **Chaos Engineering**: Test deployment resilience
- **GitOps**: Automated deployment from Git repositories