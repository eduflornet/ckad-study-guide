# Lab 8: Network Troubleshooting

**Objective**: Master network debugging techniques in Kubernetes environments
**Time**: 40 minutes
**Difficulty**: Advanced

---

## Learning Objectives

By the end of this lab, you will be able to:
- Diagnose pod-to-pod connectivity issues
- Troubleshoot service discovery problems
- Debug DNS resolution failures
- Analyze ingress and load balancer issues
- Use network debugging tools effectively
- Understand network policies and security contexts

---

## Prerequisites

- Kubernetes cluster access
- kubectl CLI configured
- Understanding of Kubernetes networking concepts
- Basic knowledge of DNS and networking

---

## Lab Environment Setup

Create a dedicated namespace for network debugging:

```bash
kubectl create namespace network-debug
kubectl config set-context --current --namespace=network-debug
```

---

## Exercise 1: Pod-to-Pod Connectivity (10 minutes)

### Task 1.1: Create Test Applications

Deploy applications to test network connectivity:

```yaml
cat << EOF > network-test-apps.yaml
# Frontend application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: web
    spec:
      containers:
      - name: frontend
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Frontend starting..."
          while true; do
            echo "Frontend: $(date) - Attempting to connect to backend..."
            
            # Test backend connectivity
            if wget -q --timeout=5 -O- http://backend-service:8080/health 2>/dev/null; then
              echo "✓ Backend connection successful"
            else
              echo "✗ Backend connection failed"
            fi
            
            # Test database connectivity
            if nc -z database-service 5432 2>/dev/null; then
              echo "✓ Database connection successful"
            else
              echo "✗ Database connection failed"
            fi
            
            sleep 30
          done
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
---
# Backend application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        tier: api
    spec:
      containers:
      - name: backend
        image: nginx:1.21
        ports:
        - containerPort: 80
        # Add custom nginx config for health endpoint
        lifecycle:
          postStart:
            exec:
              command:
              - sh
              - -c
              - |
                cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF'
                server {
                    listen 80;
                    
                    location /health {
                        access_log off;
                        return 200 "Backend healthy\n";
                        add_header Content-Type text/plain;
                    }
                    
                    location / {
                        root   /usr/share/nginx/html;
                        index  index.html index.htm;
                    }
                }
                NGINX_EOF
                nginx -s reload
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 80
---
# Database simulation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  labels:
    app: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
        tier: data
    spec:
      containers:
      - name: database
        image: postgres:13-alpine
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "testuser"
        - name: POSTGRES_PASSWORD
          value: "testpass"
        ports:
        - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: database-service
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
EOF

kubectl apply -f network-test-apps.yaml
```

### Task 1.2: Test Basic Connectivity

```bash
# Wait for deployments to be ready
kubectl wait --for=condition=available deployment/frontend deployment/backend deployment/database --timeout=120s

# Check pod and service status
echo "=== Pod Status ==="
kubectl get pods -o wide

echo -e "\n=== Service Status ==="
kubectl get services

echo -e "\n=== Service Endpoints ==="
kubectl get endpoints

# Test connectivity from frontend
echo -e "\n=== Frontend Connectivity Test ==="
FRONTEND_POD=$(kubectl get pods -l app=frontend -o jsonpath='{.items[0].metadata.name}')
kubectl logs $FRONTEND_POD --tail=10
```

### Task 1.3: Deep Network Analysis

```bash
# Check cluster DNS
echo "=== DNS Configuration ==="
kubectl exec $FRONTEND_POD -- cat /etc/resolv.conf

# Test DNS resolution
echo -e "\n=== DNS Resolution Tests ==="
kubectl exec $FRONTEND_POD -- nslookup backend-service
kubectl exec $FRONTEND_POD -- nslookup database-service
kubectl exec $FRONTEND_POD -- nslookup kubernetes.default.svc.cluster.local

# Test direct IP connectivity
echo -e "\n=== Direct IP Connectivity ==="
BACKEND_IP=$(kubectl get service backend-service -o jsonpath='{.spec.clusterIP}')
DATABASE_IP=$(kubectl get service database-service -o jsonpath='{.spec.clusterIP}')

echo "Backend service IP: $BACKEND_IP"
echo "Database service IP: $DATABASE_IP"

kubectl exec $FRONTEND_POD -- wget -q --timeout=5 -O- http://$BACKEND_IP/health
kubectl exec $FRONTEND_POD -- nc -z $DATABASE_IP 5432 && echo "Database port accessible" || echo "Database port not accessible"
```

