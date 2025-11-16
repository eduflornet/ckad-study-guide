# Lab 11: LimitRanges

## Objective
Learn to use LimitRanges to enforce resource constraints and set default resource values for containers and pods within a namespace.

## Tasks

### Task 1: Create Test Namespace with LimitRange

```bash
# Create namespace for testing
kubectl create namespace limitrange-test
```

```yaml
# basic-limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: basic-limit-range
  namespace: limitrange-test
spec:
  limits:
  - type: Container
    default:
      memory: "256Mi"
      cpu: "200m"
    defaultRequest:
      memory: "128Mi"
      cpu: "100m"
    max:
      memory: "1Gi"
      cpu: "1000m"
    min:
      memory: "64Mi"
      cpu: "50m"
  - type: Pod
    max:
      memory: "2Gi"
      cpu: "2000m"
    min:
      memory: "128Mi"
      cpu: "100m"
```

### Task 2: Container-level LimitRange

```yaml
# container-limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: limitrange-test
spec:
  limits:
  - type: Container
    default:           # Default limits if not specified
      memory: "512Mi"
      cpu: "500m"
    defaultRequest:    # Default requests if not specified
      memory: "256Mi"
      cpu: "250m"
    max:              # Maximum allowed
      memory: "2Gi"
      cpu: "2000m"
    min:              # Minimum required
      memory: "100Mi"
      cpu: "100m"
    maxLimitRequestRatio:  # Limit/Request ratio constraints
      memory: "4"     # Limit can be max 4x the request
      cpu: "2"        # Limit can be max 2x the request
```

### Task 3: Test Pods with Different Resource Specifications

```yaml
# test-pods-limitrange.yaml
# Pod with no resource specification (will get defaults)
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-resources
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args: ["-c", "echo 'Pod with default resources'; sleep 3600"]
---
# Pod with partial resource specification
apiVersion: v1
kind: Pod
metadata:
  name: pod-partial-resources
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "200Mi"
        # CPU request will be defaulted
      # Limits will be defaulted
    command: ["/bin/sh"]
    args: ["-c", "echo 'Pod with partial resources'; sleep 3600"]
---
# Pod with complete resource specification
apiVersion: v1
kind: Pod
metadata:
  name: pod-complete-resources
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "300Mi"
        cpu: "300m"
      limits:
        memory: "600Mi"
        cpu: "600m"
    command: ["/bin/sh"]
    args: ["-c", "echo 'Pod with complete resources'; sleep 3600"]
```

### Task 4: LimitRange Violations

```yaml
# violation-tests.yaml
# This pod should be rejected - exceeds max memory
apiVersion: v1
kind: Pod
metadata:
  name: pod-exceeds-max-memory
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "3Gi"  # Exceeds max memory (2Gi)
        cpu: "100m"
      limits:
        memory: "3Gi"
        cpu: "200m"
---
# This pod should be rejected - below minimum CPU
apiVersion: v1
kind: Pod
metadata:
  name: pod-below-min-cpu
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "128Mi"
        cpu: "25m"     # Below minimum CPU (100m)
      limits:
        memory: "256Mi"
        cpu: "50m"
---
# This pod should be rejected - bad limit/request ratio
apiVersion: v1
kind: Pod
metadata:
  name: pod-bad-ratio
  namespace: limitrange-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "800Mi"  # 8x request ratio (max allowed is 4x)
        cpu: "300m"      # 3x request ratio (max allowed is 2x)
```

### Task 5: Pod-level LimitRange

```yaml
# pod-limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: pod-limits
  namespace: limitrange-test
spec:
  limits:
  - type: Pod
    max:
      memory: "4Gi"
      cpu: "4000m"
    min:
      memory: "256Mi"
      cpu: "200m"
```

```yaml
# multi-container-pod-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod-test
  namespace: limitrange-test
spec:
  containers:
  - name: container1
    image: nginx:alpine
    resources:
      requests:
        memory: "200Mi"
        cpu: "200m"
      limits:
        memory: "400Mi"
        cpu: "400m"
  - name: container2
    image: alpine:latest
    resources:
      requests:
        memory: "300Mi"
        cpu: "300m"
      limits:
        memory: "600Mi"
        cpu: "600m"
    command: ["/bin/sh"]
    args: ["-c", "while true; do sleep 30; done"]
  # Total pod resources: 500Mi/500m requests, 1000Mi/1000m limits
```

