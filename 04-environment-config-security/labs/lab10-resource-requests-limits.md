# Lab 10: Resource Requests and Limits

## Objective
Master resource management by setting appropriate CPU and memory requests and limits for containers to ensure optimal resource allocation and prevent resource starvation.

## Tasks

### Task 1: Basic Resource Specification

```yaml
# basic-resource-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: basic-resource-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    ports:
    - containerPort: 80
```

### Task 2: Different Resource Units

```yaml
# resource-units-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-units-demo
spec:
  containers:
  - name: container1
    image: alpine:latest
    resources:
      requests:
        memory: "64Mi"      # Mebibytes
        cpu: "0.1"          # 100 millicores
      limits:
        memory: "128Mi"
        cpu: "500m"         # 500 millicores
    command: ["/bin/sh"]
    args: ["-c", "echo 'Container 1: 64Mi-128Mi RAM, 0.1-0.5 CPU'; sleep 3600"]
  - name: container2
    image: alpine:latest
    resources:
      requests:
        memory: "1Gi"       # Gibibytes
        cpu: "1000m"        # 1 full CPU core
      limits:
        memory: "2Gi"
        cpu: "2000m"        # 2 full CPU cores
    command: ["/bin/sh"]
    args: ["-c", "echo 'Container 2: 1Gi-2Gi RAM, 1-2 CPU cores'; sleep 3600"]
```

### Task 3: Resource Stress Testing

```yaml
# stress-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: stress-test-pod
spec:
  containers:
  - name: cpu-stress
    image: polinux/stress
    resources:
      requests:
        memory: "200Mi"
        cpu: "200m"
      limits:
        memory: "400Mi"
        cpu: "500m"
    command: ["stress"]
    args: ["--cpu", "2", "--timeout", "300s"]  # Stress 2 CPU cores for 5 minutes
  - name: memory-stress
    image: polinux/stress
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "300Mi"
        cpu: "200m"
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "250M", "--timeout", "300s"]  # Use 250MB RAM
```

### Task 4: QoS Class Examples

```yaml
# qos-classes.yaml
# Guaranteed QoS (requests = limits)
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-qos
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
        memory: "256Mi"    # Same as requests
        cpu: "250m"        # Same as requests
---
# Burstable QoS (requests < limits)
apiVersion: v1
kind: Pod
metadata:
  name: burstable-qos
  labels:
    qos: burstable
spec:
  containers:
  - name: app
    image: nginx:alpine
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"    # Higher than requests
        cpu: "500m"        # Higher than requests
---
# BestEffort QoS (no resources specified)
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-qos
  labels:
    qos: besteffort
spec:
  containers:
  - name: app
    image: nginx:alpine
    # No resources specified
```

### Task 5: Resource Monitoring Pod

```yaml
# resource-monitor-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-monitor
spec:
  containers:
  - name: monitor
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
      apk add --no-cache procps
      echo "Resource monitoring started..."
      while true; do
        echo "=== Resource Usage Report $(date) ==="
        echo "Memory usage:"
        free -h
        echo ""
        echo "CPU usage:"
        ps aux --sort=-%cpu | head -10
        echo ""
        echo "Container limits (from cgroups):"
        echo "Memory limit: $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 'Not available')"
        echo "CPU quota: $(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo 'Not available')"
        echo "CPU period: $(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 'Not available')"
        echo "=========================="
        sleep 60
      done
```

### Task 6: Deployment with Resource Management

```yaml
# resource-managed-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-with-resources
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app-resources
  template:
    metadata:
      labels:
        app: web-app-resources
    spec:
      containers:
      - name: web
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
          limits:
            memory: "200Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
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
        args: ["-c", "while true; do echo 'Sidecar heartbeat'; sleep 30; done"]
```

### Task 7: Resource Limits Testing

