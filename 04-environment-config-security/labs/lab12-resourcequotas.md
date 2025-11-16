# Lab 12: ResourceQuotas

## Objective
Learn to use ResourceQuotas to limit aggregate resource consumption and object counts within namespaces to prevent resource exhaustion and ensure fair resource allocation.

## Tasks

### Task 1: Basic ResourceQuota Setup

```bash
# Create test namespace
kubectl create namespace resourcequota-test
```

```yaml
# basic-resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: basic-quota
  namespace: resourcequota-test
spec:
  hard:
    # Compute resources
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8" 
    limits.memory: 16Gi
    
    # Object counts
    pods: "10"
    services: "5"
    secrets: "10"
    configmaps: "10"
    persistentvolumeclaims: "4"
```

### Task 2: Comprehensive ResourceQuota

```yaml
# comprehensive-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: comprehensive-quota
  namespace: resourcequota-test
spec:
  hard:
    # Compute resources
    requests.cpu: "6"
    requests.memory: 12Gi
    requests.ephemeral-storage: 50Gi
    limits.cpu: "12"
    limits.memory: 24Gi
    limits.ephemeral-storage: 100Gi
    
    # Object counts
    count/pods: "20"
    count/services: "8"
    count/secrets: "15"
    count/configmaps: "15"
    count/replicationcontrollers: "5"
    count/deployments.apps: "10"
    count/replicasets.apps: "15"
    count/statefulsets.apps: "3"
    count/jobs.batch: "5"
    count/cronjobs.batch: "3"
    
    # Storage
    persistentvolumeclaims: "6"
    requests.storage: 100Gi
    
    # Extended resources (if available)
    # requests.nvidia.com/gpu: "2"
    # limits.nvidia.com/gpu: "4"
```

### Task 3: Test Resource Consumption

```yaml
# test-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-test-deployment
  namespace: resourcequota-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quota-test
  template:
    metadata:
      labels:
        app: quota-test
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "500Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: quota-test-service
  namespace: resourcequota-test
spec:
  selector:
    app: quota-test
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### Task 4: Quota Violation Tests

```yaml
# quota-violation-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-violation-deployment
  namespace: resourcequota-test
spec:
  replicas: 8  # This might exceed pod quota
  selector:
    matchLabels:
      app: quota-violation
  template:
    metadata:
      labels:
        app: quota-violation
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "2Gi"    # Large memory request
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
# This should exceed the services quota
apiVersion: v1
kind: Service
metadata:
  name: quota-violation-service-1
  namespace: resourcequota-test
spec:
  selector:
    app: quota-violation
  ports:
  - port: 80
---
apiVersion: v1
kind: Service
metadata:
  name: quota-violation-service-2
  namespace: resourcequota-test
spec:
  selector:
    app: quota-violation
  ports:
  - port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: quota-violation-service-3
  namespace: resourcequota-test
spec:
  selector:
    app: quota-violation
  ports:
  - port: 9090
---
apiVersion: v1
kind: Service
metadata:
  name: quota-violation-service-4
  namespace: resourcequota-test
spec:
  selector:
    app: quota-violation
  ports:
  - port: 3000
---
# This should exceed services quota (6th service when quota allows 5)
apiVersion: v1
kind: Service
metadata:
  name: quota-violation-service-5
  namespace: resourcequota-test
spec:
  selector:
    app: quota-violation
  ports:
  - port: 4000
```

### Task 5: Storage Quota Testing

```yaml
# storage-quota-test.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-1
  namespace: resourcequota-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-2
  namespace: resourcequota-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 30Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-3
  namespace: resourcequota-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 25Gi
---
# This should exceed storage quota (75Gi total when quota is 100Gi)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-4
  namespace: resourcequota-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 40Gi  # This would make total 115Gi, exceeding 100Gi quota
```

### Task 6: Quota Monitoring and Status

```yaml
# quota-monitor-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-monitor
  namespace: resourcequota-test
