# Lab 5: Resource Monitoring

**Objective**: Learn to monitor and analyze resource usage in Kubernetes clusters
**Time**: 40 minutes
**Difficulty**: Intermediate

---

## Learning Outcomes

By the end of this lab, you will be able to:
- Use kubectl top commands to monitor resource usage
- Analyze CPU and memory consumption patterns
- Monitor resource usage over time
- Debug resource-related issues
- Implement resource monitoring best practices
- Set up resource alerts and thresholds

---

## Prerequisites

- Kubernetes cluster access with Metrics Server enabled
- kubectl configured
- Basic understanding of Kubernetes resources
- Completion of previous labs recommended

---

## Theory: Resource Monitoring in Kubernetes

### Resource Types

1. **CPU**: Measured in cores (1000m = 1 core)
2. **Memory**: Measured in bytes (Ki, Mi, Gi)
3. **Storage**: Persistent volume usage
4. **Network**: Bandwidth and packet metrics

### Monitoring Components

- **Metrics Server**: Collects resource metrics from kubelets
- **kubelet**: Gathers metrics from running containers
- **cAdvisor**: Container resource usage monitoring
- **kubectl top**: Command-line resource monitoring

### Resource States

- **Requests**: Guaranteed resource allocation
- **Limits**: Maximum resource usage allowed
- **Actual Usage**: Current resource consumption

---

## Exercise 1: Basic Resource Monitoring (10 minutes)

### Step 1: Verify Metrics Server

```bash
# Check if Metrics Server is running
kubectl get deployment metrics-server -n kube-system

# If not present, install metrics server (for testing environments)
if ! kubectl get deployment metrics-server -n kube-system &>/dev/null; then
    echo "Installing Metrics Server for testing..."
    cat << EOF > metrics-server.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-server
  namespace: kube-system
  labels:
    k8s-app: metrics-server
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  template:
    metadata:
      labels:
        k8s-app: metrics-server
    spec:
      containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
        image: k8s.gcr.io/metrics-server/metrics-server:v0.6.1
        imagePullPolicy: IfNotPresent
        livenessProbe:
          failureThreshold: 3
          httpGet:
            path: /livez
            port: https
            scheme: HTTPS
          periodSeconds: 10
        name: metrics-server
        ports:
        - containerPort: 4443
          name: https
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /readyz
            port: https
            scheme: HTTPS
          initialDelaySeconds: 20
          periodSeconds: 10
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
        volumeMounts:
        - mountPath: /tmp
          name: tmp-dir
      nodeSelector:
        kubernetes.io/os: linux
      priorityClassName: system-cluster-critical
      serviceAccountName: metrics-server
      volumes:
      - emptyDir: {}
        name: tmp-dir
EOF
    kubectl apply -f metrics-server.yaml
    echo "Waiting for Metrics Server to be ready..."
    sleep 30
fi

# Wait for metrics to be available
echo "Waiting for metrics to be available..."
kubectl wait --for=condition=Available deployment/metrics-server -n kube-system --timeout=60s
sleep 30
```

### Step 2: Basic Resource Monitoring Commands

```bash
# Monitor node resource usage
echo "=== Node Resource Usage ==="
kubectl top nodes

# Monitor pod resource usage
echo "=== Pod Resource Usage ==="
kubectl top pods --all-namespaces

# Monitor specific namespace
echo "=== Default Namespace Pods ==="
kubectl top pods

# Sort by CPU usage
echo "=== Pods Sorted by CPU Usage ==="
kubectl top pods --all-namespaces --sort-by='cpu'

# Sort by Memory usage
echo "=== Pods Sorted by Memory Usage ==="
kubectl top pods --all-namespaces --sort-by='memory'
```

### Step 3: Create Applications with Different Resource Usage

