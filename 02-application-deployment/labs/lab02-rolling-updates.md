# Lab 2: Rolling Updates and Rollbacks

**Objective**: Master rolling updates, rollbacks, and deployment history management
**Time**: 40 minutes
**Difficulty**: Intermediate

## Learning Goals

- Perform rolling updates safely
- Configure update strategies
- Monitor rollout progress
- Execute rollbacks when needed
- Manage deployment history
- Handle failed deployments

## Exercise 1: Rolling Updates (15 minutes)

### Task 1.1: Create Initial Deployment

```bash
# Create a deployment with version 1.20
cat << EOF > rolling-update-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rolling-app
  labels:
    app: rolling-test
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: rolling-test
  template:
    metadata:
      labels:
        app: rolling-test
        version: v1.20
    spec:
      containers:
      - name: nginx
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
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10
EOF

kubectl apply -f rolling-update-app.yaml
```

### Task 1.2: Monitor Initial Deployment

```bash
# Wait for deployment to be ready
kubectl rollout status deployment/rolling-app

# Check the pods and their images
kubectl get pods -l app=rolling-test -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,STATUS:.status.phase

# Check deployment details
kubectl describe deployment rolling-app
```

### Task 1.3: Perform Rolling Update

```bash
# Update to nginx 1.21 and watch the rollout
kubectl set image deployment/rolling-app nginx=nginx:1.21

# Watch the rolling update in real-time
kubectl rollout status deployment/rolling-app -w

# In another terminal, watch pods being replaced
kubectl get pods -l app=rolling-test -w
```

### Task 1.4: Verify Update

```bash
# Check deployment revision
kubectl rollout history deployment/rolling-app

# Verify all pods are running the new image
kubectl get pods -l app=rolling-test -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image

# Check deployment description
kubectl describe deployment rolling-app | grep Image
```

## Exercise 2: Update Strategies (10 minutes)

### Task 2.1: Configure Rolling Update Parameters

```bash
# Update with more aggressive settings
kubectl patch deployment rolling-app -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":2,"maxUnavailable":0}}}}'

# Perform another update
kubectl set image deployment/rolling-app nginx=nginx:1.22

# Watch the faster rollout
kubectl rollout status deployment/rolling-app
```

### Task 2.2: Recreate Strategy

```yaml
cat << EOF > recreate-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recreate-app
  labels:
    app: recreate-test
spec:
  replicas: 3
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: recreate-test
  template:
    metadata:
      labels:
        app: recreate-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

kubectl apply -f recreate-deployment.yaml

# Wait for deployment
kubectl rollout status deployment/recreate-app

# Update with Recreate strategy
kubectl set image deployment/recreate-app nginx=nginx:1.21

# Watch all pods terminate before new ones start
kubectl get pods -l app=recreate-test -w
```

### Task 2.3: Compare Update Strategies

```bash
# Check both deployments
kubectl get deployments

# Compare their update strategies
kubectl describe deployment rolling-app | grep -A 5 "StrategyType"
kubectl describe deployment recreate-app | grep -A 5 "StrategyType"
```

## Exercise 3: Rollbacks (10 minutes)

### Task 3.1: Check Deployment History

```bash
# View rollout history
kubectl rollout history deployment/rolling-app

# Get detailed history with change cause
kubectl rollout history deployment/rolling-app --revision=1
kubectl rollout history deployment/rolling-app --revision=2
```

### Task 3.2: Add Annotations for Better History

```bash
# Add change-cause annotation for future updates
kubectl annotate deployment rolling-app deployment.kubernetes.io/change-cause="Update to nginx 1.23 for security patches"

# Perform update with annotation
kubectl set image deployment/rolling-app nginx=nginx:1.23

# Check updated history
kubectl rollout history deployment/rolling-app
```

### Task 3.3: Rollback to Previous Version

```bash
# Rollback to previous revision
kubectl rollout undo deployment/rolling-app

# Watch the rollback
kubectl rollout status deployment/rolling-app

# Verify rollback
kubectl get pods -l app=rolling-test -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image
```

### Task 3.4: Rollback to Specific Revision

```bash
# Check current history
kubectl rollout history deployment/rolling-app

# Rollback to specific revision (e.g., revision 1)
kubectl rollout undo deployment/rolling-app --to-revision=1

# Verify the rollback
kubectl rollout status deployment/rolling-app
kubectl describe deployment rolling-app | grep Image
```

## Exercise 4: Failed Deployments and Recovery (5 minutes)

### Task 4.1: Simulate Failed Deployment

```bash
# Create a deployment with a bad image
kubectl set image deployment/rolling-app nginx=nginx:bad-tag

# Watch the failed rollout
kubectl rollout status deployment/rolling-app --timeout=60s

# Check pod status
kubectl get pods -l app=rolling-test
kubectl describe pod <failing-pod-name>
```

### Task 4.2: Handle Failed Deployment

