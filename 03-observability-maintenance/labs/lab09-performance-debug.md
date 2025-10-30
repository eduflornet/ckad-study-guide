# Lab 9: Performance Debugging and Optimization

**Objective**: Master performance analysis and optimization techniques for Kubernetes applications
**Time**: 45 minutes
**Difficulty**: Advanced

---

## Learning Objectives

By the end of this lab, you will be able to:
- Identify performance bottlenecks in Kubernetes applications
- Analyze resource utilization and constraints
- Debug memory leaks and CPU throttling
- Optimize application performance using resource management
- Monitor and analyze application metrics
- Implement performance testing strategies

---

## Prerequisites

- Kubernetes cluster access with metrics server
- kubectl CLI configured
- Understanding of Kubernetes resource management
- Basic knowledge of application performance concepts

---

## Lab Environment Setup

Create a dedicated namespace and install metrics server if needed:

```bash
kubectl create namespace performance-debug
kubectl config set-context --current --namespace=performance-debug

# Check if metrics server is available
kubectl top nodes 2>/dev/null || echo "Metrics server may not be available"
```

---

## Exercise 1: CPU Performance Issues (12 minutes)

### Task 1.1: Create CPU-Intensive Applications

Deploy applications with various CPU patterns:

```yaml
cat << EOF > cpu-performance-apps.yaml
# CPU-intensive application with resource limits
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-intensive-app
  labels:
    app: cpu-intensive
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cpu-intensive
  template:
    metadata:
      labels:
        app: cpu-intensive
        performance-type: cpu-bound
    spec:
      containers:
      - name: cpu-worker
        image: busybox:1.35
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"  # Limited CPU to cause throttling
            memory: "128Mi"
        command:
        - sh
        - -c
        - |
          echo "Starting CPU-intensive workload..."
          
          # Function to simulate CPU-intensive work
          cpu_intensive() {
            echo "Starting CPU stress test: $(date)"
            
            # CPU-bound calculation (multiple processes to stress CPU)
            for i in $(seq 1 4); do
              {
                count=0
                while [ $count -lt 1000000 ]; do
                  # Mathematical operations to consume CPU
                  result=$(( count * count / 2 + count % 17 ))
                  count=$(( count + 1 ))
                done
                echo "CPU worker $i completed 1M operations"
              } &
            done
            
            wait
            echo "CPU stress test completed: $(date)"
          }
          
          # Run continuous CPU stress with monitoring
          while true; do
            echo "=== Performance Stats: $(date) ==="
            
            # Monitor CPU usage from inside container
            if command -v top >/dev/null; then
              timeout 5 top -b -n 1 | head -10
            fi
            
            # Run CPU-intensive work
            cpu_intensive
            
            echo "Sleeping for 30 seconds..."
            sleep 30
          done
---
# Application with CPU spikes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-spike-app
  labels:
    app: cpu-spike
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cpu-spike
  template:
    metadata:
      labels:
        app: cpu-spike
        performance-type: cpu-spike
    spec:
      containers:
      - name: spike-generator
        image: alpine:3.18
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
          limits:
            cpu: "500m"
            memory: "64Mi"
        command:
        - sh
        - -c
        - |
          apk add --no-cache stress-ng
          
          echo "Starting CPU spike generator..."
          
          while true; do
            echo "Normal operation: $(date)"
            sleep 60
            
            echo "CPU SPIKE: Starting high CPU usage: $(date)"
            # Generate CPU spike for 30 seconds
            stress-ng --cpu 2 --timeout 30s --metrics-brief
            
            echo "CPU SPIKE: Completed: $(date)"
            sleep 60
          done
---
# Service for monitoring
apiVersion: v1
kind: Service
metadata:
  name: performance-monitor
spec:
  selector:
    performance-type: cpu-bound
  ports:
  - port: 8080
    targetPort: 8080
    name: metrics
EOF

kubectl apply -f cpu-performance-apps.yaml
```

### Task 1.2: Monitor CPU Performance

