# Mock 03: Resource Management

## 🎯 Scenario Description
You are managing a Kubernetes cluster shared by multiple teams with different workload characteristics. You need to implement comprehensive resource management to ensure fair resource allocation, prevent resource starvation, and maintain cluster stability while accommodating different QoS requirements.

## 📋 Requirements

### Task 1: Namespace Setup with ResourceQuotas (15 minutes)
Create three namespaces with different resource allocation strategies:

1. **`production-apps`**: High priority, guaranteed resources
   - CPU Quota: 8 cores (requests), 16 cores (limits)
   - Memory Quota: 16Gi (requests), 32Gi (limits)
   - Storage Quota: 500Gi
   - Pod Limit: 50 pods
   - Services: 20

2. **`staging-apps`**: Medium priority, burstable resources
   - CPU Quota: 4 cores (requests), 12 cores (limits)
   - Memory Quota: 8Gi (requests), 24Gi (limits)
   - Storage Quota: 200Gi
   - Pod Limit: 30 pods

3. **`development-apps`**: Low priority, best-effort friendly
   - CPU Quota: 2 cores (requests), 6 cores (limits)
   - Memory Quota: 4Gi (requests), 12Gi (limits)
   - Pod Limit: 20 pods

### Task 2: LimitRanges Configuration (10 minutes)
Configure LimitRanges for each namespace:

1. **Production**: Conservative ratios, higher defaults
2. **Staging**: Moderate ratios, medium defaults  
3. **Development**: Flexible ratios, lower defaults

### Task 3: Priority Classes (5 minutes)
Create priority classes:
- `high-priority` (value: 1000) for production
- `medium-priority` (value: 500) for staging
- `low-priority` (value: 100) for development

### Task 4: Multi-tier Application Deployment (15 minutes)
Deploy a three-tier application in each namespace:

**Components per namespace**:
- Frontend (web server)
- Backend (API server)  
- Database (persistent storage)
- Cache (Redis)

**Resource characteristics**:
- Production: Guaranteed QoS, high resources
- Staging: Burstable QoS, medium resources
- Development: Mixed QoS, minimal resources

### Task 5: Resource Monitoring and Validation (5 minutes)
1. Monitor resource usage across namespaces
2. Verify quota enforcement
3. Test resource limit violations
4. Validate priority class scheduling

## 🚀 Solution

### Step 1: Create Namespaces with ResourceQuotas

```yaml
# production-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production-apps
  labels:
    environment: production
    priority: high
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-compute-quota
  namespace: production-apps
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    requests.ephemeral-storage: 100Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    limits.ephemeral-storage: 200Gi
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-object-quota
  namespace: production-apps
spec:
  hard:
    pods: "50"
    services: "20"
    secrets: "30"
    configmaps: "30"
    persistentvolumeclaims: "20"
    requests.storage: 500Gi
    count/deployments.apps: "20"
    count/statefulsets.apps: "10"
---
# staging-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging-apps
  labels:
    environment: staging
    priority: medium
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-compute-quota
  namespace: staging-apps
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    requests.ephemeral-storage: 50Gi
    limits.cpu: "12"
    limits.memory: 24Gi
    limits.ephemeral-storage: 150Gi
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-object-quota
  namespace: staging-apps
spec:
  hard:
    pods: "30"
    services: "15"
    secrets: "20"
    configmaps: "20"
    persistentvolumeclaims: "10"
    requests.storage: 200Gi
    count/deployments.apps: "15"
---
# development-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development-apps
  labels:
    environment: development
    priority: low
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: development-compute-quota
  namespace: development-apps
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "6"
    limits.memory: 12Gi
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: development-object-quota
  namespace: development-apps
spec:
  hard:
    pods: "20"
    services: "10"
    secrets: "15"
    configmaps: "15"
    count/deployments.apps: "10"
```

### Step 2: LimitRanges for Each Namespace