```yaml
cat << EOF > resource-test-apps.yaml
apiVersion: v1
kind: Pod
metadata:
  name: cpu-intensive
  labels:
    app: cpu-intensive
spec:
  containers:
  - name: cpu-load
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting CPU intensive workload..."
      # Create high CPU load
      while true; do
        dd if=/dev/zero of=/dev/null bs=1M count=100 2>/dev/null
      done
    resources:
      requests:
        cpu: 100m
        memory: 64Mi
      limits:
        cpu: 500m
        memory: 128Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: memory-intensive
  labels:
    app: memory-intensive
spec:
  containers:
  - name: memory-load
    image: python:3.9-alpine
    command:
    - python
    - -c
    - |
      import time
      print("Starting memory intensive workload...")
      
      # Gradually consume memory
      memory_blocks = []
      block_size = 10 * 1024 * 1024  # 10MB blocks
      
      for i in range(50):  # Up to 500MB
          print(f"Allocating block {i+1} (10MB)")
          memory_blocks.append(b'x' * block_size)
          time.sleep(2)
      
      print("Memory allocation complete, holding...")
      while True:
          time.sleep(60)
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 600Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: balanced-load
  labels:
    app: balanced-load
spec:
  containers:
  - name: app
    image: node:18-alpine
    command:
    - sh
    - -c
    - |
      cat << 'NODEAPP' > app.js
      const express = require('express');
      const crypto = require('crypto');
      const app = express();
      const port = 3000;
      
      let requestCount = 0;
      
      // CPU intensive endpoint
      app.get('/cpu', (req, res) => {
        const start = Date.now();
        // Generate some CPU load
        for (let i = 0; i < 100000; i++) {
          crypto.createHash('sha256').update(String(i)).digest('hex');
        }
        requestCount++;
        res.json({
          message: 'CPU intensive task completed',
          duration: Date.now() - start,
          requestCount
        });
      });
      
      // Memory allocation endpoint
      app.get('/memory', (req, res) => {
        const size = req.query.size || 10;
        const buffer = Buffer.alloc(size * 1024 * 1024); // Allocate memory
        buffer.fill('x');
        requestCount++;
        res.json({
          message: \`Allocated \${size}MB of memory\`,
          totalRequests: requestCount,
          memoryUsage: process.memoryUsage()
        });
      });
      
      app.get('/status', (req, res) => {
        res.json({
          uptime: process.uptime(),
          memoryUsage: process.memoryUsage(),
          requestCount,
          timestamp: new Date().toISOString()
        });
      });
      
      // Simulate regular activity
      setInterval(() => {
        // Light background processing
        crypto.createHash('md5').update(String(Date.now())).digest('hex');
      }, 1000);
      
      app.listen(port, () => {
        console.log(\`Balanced load app listening on port \${port}\`);
      });
      NODEAPP
      
      npm init -y
      npm install express
      node app.js
    ports:
    - containerPort: 3000
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 300m
        memory: 256Mi
EOF

kubectl apply -f resource-test-apps.yaml
```

---

## Exercise 2: Continuous Resource Monitoring (10 minutes)

### Step 1: Set Up Monitoring Script

```bash
cat << 'SCRIPT' > monitor-resources.sh
#!/bin/bash

DURATION=${1:-300}  # Default 5 minutes
INTERVAL=${2:-10}   # Default 10 seconds

echo "Starting resource monitoring for $DURATION seconds (interval: ${INTERVAL}s)"
echo "Timestamp,Pod,CPU,Memory" > resource-log.csv

END_TIME=$(($(date +%s) + DURATION))

while [ $(date +%s) -lt $END_TIME ]; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "=== $TIMESTAMP ==="
    echo "--- Node Resources ---"
    kubectl top nodes
    
    echo "--- Pod Resources ---"
    kubectl top pods --sort-by='cpu'
    
    # Log specific pods to CSV
    kubectl top pods --no-headers | while read pod cpu memory; do
        echo "$TIMESTAMP,$pod,$cpu,$memory" >> resource-log.csv
    done
    
    echo ""
    sleep $INTERVAL
done

echo "Monitoring completed. Check resource-log.csv for data."
SCRIPT

chmod +x monitor-resources.sh
```

### Step 2: Start Monitoring and Create Load