```bash
# Check deployment status
kubectl get deployment rolling-app

# Since the bad image fails, rolling update will pause
# Some old pods remain running to maintain availability

# Rollback the failed deployment
kubectl rollout undo deployment/rolling-app

# Wait for recovery
kubectl rollout status deployment/rolling-app

# Verify recovery
kubectl get pods -l app=rolling-test
```

## Exercise 5: Advanced Rolling Update Scenarios (Bonus)

### Task 5.1: Pause and Resume Rollouts

```bash
# Start an update
kubectl set image deployment/rolling-app nginx=nginx:1.24

# Pause the rollout midway
kubectl rollout pause deployment/rolling-app

# Check status (should show paused)
kubectl rollout status deployment/rolling-app

# Check pods (some old, some new)
kubectl get pods -l app=rolling-test -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image

# Resume the rollout
kubectl rollout resume deployment/rolling-app

# Wait for completion
kubectl rollout status deployment/rolling-app
```

### Task 5.2: Blue-Green with Manual Steps

```yaml
cat << EOF > blue-green-v1.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blue-deployment
  labels:
    app: blue-green
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blue-green
      version: blue
  template:
    metadata:
      labels:
        app: blue-green
        version: blue
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: blue-green-service
spec:
  selector:
    app: blue-green
    version: blue
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f blue-green-v1.yaml

# Create green deployment
cat << EOF > blue-green-v2.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: green-deployment
  labels:
    app: blue-green
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blue-green
      version: green
  template:
    metadata:
      labels:
        app: blue-green
        version: green
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
EOF

kubectl apply -f blue-green-v2.yaml

# Switch traffic to green
kubectl patch service blue-green-service -p '{"spec":{"selector":{"version":"green"}}}'

# Verify switch
kubectl describe service blue-green-service
```

## Lab Validation and Testing

### Validation Commands

```bash
# Check all deployments
kubectl get deployments

# Verify rollout history
kubectl rollout history deployment/rolling-app

# Test rollback functionality
kubectl rollout undo deployment/rolling-app --to-revision=2
kubectl rollout status deployment/rolling-app

# Check final state
kubectl get pods -l app=rolling-test -o wide
```

### Performance Testing

```bash
# Create a service for testing
kubectl expose deployment rolling-app --port=80 --type=ClusterIP

# Test availability during rollout
kubectl run test-pod --image=busybox:1.35 --rm -it --restart=Never -- sh

# Inside the test pod:
# while true; do wget -qO- rolling-app.default.svc.cluster.local && sleep 1; done
```

## Troubleshooting Common Issues

### Issue 1: Rollout Stuck

```bash
# Check deployment status
kubectl describe deployment <deployment-name>

# Check pod events
kubectl get events --sort-by=.metadata.creationTimestamp

# Common causes:
# - Resource constraints
# - Image pull failures
# - Readiness probe failures
```

### Issue 2: Slow Rollouts

```bash
# Adjust rolling update parameters
kubectl patch deployment <deployment-name> -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":3,"maxUnavailable":1}}}}'

# Check resource availability
kubectl top nodes
kubectl describe nodes
```

### Issue 3: Failed Readiness Probes

```bash
# Check probe configuration
kubectl describe deployment <deployment-name>

# Check pod logs
kubectl logs <pod-name>

# Test probe endpoint manually
kubectl exec <pod-name> -- curl localhost:80/
```

## Cleanup

```bash
# Clean up all resources
kubectl delete deployment rolling-app recreate-app blue-deployment green-deployment
kubectl delete service blue-green-service rolling-app
kubectl delete -f rolling-update-app.yaml --ignore-not-found
kubectl delete -f recreate-deployment.yaml --ignore-not-found
kubectl delete -f blue-green-v1.yaml --ignore-not-found
kubectl delete -f blue-green-v2.yaml --ignore-not-found
```

## Key Takeaways

1. **Rolling Updates** provide zero-downtime deployments
2. **MaxSurge** and **MaxUnavailable** control update pace
3. **Rollbacks** can be performed to any previous revision
4. **Change-cause annotations** improve history tracking
5. **Readiness probes** are crucial for safe updates
6. **Pausing rollouts** allows for manual verification

## Best Practices

1. Always use readiness probes
2. Set appropriate resource limits
3. Use meaningful change-cause annotations
4. Test rollbacks in non-production environments
5. Monitor rollout progress actively
6. Keep deployment history manageable

## Common CKAD Tasks

```bash
# 1. Update deployment image
kubectl set image deployment/app container=nginx:1.21

# 2. Check rollout status
kubectl rollout status deployment/app

# 3. View rollout history
kubectl rollout history deployment/app

# 4. Rollback deployment
kubectl rollout undo deployment/app

# 5. Rollback to specific revision
kubectl rollout undo deployment/app --to-revision=2

# 6. Pause rollout
kubectl rollout pause deployment/app

# 7. Resume rollout
kubectl rollout resume deployment/app
```