spec:
  containers:
  - name: monitor
    image: bitnami/kubectl:latest
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== ResourceQuota Monitor ==="
      while true; do
        echo "$(date): Checking ResourceQuota status..."
        
        kubectl get resourcequota -n resourcequota-test -o wide
        echo ""
        
        kubectl describe resourcequota comprehensive-quota -n resourcequota-test
        echo ""
        
        echo "Current resource usage:"
        kubectl top pods -n resourcequota-test 2>/dev/null || echo "Metrics not available"
        echo ""
        
        echo "Object counts:"
        echo "Pods: $(kubectl get pods -n resourcequota-test --no-headers | wc -l)"
        echo "Services: $(kubectl get services -n resourcequota-test --no-headers | wc -l)"
        echo "Deployments: $(kubectl get deployments -n resourcequota-test --no-headers | wc -l)"
        echo "PVCs: $(kubectl get pvc -n resourcequota-test --no-headers | wc -l)"
        echo ""
        
        sleep 300  # Check every 5 minutes
      done
```

### Task 7: Scoped ResourceQuotas

```yaml
# scoped-resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: best-effort-quota
  namespace: resourcequota-test
spec:
  hard:
    pods: "5"
  scopes:
  - BestEffort  # Only applies to BestEffort QoS pods
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: not-best-effort-quota
  namespace: resourcequota-test
spec:
  hard:
    requests.cpu: "3"
    requests.memory: 6Gi
    limits.cpu: "6"
    limits.memory: 12Gi
  scopes:
  - NotBestEffort  # Applies to Guaranteed and Burstable QoS pods
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: terminating-quota
  namespace: resourcequota-test
spec:
  hard:
    pods: "3"
    requests.cpu: "2"
    requests.memory: 4Gi
  scopes:
  - Terminating  # Applies to pods with activeDeadlineSeconds
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: non-terminating-quota
  namespace: resourcequota-test
spec:
  hard:
    pods: "15"
    requests.cpu: "8"
    requests.memory: 16Gi
  scopes:
  - NotTerminating  # Applies to pods without activeDeadlineSeconds
```

### Task 8: Test Different QoS Classes with Quotas

```yaml
# qos-quota-test.yaml
# BestEffort pod (no resources specified)
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod-1
  namespace: resourcequota-test
  labels:
    qos: besteffort
spec:
  containers:
  - name: app
    image: nginx:alpine
---
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod-2
  namespace: resourcequota-test
  labels:
    qos: besteffort
spec:
  containers:
  - name: app
    image: nginx:alpine
---
# Guaranteed pod (requests = limits)
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod-1
  namespace: resourcequota-test
  labels:
    qos: guaranteed
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "256Mi"
        cpu: "250m"
---
# Burstable pod (requests < limits)
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod-1
  namespace: resourcequota-test
  labels:
    qos: burstable
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "128Mi"
        cpu: "125m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

### Task 9: Priority Class ResourceQuotas

```yaml
# priority-class-quota.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority class for critical applications"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
description: "Low priority class for batch jobs"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: high-priority-quota
  namespace: resourcequota-test
spec:
  hard:
    pods: "5"
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
  scopeSelector:
    matchExpressions:
    - operator: In
      scopeName: PriorityClass
      values: ["high-priority"]
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: low-priority-quota
  namespace: resourcequota-test
spec:
  hard:
    pods: "10"
    requests.cpu: "2"
    requests.memory: 4Gi
  scopeSelector:
    matchExpressions:
    - operator: In
      scopeName: PriorityClass
      values: ["low-priority"]
```

### Task 10: Cross-namespace Quota Comparison

```bash
# Create additional namespace for comparison
kubectl create namespace resourcequota-comparison
```

```yaml
# comparison-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: comparison-quota
  namespace: resourcequota-comparison
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "5"
    services: "3"
```

### Task 11: ResourceQuota Status Reporting

```yaml
# quota-status-reporter.yaml
apiVersion: v1
kind: Pod
metadata:
  name: quota-reporter
  namespace: resourcequota-test
spec:
  containers:
  - name: reporter
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "50m"
      limits:
        memory: "100Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args:
    - -c
    - |
      apk add --no-cache curl jq
      
      echo "=== ResourceQuota Status Report ==="
      echo "Report generated at: $(date)"
      echo ""
      
      # Create a simple report (note: this would need kubectl in real scenario)
      echo "Namespace: resourcequota-test"
      echo ""
      
      # In a real scenario, this pod would need RBAC permissions
      # to read ResourceQuota status from the Kubernetes API
      echo "To get actual quota status, run:"
      echo "kubectl describe resourcequota -n resourcequota-test"
      echo ""
      
      echo "To check quota utilization:"
      echo "kubectl get resourcequota -n resourcequota-test -o yaml"
      
      sleep 3600
```