```bash
# Wait for deployments
kubectl wait --for=condition=available deployment/cpu-intensive-app deployment/cpu-spike-app --timeout=120s

# Check resource utilization
echo "=== Resource Utilization ==="
kubectl top pods
kubectl top nodes

# Monitor CPU throttling
echo -e "\n=== CPU Throttling Analysis ==="
CPU_POD=$(kubectl get pods -l app=cpu-intensive -o jsonpath='{.items[0].metadata.name}')
SPIKE_POD=$(kubectl get pods -l app=cpu-spike -o jsonpath='{.items[0].metadata.name}')

echo "CPU-intensive pod: $CPU_POD"
echo "CPU-spike pod: $SPIKE_POD"

# Check current resource usage
kubectl describe pod $CPU_POD | grep -A 10 "Containers:"
kubectl logs $CPU_POD --tail=10

# Analyze CPU throttling from cgroup (if available)
kubectl exec $CPU_POD -- cat /sys/fs/cgroup/cpu/cpu.stat 2>/dev/null || echo "CPU stats not available"
kubectl exec $CPU_POD -- cat /proc/stat | head -5
```

### Task 1.3: Performance Analysis Tools

```bash
# Create performance monitoring script
cat << 'EOF' > cpu-performance-monitor.sh
#!/bin/bash

echo "=== CPU Performance Monitoring ==="
NAMESPACE="performance-debug"

# Function to get pod resource usage
get_pod_resources() {
    local pod_name=$1
    echo "--- Resource Usage for $pod_name ---"
    
    # Get resource requests and limits
    kubectl describe pod $pod_name | grep -A 5 -B 5 "Limits\|Requests"
    
    # Get current usage if metrics available
    kubectl top pod $pod_name 2>/dev/null || echo "Metrics not available"
    
    # Check if pod is being throttled
    local container_id=$(kubectl get pod $pod_name -o jsonpath='{.status.containerStatuses[0].containerID}' | cut -d'/' -f3)
    echo "Container ID: $container_id"
}

# Monitor all performance pods
for pod in $(kubectl get pods -l performance-type=cpu-bound -o jsonpath='{.items[*].metadata.name}'); do
    get_pod_resources $pod
    echo ""
done

echo "=== CPU Throttling Detection ==="
# Look for CPU throttling indicators
for pod in $(kubectl get pods -l app=cpu-intensive -o jsonpath='{.items[*].metadata.name}'); do
    echo "Checking $pod for CPU throttling..."
    
    # Check logs for performance indicators
    kubectl logs $pod --tail=20 | grep -E "(CPU|throttl|performance)" || echo "No CPU throttling indicators in logs"
    
    # Check pod events for throttling
    kubectl get events --field-selector involvedObject.name=$pod | grep -i throttl || echo "No throttling events"
done
EOF

chmod +x cpu-performance-monitor.sh
./cpu-performance-monitor.sh
```

---

## Exercise 2: Memory Performance Issues (12 minutes)

### Task 2.1: Create Memory-Intensive Applications

