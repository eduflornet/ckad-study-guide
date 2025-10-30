# Lab 7: Pod Debugging

**Objective**: Master techniques for debugging pod failures and issues
**Time**: 35 minutes
**Difficulty**: Intermediate

---

## Learning Objectives

By the end of this lab, you will be able to:
- Diagnose pod startup and runtime failures
- Use kubectl commands effectively for debugging
- Analyze pod events and status information
- Debug multi-container pod issues
- Troubleshoot resource constraints and limits
- Resolve configuration and image problems

---

## Prerequisites

- Kubernetes cluster access
- kubectl CLI configured
- Understanding of pod lifecycle
- Basic knowledge of container concepts

---

## Lab Environment Setup

Create a dedicated namespace for debugging exercises:

```bash
kubectl create namespace debug-lab
kubectl config set-context --current --namespace=debug-lab
```

---

## Exercise 1: Basic Pod Debugging Techniques (8 minutes)

### Task 1.1: Create Pods with Different Failure Modes

Create various pod configurations that will fail in different ways:

```yaml
# Pod with image pull error
cat << EOF > failing-pods.yaml
apiVersion: v1
kind: Pod
metadata:
  name: image-pull-fail
  labels:
    test: debug
spec:
  containers:
  - name: app
    image: nonexistent-registry.com/fake-image:latest
    ports:
    - containerPort: 80
---
# Pod with wrong command
apiVersion: v1
kind: Pod
metadata:
  name: command-fail
  labels:
    test: debug
spec:
  containers:
  - name: app
    image: busybox:1.35
    command: ["/bin/nonexistent-command"]
---
# Pod with resource constraints
apiVersion: v1
kind: Pod
metadata:
  name: resource-fail
  labels:
    test: debug
spec:
  containers:
  - name: app
    image: nginx:1.21
    resources:
      requests:
        memory: "10Gi"  # Unrealistic memory request
        cpu: "8"        # Unrealistic CPU request
      limits:
        memory: "10Gi"
        cpu: "8"
---
# Pod with failing health check
apiVersion: v1
kind: Pod
metadata:
  name: healthcheck-fail
  labels:
    test: debug
spec:
  containers:
  - name: app
    image: nginx:1.21
    livenessProbe:
      httpGet:
        path: /nonexistent
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 2
---
# Pod with configuration error
apiVersion: v1
kind: Pod
metadata:
  name: config-fail
  labels:
    test: debug
spec:
  containers:
  - name: app
    image: postgres:13
    env:
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: nonexistent-secret
          key: password
EOF

kubectl apply -f failing-pods.yaml
```

### Task 1.2: Diagnose Each Failure

Use systematic debugging approach for each failing pod:

```bash
# Basic status overview
echo "=== Pod Status Overview ==="
kubectl get pods -l test=debug

# Detailed status for each pod
echo -e "\n=== Detailed Pod Information ==="
for pod in image-pull-fail command-fail resource-fail healthcheck-fail config-fail; do
    echo "--- Debugging $pod ---"
    kubectl get pod $pod -o wide
    echo "Status: $(kubectl get pod $pod -o jsonpath='{.status.phase}')"
    echo "Conditions:"
    kubectl get pod $pod -o jsonpath='{.status.conditions[*].type}: {.status.conditions[*].status}' | tr ' ' '\n'
    echo
done

# Check events for all pods
echo "=== Recent Events ==="
kubectl get events --sort-by=.metadata.creationTimestamp

# Describe each failing pod
echo -e "\n=== Pod Descriptions ==="
kubectl describe pods -l test=debug
```

### Task 1.3: Advanced Debugging Commands