## Verification Commands

```bash
# Check ResourceQuota status
kubectl get resourcequota -n resourcequota-test
kubectl get resourcequota -n resourcequota-test -o wide

# Detailed quota information
kubectl describe resourcequota basic-quota -n resourcequota-test
kubectl describe resourcequota comprehensive-quota -n resourcequota-test

# Check quota usage vs limits
kubectl get resourcequota comprehensive-quota -n resourcequota-test -o yaml

# Try to create resources that exceed quota
kubectl apply -f quota-violation-deployment.yaml
kubectl get events -n resourcequota-test --sort-by='.lastTimestamp' | grep -i quota

# Check current resource consumption
kubectl top pods -n resourcequota-test
kubectl get pods -n resourcequota-test -o custom-columns=NAME:.metadata.name,CPU-REQUEST:.spec.containers[0].resources.requests.cpu,MEMORY-REQUEST:.spec.containers[0].resources.requests.memory

# Count objects against quotas
echo "Current object counts:"
echo "Pods: $(kubectl get pods -n resourcequota-test --no-headers | wc -l)"
echo "Services: $(kubectl get services -n resourcequota-test --no-headers | wc -l)"
echo "Deployments: $(kubectl get deployments -n resourcequota-test --no-headers | wc -l)"
echo "PVCs: $(kubectl get pvc -n resourcequota-test --no-headers | wc -l)"

# Check scoped quotas
kubectl describe resourcequota best-effort-quota -n resourcequota-test
kubectl describe resourcequota not-best-effort-quota -n resourcequota-test

# Verify QoS class assignments
kubectl get pods -n resourcequota-test -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass

# Check PVC storage consumption
kubectl get pvc -n resourcequota-test -o custom-columns=NAME:.metadata.name,STORAGE:.spec.resources.requests.storage,STATUS:.status.phase

# Monitor quota status
kubectl logs quota-monitor -n resourcequota-test
```

## ResourceQuota Calculations

### Task 12: Quota Planning and Analysis

```bash
# Create quota analysis script
cat > analyze-quotas.sh << 'EOF'
#!/bin/bash

echo "=== ResourceQuota Analysis ==="
echo "Namespace: resourcequota-test"
echo ""

# Function to convert memory units to bytes for calculation
convert_memory() {
    local value=$1
    if [[ $value =~ ^([0-9]+)Gi$ ]]; then
        echo $(( ${BASH_REMATCH[1]} * 1024 * 1024 * 1024 ))
    elif [[ $value =~ ^([0-9]+)Mi$ ]]; then
        echo $(( ${BASH_REMATCH[1]} * 1024 * 1024 ))
    else
        echo "0"
    fi
}

# Function to convert CPU units to millicores
convert_cpu() {
    local value=$1
    if [[ $value =~ ^([0-9]+)$ ]]; then
        echo $(( ${BASH_REMATCH[1]} * 1000 ))
    elif [[ $value =~ ^([0-9]+)m$ ]]; then
        echo ${BASH_REMATCH[1]}
    else
        echo "0"
    fi
}

echo "Current ResourceQuota Status:"
kubectl get resourcequota comprehensive-quota -n resourcequota-test -o yaml | grep -A 20 "status:"

echo ""
echo "Resource Utilization Analysis:"

# Get quota limits
cpu_limit=$(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.spec.hard.limits\.cpu}')
memory_limit=$(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.spec.hard.limits\.memory}')

# Get current usage
cpu_used=$(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.status.used.limits\.cpu}' 2>/dev/null || echo "0")
memory_used=$(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.status.used.limits\.memory}' 2>/dev/null || echo "0Mi")

echo "CPU Limit: $cpu_limit"
echo "CPU Used: $cpu_used"
echo "Memory Limit: $memory_limit"
echo "Memory Used: $memory_used"

# Calculate percentages (simplified)
echo ""
echo "Utilization Percentages:"
echo "CPU: $(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.status.used.limits\.cpu}' 2>/dev/null || echo 'N/A') / $(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.spec.hard.limits\.cpu}')"
echo "Memory: $(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.status.used.limits\.memory}' 2>/dev/null || echo 'N/A') / $(kubectl get resourcequota comprehensive-quota -n resourcequota-test -o jsonpath='{.spec.hard.limits\.memory}')"