```yaml
cat << EOF > memory-performance-apps.yaml
# Memory leak simulation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-leak-app
  labels:
    app: memory-leak
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-leak
  template:
    metadata:
      labels:
        app: memory-leak
        performance-type: memory-leak
    spec:
      containers:
      - name: memory-leaker
        image: python:3.11-alpine
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"  # Will hit OOM eventually
        command:
        - python3
        - -c
        - |
          import time
          import gc
          import sys
          
          print("Starting memory leak simulation...")
          
          # List to hold references (causing memory leak)
          memory_hog = []
          iteration = 0
          
          def get_memory_info():
              """Get current memory usage info"""
              try:
                  with open('/proc/meminfo', 'r') as f:
                      lines = f.readlines()
                      for line in lines:
                          if 'MemAvailable' in line:
                              return line.strip()
              except:
                  return "Memory info not available"
          
          while True:
              iteration += 1
              
              # Allocate memory that won't be freed (memory leak)
              # Each iteration adds ~1MB of data
              large_data = ['x' * 1024 for _ in range(1024)]  # ~1MB
              memory_hog.extend(large_data)
              
              # Print memory statistics
              current_memory = len(memory_hog) * 1024 / (1024 * 1024)  # MB
              print(f"Iteration {iteration}: Allocated ~{current_memory:.1f}MB total")
              print(f"Memory info: {get_memory_info()}")
              print(f"List length: {len(memory_hog)}")
              
              # Force garbage collection (won't help with intentional leak)
              gc.collect()
              
              # Sleep between allocations
              time.sleep(10)
              
              # Optional: Clear some memory occasionally to show variance
              if iteration % 20 == 0:
                  print("Clearing 25% of memory...")
                  memory_hog = memory_hog[len(memory_hog)//4:]
---
# Memory spike application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-spike-app
  labels:
    app: memory-spike
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-spike
  template:
    metadata:
      labels:
        app: memory-spike
        performance-type: memory-spike
    spec:
      containers:
      - name: memory-spiker
        image: alpine:3.18
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
        command:
        - sh
        - -c
        - |
          apk add --no-cache stress-ng
          
          echo "Starting memory spike generator..."
          
          while true; do
            echo "Normal operation: $(date)"
            echo "Current memory usage:"
            free -m 2>/dev/null || echo "free command not available"
            
            sleep 60
            
            echo "MEMORY SPIKE: Starting high memory usage: $(date)"
            # Generate memory spike
            stress-ng --vm 1 --vm-bytes 80M --timeout 30s --metrics-brief
            
            echo "MEMORY SPIKE: Completed: $(date)"
            sleep 60
          done
---
# High-memory application with proper limits
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-optimized-app
  labels:
    app: memory-optimized
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-optimized
  template:
    metadata:
      labels:
        app: memory-optimized
        performance-type: memory-optimized
    spec:
      containers:
      - name: memory-worker
        image: python:3.11-alpine
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        command:
        - python3
        - -c
        - |
          import time
          import gc
          import psutil
          import sys
          
          print("Starting memory-optimized application...")
          
          def memory_intensive_task():
              """Perform memory-intensive task with proper cleanup"""
              print("Starting memory-intensive task...")
              
              # Create large data structure
              data = []
              for i in range(10000):
                  data.append([j for j in range(100)])
              
              # Process data
              result = sum(len(sublist) for sublist in data)
              print(f"Processed {result} items")
              
              # Explicit cleanup
              del data
              gc.collect()
              print("Memory cleanup completed")
          
          while True:
              try:
                  # Get memory info
                  process = psutil.Process()
                  memory_info = process.memory_info()
                  memory_percent = process.memory_percent()
                  
                  print(f"Current memory: {memory_info.rss / 1024 / 1024:.1f}MB ({memory_percent:.1f}%)")
                  
                  # Perform task
                  memory_intensive_task()
                  
                  print("Sleeping for 45 seconds...")
                  time.sleep(45)
                  
              except Exception as e:
                  print(f"Error: {e}")
                  time.sleep(30)
EOF

kubectl apply -f memory-performance-apps.yaml
```

### Task 2.2: Monitor Memory Usage

```bash
# Wait for deployments
kubectl wait --for=condition=available deployment/memory-leak-app deployment/memory-spike-app deployment/memory-optimized-app --timeout=120s

# Get pod names
LEAK_POD=$(kubectl get pods -l app=memory-leak -o jsonpath='{.items[0].metadata.name}')
SPIKE_POD=$(kubectl get pods -l app=memory-spike -o jsonpath='{.items[0].metadata.name}')
OPTIMIZED_POD=$(kubectl get pods -l app=memory-optimized -o jsonpath='{.items[0].metadata.name}')

echo "Memory leak pod: $LEAK_POD"
echo "Memory spike pod: $SPIKE_POD"
echo "Optimized pod: $OPTIMIZED_POD"

# Monitor memory usage
echo -e "\n=== Memory Usage Monitoring ==="
kubectl top pods

# Check memory limits and usage
echo -e "\n=== Memory Limits Analysis ==="
for pod in $LEAK_POD $SPIKE_POD $OPTIMIZED_POD; do
    echo "--- $pod ---"
    kubectl describe pod $pod | grep -A 5 -B 5 "Limits\|Requests"
done

# Watch for OOM kills
echo -e "\n=== OOM Kill Detection ==="
kubectl get events --field-selector reason=OOMKilling,reason=FailedMount
```

### Task 2.3: Memory Performance Analysis