```bash
# Get detailed pod information in JSON/YAML
echo "=== Pod YAML Analysis ==="
kubectl get pod image-pull-fail -o yaml > image-pull-debug.yaml
kubectl get pod command-fail -o yaml > command-fail-debug.yaml

# Check container statuses
echo -e "\n=== Container Status Analysis ==="
kubectl get pods -l test=debug -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{range .status.containerStatuses[*]}  {.name}: {.state}{"\n"}{end}{"\n"}{end}'

# Look for specific error patterns
echo -e "\n=== Error Pattern Analysis ==="
kubectl get events -o json | jq -r '.items[] | select(.reason == "Failed" or .reason == "FailedMount" or .reason == "ErrImagePull") | "\(.reason): \(.message)"'
```

---

## Exercise 2: Multi-Container Pod Debugging (8 minutes)

### Task 2.1: Create Multi-Container Pod with Issues

```yaml
cat << EOF > multi-container-debug.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-issues
  labels:
    app: multi-debug
spec:
  containers:
  # Main application container
  - name: web-app
    image: nginx:1.21
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
  
  # Sidecar container with issues
  - name: log-processor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting log processor..."
      sleep 10
      
      # This will cause OOMKilled due to memory limit
      echo "Allocating memory..."
      head -c 200M </dev/zero >memory-hog
      
      while true; do
        echo "Processing logs..."
        sleep 30
      done
    volumeMounts:
    - name: shared-data
      mountPath: /data
    resources:
      requests:
        memory: "32Mi"
        cpu: "25m"
      limits:
        memory: "64Mi"   # Too low for the memory allocation
        cpu: "50m"
  
  # Init container with failure
  initContainers:
  - name: init-setup
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Initializing..."
      sleep 5
      
      # This will fail
      wget http://nonexistent-url.com/setup.sh
      
      echo "Setup complete"
    volumeMounts:
    - name: shared-data
      mountPath: /setup
  
  volumes:
  - name: shared-data
    emptyDir: {}
EOF

kubectl apply -f multi-container-debug.yaml
```

### Task 2.2: Debug Multi-Container Issues

```bash
# Monitor the pod startup
kubectl get pod multi-container-issues -w &
WATCH_PID=$!

sleep 60
kill $WATCH_PID

# Check overall pod status
echo "=== Multi-Container Pod Status ==="
kubectl get pod multi-container-issues -o wide

# Check init container status
echo -e "\n=== Init Container Status ==="
kubectl describe pod multi-container-issues | grep -A 20 "Init Containers"

# Check individual container statuses
echo -e "\n=== Container Status Details ==="
kubectl get pod multi-container-issues -o jsonpath='{.status.initContainerStatuses[0].state}' | jq '.'
kubectl get pod multi-container-issues -o jsonpath='{.status.containerStatuses[*].state}' | jq '.'

# Get logs from each container
echo -e "\n=== Container Logs ==="
echo "--- Init Container Logs ---"
kubectl logs multi-container-issues -c init-setup

echo -e "\n--- Web App Container Logs ---"
kubectl logs multi-container-issues -c web-app

echo -e "\n--- Log Processor Container Logs ---"
kubectl logs multi-container-issues -c log-processor

# Check for OOMKilled events
echo -e "\n=== OOM Events ==="
kubectl get events | grep -i "oom\|killed"
```

### Task 2.3: Fix Multi-Container Issues

Create a fixed version of the multi-container pod:

```yaml
cat << EOF > multi-container-fixed.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-fixed
  labels:
    app: multi-debug-fixed
spec:
  containers:
  # Main application container
  - name: web-app
    image: nginx:1.21
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
  
  # Fixed sidecar container
  - name: log-processor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting log processor..."
      sleep 10
      
      # Fixed: No memory allocation
      echo "Processing logs without memory issues..."
      
      while true; do
        echo "Processing logs at $(date)"
        # Simulate log processing
        ls /data > /tmp/log-summary
        sleep 30
      done
    volumeMounts:
    - name: shared-data
      mountPath: /data
    resources:
      requests:
        memory: "32Mi"
        cpu: "25m"
      limits:
        memory: "64Mi"
        cpu: "50m"
  
  # Fixed init container
  initContainers:
  - name: init-setup
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Initializing..."
      sleep 5
      
      # Fixed: Create setup file instead of downloading
      echo "Setup data" > /setup/config.txt
      echo "Initial HTML content" > /setup/index.html
      
      echo "Setup complete"
    volumeMounts:
    - name: shared-data
      mountPath: /setup
  
  volumes:
  - name: shared-data
    emptyDir: {}
EOF

kubectl apply -f multi-container-fixed.yaml

# Monitor the fixed version
kubectl get pod multi-container-fixed -w &
WATCH_PID=$!

sleep 45
kill $WATCH_PID

# Verify fixed pod is working
kubectl get pod multi-container-fixed
kubectl describe pod multi-container-fixed
```