---

## Exercise 2: Service Discovery Issues (8 minutes)

### Task 2.1: Create Problematic Services

```yaml
cat << EOF > broken-services.yaml
# Service with wrong selector
apiVersion: v1
kind: Service
metadata:
  name: broken-backend-service
spec:
  selector:
    app: wrong-backend  # Incorrect selector
  ports:
  - port: 8080
    targetPort: 80
---
# Service with wrong port
apiVersion: v1
kind: Service
metadata:
  name: wrong-port-service
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 9999  # Wrong target port
---
# Pod with wrong labels
apiVersion: v1
kind: Pod
metadata:
  name: mislabeled-pod
  labels:
    app: wrong-label  # Won't be selected by services
spec:
  containers:
  - name: web
    image: nginx:1.21
    ports:
    - containerPort: 80
EOF

kubectl apply -f broken-services.yaml
```

### Task 2.2: Diagnose Service Issues

```bash
# Check service endpoints
echo "=== Service Endpoint Analysis ==="
kubectl get endpoints
kubectl describe endpoints broken-backend-service
kubectl describe endpoints wrong-port-service

# Check service selectors vs pod labels
echo -e "\n=== Selector vs Labels Analysis ==="
echo "Backend service selector:"
kubectl get service backend-service -o jsonpath='{.spec.selector}' | jq '.'

echo -e "\nBackend pod labels:"
kubectl get pods -l app=backend --show-labels

echo -e "\nBroken service selector:"
kubectl get service broken-backend-service -o jsonpath='{.spec.selector}' | jq '.'

echo -e "\nMislabeled pod labels:"
kubectl get pod mislabeled-pod --show-labels

# Test broken service connectivity
echo -e "\n=== Broken Service Connectivity Tests ==="
kubectl exec $FRONTEND_POD -- nslookup broken-backend-service
kubectl exec $FRONTEND_POD -- wget -q --timeout=5 -O- http://broken-backend-service:8080/health || echo "Connection failed as expected"
```

### Task 2.3: Fix Service Issues

```bash
# Fix the broken service selector
kubectl patch service broken-backend-service -p '{"spec":{"selector":{"app":"backend"}}}'

# Fix the wrong port service
kubectl patch service wrong-port-service -p '{"spec":{"ports":[{"port":8080,"targetPort":80}]}}'

# Fix the mislabeled pod
kubectl label pod mislabeled-pod app=backend --overwrite

# Verify fixes
echo "=== Post-Fix Verification ==="
kubectl get endpoints
kubectl exec $FRONTEND_POD -- wget -q --timeout=5 -O- http://broken-backend-service:8080/health
```

---

## Exercise 3: DNS Resolution Problems (8 minutes)

### Task 3.1: Create DNS Issues

```yaml
cat << EOF > dns-issues.yaml
# Pod with custom DNS config that might cause issues
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  dnsPolicy: None  # Disable default DNS
  dnsConfig:
    nameservers:
    - "8.8.8.8"  # Only external DNS, no cluster DNS
    searches:
    - "example.com"
  containers:
  - name: dns-test
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Testing DNS resolution..."
      while true; do
        echo "--- DNS Test $(date) ---"
        
        # Test external DNS
        nslookup google.com || echo "External DNS failed"
        
        # Test cluster DNS (should fail)
        nslookup backend-service || echo "Cluster DNS failed"
        nslookup kubernetes.default.svc.cluster.local || echo "Cluster service DNS failed"
        
        sleep 60
      done
---
# Pod in different namespace to test cross-namespace DNS
apiVersion: v1
kind: Namespace
metadata:
  name: dns-test-ns
---
apiVersion: v1
kind: Pod
metadata:
  name: cross-namespace-pod
  namespace: dns-test-ns
spec:
  containers:
  - name: dns-test
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Testing cross-namespace DNS..."
      while true; do
        echo "--- Cross-Namespace DNS Test $(date) ---"
        
        # Test same namespace (should fail - no services in dns-test-ns)
        nslookup backend-service || echo "Same namespace DNS failed (expected)"
        
        # Test cross-namespace DNS
        nslookup backend-service.network-debug.svc.cluster.local || echo "Cross-namespace DNS failed"
        
        # Test short form cross-namespace
        nslookup backend-service.network-debug || echo "Short cross-namespace DNS failed"
        
        sleep 60
      done
EOF

kubectl apply -f dns-issues.yaml
```

