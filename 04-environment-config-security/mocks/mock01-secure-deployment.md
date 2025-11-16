# Mock 01: Secure Application Deployment

## 🎯 Scenario Description
You are tasked with deploying a secure web application for a financial services company. The application must follow strict security guidelines including non-root execution, resource limits, secrets management, and proper configuration handling.

## 📋 Requirements

### Task 1: Create Namespace and Security Setup (15 minutes)
Create a namespace called `secure-banking-app` and configure the following security measures:

1. **ServiceAccount**: Create a ServiceAccount named `banking-app-sa`
2. **Security Context**: Configure pod and container security contexts to run as non-root
3. **Resource Limits**: Set appropriate resource requests and limits
4. **Network Policy**: Basic network isolation (if supported)

### Task 2: Configuration Management (10 minutes)
Set up configuration management for the application:

1. **ConfigMap**: Create a ConfigMap named `app-config` with:
   - `database.host=db.secure-banking-app.svc.cluster.local`
   - `database.port=5432`
   - `app.environment=production`
   - `log.level=INFO`
   - `feature.audit=enabled`

2. **Secret**: Create a Secret named `db-credentials` with:
   - `username=bankinguser`
   - `password=SecurePass123!`
   - `api-key=banking-api-key-xyz789`

### Task 3: Secure Deployment (20 minutes)
Deploy the application with the following specifications:

**Deployment Name**: `secure-banking-app`
**Image**: `nginx:alpine`
**Replicas**: 3
**Security Requirements**:
- Run as user ID 1000, group ID 2000
- Non-root execution enforced
- Read-only root filesystem
- Drop all capabilities, add only NET_BIND_SERVICE
- No privilege escalation allowed

**Resource Requirements**:
- CPU Request: 250m, Limit: 500m
- Memory Request: 256Mi, Limit: 512Mi
- Ephemeral Storage Request: 1Gi, Limit: 2Gi

**Configuration Integration**:
- Mount ConfigMap as environment variables
- Mount Secret as environment variables with prefix `DB_`
- Add custom nginx configuration via ConfigMap volume mount

### Task 4: Service and Ingress (10 minutes)
1. Create a Service named `banking-app-service` exposing port 80
2. Ensure the service is only accessible within the cluster

### Task 5: Security Validation (5 minutes)
Verify the security configuration:
1. Check that pods are running as non-root
2. Verify resource limits are applied
3. Test that secrets are properly mounted
4. Confirm configuration is loaded

## 🚀 Solution

### Step 1: Namespace and ServiceAccount Setup

```bash
# Create namespace
kubectl create namespace secure-banking-app

# Create ServiceAccount
kubectl create serviceaccount banking-app-sa -n secure-banking-app
```

### Step 2: Configuration Resources

```yaml
# app-config-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: secure-banking-app
data:
  database.host: "db.secure-banking-app.svc.cluster.local"
  database.port: "5432"
  app.environment: "production"
  log.level: "INFO"
  feature.audit: "enabled"
  nginx.conf: |
    server {
        listen 8080;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        location / {
            try_files $uri $uri/ =404;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
---
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: secure-banking-app
type: Opaque
data:
  username: YmFua2luZ3VzZXI=  # bankinguser
  password: U2VjdXJlUGFzczEyMyE=  # SecurePass123!
  api-key: YmFua2luZy1hcGkta2V5LXh5ejc4OQ==  # banking-api-key-xyz789
```

### Step 3: Secure Deployment

```yaml
# secure-banking-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-banking-app
  namespace: secure-banking-app
  labels:
    app: secure-banking-app
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-banking-app
  template:
    metadata:
      labels:
        app: secure-banking-app
        tier: frontend
    spec:
      serviceAccountName: banking-app-sa
      securityContext:
        runAsUser: 1000
        runAsGroup: 2000
        runAsNonRoot: true
        fsGroup: 3000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: banking-app
        image: nginx:alpine
        ports:
        - containerPort: 8080
          name: http
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          runAsGroup: 2000
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "512Mi"
            cpu: "500m"
            ephemeral-storage: "2Gi"
        env:
        # ConfigMap environment variables
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: database.host
        - name: DATABASE_PORT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: database.port
        - name: APP_ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: app.environment
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: log.level
        - name: FEATURE_AUDIT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: feature.audit
        # Secret environment variables with prefix
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: DB_API_KEY
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: api-key
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: nginx.conf
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp
        - name: var-cache
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
        - name: var-log
          mountPath: /var/log/nginx
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      volumes:
      - name: nginx-config
        configMap:
          name: app-config
          items:
          - key: nginx.conf
            path: nginx.conf
      - name: tmp-volume
        emptyDir: {}
      - name: var-cache
        emptyDir: {}
      - name: var-run
        emptyDir: {}
      - name: var-log
        emptyDir: {}
```

### Step 4: Service

```yaml
# banking-app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: banking-app-service
  namespace: secure-banking-app
  labels:
    app: secure-banking-app
spec:
  selector:
    app: secure-banking-app
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  type: ClusterIP
```

### Step 5: Apply All Resources

```bash
# Apply all configurations
kubectl apply -f app-config-configmap.yaml
kubectl apply -f secure-banking-deployment.yaml
kubectl apply -f banking-app-service.yaml
```

## ✅ Verification Commands

```bash
# Check namespace and resources
kubectl get all -n secure-banking-app

# Verify security context
kubectl get pods -n secure-banking-app -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext.runAsUser}{"\t"}{.spec.containers[0].securityContext.runAsUser}{"\n"}{end}'

# Check resource limits
kubectl describe deployment secure-banking-app -n secure-banking-app | grep -A 10 "Limits"

# Verify environment variables
kubectl exec -n secure-banking-app deployment/secure-banking-app -- env | grep -E "(DATABASE|APP|LOG|FEATURE|DB_)"

# Test application health
kubectl get pods -n secure-banking-app
kubectl exec -n secure-banking-app deployment/secure-banking-app -- curl -s http://localhost:8080/health

# Check security compliance
kubectl exec -n secure-banking-app deployment/secure-banking-app -- whoami
kubectl exec -n secure-banking-app deployment/secure-banking-app -- id

# Verify read-only filesystem
kubectl exec -n secure-banking-app deployment/secure-banking-app -- touch /test-file 2>&1 | grep -i "read-only"

# Test service connectivity
kubectl run test-pod -n secure-banking-app --image=alpine --rm -it -- wget -qO- http://banking-app-service/health
```

## 🎯 Success Criteria

- ✅ All pods running as non-root user (UID 1000)
- ✅ Resource limits properly applied and enforced
- ✅ ConfigMap and Secret values accessible as environment variables
- ✅ Read-only root filesystem preventing file modifications
- ✅ Service accessible within the cluster
- ✅ Health checks working correctly
- ✅ Security headers present in HTTP responses
- ✅ No privileged containers or capabilities beyond NET_BIND_SERVICE

## 🧹 Cleanup

```bash
kubectl delete namespace secure-banking-app
```

## 📚 Key Learning Points

- **Defense in Depth**: Multiple security layers (non-root, read-only FS, dropped capabilities)
- **Configuration Management**: Separation of config (ConfigMap) and secrets (Secret)
- **Resource Governance**: Proper resource requests and limits for stability
- **Security Context**: Both pod-level and container-level security settings
- **Health Monitoring**: Proper liveness and readiness probes
- **Principle of Least Privilege**: Minimal required permissions and capabilities