```yaml
# resource-limits-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-limit-test
spec:
  containers:
  - name: memory-hog
    image: alpine:latest
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"    # This will be enforced
        cpu: "200m"
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Starting memory consumption test..."
      echo "Container memory limit: 200Mi"
      
      # Try to allocate more memory than the limit
      echo "Attempting to allocate 300MB (exceeds 200Mi limit)..."
      
      # This should cause the container to be killed by OOMKiller
      dd if=/dev/zero of=/tmp/memory_eater bs=1M count=300
      
      echo "If you see this, something went wrong - should have been killed by OOM"
      sleep 3600
---
apiVersion: v1
kind: Pod
metadata:
  name: cpu-limit-test
spec:
  containers:
  - name: cpu-intensive
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "100m"
      limits:
        memory: "100Mi"
        cpu: "200m"        # CPU will be throttled at 200m
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Starting CPU intensive task..."
      echo "CPU limit: 200m (20% of 1 core)"
      
      # CPU intensive loop - will be throttled
      while true; do
        echo "CPU spinning..." > /dev/null
      done
```

### Task 8: Resource Requests Impact on Scheduling

```yaml
# scheduling-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: large-resource-request
spec:
  containers:
  - name: resource-hungry
    image: nginx:alpine
    resources:
      requests:
        memory: "16Gi"     # Large memory request - may not be schedulable
        cpu: "8000m"       # 8 CPU cores request
      limits:
        memory: "32Gi"
        cpu: "16000m"
---
apiVersion: v1
kind: Pod
metadata:
  name: small-resource-request
spec:
  containers:
  - name: lightweight
    image: nginx:alpine
    resources:
      requests:
        memory: "32Mi"     # Small memory request - should schedule easily
        cpu: "10m"
      limits:
        memory: "64Mi"
        cpu: "50m"
```

### Task 9: Multi-container Resource Allocation

```yaml
# multi-container-resources.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-resources
spec:
  containers:
  - name: web-server
    image: nginx:alpine
    resources:
      requests:
        memory: "200Mi"
        cpu: "200m"
      limits:
        memory: "400Mi"
        cpu: "500m"
    ports:
    - containerPort: 80
  - name: log-processor
    image: alpine:latest
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Processing logs...'; sleep 10; done"]
  - name: metrics-collector
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "50m"
      limits:
        memory: "100Mi"
        cpu: "100m"
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'Collecting metrics...'; sleep 15; done"]
  initContainers:
  - name: setup
    image: alpine:latest
    resources:
      requests:
        memory: "50Mi"
        cpu: "100m"
      limits:
        memory: "100Mi"
        cpu: "200m"
    command: ["/bin/sh"]
    args: ["-c", "echo 'Initialization complete'; sleep 5"]
```

### Task 10: Resource Management Best Practices

```yaml
# best-practices-example.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-app
  labels:
    app: production-app
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: production-app
  template:
    metadata:
      labels:
        app: production-app
        tier: frontend
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "256Mi"    # Based on observed baseline usage
            cpu: "250m"
          limits:
            memory: "512Mi"    # 2x requests for burst capacity
            cpu: "500m"        # 2x requests for CPU bursts
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /healthz
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        env:
        - name: RESOURCE_REQUESTS_MEMORY
          valueFrom:
            resourceFieldRef:
              containerName: app
              resource: requests.memory
        - name: RESOURCE_LIMITS_CPU
          valueFrom:
            resourceFieldRef:
              containerName: app
              resource: limits.cpu
```

## Verification Commands

```bash
# Check resource allocation for pods
kubectl describe pod basic-resource-pod | grep -A 10 "Containers:"
kubectl describe pod resource-units-demo | grep -A 20 "Containers:"

# Check QoS classes
kubectl get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass

# Monitor resource usage (requires metrics-server)
kubectl top pods
kubectl top pods --sort-by=memory
kubectl top pods --sort-by=cpu

# Check node resource capacity and allocation
kubectl describe nodes | grep -A 5 -E "(Capacity|Allocatable|Allocated resources)"
kubectl top nodes

# Check resource limits in deployment
kubectl describe deployment web-app-with-resources | grep -A 10 "Containers:"

# Monitor stress tests
kubectl logs stress-test-pod -c cpu-stress
kubectl logs stress-test-pod -c memory-stress

# Check if pods are pending due to resource constraints
kubectl get pods | grep Pending
kubectl describe pod large-resource-request | grep Events

# Monitor resource consumption
kubectl exec resource-monitor -- cat /proc/meminfo
kubectl logs resource-monitor

# Check container resource limits from inside pod
kubectl exec multi-container-resources -c web-server -- cat /sys/fs/cgroup/memory/memory.limit_in_bytes
kubectl exec multi-container-resources -c web-server -- cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us
```

