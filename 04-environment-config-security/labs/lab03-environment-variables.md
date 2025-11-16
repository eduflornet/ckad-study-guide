# Lab 03: Environment Variables

## Objective
Master different methods of injecting environment variables into containers using ConfigMaps, Secrets, and direct assignment.

## Tasks

### Task 1: Direct Environment Variable Assignment

```yaml
# pod-direct-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: direct-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    - name: APP_NAME
      value: "my-application"
    - name: APP_VERSION
      value: "1.0.0"
    - name: ENVIRONMENT
      value: "production"
    - name: LOG_LEVEL
      value: "info"
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'App: $APP_NAME v$APP_VERSION in $ENVIRONMENT'; sleep 30; done"]
```

### Task 2: Environment Variables from ConfigMaps

First, create ConfigMaps for different configurations:

```bash
# Create app configuration
kubectl create configmap app-settings \
  --from-literal=database_host=db.example.com \
  --from-literal=database_port=5432 \
  --from-literal=cache_enabled=true \
  --from-literal=debug_mode=false

# Create feature flags
kubectl create configmap feature-flags \
  --from-literal=enable_new_ui=true \
  --from-literal=enable_beta_features=false \
  --from-literal=maintenance_mode=false
```

```yaml
# pod-configmap-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    # Single environment variable from ConfigMap
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-settings
          key: database_host
    - name: DATABASE_PORT
      valueFrom:
        configMapKeyRef:
          name: app-settings
          key: database_port
    # All keys from ConfigMap with prefix
    envFrom:
    - configMapRef:
        name: feature-flags
      prefix: FEATURE_
    # All keys from ConfigMap without prefix
    - configMapRef:
        name: app-settings
    command: ["/bin/sh"]
    args: ["-c", "while true; do env | grep -E '(DATABASE|FEATURE|cache)' | sort; sleep 60; done"]
```

### Task 3: Environment Variables from Secrets

```bash
# Create database credentials
kubectl create secret generic db-secret \
  --from-literal=username=postgres \
  --from-literal=password=secretpassword \
  --from-literal=connection_string=postgresql://postgres:secretpassword@db:5432/myapp

# Create API keys
kubectl create secret generic api-keys \
  --from-literal=stripe_key=sk_test_123456789 \
  --from-literal=sendgrid_key=SG.abc123xyz \
  --from-literal=jwt_secret=mysupersecretjwtkey
```

```yaml
# pod-secret-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    # Individual secret values
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
    # All secrets with prefix
    envFrom:
    - secretRef:
        name: api-keys
      prefix: API_
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'DB User: $DB_USERNAME, API Keys loaded'; sleep 30; done"]
```

### Task 4: Mixed Environment Variables

```yaml
# pod-mixed-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: mixed-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    # Direct assignment
    - name: APP_ENV
      value: "production"
    # From ConfigMap
    - name: CACHE_ENABLED
      valueFrom:
        configMapKeyRef:
          name: app-settings
          key: cache_enabled
    # From Secret
    - name: JWT_SECRET
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: jwt_secret
    # Computed from other env vars
    - name: DATABASE_URL
      value: "postgresql://$(DB_USERNAME):$(DB_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/myapp"
    envFrom:
    # Load all from ConfigMap
    - configMapRef:
        name: app-settings
    # Load all from Secret with prefix
    - secretRef:
        name: db-secret
      prefix: DB_
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Environment loaded successfully'; env | wc -l; sleep 45; done"]
```

### Task 5: Environment Variables in Deployments

```yaml
# deployment-with-env.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: nginx:alpine
        ports:
        - containerPort: 80
        env:
        - name: INSTANCE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        envFrom:
        - configMapRef:
            name: app-settings
        - secretRef:
            name: api-keys
          prefix: SECRET_
```

### Task 6: Environment Variables from Downward API

```yaml
# pod-downward-api-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-api-pod
  labels:
    app: demo
    version: v1.0
  annotations:
    description: "Demo pod for downward API"
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    # Pod metadata
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    # Resource information
    - name: CPU_REQUEST
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: requests.cpu
    - name: MEMORY_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: limits.memory
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        memory: 256Mi
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Pod: $POD_NAME on $NODE_NAME ($POD_IP)'; sleep 30; done"]
```

### Task 7: Handling Environment Variable Precedence

```yaml
# pod-env-precedence.yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-precedence-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    # This will override the same key from ConfigMap
    - name: database_host
      value: "override.example.com"
    envFrom:
    # ConfigMap loaded first
    - configMapRef:
        name: app-settings
    # Secret loaded after (can override ConfigMap values)
    - secretRef:
        name: db-secret
      prefix: DB_
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'database_host: $database_host'; sleep 30; done"]
```

## Verification Commands

```bash
# Check environment variables in pods
kubectl exec direct-env-pod -- env | sort
kubectl exec configmap-env-pod -- env | grep -E "(DATABASE|FEATURE|cache)"
kubectl exec secret-env-pod -- env | grep -v PASSWORD  # Don't show password
kubectl exec mixed-env-pod -- env | wc -l
kubectl exec downward-api-pod -- env | grep -E "(POD|NODE|CPU|MEMORY)"

# Check logs
kubectl logs direct-env-pod
kubectl logs configmap-env-pod
kubectl logs downward-api-pod

# Describe pods to see environment configuration
kubectl describe pod mixed-env-pod | grep -A 20 Environment

# Check deployment pods
kubectl get pods -l app=web-app
kubectl exec deployment/web-app -- env | grep INSTANCE_ID
```

## Troubleshooting Common Issues

### Task 8: Debug Environment Variable Issues

```yaml
# debug-env-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug-env-pod
spec:
  containers:
  - name: debug
    image: nginx:alpine
    env:
    - name: EXISTING_VAR
      value: "I exist"
    - name: MISSING_VAR
      valueFrom:
        configMapKeyRef:
          name: non-existent-config
          key: missing-key
          optional: true  # Won't fail if missing
    - name: REQUIRED_VAR
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    command: ["/bin/sh"]
    args: ["-c", "echo 'Checking vars...'; env | grep '_VAR'; sleep 3600"]
```

## Cleanup

```bash
kubectl delete pod direct-env-pod configmap-env-pod secret-env-pod mixed-env-pod downward-api-pod env-precedence-pod debug-env-pod
kubectl delete deployment web-app
kubectl delete configmap app-settings feature-flags
kubectl delete secret db-secret api-keys
```

## 🎯 Key Learning Points

- Environment variables can come from multiple sources
- envFrom loads all keys vs env loads specific keys
- Direct env assignments override envFrom values
- Secrets in environment variables are visible in process lists
- Use optional: true for non-critical environment variables
- Downward API provides pod and node information
- Environment variable precedence: env > envFrom (later sources override earlier)
- Resource requests/limits can be accessed via environment variables
- ConfigMaps and Secrets update pods differently (restart may be needed)