```yaml
# production-limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production-apps
spec:
  limits:
  - type: Container
    default:
      memory: "1Gi"
      cpu: "500m"
      ephemeral-storage: "2Gi"
    defaultRequest:
      memory: "512Mi"
      cpu: "250m"
      ephemeral-storage: "1Gi"
    max:
      memory: "4Gi"
      cpu: "2000m"
      ephemeral-storage: "10Gi"
    min:
      memory: "256Mi"
      cpu: "100m"
      ephemeral-storage: "500Mi"
    maxLimitRequestRatio:
      memory: "2"
      cpu: "2"
  - type: Pod
    max:
      memory: "8Gi"
      cpu: "4000m"
---
# staging-limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: staging-limits
  namespace: staging-apps
spec:
  limits:
  - type: Container
    default:
      memory: "512Mi"
      cpu: "250m"
      ephemeral-storage: "1Gi"
    defaultRequest:
      memory: "256Mi"
      cpu: "125m"
      ephemeral-storage: "500Mi"
    max:
      memory: "2Gi"
      cpu: "1000m"
      ephemeral-storage: "5Gi"
    min:
      memory: "128Mi"
      cpu: "50m"
      ephemeral-storage: "250Mi"
    maxLimitRequestRatio:
      memory: "3"
      cpu: "3"
  - type: Pod
    max:
      memory: "4Gi"
      cpu: "2000m"
---
# development-limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: development-limits
  namespace: development-apps
spec:
  limits:
  - type: Container
    default:
      memory: "256Mi"
      cpu: "125m"
    defaultRequest:
      memory: "128Mi"
      cpu: "50m"
    max:
      memory: "1Gi"
      cpu: "500m"
    min:
      memory: "64Mi"
      cpu: "25m"
    maxLimitRequestRatio:
      memory: "4"
      cpu: "4"
  - type: Pod
    max:
      memory: "2Gi"
      cpu: "1000m"
```

### Step 3: Priority Classes

```yaml
# priority-classes.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority class for production workloads"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: medium-priority
value: 500
globalDefault: false
description: "Medium priority class for staging workloads"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
description: "Low priority class for development workloads"
```

### Step 4: Multi-tier Application Deployments

```yaml
# production-app.yaml
# Frontend - Production
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: production-apps
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
      tier: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      priorityClassName: high-priority
      containers:
      - name: web
        image: nginx:alpine
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        ports:
        - containerPort: 80
---
# Backend - Production
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: production-apps
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
      tier: backend
  template:
    metadata:
      labels:
        app: backend
        tier: backend
    spec:
      priorityClassName: high-priority
      containers:
      - name: api
        image: nginx:alpine
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        ports:
        - containerPort: 8080
---
# Database - Production (StatefulSet)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database
  namespace: production-apps
spec:
  replicas: 1
  serviceName: database
  selector:
    matchLabels:
      app: database
      tier: database
  template:
    metadata:
      labels:
        app: database
        tier: database
    spec:
      priorityClassName: high-priority
      containers:
      - name: db
        image: postgres:13-alpine
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: POSTGRES_DB
          value: "proddb"
        - name: POSTGRES_USER
          value: "produser"
        - name: POSTGRES_PASSWORD
          value: "prodpass"
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
# Cache - Production
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache
  namespace: production-apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cache
      tier: cache
  template:
    metadata:
      labels:
        app: cache
        tier: cache
    spec:
      priorityClassName: high-priority
      containers:
      - name: redis
        image: redis:alpine
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        ports:
        - containerPort: 6379
```

```yaml
# staging-app.yaml
# Frontend - Staging
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: staging-apps
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
      tier: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      priorityClassName: medium-priority
      containers:
      - name: web
        image: nginx:alpine
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
          limits:
            memory: "768Mi"
            cpu: "375m"
        ports:
        - containerPort: 80
---
# Backend - Staging
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: staging-apps
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
      tier: backend
  template:
    metadata:
      labels:
        app: backend
        tier: backend
    spec:
      priorityClassName: medium-priority
      containers:
      - name: api
        image: nginx:alpine
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1536Mi"
            cpu: "750m"
        ports:
        - containerPort: 8080
---
# Database - Staging
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database
  namespace: staging-apps
spec:
  replicas: 1
  serviceName: database
  selector:
    matchLabels:
      app: database
      tier: database
  template:
    metadata:
      labels:
        app: database
        tier: database
    spec:
      priorityClassName: medium-priority
      containers:
      - name: db
        image: postgres:13-alpine
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: POSTGRES_DB
          value: "stagingdb"
        - name: POSTGRES_USER
          value: "staginguser"
        - name: POSTGRES_PASSWORD
          value: "stagingpass"
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

```yaml
# development-app.yaml
# Frontend - Development (BestEffort QoS)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: development-apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
      tier: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      priorityClassName: low-priority
      containers:
      - name: web
        image: nginx:alpine
        # No resources specified = BestEffort QoS
        ports:
        - containerPort: 80