---

## Exercise 3: Resource Constraint Debugging (7 minutes)

### Task 3.1: Create Pods with Resource Issues

```yaml
cat << EOF > resource-debug.yaml
# Pod that exceeds CPU limits
apiVersion: v1
kind: Pod
metadata:
  name: cpu-throttled
  labels:
    resource-test: cpu
spec:
  containers:
  - name: cpu-intensive
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting CPU intensive task..."
      # Generate high CPU load
      while true; do
        echo "CPU load..." > /dev/null
      done
    resources:
      requests:
        cpu: "100m"
        memory: "64Mi"
      limits:
        cpu: "200m"    # Will be throttled
        memory: "128Mi"
---
# Pod that uses too much memory
apiVersion: v1
kind: Pod
metadata:
  name: memory-pressure
  labels:
    resource-test: memory
spec:
  containers:
  - name: memory-hog
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting memory allocation..."
      sleep 10
      
      # Gradually allocate memory
      for i in {1..10}; do
        echo "Allocating memory chunk $i"
        head -c 20M </dev/zero >memory-chunk-$i &
        sleep 5
      done
      
      wait
    resources:
      requests:
        cpu: "50m"
        memory: "64Mi"
      limits:
        cpu: "100m"
        memory: "128Mi"  # Will exceed this
---
# Pod with insufficient resources to schedule
apiVersion: v1
kind: Pod
metadata:
  name: unschedulable
  labels:
    resource-test: unschedulable
spec:
  containers:
  - name: resource-hungry
    image: nginx:1.21
    resources:
      requests:
        cpu: "100"      # 100 cores - impossible on most clusters
        memory: "1Ti"   # 1TB memory - impossible on most clusters
EOF

kubectl apply -f resource-debug.yaml
```

### Task 3.2: Analyze Resource Issues

```bash
# Check pod status focusing on resource issues
echo "=== Resource Pod Status ==="
kubectl get pods -l resource-test

# Check node resources
echo -e "\n=== Node Resource Status ==="
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check pod resource usage
echo -e "\n=== Pod Resource Usage ==="
kubectl top pods

# Check for scheduling issues
echo -e "\n=== Scheduling Events ==="
kubectl get events | grep -i "schedule\|insufficient\|resource"

# Detailed analysis of unschedulable pod
echo -e "\n=== Unschedulable Pod Analysis ==="
kubectl describe pod unschedulable | grep -A 10 "Events"

# Check for OOMKilled or throttling
echo -e "\n=== Resource Constraint Events ==="
kubectl get events | grep -i "oom\|killed\|throttl"
```

### Task 3.3: Monitor Resource Metrics

```bash
# Create a monitoring script
cat << 'EOF' > monitor-resources.sh
#!/bin/bash

echo "=== Resource Monitoring ==="
while true; do
    echo "--- $(date) ---"
    
    # Pod resource usage
    echo "Pod CPU/Memory usage:"
    kubectl top pods -l resource-test --no-headers | awk '{print $1, $2, $3}'
    
    # Check for new events
    echo "Recent resource events:"
    kubectl get events --sort-by=.metadata.creationTimestamp | tail -3
    
    # Pod status
    echo "Pod status:"
    kubectl get pods -l resource-test --no-headers | awk '{print $1, $3, $4}'
    
    echo "---"
    sleep 10
done
EOF

chmod +x monitor-resources.sh

# Run monitoring for 2 minutes
timeout 120 ./monitor-resources.sh

# Final resource analysis
echo -e "\n=== Final Resource Analysis ==="
kubectl describe pods -l resource-test | grep -A 5 "Limits\|Requests\|State\|Last State"
```