### Task 6: PersistentVolumeClaim LimitRange

```yaml
# pvc-limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: pvc-limits
  namespace: limitrange-test
spec:
  limits:
  - type: PersistentVolumeClaim
    max:
      storage: "10Gi"
    min:
      storage: "1Gi"
```

```yaml
# test-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
  namespace: limitrange-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: "5Gi"  # Within the 1Gi-10Gi range
---
# This PVC should be rejected
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: oversized-pvc
  namespace: limitrange-test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: "20Gi"  # Exceeds max storage (10Gi)
```

### Task 7: Comprehensive LimitRange

```yaml
# comprehensive-limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: comprehensive-limits
  namespace: limitrange-test
spec:
  limits:
  # Container limits
  - type: Container
    default:
      memory: "512Mi"
      cpu: "500m"
      ephemeral-storage: "1Gi"
    defaultRequest:
      memory: "256Mi"
      cpu: "250m"
      ephemeral-storage: "500Mi"
    max:
      memory: "4Gi"
      cpu: "4000m"
      ephemeral-storage: "10Gi"
    min:
      memory: "128Mi"
      cpu: "100m"
      ephemeral-storage: "100Mi"
    maxLimitRequestRatio:
      memory: "3"
      cpu: "2"
      ephemeral-storage: "4"
  # Pod limits
  - type: Pod
    max:
      memory: "8Gi"
      cpu: "8000m"
      ephemeral-storage: "20Gi"
    min:
      memory: "256Mi"
      cpu: "200m"
      ephemeral-storage: "200Mi"
  # PVC limits
  - type: PersistentVolumeClaim
    max:
      storage: "100Gi"
    min:
      storage: "1Gi"
```

### Task 8: Deployment with LimitRange

```yaml
# deployment-with-limitrange.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-limitrange
  namespace: limitrange-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app-limitrange
  template:
    metadata:
      labels:
        app: web-app-limitrange
    spec:
      containers:
      - name: web
        image: nginx:alpine
        # No resources specified - will get defaults from LimitRange
        ports:
        - containerPort: 80
      - name: sidecar
        image: alpine:latest
        resources:
          requests:
            memory: "150Mi"
            cpu: "150m"
          # Limits will be defaulted
        command: ["/bin/sh"]
        args: ["-c", "while true; do echo 'Sidecar running'; sleep 30; done"]
```

### Task 9: LimitRange with Different Resource Types

```yaml
# resource-types-limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-types-limits
  namespace: limitrange-test
spec:
  limits:
  # GPU limits (if GPU nodes available)
  - type: Container
    default:
      nvidia.com/gpu: "0"
    max:
      nvidia.com/gpu: "2"
    min:
      nvidia.com/gpu: "0"
  # Extended resources
  - type: Container
    max:
      example.com/custom-resource: "10"
    min:
      example.com/custom-resource: "1"
```

### Task 10: LimitRange Monitoring and Validation

```yaml
# validation-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: validation-test
  namespace: limitrange-test
spec:
  containers:
  - name: validator
    image: alpine:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== LimitRange Validation Test ==="
      echo "Container resource information:"
      
      # Check cgroup limits
      echo "Memory limit from cgroup:"
      cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo "Not available"
      
      echo "CPU quota from cgroup:"
      cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo "Not available"
      
      echo "CPU period from cgroup:"
      cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo "Not available"
      
      # Calculate CPU limit
      quota=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo "-1")
      period=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo "100000")
      
      if [ "$quota" != "-1" ] && [ "$period" != "0" ]; then
        cpu_limit=$((quota * 1000 / period))
        echo "Calculated CPU limit: ${cpu_limit}m"
      fi
      
      sleep 3600
```

## Verification Commands

