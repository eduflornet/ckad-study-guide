# Lab 2: NodePort Service Configuration

**Learning Objective**: Configure NodePort services to expose applications externally through node IPs.

**Time**: 25 minutes

## 📋 Prerequisites

- Kubernetes cluster with accessible nodes
- kubectl configured
- Understanding of ClusterIP services

## 🎯 Lab Overview

NodePort services extend ClusterIP functionality by exposing services on a static port on each node, making applications accessible from outside the cluster.

## 📝 Tasks

### Task 1: Create a Web Application

Deploy a web application that shows node information:

```yaml
# node-info-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-info-app
  labels:
    app: node-info
spec:
  replicas: 2
  selector:
    matchLabels:
      app: node-info
  template:
    metadata:
      labels:
        app: node-info
    spec:
      containers:
      - name: node-info
        image: k8s.gcr.io/serve_hostname:1.4
        ports:
        - containerPort: 9376
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
            cpu: "50m"
```

### Task 2: Create NodePort Service

Create a NodePort service:

```yaml
# nodeport-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: node-info-nodeport
  labels:
    app: node-info
spec:
  type: NodePort
  selector:
    app: node-info
  ports:
  - name: http
    port: 80
    targetPort: 9376
    nodePort: 30080  # Optional: specify port (30000-32767)
    protocol: TCP
```

### Task 3: Test External Access

1. **Get node information**:
   ```bash
   kubectl get nodes -o wide
   kubectl get service node-info-nodeport
   ```

2. **Test access from outside cluster**:
   ```bash
   # Replace NODE_IP with actual node IP
   curl http://NODE_IP:30080
   
   # If using minikube
   minikube service node-info-nodeport
   ```

3. **Test multiple requests to see load balancing**:
   ```bash
   for i in {1..10}; do curl http://NODE_IP:30080; done
   ```

### Task 4: Dynamic NodePort Assignment

Let Kubernetes assign a random NodePort:

```yaml
# auto-nodeport-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: auto-nodeport
spec:
  type: NodePort
  selector:
    app: node-info
  ports:
  - name: http
    port: 80
    targetPort: 9376
    # nodePort not specified - will be auto-assigned
```

Check the assigned port:
```bash
kubectl get service auto-nodeport
```

### Task 5: Multiple NodePort Services

Create services for different environments:

```yaml
# staging-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: staging-service
  labels:
    env: staging
spec:
  type: NodePort
  selector:
    app: node-info
  ports:
  - name: http
    port: 80
    targetPort: 9376
    nodePort: 30081
---
apiVersion: v1
kind: Service
metadata:
  name: prod-service
  labels:
    env: production
spec:
  type: NodePort
  selector:
    app: node-info
  ports:
  - name: http
    port: 80
    targetPort: 9376
    nodePort: 30082
```

## ✅ Verification Steps

1. **Service has NodePort assigned**:
   ```bash
   kubectl get services -o wide
   kubectl describe service node-info-nodeport
   ```

2. **External connectivity works**:
   ```bash
   curl http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'):30080
   ```

3. **Load balancing between pods**:
   ```bash
   # Multiple requests should hit different pods
   for i in {1..5}; do
     echo "Request $i:"
     curl -s http://NODE_IP:30080
     echo
   done
   ```

4. **Service accessible from all nodes**:
   ```bash
   # Test each node IP
   kubectl get nodes -o wide
   curl http://NODE1_IP:30080
   curl http://NODE2_IP:30080
   ```

## 🔧 Advanced Configuration

### External Traffic Policy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: local-traffic-service
spec:
  type: NodePort
  externalTrafficPolicy: Local  # Preserves source IP
  selector:
    app: node-info
  ports:
  - port: 80
    targetPort: 9376
    nodePort: 30083
```

### Health Check Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: health-check-service
spec:
  type: NodePort
  selector:
    app: node-info
  ports:
  - name: http
    port: 80
    targetPort: 9376
  - name: health
    port: 8080
    targetPort: 8080
    nodePort: 30084
```

## 🧹 Cleanup

```bash
kubectl delete deployment node-info-app
kubectl delete service node-info-nodeport auto-nodeport staging-service prod-service
kubectl delete service local-traffic-service health-check-service
```

## 📚 Key Learnings

- NodePort services expose applications on all node IPs
- NodePort range is 30000-32767 by default
- External traffic policy affects source IP preservation
- NodePort includes ClusterIP functionality
- Load balancing occurs across all healthy pods

## 🔍 Troubleshooting Tips

- Check if NodePort is in valid range (30000-32767)
- Verify firewall rules allow traffic on NodePort
- Test internal ClusterIP first, then external NodePort
- Check if pods are ready and endpoints populated
- Verify node IPs are accessible from external network

## 📖 Additional Resources

- [NodePort Service Type](https://kubernetes.io/docs/concepts/services-networking/service/#nodeport)
- [External Traffic Policy](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip)