# Lab 5: Basic Ingress Setup

**Learning Objective**: Configure basic Ingress resources for HTTP routing and understand Ingress controller requirements.

**Time**: 30 minutes

## 📋 Prerequisites

- Kubernetes cluster with Ingress controller (nginx, traefik, etc.)
- kubectl configured
- Basic understanding of services
- DNS or hosts file configuration capability

## 🎯 Lab Overview

Ingress provides HTTP and HTTPS routing to services based on hostnames and paths. This lab covers basic Ingress setup and configuration.

## 📝 Tasks

### Task 1: Verify Ingress Controller

First, ensure an Ingress controller is running:

```bash
# Check for NGINX Ingress Controller
kubectl get pods -n ingress-nginx

# If not installed, install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s
```

### Task 2: Create Backend Applications

Deploy multiple applications to route traffic to:

```yaml
# backend-apps.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-v1
  labels:
    app: webapp
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
      version: v1
  template:
    metadata:
      labels:
        app: webapp
        version: v1
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html
        configMap:
          name: app-v1-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-v2
  labels:
    app: webapp
    version: v2
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
      version: v2
  template:
    metadata:
      labels:
        app: webapp
        version: v2
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html
        configMap:
          name: app-v2-content
---
# ConfigMaps for different content
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-v1-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>App V1</title></head>
    <body style="background-color: lightblue; font-family: Arial;">
      <h1>Application Version 1</h1>
      <p>This is the V1 backend application.</p>
      <p>Served by: $(hostname)</p>
    </body>
    </html>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-v2-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>App V2</title></head>
    <body style="background-color: lightgreen; font-family: Arial;">
      <h1>Application Version 2</h1>
      <p>This is the V2 backend application.</p>
      <p>Served by: $(hostname)</p>
    </body>
    </html>
```

### Task 3: Create Services

Create services for the backend applications:

```yaml
# backend-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: app-v1-service
  labels:
    app: webapp
    version: v1
spec:
  selector:
    app: webapp
    version: v1
  ports:
  - name: http
    port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: app-v2-service
  labels:
    app: webapp
    version: v2
spec:
  selector:
    app: webapp
    version: v2
  ports:
  - name: http
    port: 80
    targetPort: 80
```

### Task 4: Create Basic Ingress

Create a simple Ingress resource:

```yaml
# basic-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: basic-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx  # Specify ingress class
  rules:
  - host: myapp.local  # Replace with your domain
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-v1-service
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: app-v2-service
            port:
              number: 80
```

### Task 5: Configure DNS/Hosts

Configure DNS resolution for testing:

```bash
# Get Ingress Controller external IP
kubectl get service -n ingress-nginx ingress-nginx-controller

# For LoadBalancer type
INGRESS_IP=$(kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# For NodePort type (using minikube or kind)
INGRESS_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
echo "$INGRESS_IP myapp.local" | sudo tee -a /etc/hosts
```

### Task 6: Test Ingress Routing

Test the Ingress configuration:

```bash
# Test root path (should go to app-v1)
curl http://myapp.local

# Test /v2 path (should go to app-v2)
curl http://myapp.local/v2

# Test with headers
curl -H "Host: myapp.local" http://INGRESS_IP
curl -H "Host: myapp.local" http://INGRESS_IP/v2

# Test from browser
echo "Visit: http://myapp.local and http://myapp.local/v2"
```

## ✅ Verification Steps

1. **Ingress resource created successfully**:
   ```bash
   kubectl get ingress basic-ingress
   kubectl describe ingress basic-ingress
   ```

2. **Ingress has assigned address**:
   ```bash
   kubectl get ingress basic-ingress -o wide
   # ADDRESS column should show IP
   ```

3. **Backend services are accessible**:
   ```bash
   # Direct service access
   kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never -- curl app-v1-service
   kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never -- curl app-v2-service
   ```

4. **HTTP routing works correctly**:
   ```bash
   # Root path goes to v1
   curl -s http://myapp.local | grep "Version 1"
   
   # /v2 path goes to v2
   curl -s http://myapp.local/v2 | grep "Version 2"
   ```

## 🔧 Advanced Ingress Configuration

### Default Backend

```yaml
# ingress-with-default.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-with-default
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: default-backend
      port:
        number: 80
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /app
        pathType: Prefix
        backend:
          service:
            name: app-v1-service
            port:
              number: 80
```

### Multiple Hosts

```yaml
# multi-host-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app1.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-v1-service
            port:
              number: 80
  - host: app2.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-v2-service
            port:
              number: 80
```

### Custom Annotations

```yaml
# annotated-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Custom-Header: MyValue";
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: app-v1-service
            port:
              number: 80
```

## 🔍 Troubleshooting

### Debug Ingress Issues

```bash
# Check Ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check Ingress resource status
kubectl describe ingress basic-ingress

# Check service endpoints
kubectl get endpoints app-v1-service app-v2-service

# Test internal service connectivity
kubectl run debug --image=curlimages/curl --rm -it --restart=Never -- sh
```

### Common Issues

1. **404 Not Found**: Check path matching and rewrite rules
2. **502 Bad Gateway**: Check backend service and pod health
3. **DNS Resolution**: Verify hosts file or DNS configuration
4. **SSL Issues**: Check certificate configuration

## 🧹 Cleanup

```bash
kubectl delete ingress basic-ingress
kubectl delete deployment app-v1 app-v2
kubectl delete service app-v1-service app-v2-service
kubectl delete configmap app-v1-content app-v2-content

# Remove from hosts file
sudo sed -i '/myapp.local/d' /etc/hosts
```

## 📚 Key Learnings

- Ingress provides HTTP/HTTPS routing to services
- Requires an Ingress controller to function
- Uses host and path-based routing rules
- Annotations control controller-specific behavior
- IngressClass determines which controller handles the resource

## 📖 Additional Resources

- [Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)