### Task 3.2: Analyze DNS Problems

```bash
# Check DNS configuration in problematic pod
echo "=== Custom DNS Pod Analysis ==="
kubectl describe pod custom-dns-pod | grep -A 10 "DNS"
kubectl exec custom-dns-pod -- cat /etc/resolv.conf
kubectl logs custom-dns-pod --tail=10

# Check cross-namespace DNS
echo -e "\n=== Cross-Namespace DNS Analysis ==="
kubectl exec cross-namespace-pod -n dns-test-ns -- cat /etc/resolv.conf
kubectl logs cross-namespace-pod -n dns-test-ns --tail=10

# Compare with working DNS configuration
echo -e "\n=== Working DNS Configuration ==="
kubectl exec $FRONTEND_POD -- cat /etc/resolv.conf

# Test DNS from working pod
echo -e "\n=== DNS Resolution from Working Pod ==="
kubectl exec $FRONTEND_POD -- nslookup backend-service
kubectl exec $FRONTEND_POD -- nslookup backend-service.network-debug.svc.cluster.local
```

### Task 3.3: Debug DNS Service

```bash
# Check CoreDNS status
echo "=== CoreDNS Status ==="
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS configuration
echo -e "\n=== CoreDNS Configuration ==="
kubectl get configmap coredns -n kube-system -o yaml

# Test CoreDNS directly
echo -e "\n=== Direct CoreDNS Test ==="
COREDNS_IP=$(kubectl get service kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}')
echo "CoreDNS IP: $COREDNS_IP"

kubectl exec $FRONTEND_POD -- nslookup backend-service $COREDNS_IP
```

---

## Exercise 4: Ingress and Load Balancer Issues (7 minutes)

### Task 4.1: Create Ingress Configuration

```yaml
cat << EOF > ingress-debug.yaml
# Ingress with potential issues
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: debug-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: debug-app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.debug-app.local
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8080
---
# NodePort service for testing
apiVersion: v1
kind: Service
metadata:
  name: frontend-nodeport
spec:
  type: NodePort
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
---
# LoadBalancer service (may not work in all environments)
apiVersion: v1
kind: Service
metadata:
  name: backend-loadbalancer
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f ingress-debug.yaml
```

### Task 4.2: Debug Ingress Issues

```bash
# Check ingress status
echo "=== Ingress Status ==="
kubectl get ingress
kubectl describe ingress debug-ingress

# Check ingress controller
echo -e "\n=== Ingress Controller Status ==="
kubectl get pods -n ingress-nginx 2>/dev/null || echo "Ingress controller not found in ingress-nginx namespace"
kubectl get pods -A | grep ingress || echo "No ingress controller found"

# Check service types and external access
echo -e "\n=== Service External Access ==="
kubectl get services
kubectl describe service frontend-nodeport
kubectl describe service backend-loadbalancer

# Test NodePort access (if available)
echo -e "\n=== NodePort Access Test ==="
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "Node IP: $NODE_IP"
echo "NodePort: 30080"
echo "Test with: curl http://$NODE_IP:30080"

# Check for load balancer external IP
EXTERNAL_IP=$(kubectl get service backend-loadbalancer -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ ! -z "$EXTERNAL_IP" ]; then
    echo "LoadBalancer External IP: $EXTERNAL_IP"
    echo "Test with: curl http://$EXTERNAL_IP"
else
    echo "LoadBalancer external IP not assigned (may be pending or unsupported)"
fi
```

---

## Exercise 5: Network Policies and Security (7 minutes)

### Task 5.1: Create Network Policies

```yaml
cat << EOF > network-policies.yaml
# Deny all ingress traffic by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow frontend to backend communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 80
---
# Allow backend to database communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-database
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5432
---
# Restrictive network policy that blocks legitimate traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: overly-restrictive
spec:
  podSelector:
    matchLabels:
      tier: api
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # Block all ingress
  egress: []   # Block all egress
EOF

kubectl apply -f network-policies.yaml
```

### Task 5.2: Test Network Policy Impact