```bash
# Create memory analysis script
cat << 'EOF' > memory-performance-analysis.sh
#!/bin/bash

echo "=== Memory Performance Analysis ==="

# Function to analyze memory usage patterns
analyze_memory_usage() {
    local pod_name=$1
    local app_label=$2
    
    echo "--- Memory Analysis for $pod_name ($app_label) ---"
    
    # Get current memory usage
    echo "Current memory usage:"
    kubectl top pod $pod_name 2>/dev/null || echo "Metrics not available"
    
    # Check memory-related events
    echo "Memory-related events:"
    kubectl get events --field-selector involvedObject.name=$pod_name | grep -i -E "(memory|oom|kill)" || echo "No memory events"
    
    # Check container memory statistics
    echo "Container memory info:"
    kubectl exec $pod_name -- cat /proc/meminfo 2>/dev/null | head -5 || echo "Memory info not accessible"
    
    # Check for memory pressure
    kubectl describe pod $pod_name | grep -A 3 -B 3 "memory" | grep -v "^--$"
    
    echo ""
}

# Analyze each memory performance pod
LEAK_POD=$(kubectl get pods -l app=memory-leak -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
SPIKE_POD=$(kubectl get pods -l app=memory-spike -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
OPTIMIZED_POD=$(kubectl get pods -l app=memory-optimized -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

[ ! -z "$LEAK_POD" ] && analyze_memory_usage $LEAK_POD "memory-leak"
[ ! -z "$SPIKE_POD" ] && analyze_memory_usage $SPIKE_POD "memory-spike"
[ ! -z "$OPTIMIZED_POD" ] && analyze_memory_usage $OPTIMIZED_POD "memory-optimized"

echo "=== Memory Performance Summary ==="
echo "Check logs for memory usage patterns:"
[ ! -z "$LEAK_POD" ] && echo "Memory leak app logs:" && kubectl logs $LEAK_POD --tail=5
[ ! -z "$OPTIMIZED_POD" ] && echo "Optimized app logs:" && kubectl logs $OPTIMIZED_POD --tail=5
EOF

chmod +x memory-performance-analysis.sh
./memory-performance-analysis.sh
```

---

## Exercise 3: I/O and Storage Performance (8 minutes)

### Task 3.1: Create Storage-Intensive Application

```yaml
cat << EOF > storage-performance-apps.yaml
# Storage I/O intensive application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: storage-io-app
  labels:
    app: storage-io
spec:
  replicas: 1
  selector:
    matchLabels:
      app: storage-io
  template:
    metadata:
      labels:
        app: storage-io
        performance-type: storage-io
    spec:
      containers:
      - name: io-worker
        image: alpine:3.18
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        volumeMounts:
        - name: test-volume
          mountPath: /data
        - name: temp-volume
          mountPath: /tmp/test
        command:
        - sh
        - -c
        - |
          apk add --no-cache fio
          
          echo "Starting storage I/O performance test..."
          
          # Function to run I/O benchmark
          run_io_benchmark() {
            local test_type=$1
            local test_dir=$2
            
            echo "=== $test_type I/O Test: $(date) ==="
            echo "Test directory: $test_dir"
            
            # Sequential write test
            echo "Sequential write test:"
            fio --name=seqwrite --ioengine=sync --rw=write --bs=1M \
                --size=50M --numjobs=1 --runtime=30 \
                --filename=$test_dir/seqwrite.dat --minimal
            
            # Random read test  
            echo "Random read test:"
            fio --name=randread --ioengine=sync --rw=randread --bs=4K \
                --size=50M --numjobs=1 --runtime=30 \
                --filename=$test_dir/randread.dat --minimal
            
            # Clean up test files
            rm -f $test_dir/*.dat
            
            echo "$test_type I/O test completed"
          }
          
          # Continuous I/O testing
          while true; do
            echo "Starting I/O performance cycle: $(date)"
            
            # Test persistent volume I/O
            run_io_benchmark "Persistent Volume" "/data"
            
            sleep 30
            
            # Test temporary volume I/O
            run_io_benchmark "Temporary Volume" "/tmp/test"
            
            echo "I/O cycle completed. Sleeping for 60 seconds..."
            sleep 60
          done
      volumes:
      - name: test-volume
        emptyDir: {}
      - name: temp-volume
        emptyDir:
          medium: Memory  # Use memory-backed storage for comparison
---
# PersistentVolume test application
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: performance-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pv-performance-app
  labels:
    app: pv-performance
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pv-performance
  template:
    metadata:
      labels:
        app: pv-performance
        performance-type: storage-pv
    spec:
      containers:
      - name: pv-worker
        image: alpine:3.18
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
          limits:
            cpu: "100m"
            memory: "64Mi"
        volumeMounts:
        - name: persistent-storage
          mountPath: /persistent
        command:
        - sh
        - -c
        - |
          echo "Starting PersistentVolume performance test..."
          
          # Simple file I/O operations
          while true; do
            echo "=== PV Performance Test: $(date) ==="
            
            # Write test
            echo "Writing large file..."
            time dd if=/dev/zero of=/persistent/test.dat bs=1M count=100 2>&1 || echo "Write failed"
            
            # Read test
            echo "Reading large file..."
            time dd if=/persistent/test.dat of=/dev/null bs=1M 2>&1 || echo "Read failed"
            
            # Cleanup
            rm -f /persistent/test.dat
            
            # Check disk usage
            echo "Disk usage:"
            df -h /persistent
            
            echo "PV test completed. Sleeping for 120 seconds..."
            sleep 120
          done
      volumes:
      - name: persistent-storage
        persistentVolumeClaim:
          claimName: performance-pvc
EOF

kubectl apply -f storage-performance-apps.yaml
```

### Task 3.2: Monitor Storage Performance

```bash
# Wait for deployments
kubectl wait --for=condition=available deployment/storage-io-app deployment/pv-performance-app --timeout=120s

# Get pod names
IO_POD=$(kubectl get pods -l app=storage-io -o jsonpath='{.items[0].metadata.name}')
PV_POD=$(kubectl get pods -l app=pv-performance -o jsonpath='{.items[0].metadata.name}')

echo "Storage I/O pod: $IO_POD"
echo "PV performance pod: $PV_POD"

# Monitor storage I/O
echo -e "\n=== Storage I/O Monitoring ==="
kubectl logs $IO_POD --tail=10
kubectl logs $PV_POD --tail=10

# Check volume mounts
echo -e "\n=== Volume Mount Analysis ==="
kubectl describe pod $IO_POD | grep -A 10 "Volumes:"
kubectl describe pod $PV_POD | grep -A 10 "Volumes:"

# Check PVC status
echo -e "\n=== PVC Status ==="
kubectl get pvc
kubectl describe pvc performance-pvc
```

---

## Exercise 4: Resource Optimization (8 minutes)

### Task 4.1: Resource Optimization Analysis

```bash
# Create resource optimization script
cat << 'EOF' > resource-optimization.sh
#!/bin/bash

echo "=== Resource Optimization Analysis ==="

# Function to analyze resource utilization
analyze_resource_utilization() {
    echo "--- Current Resource Utilization ---"
    
    # Get current resource usage
    echo "Pod resource usage:"
    kubectl top pods --containers 2>/dev/null || echo "Metrics not available"
    
    echo -e "\nNode resource usage:"
    kubectl top nodes 2>/dev/null || echo "Node metrics not available"
    
    # Analyze resource requests vs limits vs actual usage
    echo -e "\n--- Resource Configuration Analysis ---"
    for pod in $(kubectl get pods -o jsonpath='{.items[*].metadata.name}'); do
        echo "Pod: $pod"
        
        # Get resource configuration
        kubectl get pod $pod -o jsonpath='{.spec.containers[*].resources}' | jq '.' 2>/dev/null || \
        kubectl describe pod $pod | grep -A 5 "Limits\|Requests"
        
        echo ""
    done
}

# Function to identify optimization opportunities
identify_optimization_opportunities() {
    echo "--- Optimization Opportunities ---"
    
    # Check for pods without resource limits
    echo "Pods without resource limits:"
    kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.limits}{"\n"}{end}' | \
    grep -v "cpu\|memory" || echo "All pods have resource limits"
    
    # Check for pods with very high requests vs actual usage
    echo -e "\nPods with potentially over-provisioned resources:"
    kubectl top pods 2>/dev/null | awk 'NR>1 {print $1, $2, $3}' | while read pod cpu memory; do
        cpu_num=$(echo $cpu | sed 's/m//')
        memory_num=$(echo $memory | sed 's/Mi//')
        
        if [ "$cpu_num" -lt 50 ] && [ "$memory_num" -lt 50 ]; then
            echo "Pod $pod may be over-provisioned (CPU: ${cpu}, Memory: ${memory})"
        fi
    done
    
    # Check for resource conflicts
    echo -e "\nChecking for resource conflicts:"
    kubectl describe nodes | grep -A 5 "Allocated resources" || echo "Node resource info not available"
}

# Function to suggest optimizations
suggest_optimizations() {
    echo "--- Optimization Suggestions ---"
    
    # Analyze each performance pod
    for pod in $(kubectl get pods -l performance-type -o jsonpath='{.items[*].metadata.name}'); do
        performance_type=$(kubectl get pod $pod -o jsonpath='{.metadata.labels.performance-type}')
        
        echo "Pod: $pod (Type: $performance_type)"
        
        case $performance_type in
            "cpu-bound")
                echo "  - Consider increasing CPU limits for better performance"
                echo "  - Monitor for CPU throttling"
                echo "  - Consider vertical pod autoscaling"
                ;;
            "memory-leak")
                echo "  - Monitor for memory leaks and OOM kills"
                echo "  - Implement proper memory management"
                echo "  - Consider memory profiling tools"
                ;;
            "storage-io")
                echo "  - Consider faster storage classes"
                echo "  - Optimize I/O patterns"
                echo "  - Monitor disk usage and IOPS"
                ;;
            *)
                echo "  - Monitor resource usage patterns"
                echo "  - Adjust requests/limits based on actual usage"
                ;;
        esac
        echo ""
    done
}

# Run analysis
analyze_resource_utilization
identify_optimization_opportunities
suggest_optimizations
EOF

chmod +x resource-optimization.sh
./resource-optimization.sh
```