## Resource Calculation Examples

### Task 11: Resource Planning and Calculation

```bash
# Calculate total resource requirements
echo "=== Resource Planning Calculator ==="

# Example: 3 replicas of production-app
replicas=3
memory_request_per_pod="256Mi"
cpu_request_per_pod="250m"
memory_limit_per_pod="512Mi"
cpu_limit_per_pod="500m"

echo "Application: production-app"
echo "Replicas: $replicas"
echo ""
echo "Per Pod Resources:"
echo "  Memory Request: $memory_request_per_pod"
echo "  Memory Limit: $memory_limit_per_pod" 
echo "  CPU Request: $cpu_request_per_pod"
echo "  CPU Limit: $cpu_limit_per_pod"
echo ""

# Convert to bytes/millicores for calculation
memory_request_mb=$((256 * replicas))
memory_limit_mb=$((512 * replicas))
cpu_request_mc=$((250 * replicas))
cpu_limit_mc=$((500 * replicas))

echo "Total Cluster Requirements:"
echo "  Memory Requests: ${memory_request_mb}Mi"
echo "  Memory Limits: ${memory_limit_mb}Mi"
echo "  CPU Requests: ${cpu_request_mc}m"
echo "  CPU Limits: ${cpu_limit_mc}m"
```

## Troubleshooting Resource Issues

### Task 12: Common Resource Problems

```bash
# Debug resource issues
echo "=== Resource Troubleshooting Guide ==="

# Check pod events for resource-related issues
kubectl get events --sort-by='.lastTimestamp' | grep -E "(Failed|Insufficient|OOM|Evicted)"

# Check node resource pressure
kubectl describe nodes | grep -E "(Pressure|Condition)"

# Identify resource-hungry pods
kubectl top pods --sort-by=memory | head -10
kubectl top pods --sort-by=cpu | head -10

# Check for pending pods due to resources
kubectl get pods --field-selector=status.phase=Pending

# Examine OOMKilled containers
kubectl get pods -o wide | grep -E "(OOMKilled|Error)"
kubectl describe pod memory-limit-test | grep -A 10 "Last State"
```

## Cleanup

```bash
kubectl delete pod basic-resource-pod resource-units-demo stress-test-pod guaranteed-qos burstable-qos besteffort-qos resource-monitor memory-limit-test cpu-limit-test large-resource-request small-resource-request multi-container-resources
kubectl delete deployment web-app-with-resources production-app
```

## 🎯 Key Learning Points

- **Requests vs Limits**: Requests for scheduling, limits for enforcement
- **Resource Units**: 
  - Memory: Mi (mebibytes), Gi (gibibytes), M (megabytes), G (gigabytes)
  - CPU: m (millicores), whole numbers (cores)
- **QoS Classes**: Guaranteed > Burstable > BestEffort (eviction priority)
- **Resource Monitoring**: Use `kubectl top` and monitoring tools
- **Container Limits**: Memory limits enforced by OOMKiller, CPU limits by throttling
- **Scheduling**: Pods scheduled based on requests, not limits
- **Best Practices**:
  - Always set both requests and limits
  - Limits should be 1.5-2x requests for burst capacity
  - Monitor actual usage to tune values
  - Use Guaranteed QoS for critical workloads
- **Troubleshooting**: Check events, node pressure, resource usage patterns
- **Planning**: Calculate total cluster resource requirements
- **Multi-container**: Each container has its own resource specification
- **Init Containers**: Resources counted during initialization phase only
