# Lab 1: ClusterIP Service Basics

**Learning Objective**: Understand and implement ClusterIP services for internal pod communication.

**Time**: 20 minutes

## 📋 Prerequisites

- Kubernetes cluster running
- kubectl configured
- Basic understanding of pods and deployments

## 🎯 Lab Overview

In this lab, you'll create a ClusterIP service to enable internal communication between pods. ClusterIP is the default service type and provides a stable internal IP for accessing pods.

## 📝 Tasks

### Task 1: Create a Deployment

Create a simple web application deployment:

```yaml
# web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
```

Apply the deployment:
```bash
kubectl apply -f web-deployment.yaml
```

### Task 2: Create a ClusterIP Service

Create a ClusterIP service to expose the deployment:

```yaml
# web-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  labels:
    app: web
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
```

Apply the service:
```bash
kubectl apply -f web-service.yaml
```

### Task 3: Test Internal Connectivity

1. **Check service details**:
   ```bash
   kubectl get services
   kubectl describe service web-service
   kubectl get endpoints web-service
   ```

2. **Test connectivity from within cluster**:
   ```bash
   # Create a test pod
   kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh
   
   # Inside the pod, test connectivity
   wget -qO- http://web-service
   nslookup web-service
   ```

### Task 4: Service Discovery

1. **Check environment variables**:
   ```bash
   kubectl run env-test --image=busybox --rm -it --restart=Never -- env | grep WEB_SERVICE
   ```

2. **Test DNS resolution**:
   ```bash
   kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-service.default.svc.cluster.local
   ```

### Task 5: Multiple Port Services

Create a service with multiple ports:

```yaml
# multi-port-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: https
    port: 443
    targetPort: 80
```

## ✅ Verification Steps

1. **Service exists and has ClusterIP**:
   ```bash
   kubectl get service web-service -o wide
   ```

2. **Endpoints are populated**:
   ```bash
   kubectl get endpoints web-service
   ```

3. **Service responds to requests**:
   ```bash
   kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- curl -s http://web-service
   ```

4. **DNS resolution works**:
   ```bash
   kubectl run nslookup-test --image=busybox --rm -it --restart=Never -- nslookup web-service
   ```

## 🧹 Cleanup

```bash
kubectl delete deployment web-app
kubectl delete service web-service multi-port-service
```

## 📚 Key Learnings

- ClusterIP services provide internal load balancing
- Services use label selectors to target pods
- DNS resolution works with service names
- Environment variables are created for service discovery
- Endpoints track healthy pod IPs automatically

## 🔍 Troubleshooting Tips

- Check if service selector matches pod labels
- Verify endpoints are populated
- Test DNS resolution from within cluster
- Check if target ports match container ports

## 📖 Additional Resources

- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Service Types](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types)