### Task 4.2: Implement Resource Optimizations

```yaml
# Create optimized versions of applications
cat << EOF > optimized-apps.yaml
# Optimized CPU-intensive application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-optimized-app
  labels:
    app: cpu-optimized
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cpu-optimized
  template:
    metadata:
      labels:
        app: cpu-optimized
        performance-type: cpu-optimized
    spec:
      containers:
      - name: cpu-worker
        image: alpine:3.18
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "500m"  # Increased CPU limit
            memory: "128Mi"
        command:
        - sh
        - -c
        - |
          apk add --no-cache stress-ng
          
          echo "Starting optimized CPU workload..."
          
          while true; do
            echo "=== Optimized CPU Test: $(date) ==="
            
            # More efficient CPU usage pattern
            stress-ng --cpu 1 --cpu-load 70 --timeout 60s --metrics-brief
            
            echo "CPU work completed. Resting..."
            sleep 60
          done
---
# HorizontalPodAutoscaler for CPU-optimized app
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cpu-optimized-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cpu-optimized-app
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
# VerticalPodAutoscaler (if supported)
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: cpu-optimized-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cpu-optimized-app
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: cpu-worker
      maxAllowed:
        cpu: 1
        memory: 512Mi
      minAllowed:
        cpu: 100m
        memory: 64Mi
EOF

kubectl apply -f optimized-apps.yaml 2>/dev/null || echo "Some resources may not be supported (VPA, etc.)"
```

---

## Exercise 5: Performance Testing and Monitoring (5 minutes)

### Task 5.1: Create Performance Test Suite