---

## Exercise 4: Configuration and Secret Debugging (6 minutes)

### Task 4.1: Create Pods with Configuration Issues

```yaml
cat << EOF > config-debug.yaml
# Pod with missing ConfigMap
apiVersion: v1
kind: Pod
metadata:
  name: missing-configmap
  labels:
    config-test: configmap
spec:
  containers:
  - name: app
    image: nginx:1.21
    envFrom:
    - configMapRef:
        name: nonexistent-config
---
# Pod with missing Secret
apiVersion: v1
kind: Pod
metadata:
  name: missing-secret
  labels:
    config-test: secret
spec:
  containers:
  - name: app
    image: nginx:1.21
    env:
    - name: PASSWORD
      valueFrom:
        secretKeyRef:
          name: nonexistent-secret
          key: password
---
# Pod with missing volume
apiVersion: v1
kind: Pod
metadata:
  name: missing-volume
  labels:
    config-test: volume
spec:
  containers:
  - name: app
    image: nginx:1.21
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: nonexistent-configmap
EOF

kubectl apply -f config-debug.yaml
```

### Task 4.2: Debug Configuration Issues

```bash
# Check configuration pod status
echo "=== Configuration Pod Status ==="
kubectl get pods -l config-test

# Check for mount failures
echo -e "\n=== Mount Failures ==="
kubectl get events | grep -i "mount\|volume"

# Describe each configuration issue
echo -e "\n=== Configuration Issue Details ==="
for pod in missing-configmap missing-secret missing-volume; do
    echo "--- $pod ---"
    kubectl describe pod $pod | grep -A 10 "Events\|Volumes\|Mounts"
done

# Check what ConfigMaps and Secrets exist
echo -e "\n=== Available ConfigMaps and Secrets ==="
kubectl get configmaps
kubectl get secrets
```

### Task 4.3: Fix Configuration Issues

```bash
# Create required ConfigMap and Secret
kubectl create configmap app-config --from-literal=database_url=postgres://localhost:5432/mydb
kubectl create secret generic app-secret --from-literal=password=mysecretpassword

# Create fixed pods
cat << EOF > config-fixed.yaml
# Fixed pod with existing ConfigMap
apiVersion: v1
kind: Pod
metadata:
  name: fixed-configmap
  labels:
    config-test: fixed
spec:
  containers:
  - name: app
    image: nginx:1.21
    envFrom:
    - configMapRef:
        name: app-config
---
# Fixed pod with existing Secret
apiVersion: v1
kind: Pod
metadata:
  name: fixed-secret
  labels:
    config-test: fixed
spec:
  containers:
  - name: app
    image: nginx:1.21
    env:
    - name: PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: password
---
# Fixed pod with existing volume
apiVersion: v1
kind: Pod
metadata:
  name: fixed-volume
  labels:
    config-test: fixed
spec:
  containers:
  - name: app
    image: nginx:1.21
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
EOF

kubectl apply -f config-fixed.yaml

# Verify fixes
kubectl get pods -l config-test=fixed
kubectl describe pods -l config-test=fixed
```

---

## Exercise 5: Networking and Service Debugging (6 minutes)

### Task 5.1: Create Networking Issues