```bash
# Start monitoring in background
./monitor-resources.sh 180 15 &
MONITOR_PID=$!

# Wait for apps to start
kubectl wait --for=condition=Ready pod/cpu-intensive pod/memory-intensive pod/balanced-load --timeout=60s

# Generate load on balanced app
kubectl port-forward balanced-load 3000:3000 &
PF_PID=$!
sleep 5

# Create CPU load
echo "Generating CPU load..."
for i in {1..10}; do
    curl -s http://localhost:3000/cpu > /dev/null &
done

# Create memory load
echo "Generating memory load..."
for i in {1..5}; do
    curl -s "http://localhost:3000/memory?size=20" > /dev/null &
done

sleep 30

# Monitor resources manually during load
echo "=== Resource Usage During Load ==="
kubectl top pods

sleep 60

# Clean up
kill $PF_PID 2>/dev/null
wait $MONITOR_PID
```

### Step 3: Analyze Resource Patterns

```bash
# Analyze the collected data
echo "=== Resource Usage Analysis ==="

if [ -f resource-log.csv ]; then
    echo "Total data points collected: $(wc -l < resource-log.csv)"
    echo ""
    
    echo "--- Average CPU Usage by Pod ---"
    awk -F',' 'NR>1 {gsub(/m/, "", $3); pods[$2] += $3; counts[$2]++} END {for (pod in pods) printf "%s: %.1fm\n", pod, pods[pod]/counts[pod]}' resource-log.csv | sort -k2 -nr
    
    echo ""
    echo "--- Average Memory Usage by Pod ---"
    awk -F',' 'NR>1 {gsub(/Mi/, "", $4); pods[$2] += $4; counts[$2]++} END {for (pod in pods) printf "%s: %.1fMi\n", pod, pods[pod]/counts[pod]}' resource-log.csv | sort -k2 -nr
    
    echo ""
    echo "--- Peak Resource Usage ---"
    echo "Peak CPU usage:"
    awk -F',' 'NR>1 {gsub(/m/, "", $3); if ($3 > max_cpu) {max_cpu = $3; max_cpu_pod = $2; max_cpu_time = $1}} END {printf "%s: %sm at %s\n", max_cpu_pod, max_cpu, max_cpu_time}' resource-log.csv
    
    echo "Peak Memory usage:"
    awk -F',' 'NR>1 {gsub(/Mi/, "", $4); if ($4 > max_mem) {max_mem = $4; max_mem_pod = $2; max_mem_time = $1}} END {printf "%s: %sMi at %s\n", max_mem_pod, max_mem, max_mem_time}' resource-log.csv
fi
```

---

## Exercise 3: Resource Constraint Analysis (10 minutes)

### Step 1: Create Resource-Constrained Applications

```yaml
cat << EOF > resource-constrained.yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-limited
  labels:
    app: memory-limited
spec:
  containers:
  - name: app
    image: python:3.9-alpine
    command:
    - python
    - -c
    - |
      import time
      import os
      
      print("Starting memory limited application...")
      print(f"Container memory limit: {os.environ.get('MEMORY_LIMIT', 'unknown')}")
      
      try:
          # Try to allocate more memory than limit
          memory_blocks = []
          block_size = 50 * 1024 * 1024  # 50MB blocks
          
          for i in range(20):  # Try to allocate 1GB total
              print(f"Allocating block {i+1} (50MB) - Total: {(i+1)*50}MB")
              memory_blocks.append(b'x' * block_size)
              time.sleep(1)
              
      except MemoryError:
          print("MemoryError: Hit memory limit!")
      except Exception as e:
          print(f"Error: {e}")
      
      print("Holding allocated memory...")
      while True:
          time.sleep(30)
    env:
    - name: MEMORY_LIMIT
      value: "200Mi"
    resources:
      requests:
        cpu: 50m
        memory: 100Mi
      limits:
        cpu: 100m
        memory: 200Mi  # Low memory limit to trigger OOM
---
apiVersion: v1
kind: Pod
metadata:
  name: cpu-throttled
  labels:
    app: cpu-throttled
spec:
  containers:
  - name: app
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting CPU throttled application..."
      echo "This app will be CPU throttled due to low limits"
      
      # Generate continuous CPU load
      while true; do
        echo "High CPU task starting..."
        # Multiple CPU intensive operations
        dd if=/dev/zero of=/dev/null bs=1M count=500 2>/dev/null &
        dd if=/dev/zero of=/dev/null bs=1M count=500 2>/dev/null &
        dd if=/dev/zero of=/dev/null bs=1M count=500 2>/dev/null &
        wait
        echo "High CPU task completed, brief pause..."
        sleep 2
      done
    resources:
      requests:
        cpu: 50m
        memory: 32Mi
      limits:
        cpu: 100m  # Low CPU limit to trigger throttling
        memory: 64Mi
EOF

kubectl apply -f resource-constrained.yaml
```

