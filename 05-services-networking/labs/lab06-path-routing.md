# Lab 6: Path-based Routing with Ingress

**Learning Objective**: Implement advanced path-based routing patterns using Ingress resources.

**Time**: 35 minutes

## 📋 Prerequisites

- Kubernetes cluster with Ingress controller
- kubectl configured
- Completed Lab 5 (Basic Ingress Setup)
- Understanding of HTTP paths and routing

## 🎯 Lab Overview

Path-based routing allows you to route different URL paths to different backend services, enabling microservice architectures and API versioning through a single entry point.

## 📝 Tasks

### Task 1: Create Microservice Applications

Deploy multiple microservices:

```yaml
# microservices.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  labels:
    app: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: api-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-service
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
    spec:
      containers:
      - name: frontend
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: frontend-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-service
  labels:
    app: admin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: admin
  template:
    metadata:
      labels:
        app: admin
    spec:
      containers:
      - name: admin
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: admin-content
---
# ConfigMaps for different services
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>API Service</title></head>
    <body style="background-color: #e3f2fd; font-family: Arial; padding: 20px;">
      <h1>🔌 API Service</h1>
      <p>This is the API microservice endpoint.</p>
      <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px;">
        <h3>Available Endpoints:</h3>
        <ul>
          <li>GET /api/users</li>
          <li>GET /api/orders</li>
          <li>POST /api/auth</li>
        </ul>
      </div>
      <p><strong>Pod:</strong> $(hostname)</p>
    </body>
    </html>
  users.html: |
    {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
  orders.html: |
    {"orders": [{"id": 101, "item": "Widget", "qty": 5}]}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>Frontend Application</title></head>
    <body style="background-color: #f3e5f5; font-family: Arial; padding: 20px;">
      <h1>🖥️ Frontend Application</h1>
      <p>Welcome to our application frontend!</p>
      <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px;">
        <h3>Features:</h3>
        <ul>
          <li>User Dashboard</li>
          <li>Product Catalog</li>
          <li>Shopping Cart</li>
        </ul>
      </div>
      <p><strong>Pod:</strong> $(hostname)</p>
    </body>
    </html>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: admin-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>Admin Panel</title></head>
    <body style="background-color: #ffebee; font-family: Arial; padding: 20px;">
      <h1>⚙️ Admin Panel</h1>
      <p>Administrative interface - Restricted Access</p>
      <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px;">
        <h3>Admin Functions:</h3>
        <ul>
          <li>User Management</li>
          <li>System Configuration</li>
          <li>Analytics Dashboard</li>
        </ul>
      </div>
      <p><strong>Pod:</strong> $(hostname)</p>
    </body>
    </html>
```

### Task 2: Create Services

```yaml
# microservice-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 80
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
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: admin-service
spec:
  selector:
    app: admin
  ports:
  - port: 80
    targetPort: 80
```

### Task 3: Path-based Routing Ingress

Create an Ingress with multiple path rules:

```yaml
# path-based-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.local
    http:
      paths:
      # API routes with rewrite
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      # Admin routes
      - path: /admin
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 80
      # Frontend (default/root)
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Task 4: Exact Path Matching

Create an Ingress with exact path matching:

```yaml
# exact-path-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: exact-path-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
  - host: exact.local
    http:
      paths:
      # Exact match for specific endpoints
      - path: /api/users
        pathType: Exact
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /api/orders
        pathType: Exact
        backend:
          service:
            name: api-service
            port:
              number: 80
      # Prefix match for everything else
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Task 5: Advanced Path Patterns

Implement complex routing patterns:

```yaml
# advanced-routing.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: advanced-routing
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    # Route specific API versions
    nginx.ingress.kubernetes.io/configuration-snippet: |
      if ($request_uri ~ "^/api/v1/.*$") {
        set $api_version "v1";
      }
      if ($request_uri ~ "^/api/v2/.*$") {
        set $api_version "v2";
      }
      more_set_headers "X-API-Version: $api_version";
spec:
  ingressClassName: nginx
  rules:
  - host: advanced.local
    http:
      paths:
      # API v1 routes
      - path: /api/v1(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      # API v2 routes (could go to different service)
      - path: /api/v2(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-service  # or api-v2-service
            port:
              number: 80
      # Static assets
      - path: /static
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
      # Default route
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Task 6: Test Path Routing

Test all routing patterns:

```bash
# Update hosts file
echo "$(kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}') myapp.local exact.local advanced.local" | sudo tee -a /etc/hosts

# Test path-based routing
curl http://myapp.local/          # Should go to frontend
curl http://myapp.local/api/      # Should go to api service
curl http://myapp.local/admin     # Should go to admin service

# Test exact path matching
curl http://exact.local/api/users   # Should work (exact match)
curl http://exact.local/api/orders  # Should work (exact match)
curl http://exact.local/api/other   # Should go to frontend (no exact match)

# Test advanced routing
curl http://advanced.local/api/v1/users  # Should go to API with v1 header
curl http://advanced.local/api/v2/users  # Should go to API with v2 header
curl http://advanced.local/static/css   # Should go to frontend
```

## ✅ Verification Steps

1. **All Ingress resources created**:
   ```bash
   kubectl get ingress
   kubectl describe ingress path-based-ingress
   ```

2. **Path routing works correctly**:
   ```bash
   # Root path
   curl -s http://myapp.local/ | grep "Frontend"
   
   # API path
   curl -s http://myapp.local/api/ | grep "API Service"
   
   # Admin path
   curl -s http://myapp.local/admin | grep "Admin Panel"
   ```

3. **Exact path matching**:
   ```bash
   # Exact matches work
   curl -s http://exact.local/api/users | grep "API"
   curl -s http://exact.local/api/orders | grep "API"
   
   # Non-exact goes to default
   curl -s http://exact.local/api/other | grep "Frontend"
   ```

4. **Rewrite rules function**:
   ```bash
   # Check that /api/users gets rewritten properly
   curl -v http://myapp.local/api/users 2>&1 | grep -E '(GET|POST)'
   ```

## 🔧 Troubleshooting Path Issues

### Debug Path Matching

```bash
# Check Ingress controller configuration
kubectl get ingress path-based-ingress -o yaml

# Check nginx configuration (if using nginx controller)
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A 10 -B 10 "myapp.local"

# Test with verbose curl
curl -v http://myapp.local/api/test

# Check Ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=50
```

### Common Path Issues

1. **Wrong path priority**: More specific paths should come first
2. **Incorrect rewrite rules**: Check rewrite-target annotations
3. **Trailing slashes**: Be consistent with trailing slash handling
4. **Regex patterns**: Verify regex syntax in use-regex annotations

## 🧹 Cleanup

```bash
kubectl delete ingress path-based-ingress exact-path-ingress advanced-routing
kubectl delete deployment api-service frontend-service admin-service
kubectl delete service api-service frontend-service admin-service
kubectl delete configmap api-content frontend-content admin-content

# Remove from hosts file
sudo sed -i '/myapp.local\|exact.local\|advanced.local/d' /etc/hosts
```

## 📚 Key Learnings

- Path-based routing enables microservice architecture
- Path order matters - more specific paths first
- Rewrite rules modify the request path sent to backends
- Exact vs Prefix path types have different matching behavior
- Regular expressions enable complex routing patterns

## 📖 Additional Resources

- [Ingress Path Types](https://kubernetes.io/docs/concepts/services-networking/ingress/#path-types)
- [NGINX Ingress Annotations](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/)
- [URL Rewriting](https://kubernetes.github.io/ingress-nginx/examples/rewrite/)