```yaml
cat << EOF > network-debug.yaml
# Pod with network connectivity issues
apiVersion: v1
kind: Pod
metadata:
  name: network-test
  labels:
    network-test: connectivity
spec:
  containers:
  - name: network-tool
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Starting network diagnostics..."
      
      # Test external connectivity
      echo "Testing external DNS..."
      nslookup google.com || echo "External DNS failed"
      
      # Test cluster DNS
      echo "Testing cluster DNS..."
      nslookup kubernetes.default.svc.cluster.local || echo "Cluster DNS failed"
      
      # Test service connectivity
      echo "Testing service connectivity..."
      wget -O- http://nonexistent-service:80 || echo "Service connection failed"
      
      # Keep container running for debugging
      while true; do
        echo "Network test pod running..."
        sleep 30
      done
---
# Service with wrong selector
apiVersion: v1
kind: Service
metadata:
  name: broken-service
spec:
  selector:
    app: nonexistent-app  # Wrong selector
  ports:
  - port: 80
    targetPort: 80
---
# Pod that should be selected by service but isn't
apiVersion: v1
kind: Pod
metadata:
  name: orphaned-pod
  labels:
    app: web-app  # Different from service selector
spec:
  containers:
  - name: web
    image: nginx:1.21
    ports:
    - containerPort: 80
EOF

kubectl apply -f network-debug.yaml
```

### Task 5.2: Debug Networking Issues

```bash
# Check networking pod status
echo "=== Network Pod Status ==="
kubectl get pods -l network-test=connectivity

# Check service endpoints
echo -e "\n=== Service Endpoints ==="
kubectl get endpoints
kubectl describe service broken-service

# Test network connectivity from pod
echo -e "\n=== Network Connectivity Tests ==="
kubectl logs network-test

# Check DNS resolution
echo -e "\n=== DNS Resolution Test ==="
kubectl exec network-test -- nslookup kubernetes.default.svc.cluster.local

# Check cluster networking
echo -e "\n=== Cluster Network Status ==="
kubectl get pods -o wide
kubectl get services

# Test service discovery
echo -e "\n=== Service Discovery Debug ==="
kubectl get endpoints broken-service
kubectl describe endpoints broken-service

# Check if pods match service selectors
echo -e "\n=== Service Selector Analysis ==="
kubectl get service broken-service -o yaml | grep -A 3 selector
kubectl get pods --show-labels | grep web-app
```

---

## Advanced Debugging Techniques

### Debug Information Collection Script

Create a comprehensive debugging script:

```bash
cat << 'EOF' > debug-pod.sh
#!/bin/bash

POD_NAME=$1
NAMESPACE=${2:-debug-lab}

if [ -z "$POD_NAME" ]; then
    echo "Usage: $0 <pod-name> [namespace]"
    exit 1
fi

echo "=== Debugging Pod: $POD_NAME in namespace: $NAMESPACE ==="

# Basic information
echo "--- Basic Pod Information ---"
kubectl get pod $POD_NAME -n $NAMESPACE -o wide

# Pod status details
echo -e "\n--- Pod Status Details ---"
kubectl describe pod $POD_NAME -n $NAMESPACE

# Pod YAML for analysis
echo -e "\n--- Pod YAML Configuration ---"
kubectl get pod $POD_NAME -n $NAMESPACE -o yaml > ${POD_NAME}-debug.yaml
echo "Pod YAML saved to ${POD_NAME}-debug.yaml"

# Container logs
echo -e "\n--- Container Logs ---"
containers=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[*].name}')
for container in $containers; do
    echo "--- Logs for container: $container ---"
    kubectl logs $POD_NAME -n $NAMESPACE -c $container --tail=50
done

# Previous container logs if restarted
echo -e "\n--- Previous Container Logs (if any) ---"
for container in $containers; do
    echo "--- Previous logs for container: $container ---"
    kubectl logs $POD_NAME -n $NAMESPACE -c $container --previous --tail=50 2>/dev/null || echo "No previous logs"
done

# Events related to the pod
echo -e "\n--- Pod Related Events ---"
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$POD_NAME

# Resource usage
echo -e "\n--- Resource Usage ---"
kubectl top pod $POD_NAME -n $NAMESPACE 2>/dev/null || echo "Resource usage not available"

# Node information
echo -e "\n--- Node Information ---"
node=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.nodeName}')
if [ ! -z "$node" ]; then
    echo "Pod is scheduled on node: $node"
    kubectl describe node $node | grep -A 10 "Allocated resources"
fi

echo -e "\n=== Debug Summary Complete ==="
EOF

chmod +x debug-pod.sh

# Test the debugging script
./debug-pod.sh image-pull-fail
./debug-pod.sh multi-container-issues
```