```bash
# Check LimitRanges in namespace
kubectl get limitrange -n limitrange-test
kubectl describe limitrange basic-limit-range -n limitrange-test

# Check how LimitRange affects pods
kubectl describe pod pod-no-resources -n limitrange-test | grep -A 10 "Containers:"
kubectl describe pod pod-partial-resources -n limitrange-test | grep -A 10 "Containers:"

# Try to create violation pods (should fail)
kubectl apply -f violation-tests.yaml
kubectl get events -n limitrange-test --sort-by='.lastTimestamp' | grep -E "(Failed|Invalid)"

# Check deployment pods get defaults
kubectl get pods -n limitrange-test -l app=web-app-limitrange
kubectl describe pod -l app=web-app-limitrange -n limitrange-test | grep -A 5 "Containers:"

# Compare resource allocations
kubectl get pods -n limitrange-test -o custom-columns=NAME:.metadata.name,MEMORY-REQUEST:.spec.containers[0].resources.requests.memory,MEMORY-LIMIT:.spec.containers[0].resources.limits.memory,CPU-REQUEST:.spec.containers[0].resources.requests.cpu,CPU-LIMIT:.spec.containers[0].resources.limits.cpu

# Check PVC creation
kubectl get pvc -n limitrange-test
kubectl describe pvc test-pvc -n limitrange-test

# Validate comprehensive limits
kubectl describe limitrange comprehensive-limits -n limitrange-test
```

## LimitRange Best Practices

### Task 11: Production LimitRange Example

```yaml
# production-limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: limitrange-test
  annotations:
    description: "Production environment resource limits"
    contact: "platform-team@company.com"
spec:
  limits:
  # Microservices container limits
  - type: Container
    default:
      memory: "1Gi"
      cpu: "1000m"
      ephemeral-storage: "2Gi"
    defaultRequest:
      memory: "512Mi"
      cpu: "500m"
      ephemeral-storage: "1Gi"
    max:
      memory: "8Gi"
      cpu: "8000m"
      ephemeral-storage: "20Gi"
    min:
      memory: "256Mi"
      cpu: "250m"
      ephemeral-storage: "512Mi"
    maxLimitRequestRatio:
      memory: "2"     # Conservative ratio for memory
      cpu: "2"        # Conservative ratio for CPU
      ephemeral-storage: "4"
  # Pod-level limits (sum of all containers)
  - type: Pod
    max:
      memory: "16Gi"
      cpu: "16000m"
      ephemeral-storage: "40Gi"
    min:
      memory: "512Mi"
      cpu: "500m"
      ephemeral-storage: "1Gi"
  # Storage limits
  - type: PersistentVolumeClaim
    max:
      storage: "1Ti"
    min:
      storage: "10Gi"
```

## Troubleshooting LimitRange Issues

### Task 12: Common LimitRange Problems

```bash
# Debug LimitRange issues
echo "=== LimitRange Troubleshooting ==="

# Check if LimitRange exists
kubectl get limitrange -n limitrange-test

# Check LimitRange details
kubectl describe limitrange -n limitrange-test

# Look for admission controller errors
kubectl get events -n limitrange-test --field-selector reason=FailedCreate

# Check pod resource assignments
kubectl get pods -n limitrange-test -o yaml | grep -A 20 resources:

# Validate resource calculations for multi-container pods
kubectl describe pod multi-container-pod-test -n limitrange-test | grep -A 30 "Containers:"

# Check if pods are pending due to LimitRange violations
kubectl get pods -n limitrange-test --field-selector=status.phase=Pending
kubectl describe pod pod-exceeds-max-memory -n limitrange-test 2>/dev/null || echo "Pod creation failed as expected"
```

## Cleanup

```bash
kubectl delete namespace limitrange-test
```

## 🎯 Key Learning Points

- **LimitRange Scope**: Applies to individual objects (containers, pods, PVCs) within a namespace
- **Types of Limits**:
  - **Container**: Per-container resource constraints
  - **Pod**: Aggregate limits for all containers in a pod
  - **PersistentVolumeClaim**: Storage size constraints
- **Constraint Types**:
  - **min**: Minimum required resources
  - **max**: Maximum allowed resources  
  - **default**: Default limits when not specified
  - **defaultRequest**: Default requests when not specified
  - **maxLimitRequestRatio**: Maximum ratio between limits and requests
- **Admission Control**: LimitRange is enforced by admission controllers at creation time
- **Default Behavior**: Missing resource specs get populated with defaults
- **Multi-container**: Pod limits apply to the sum of all container resources
- **Inheritance**: Deployments and ReplicaSets inherit LimitRange defaults
- **Validation**: Resource specs are validated against LimitRange constraints
- **Best Practices**:
  - Set reasonable defaults to prevent resource starvation
  - Use conservative limit/request ratios
  - Monitor actual usage to adjust limits
  - Document LimitRange policies for developers
- **Troubleshooting**: Check events for admission controller failures
- **Planning**: Consider cluster capacity when setting limits