### Step 2: Monitor Resource Constraints

```bash
# Watch for OOM kills and CPU throttling
kubectl get events --sort-by='.lastTimestamp' -w &
EVENTS_PID=$!

# Monitor resource usage of constrained apps
for i in {1..20}; do
    echo "=== Check $i ==="
    echo "Memory Limited Pod:"
    kubectl top pod memory-limited 2>/dev/null || echo "Pod not ready or terminated"
    
    echo "CPU Throttled Pod:"
    kubectl top pod cpu-throttled 2>/dev/null || echo "Pod not ready or terminated"
    
    # Check pod status
    kubectl get pods memory-limited cpu-throttled -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount
    
    sleep 10
done

kill $EVENTS_PID 2>/dev/null
```

### Step 3: Analyze Resource Events

```bash
# Check for OOM kills
echo "=== OOM Kill Events ==="
kubectl get events --field-selector reason=OOMKilling --sort-by='.lastTimestamp'

# Check for resource-related events
echo "=== Resource Related Events ==="
kubectl get events --field-selector 'reason in (FailedScheduling,OOMKilling,Killing)' --sort-by='.lastTimestamp'

# Describe pods to see resource issues
echo "=== Memory Limited Pod Details ==="
kubectl describe pod memory-limited | grep -A 10 -B 5 -E "(Events|Resources|Limits|Requests)"

echo "=== CPU Throttled Pod Details ==="
kubectl describe pod cpu-throttled | grep -A 10 -B 5 -E "(Events|Resources|Limits|Requests)"
```

---

## Exercise 4: Advanced Resource Monitoring (10 minutes)

### Step 1: Create Monitoring Dashboard Script

```bash
cat << 'DASHBOARD' > resource-dashboard.sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Kubernetes Resource Monitoring Dashboard${NC}"
    echo -e "${BLUE}  $(date)${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

function print_section() {
    echo -e "${GREEN}--- $1 ---${NC}"
}

function check_metrics_server() {
    if ! kubectl top nodes &>/dev/null; then
        echo -e "${RED}ERROR: Metrics Server not available${NC}"
        return 1
    fi
    return 0
}

function show_cluster_overview() {
    print_section "Cluster Resource Overview"
    
    # Node resources
    echo "Node Resources:"
    kubectl top nodes
    echo ""
    
    # Total cluster capacity
    echo "Cluster Capacity Summary:"
    kubectl describe nodes | grep -E "(cpu|memory):" | \
    awk '/cpu:/ {cpu+=$2} /memory:/ {mem+=$2} END {printf "Total CPU: %.1f cores, Total Memory: %.1f Gi\n", cpu/1000, mem/1024/1024}'
    echo ""
}

function show_resource_usage() {
    print_section "Pod Resource Usage"
    
    echo "Top CPU Consumers:"
    kubectl top pods --all-namespaces --sort-by='cpu' | head -10
    echo ""
    
    echo "Top Memory Consumers:"
    kubectl top pods --all-namespaces --sort-by='memory' | head -10
    echo ""
}

function show_resource_issues() {
    print_section "Resource-Related Issues"
    
    # Recent resource events
    echo "Recent Resource Events:"
    kubectl get events --all-namespaces --field-selector 'reason in (FailedScheduling,OOMKilling,Killing,Unhealthy)' \
    --sort-by='.lastTimestamp' | tail -10
    echo ""
    
    # Pods with high restart counts (potential resource issues)
    echo "Pods with High Restart Counts:"
    kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount | \
    awk 'NR>1 && $3>0 {print}' | sort -k3 -nr | head -5
    echo ""
}

function show_namespace_breakdown() {
    print_section "Resource Usage by Namespace"
    
    # Get all namespaces and their resource usage
    for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
        pod_count=$(kubectl get pods -n $ns --no-headers 2>/dev/null | wc -l)
        if [ $pod_count -gt 0 ]; then
            echo "Namespace: $ns ($pod_count pods)"
            kubectl top pods -n $ns 2>/dev/null | head -5
            echo ""
        fi
    done
}

function monitor_specific_pods() {
    print_section "Monitoring Specific Pods"
    
    # Monitor our test pods
    for pod in cpu-intensive memory-intensive balanced-load memory-limited cpu-throttled; do
        if kubectl get pod $pod &>/dev/null; then
            echo "Pod: $pod"
            kubectl top pod $pod 2>/dev/null || echo "  Metrics not available"
            kubectl get pod $pod -o custom-columns=STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount
            echo ""
        fi
    done
}

# Main dashboard loop
if ! check_metrics_server; then
    exit 1
fi

# Run dashboard once or in loop
if [ "$1" = "loop" ]; then
    while true; do
        clear
        print_header
        show_cluster_overview
        show_resource_usage
        show_resource_issues
        show_namespace_breakdown
        monitor_specific_pods
        echo -e "${YELLOW}Refreshing in 30 seconds... (Ctrl+C to stop)${NC}"
        sleep 30
    done
else
    print_header
    show_cluster_overview
    show_resource_usage
    show_resource_issues
    show_namespace_breakdown
    monitor_specific_pods
fi
DASHBOARD

chmod +x resource-dashboard.sh
```