### Interactive Debugging Session

```bash
# Create a debug pod for interactive troubleshooting
kubectl run debug-toolkit --image=busybox:1.35 --rm -it --restart=Never -- sh

# Inside the debug pod, test connectivity:
# ping 8.8.8.8
# nslookup kubernetes.default.svc.cluster.local
# wget -O- http://kubernetes.default.svc.cluster.local
# exit

# Debug using existing pod
kubectl exec -it network-test -- sh

# Test commands inside pod:
# ps aux
# netstat -ln
# cat /etc/resolv.conf
# exit
```

---

## Debugging Best Practices

### Systematic Debugging Approach

1. **Check Pod Status**: `kubectl get pods`
2. **Get Detailed Information**: `kubectl describe pod <name>`
3. **Check Events**: `kubectl get events`
4. **Examine Logs**: `kubectl logs <pod> -c <container>`
5. **Check Configuration**: `kubectl get pod <name> -o yaml`
6. **Test Interactively**: `kubectl exec -it <pod> -- sh`

### Common Debug Commands

```bash
# Pod status and details
kubectl get pods -o wide
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o yaml

# Logs and events
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous
kubectl get events --sort-by=.metadata.creationTimestamp

# Interactive debugging
kubectl exec -it <pod-name> -- /bin/bash
kubectl port-forward <pod-name> 8080:80

# Resource monitoring
kubectl top pods
kubectl top nodes

# Network debugging
kubectl run debug --image=busybox:1.35 --rm -it -- sh
kubectl exec <pod-name> -- nslookup <service-name>
```

---

## Validation and Testing

### Test Your Knowledge

1. **Debug a failing pod** using systematic approach
2. **Identify resource constraint issues** and propose solutions
3. **Troubleshoot multi-container pod problems**
4. **Fix configuration and networking issues**

### Verification Commands

```bash
# Check for any remaining failed pods
kubectl get pods | grep -v Running

# Verify debugging skills with a complex scenario
kubectl run test-debug --image=nginx:fake-tag --dry-run=client -o yaml | kubectl apply -f -
./debug-pod.sh test-debug

# Clean up test pod
kubectl delete pod test-debug
```

---

## Cleanup

```bash
# Delete all debug resources
kubectl delete pods --all -n debug-lab
kubectl delete services --all -n debug-lab
kubectl delete configmaps --all -n debug-lab
kubectl delete secrets --all -n debug-lab
kubectl delete namespace debug-lab

# Clean up files
rm -f failing-pods.yaml multi-container-debug.yaml multi-container-fixed.yaml
rm -f resource-debug.yaml config-debug.yaml config-fixed.yaml network-debug.yaml
rm -f monitor-resources.sh debug-pod.sh *-debug.yaml

# Reset context
kubectl config set-context --current --namespace=default
```

---

## Summary

In this lab, you learned how to:

- ✅ Use systematic debugging approaches for pod failures
- ✅ Diagnose different types of pod issues (image, resource, configuration)
- ✅ Debug multi-container pod problems
- ✅ Analyze resource constraints and scheduling issues
- ✅ Troubleshoot configuration and networking problems
- ✅ Use interactive debugging techniques effectively
- ✅ Create comprehensive debugging scripts and workflows

**Key Debugging Skills**:
- Always start with `kubectl get pods` and `kubectl describe pod`
- Check events for failure reasons
- Examine logs for runtime issues
- Use `kubectl exec` for interactive debugging
- Monitor resource usage with `kubectl top`
- Understand the relationship between pods, services, and networking

**Next Steps**: Proceed to [Lab 8: Network Troubleshooting](lab08-network-debug.md) to learn specialized network debugging techniques.