```bash
# Create comprehensive performance test script
cat << 'EOF' > performance-test-suite.sh
#!/bin/bash

echo "=== Comprehensive Performance Test Suite ==="

# Function to run load test
run_load_test() {
    local app_name=$1
    local test_duration=${2:-60}
    
    echo "--- Load Test for $app_name ---"
    
    # Get pod name
    local pod=$(kubectl get pods -l app=$app_name -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod" ]; then
        echo "No pods found for app: $app_name"
        return
    fi
    
    echo "Testing pod: $pod"
    
    # Baseline resource usage
    echo "Baseline resource usage:"
    kubectl top pod $pod 2>/dev/null || echo "Metrics not available"
    
    # Monitor during load
    echo "Starting load test for $test_duration seconds..."
    
    # Background monitoring
    {
        for i in $(seq 1 $((test_duration/10))); do
            sleep 10
            echo "$(date): $(kubectl top pod $pod 2>/dev/null | grep $pod)" >> /tmp/load_test_$app_name.log
        done
    } &
    
    local monitor_pid=$!
    
    # Wait for test duration
    sleep $test_duration
    
    # Stop monitoring
    kill $monitor_pid 2>/dev/null
    
    # Show results
    echo "Load test completed. Resource usage during test:"
    cat /tmp/load_test_$app_name.log 2>/dev/null || echo "No monitoring data collected"
    rm -f /tmp/load_test_$app_name.log
    
    echo ""
}

# Function to test autoscaling
test_autoscaling() {
    echo "--- Autoscaling Test ---"
    
    # Check HPA status
    kubectl get hpa 2>/dev/null && echo "HPA configured" || echo "No HPA found"
    
    # Check VPA status  
    kubectl get vpa 2>/dev/null && echo "VPA configured" || echo "No VPA found"
    
    # Monitor scaling events
    echo "Recent scaling events:"
    kubectl get events | grep -i "scale\|autoscal" | tail -5
}

# Function to performance summary
generate_performance_summary() {
    echo "--- Performance Summary ---"
    
    echo "Resource utilization summary:"
    kubectl top pods 2>/dev/null || echo "Pod metrics not available"
    kubectl top nodes 2>/dev/null || echo "Node metrics not available"
    
    echo -e "\nResource configuration summary:"
    for pod in $(kubectl get pods -o jsonpath='{.items[*].metadata.name}'); do
        app=$(kubectl get pod $pod -o jsonpath='{.metadata.labels.app}')
        echo "Pod: $pod (App: $app)"
        kubectl describe pod $pod | grep -A 2 -B 2 "Limits\|Requests" | grep -E "cpu|memory"
    done
    
    echo -e "\nPerformance issues detected:"
    # Check for common performance problems
    kubectl get events | grep -i -E "oom|kill|throttl|fail" | tail -5
}

# Run performance tests
echo "Starting performance test suite..."

# Test each application type
run_load_test "cpu-intensive" 30
run_load_test "memory-leak" 30
run_load_test "storage-io" 30
run_load_test "cpu-optimized" 30

# Test autoscaling
test_autoscaling

# Generate summary
generate_performance_summary

echo "=== Performance Test Suite Complete ==="
EOF

chmod +x performance-test-suite.sh
./performance-test-suite.sh
```

### Task 5.2: Performance Monitoring Dashboard

```bash
# Create performance monitoring dashboard
cat << 'EOF' > performance-dashboard.sh
#!/bin/bash

echo "=== Performance Monitoring Dashboard ==="

# Function to display real-time performance data
display_performance_dashboard() {
    while true; do
        clear
        echo "======================================================"
        echo "Kubernetes Performance Dashboard - $(date)"
        echo "======================================================"
        
        echo -e "\n📊 CLUSTER RESOURCE USAGE"
        echo "------------------------------------------------------"
        kubectl top nodes 2>/dev/null || echo "Node metrics not available"
        
        echo -e "\n🔧 POD RESOURCE USAGE"
        echo "------------------------------------------------------"
        kubectl top pods 2>/dev/null || echo "Pod metrics not available"
        
        echo -e "\n⚠️  RECENT EVENTS"
        echo "------------------------------------------------------"
        kubectl get events --sort-by='.lastTimestamp' | tail -5
        
        echo -e "\n🎯 PERFORMANCE PODS STATUS"
        echo "------------------------------------------------------"
        kubectl get pods -l performance-type --show-labels
        
        echo -e "\n🔄 AUTOSCALING STATUS"
        echo "------------------------------------------------------"
        kubectl get hpa 2>/dev/null || echo "No HPA configured"
        
        echo -e "\n💾 STORAGE STATUS"
        echo "------------------------------------------------------"
        kubectl get pvc
        
        echo -e "\nPress Ctrl+C to exit dashboard"
        echo "======================================================"
        
        sleep 10
    done
}

# Ask user if they want interactive dashboard
echo "Would you like to start the interactive performance dashboard? (y/n)"
read -r response

if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    echo "Starting performance dashboard... (Press Ctrl+C to exit)"
    sleep 2
    display_performance_dashboard
else
    echo "Displaying one-time performance snapshot:"
    echo ""
    display_performance_dashboard | head -50
fi
EOF

chmod +x performance-dashboard.sh
./performance-dashboard.sh
```