### Step 2: Run the Dashboard

```bash
# Run dashboard once
echo "Running resource dashboard..."
./resource-dashboard.sh

echo ""
echo "=== Resource Utilization Summary ==="

# Calculate resource utilization percentages
kubectl describe nodes | grep -A 2 -E "Allocated resources:" | \
grep -E "(cpu|memory)" | \
awk '
/cpu/ {cpu_used = $2; cpu_total = $4; gsub(/[()%]/, "", cpu_used); print "CPU Utilization: " cpu_used "%"}
/memory/ {mem_used = $2; mem_total = $4; gsub(/[()%]/, "", mem_used); print "Memory Utilization: " mem_used "%"}
'
```

### Step 3: Resource Alert Simulation

```bash
cat << 'ALERT_SCRIPT' > resource-alerts.sh
#!/bin/bash

# Resource monitoring with alerts
CPU_THRESHOLD=80    # Alert if pod CPU > 80%
MEMORY_THRESHOLD=80 # Alert if pod memory > 80%

echo "Starting resource monitoring with alerts..."
echo "CPU Alert Threshold: ${CPU_THRESHOLD}%"
echo "Memory Alert Threshold: ${MEMORY_THRESHOLD}%"
echo ""

function check_resource_alerts() {
    local alerts_found=0
    
    # Get pod resource usage
    kubectl top pods --all-namespaces --no-headers | while read namespace pod cpu memory; do
        # Extract numeric values
        cpu_value=$(echo $cpu | sed 's/m//')
        memory_value=$(echo $memory | sed 's/Mi//')
        
        # Get pod limits for percentage calculation
        limits=$(kubectl get pod $pod -n $namespace -o jsonpath='{.spec.containers[0].resources.limits}' 2>/dev/null)
        
        if [ -n "$limits" ]; then
            cpu_limit=$(echo $limits | jq -r '.cpu // empty' | sed 's/m//')
            memory_limit=$(echo $limits | jq -r '.memory // empty' | sed 's/Mi//')
            
            # Calculate percentages if limits exist
            if [ -n "$cpu_limit" ] && [ "$cpu_limit" -gt 0 ]; then
                cpu_percent=$((cpu_value * 100 / cpu_limit))
                if [ $cpu_percent -gt $CPU_THRESHOLD ]; then
                    echo "ALERT: High CPU usage in $namespace/$pod: ${cpu_percent}% (${cpu})"
                    alerts_found=1
                fi
            fi
            
            if [ -n "$memory_limit" ] && [ "$memory_limit" -gt 0 ]; then
                memory_percent=$((memory_value * 100 / memory_limit))
                if [ $memory_percent -gt $MEMORY_THRESHOLD ]; then
                    echo "ALERT: High Memory usage in $namespace/$pod: ${memory_percent}% (${memory})"
                    alerts_found=1
                fi
            fi
        fi
    done
    
    return $alerts_found
}

# Monitor for 2 minutes
for i in {1..12}; do
    echo "=== Check $i ($(date)) ==="
    
    if check_resource_alerts; then
        echo "No resource alerts"
    fi
    
    # Check for recent OOM kills
    recent_oom=$(kubectl get events --all-namespaces --field-selector reason=OOMKilling \
                 --sort-by='.lastTimestamp' -o custom-columns=TIME:.lastTimestamp,NAMESPACE:.namespace,POD:.involvedObject.name \
                 | tail -1)
    
    if echo "$recent_oom" | grep -v "TIME" | grep -q "."; then
        echo "CRITICAL ALERT: Recent OOM Kill detected - $recent_oom"
    fi
    
    echo ""
    sleep 10
done
ALERT_SCRIPT

chmod +x resource-alerts.sh
./resource-alerts.sh
```