```bash
# Check network policies
echo "=== Network Policies ==="
kubectl get networkpolicies
kubectl describe networkpolicy default-deny-ingress

# Test connectivity before and after network policies
echo -e "\n=== Testing Connectivity with Network Policies ==="

# This should fail due to overly-restrictive policy
echo "Testing frontend to backend (should fail):"
kubectl exec $FRONTEND_POD -- wget -q --timeout=5 -O- http://backend-service:8080/health || echo "Connection blocked by network policy"

# Check network policy impact
echo -e "\n=== Network Policy Impact Analysis ==="
kubectl describe networkpolicy overly-restrictive

# Remove the overly restrictive policy
kubectl delete networkpolicy overly-restrictive

# Test again
echo -e "\n=== Testing after removing restrictive policy ==="
sleep 5
kubectl exec $FRONTEND_POD -- wget -q --timeout=5 -O- http://backend-service:8080/health || echo "Still failing - check other policies"
```

---

## Advanced Network Debugging Tools

### Create Network Debugging Toolkit

```bash
# Create a comprehensive network debugging pod
cat << EOF > network-debug-toolkit.yaml
apiVersion: v1
kind: Pod
metadata:
  name: network-debug-toolkit
  labels:
    app: debug-toolkit
spec:
  containers:
  - name: network-tools
    image: nicolaka/netshoot:latest
    command:
    - sh
    - -c
    - |
      echo "Network debugging toolkit ready"
      echo "Available tools: dig, nslookup, ping, wget, curl, netstat, ss, tcpdump, nmap"
      echo "Usage examples:"
      echo "  dig backend-service.network-debug.svc.cluster.local"
      echo "  nmap -p 80,8080 backend-service"
      echo "  tcpdump -i eth0 host backend-service"
      
      # Keep container running
      while true; do
        echo "Network toolkit running... $(date)"
        sleep 300
      done
    securityContext:
      capabilities:
        add: ["NET_ADMIN", "NET_RAW"]
  hostNetwork: false
  dnsPolicy: ClusterFirst
EOF

kubectl apply -f network-debug-toolkit.yaml

# Wait for toolkit pod to be ready
kubectl wait --for=condition=ready pod/network-debug-toolkit --timeout=60s

# Advanced network diagnostics
echo "=== Advanced Network Diagnostics ==="

# DNS debugging
echo "--- DNS Debugging ---"
kubectl exec network-debug-toolkit -- dig backend-service.network-debug.svc.cluster.local

# Port scanning
echo -e "\n--- Port Scanning ---"
kubectl exec network-debug-toolkit -- nmap -p 80,8080 backend-service

# Network interface information
echo -e "\n--- Network Interface Info ---"
kubectl exec network-debug-toolkit -- ip addr show
kubectl exec network-debug-toolkit -- ip route show

# Connection testing
echo -e "\n--- Connection Testing ---"
kubectl exec network-debug-toolkit -- curl -v http://backend-service:8080/health
```

### Network Performance Testing

```bash
# Create a performance test script
cat << 'EOF' > network-perf-test.sh
#!/bin/bash

echo "=== Network Performance Testing ==="

# Test latency between pods
echo "--- Latency Testing ---"
BACKEND_POD=$(kubectl get pods -l app=backend -o jsonpath='{.items[0].metadata.name}')
BACKEND_IP=$(kubectl get pod $BACKEND_POD -o jsonpath='{.status.podIP}')

echo "Testing latency to backend pod ($BACKEND_IP):"
kubectl exec network-debug-toolkit -- ping -c 5 $BACKEND_IP

# Test service latency
echo -e "\n--- Service Latency Testing ---"
kubectl exec network-debug-toolkit -- ping -c 5 backend-service

# Test DNS resolution time
echo -e "\n--- DNS Resolution Performance ---"
kubectl exec network-debug-toolkit -- time nslookup backend-service

# Test HTTP performance
echo -e "\n--- HTTP Performance Testing ---"
kubectl exec network-debug-toolkit -- time curl -s http://backend-service:8080/health

echo "=== Performance Testing Complete ==="
EOF

chmod +x network-perf-test.sh
./network-perf-test.sh
```

---

## Network Troubleshooting Checklist

### Systematic Network Debugging Process