---

## Performance Debugging Checklist

```bash
cat << 'EOF' > performance-debug-checklist.sh
#!/bin/bash

echo "=== Performance Debugging Checklist ==="

# 1. Resource Configuration Check
echo "✅ 1. Resource Configuration"
echo "   - Checking resource requests and limits..."
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}' | \
while read pod resources; do
    echo "   Pod: $pod"
    echo "   Resources: $resources" | jq '.' 2>/dev/null || echo "   Resources: $resources"
done

# 2. Current Resource Usage
echo -e "\n✅ 2. Current Resource Usage"
kubectl top pods 2>/dev/null || echo "   Metrics server not available"
kubectl top nodes 2>/dev/null || echo "   Node metrics not available"

# 3. Performance Issues Detection
echo -e "\n✅ 3. Performance Issues Detection"
echo "   - Checking for OOM kills, CPU throttling, and failures..."
kubectl get events | grep -i -E "oom|kill|throttl|fail|error" | tail -10

# 4. Storage Performance
echo -e "\n✅ 4. Storage Performance"
echo "   - Checking PVC status and storage usage..."
kubectl get pvc
kubectl describe pvc 2>/dev/null | grep -E "Status|Capacity|Access"

# 5. Network Performance
echo -e "\n✅ 5. Network Performance"
echo "   - Checking service endpoints and connectivity..."
kubectl get endpoints | head -10

# 6. Autoscaling Configuration
echo -e "\n✅ 6. Autoscaling Configuration"
kubectl get hpa 2>/dev/null || echo "   No HPA configured"
kubectl get vpa 2>/dev/null || echo "   No VPA configured"

echo -e "\n=== Performance Debugging Checklist Complete ==="
EOF

chmod +x performance-debug-checklist.sh
./performance-debug-checklist.sh
```

---

## Cleanup

```bash
# Stop any running performance tests
pkill -f "performance-dashboard" 2>/dev/null

# Delete all performance applications
kubectl delete -f cpu-performance-apps.yaml
kubectl delete -f memory-performance-apps.yaml
kubectl delete -f storage-performance-apps.yaml
kubectl delete -f optimized-apps.yaml

# Delete PVC
kubectl delete pvc performance-pvc

# Delete namespace
kubectl delete namespace performance-debug

# Clean up scripts and files
rm -f cpu-performance-apps.yaml memory-performance-apps.yaml storage-performance-apps.yaml optimized-apps.yaml
rm -f cpu-performance-monitor.sh memory-performance-analysis.sh resource-optimization.sh
rm -f performance-test-suite.sh performance-dashboard.sh performance-debug-checklist.sh

# Reset context
kubectl config set-context --current --namespace=default

echo "Cleanup completed successfully!"
```

---

## Summary

In this lab, you learned how to:

- ✅ Identify and analyze CPU performance bottlenecks and throttling
- ✅ Debug memory leaks, spikes, and OOM conditions
- ✅ Monitor and optimize storage I/O performance  
- ✅ Implement resource optimization strategies
- ✅ Use horizontal and vertical pod autoscaling
- ✅ Create comprehensive performance testing suites
- ✅ Build real-time performance monitoring dashboards
- ✅ Apply systematic performance debugging approaches

**Key Performance Debugging Skills**:
- Always establish baseline resource usage before optimization
- Monitor resource requests vs limits vs actual usage
- Use appropriate tools for different performance issues
- Implement proper resource management and autoscaling
- Test performance under various load conditions

**Common Performance Issues and Solutions**:
- **CPU throttling**: Increase CPU limits or optimize workload
- **Memory leaks**: Implement proper memory management and monitoring
- **I/O bottlenecks**: Use faster storage classes and optimize access patterns
- **Resource waste**: Right-size requests/limits based on actual usage
- **Scaling issues**: Implement appropriate autoscaling strategies

**Performance Optimization Best Practices**:
- Set appropriate resource requests and limits
- Monitor actual vs configured resource usage
- Use autoscaling for dynamic workloads
- Implement proper application performance monitoring
- Regular performance testing and optimization cycles

**Next Steps**: Complete the Observability & Maintenance section by working through the [Mock Scenarios](../mock-scenarios/) and [Mock Exams](../mock-exams/) to prepare for the CKAD exam.