---

## Troubleshooting Resource Issues

### Common Resource Problems

#### Issue 1: Pod Not Scheduling Due to Resources

```bash
# Check pending pods
kubectl get pods --field-selector=status.phase=Pending

# Check scheduling events
kubectl get events --field-selector reason=FailedScheduling --sort-by='.lastTimestamp'

# Check node capacity
kubectl describe nodes | grep -A 5 "Allocated resources:"
```

#### Issue 2: Container Getting OOM Killed

```bash
# Check for OOM events
kubectl get events --field-selector reason=OOMKilling

# Check container resource limits
kubectl describe pod <pod-name> | grep -A 5 "Limits:"

# Monitor memory usage leading up to OOM
kubectl top pod <pod-name>
```

#### Issue 3: CPU Throttling

```bash
# Monitor CPU usage vs limits
kubectl top pod <pod-name>
kubectl describe pod <pod-name> | grep -A 5 "Limits:"

# Check for CPU throttling in node metrics (requires node access)
# Look for high CPU wait times or throttling counters
```

### Resource Optimization Tips

```yaml
# Example of well-configured resources
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    resources:
      requests:
        cpu: 100m      # Minimum guaranteed
        memory: 128Mi
      limits:
        cpu: 500m      # Maximum allowed (5x request)
        memory: 256Mi  # Maximum allowed (2x request)
```

---

## Validation and Testing

### Test Your Understanding

1. **Monitor cluster resource usage** and identify top consumers
2. **Detect resource-constrained pods** using kubectl top and events
3. **Calculate resource utilization percentages** for nodes and pods
4. **Set up automated resource monitoring** with alert thresholds

### Verification Commands

```bash
# Resource monitoring skills
kubectl top nodes
kubectl top pods --all-namespaces --sort-by='cpu'
kubectl top pods --all-namespaces --sort-by='memory'

# Resource analysis
kubectl describe node <node-name> | grep -A 10 "Allocated resources:"
kubectl get events --field-selector reason=FailedScheduling
kubectl get events --field-selector reason=OOMKilling

# Pod resource investigation
kubectl describe pod <pod-name> | grep -A 10 "Resources:"
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[0].resources}'
```

---

## Cleanup

```bash
# Delete all lab resources
kubectl delete pod cpu-intensive memory-intensive balanced-load memory-limited cpu-throttled

# Remove files
rm -f resource-test-apps.yaml resource-constrained.yaml metrics-server.yaml
rm -f monitor-resources.sh resource-dashboard.sh resource-alerts.sh
rm -f resource-log.csv
```

---

## Key Takeaways

1. **kubectl top** commands provide real-time resource usage data
2. **Metrics Server** is required for resource monitoring
3. **Resource requests and limits** control scheduling and usage
4. **Continuous monitoring** helps identify patterns and issues
5. **Resource events** provide insights into constraint violations
6. **Proper resource configuration** prevents scheduling and performance issues

---

## Next Steps

- Proceed to [Lab 6: Application Metrics](lab06-metrics.md)
- Learn about [Pod Debugging](lab07-pod-debugging.md)
- Practice [Performance Debugging](lab09-performance-debug.md)

---

## Additional Resources

- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Monitoring Resource Usage](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)
- [Metrics Server](https://github.com/kubernetes-sigs/metrics-server)