```bash
cat << 'EOF' > network-troubleshoot.sh
#!/bin/bash

echo "=== Kubernetes Network Troubleshooting Checklist ==="

# 1. Basic connectivity
echo "1. Basic Pod and Service Status:"
kubectl get pods,services -o wide

# 2. DNS resolution
echo -e "\n2. DNS Resolution Test:"
kubectl run dns-test --image=busybox:1.35 --rm -it --restart=Never -- nslookup kubernetes.default.svc.cluster.local

# 3. Service endpoints
echo -e "\n3. Service Endpoints:"
kubectl get endpoints

# 4. Network policies
echo -e "\n4. Network Policies:"
kubectl get networkpolicies

# 5. CoreDNS status
echo -e "\n5. CoreDNS Status:"
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 6. Node network status
echo -e "\n6. Node Network Status:"
kubectl get nodes -o wide

echo -e "\n=== Troubleshooting Checklist Complete ==="
EOF

chmod +x network-troubleshoot.sh
./network-troubleshoot.sh
```

---

## Validation and Testing

### Network Connectivity Test Suite

```bash
# Create comprehensive connectivity test
cat << 'EOF' > connectivity-test.sh
#!/bin/bash

echo "=== Comprehensive Network Connectivity Test ==="

FRONTEND_POD=$(kubectl get pods -l app=frontend -o jsonpath='{.items[0].metadata.name}')
BACKEND_POD=$(kubectl get pods -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Test 1: Pod-to-Pod direct IP
echo "Test 1: Pod-to-Pod Direct IP Communication"
BACKEND_IP=$(kubectl get pod $BACKEND_POD -o jsonpath='{.status.podIP}')
kubectl exec $FRONTEND_POD -- ping -c 3 $BACKEND_IP && echo "✓ PASS" || echo "✗ FAIL"

# Test 2: Service discovery
echo -e "\nTest 2: Service Discovery"
kubectl exec $FRONTEND_POD -- nslookup backend-service && echo "✓ PASS" || echo "✗ FAIL"

# Test 3: Service communication
echo -e "\nTest 3: Service Communication"
kubectl exec $FRONTEND_POD -- wget -q -O- http://backend-service:8080/health && echo "✓ PASS" || echo "✗ FAIL"

# Test 4: Cross-namespace communication
echo -e "\nTest 4: Cross-Namespace Communication"
kubectl exec $FRONTEND_POD -- nslookup kubernetes.default.svc.cluster.local && echo "✓ PASS" || echo "✗ FAIL"

# Test 5: External connectivity
echo -e "\nTest 5: External Connectivity"
kubectl exec $FRONTEND_POD -- ping -c 3 8.8.8.8 && echo "✓ PASS" || echo "✗ FAIL"

echo -e "\n=== Connectivity Test Complete ==="
EOF

chmod +x connectivity-test.sh
./connectivity-test.sh
```

---

## Cleanup

```bash
# Delete all network debug resources
kubectl delete -f network-test-apps.yaml
kubectl delete -f broken-services.yaml
kubectl delete -f dns-issues.yaml
kubectl delete -f ingress-debug.yaml
kubectl delete -f network-policies.yaml
kubectl delete -f network-debug-toolkit.yaml

# Delete test namespace
kubectl delete namespace dns-test-ns
kubectl delete namespace network-debug

# Clean up scripts and files
rm -f network-test-apps.yaml broken-services.yaml dns-issues.yaml
rm -f ingress-debug.yaml network-policies.yaml network-debug-toolkit.yaml
rm -f network-perf-test.sh network-troubleshoot.sh connectivity-test.sh

# Reset context
kubectl config set-context --current --namespace=default
```

---

## Summary

In this lab, you learned how to:

- ✅ Diagnose pod-to-pod connectivity issues systematically
- ✅ Troubleshoot service discovery and DNS problems
- ✅ Debug ingress and load balancer configurations
- ✅ Analyze network policy impacts on connectivity
- ✅ Use advanced network debugging tools effectively
- ✅ Create comprehensive network testing procedures
- ✅ Implement systematic network troubleshooting workflows

**Key Network Debugging Skills**:
- Always verify basic pod and service status first
- Test DNS resolution before investigating connectivity
- Check service endpoints and selectors
- Use network debugging tools for deep analysis
- Understand the impact of network policies
- Test both intra-cluster and external connectivity

**Common Network Issues and Solutions**:
- **Service discovery fails**: Check DNS configuration and CoreDNS status
- **Pod connectivity fails**: Verify network policies and routes
- **Intermittent failures**: Check resource constraints and network performance
- **Cross-namespace issues**: Verify FQDN usage and RBAC permissions

**Next Steps**: Proceed to [Lab 9: Performance Debugging](lab09-performance-debug.md) to learn about identifying and resolving performance bottlenecks.