---
# Backend - Development (Burstable QoS)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: development-apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
      tier: backend
  template:
    metadata:
      labels:
        app: backend
        tier: backend
    spec:
      priorityClassName: low-priority
      containers:
      - name: api
        image: nginx:alpine
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        ports:
        - containerPort: 8080
---
# Database - Development (Guaranteed QoS)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: development-apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
      tier: database
  template:
    metadata:
      labels:
        app: database
        tier: database
    spec:
      priorityClassName: low-priority
      containers:
      - name: db
        image: postgres:13-alpine
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
          limits:
            memory: "256Mi"  # Same as requests = Guaranteed
            cpu: "125m"
        env:
        - name: POSTGRES_DB
          value: "devdb"
        - name: POSTGRES_USER
          value: "devuser"
        - name: POSTGRES_PASSWORD
          value: "devpass"
```

### Step 5: Services for Each Tier

```yaml
# services.yaml
# Production Services
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: production-apps
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: production-apps
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: production-apps
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: cache
  namespace: production-apps
spec:
  selector:
    app: cache
  ports:
  - port: 6379
    targetPort: 6379
---
# Staging Services
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: staging-apps
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: staging-apps
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: staging-apps
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
---
# Development Services
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: development-apps
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: development-apps
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: development-apps
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
```

### Step 6: Resource Monitoring Pod

```yaml
# resource-monitor.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-monitor
  namespace: production-apps
spec:
  containers:
  - name: monitor
    image: bitnami/kubectl:latest
    resources:
      requests:
        memory: "100Mi"
        cpu: "50m"
      limits:
        memory: "200Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args:
    - -c
    - |
      while true; do
        echo "=== Resource Usage Report $(date) ==="
        
        echo "ResourceQuota Status:"
        kubectl get resourcequota --all-namespaces
        echo ""
        
        echo "Pod Resource Usage:"
        kubectl top pods --all-namespaces --sort-by=memory 2>/dev/null || echo "Metrics not available"
        echo ""
        
        echo "Node Resource Usage:"
        kubectl top nodes 2>/dev/null || echo "Node metrics not available"
        echo ""
        
        echo "QoS Classes Distribution:"
        kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,QOS:.status.qosClass | grep -v "^$"
        echo ""
        
        sleep 300
      done
```

## ✅ Verification Commands

```bash
# Apply all configurations
kubectl apply -f production-namespace.yaml
kubectl apply -f staging-namespace.yaml
kubectl apply -f development-namespace.yaml
kubectl apply -f production-limitrange.yaml
kubectl apply -f staging-limitrange.yaml
kubectl apply -f development-limitrange.yaml
kubectl apply -f priority-classes.yaml
kubectl apply -f production-app.yaml
kubectl apply -f staging-app.yaml
kubectl apply -f development-app.yaml
kubectl apply -f services.yaml
kubectl apply -f resource-monitor.yaml

# Check ResourceQuotas
kubectl get resourcequota --all-namespaces
kubectl describe resourcequota -n production-apps
kubectl describe resourcequota -n staging-apps
kubectl describe resourcequota -n development-apps

# Check LimitRanges
kubectl get limitrange --all-namespaces
kubectl describe limitrange -n production-apps
kubectl describe limitrange -n staging-apps
kubectl describe limitrange -n development-apps

# Check Priority Classes
kubectl get priorityclasses

# Verify deployments and resource allocation
kubectl get deployments --all-namespaces
kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,QOS:.status.qosClass,PRIORITY:.spec.priorityClassName

# Check resource usage (if metrics-server available)
kubectl top pods --all-namespaces --sort-by=memory
kubectl top nodes

# Verify quota usage
kubectl get resourcequota production-compute-quota -n production-apps -o yaml | grep -A 10 status
kubectl get resourcequota staging-compute-quota -n staging-apps -o yaml | grep -A 10 status
kubectl get resourcequota development-compute-quota -n development-apps -o yaml | grep -A 10 status

# Test quota violations (should fail)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: quota-violation-test
  namespace: development-apps
spec:
  containers:
  - name: resource-hog
    image: nginx:alpine
    resources:
      requests:
        memory: "5Gi"  # Exceeds development namespace quota
        cpu: "3000m"
      limits:
        memory: "10Gi"
        cpu: "6000m"
