# Lab 07: Resource Quotas and Limits

## Objective
Learn to manage resource consumption using ResourceQuotas, LimitRanges, and pod resource specifications.

## Tasks

### Task 1: Basic Resource Requests and Limits

```yaml
# pod-with-resources.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Resource demo running'; sleep 30; done"]
```

### Task 2: Create Namespace with ResourceQuota

```bash
# Create a test namespace
kubectl create namespace resource-test
```

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: resource-test
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "10"
    persistentvolumeclaims: "4"
    services: "5"
    secrets: "10"
    configmaps: "10"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-quota
  namespace: resource-test
spec:
  hard:
    count/deployments.apps: "3"
    count/services: "5"
    count/secrets: "10"
    count/configmaps: "10"
    count/replicasets.apps: "5"
```

### Task 3: LimitRange for Default Resources

```yaml
# limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limit-range
  namespace: resource-test
spec:
  limits:
  - default:
      memory: "256Mi"
      cpu: "200m"
    defaultRequest:
      memory: "128Mi"
      cpu: "100m"
    max:
      memory: "1Gi"
      cpu: "500m"
    min:
      memory: "64Mi"
      cpu: "50m"
    type: Container
  - max:
      memory: "2Gi"
      cpu: "1000m"
    min:
      memory: "128Mi"
      cpu: "100m"
    type: Pod
```

### Task 4: Test ResourceQuota with Deployments

```yaml
# deployment-within-quota.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-test-deployment
  namespace: resource-test
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
            memory: "100Mi"
            cpu: "100m"
          limits:
            memory: "200Mi"
            cpu: "200m"
        ports:
        - containerPort: 80
```

### Task 5: Test ResourceQuota Enforcement

```yaml
# deployment-exceeding-quota.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-exceed-deployment
  namespace: resource-test
spec:
  replicas: 5  # This might exceed pod quota
  selector:
    matchLabels:
      app: quota-exceed
  template:
    metadata:
      labels:
        app: quota-exceed
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "500Mi"  # This will exceed memory quota
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Task 6: QoS Classes Demonstration

```yaml
# qos-guaranteed.yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos-guaranteed
  namespace: resource-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "200Mi"
        cpu: "200m"
      limits:
        memory: "200Mi"  # Same as requests = Guaranteed QoS
        cpu: "200m"
---
# qos-burstable.yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos-burstable
  namespace: resource-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "300Mi"  # Different from requests = Burstable QoS
        cpu: "400m"
---
# qos-besteffort.yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos-besteffort
  namespace: resource-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    # No resources specified = BestEffort QoS
```

### Task 7: Priority Classes

```yaml
# priority-classes.yaml
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
description: "Low priority class for background jobs"
---
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-pod
  namespace: resource-test
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
---
apiVersion: v1
kind: Pod
metadata:
  name: low-priority-pod
  namespace: resource-test
spec:
  priorityClassName: low-priority
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
```

### Task 8: Resource Monitoring and Stress Testing

```yaml
# stress-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: stress-test-pod
  namespace: resource-test
spec:
  containers:
  - name: stress
    image: polinux/stress
    resources:
      requests:
        memory: "200Mi"
        cpu: "200m"
      limits:
        memory: "400Mi"
        cpu: "500m"
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "300M", "--cpu", "1", "--timeout", "60s"]
```

### Task 9: Multi-container Pod Resources

```yaml
# multi-container-resources.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-resources
  namespace: resource-test
spec:
  containers:
  - name: web
    image: nginx:alpine
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
    ports:
    - containerPort: 80
  - name: sidecar
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "50m"
      limits:
        memory: "100Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Sidecar running'; sleep 30; done"]
  initContainers:
  - name: init
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "50m"
      limits:
        memory: "100Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args: ["-c", "echo 'Init container completed'; sleep 5"]
```

## Verification Commands

```bash
# Check resource quotas
kubectl get resourcequota -n resource-test
kubectl describe resourcequota compute-quota -n resource-test
kubectl describe resourcequota object-quota -n resource-test

# Check limit ranges
kubectl get limitrange -n resource-test
kubectl describe limitrange resource-limit-range -n resource-test

# Check pod resource usage
kubectl top pods -n resource-test --use-protocol-buffers

# Check pod QoS classes
kubectl get pods -n resource-test -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass

# Check priority classes
kubectl get priorityclasses

# Check resource requests and limits for pods
kubectl describe pod resource-demo-pod | grep -A 5 Requests
kubectl describe pod qos-guaranteed -n resource-test | grep -A 10 Containers:

# Check deployment resource allocation
kubectl describe deployment quota-test-deployment -n resource-test

# Monitor resource usage
kubectl top nodes
kubectl top pods -n resource-test

# Check if quota is exceeded
kubectl get events -n resource-test | grep -i quota
kubectl get replicasets -n resource-test
```

## Troubleshooting Resource Issues

### Task 10: Common Resource Problems

```yaml
# problematic-pod.yaml (Will fail due to resource constraints)
apiVersion: v1
kind: Pod
metadata:
  name: problematic-pod
  namespace: resource-test
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "2Gi"  # Exceeds LimitRange max
        cpu: "600m"    # Exceeds LimitRange max
      limits:
        memory: "4Gi"
        cpu: "1000m"
```

```bash
# Debug resource issues
kubectl describe pod problematic-pod -n resource-test
kubectl get events -n resource-test --sort-by='.lastTimestamp'

# Check current quota usage
kubectl describe resourcequota -n resource-test

# List all resources consuming quota
kubectl get pods -n resource-test -o=custom-columns=NAME:.metadata.name,CPU-REQUEST:.spec.containers[*].resources.requests.cpu,MEMORY-REQUEST:.spec.containers[*].resources.requests.memory
```

## Cleanup

```bash
kubectl delete pod resource-demo-pod
kubectl delete namespace resource-test
kubectl delete priorityclass high-priority low-priority
```

## 🎯 Key Learning Points

- **Resource Requests**: Minimum guaranteed resources (used for scheduling)
- **Resource Limits**: Maximum allowed resources (enforced at runtime)
- **ResourceQuota**: Limits total resource consumption in a namespace
- **LimitRange**: Sets default, min, max resource values for individual objects
- **QoS Classes**:
  - **Guaranteed**: requests = limits for all containers
  - **Burstable**: requests < limits (or only requests specified)
  - **BestEffort**: no requests or limits specified
- **Priority Classes**: Influence pod scheduling and eviction order
- **Resource Types**: CPU (millicores), Memory (bytes), Storage, Object counts
- **Enforcement**: Quota checked at creation time, limits enforced at runtime
- **Monitoring**: Use `kubectl top` and metrics-server for resource usage
- **Troubleshooting**: Check events, describe resources, verify quotas
- **Best Practices**: Always set requests and limits, monitor usage, use appropriate QoS
