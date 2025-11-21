# Lab 7: Host-based Routing with Ingress

**Learning Objective**: Configure host-based routing to serve different applications based on domain names.

**Time**: 30 minutes

## 📋 Prerequisites

- Kubernetes cluster with Ingress controller
- kubectl configured
- Basic understanding of DNS and virtual hosts
- Ability to modify hosts file or control DNS

## 🎯 Lab Overview

Host-based routing allows you to serve different applications based on the Host header in HTTP requests, enabling multiple domains to be served from a single Ingress controller.

## 📝 Tasks

### Task 1: Create Multi-tenant Applications

Deploy applications for different tenants/domains:

```yaml
# tenant-applications.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: company-a-app
  labels:
    tenant: company-a
spec:
  replicas: 2
  selector:
    matchLabels:
      tenant: company-a
  template:
    metadata:
      labels:
        tenant: company-a
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: company-a-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: company-b-app
  labels:
    tenant: company-b
spec:
  replicas: 2
  selector:
    matchLabels:
      tenant: company-b
  template:
    metadata:
      labels:
        tenant: company-b
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: company-b-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-app
  labels:
    app: blog
spec:
  replicas: 2
  selector:
    matchLabels:
      app: blog
  template:
    metadata:
      labels:
        app: blog
    spec:
      containers:
      - name: blog
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: blog-content
---
# Content for different tenants
apiVersion: v1
kind: ConfigMap
metadata:
  name: company-a-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>Company A Portal</title>
      <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; }
        .container { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
        .logo { font-size: 2em; margin-bottom: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">🏢 Company A</div>
        <h1>Welcome to Company A Portal</h1>
        <p>This is Company A's dedicated application instance.</p>
        <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
          <h3>Services Available:</h3>
          <ul>
            <li>Employee Portal</li>
            <li>Project Management</li>
            <li>Document Library</li>
          </ul>
        </div>
        <p><strong>Served by pod:</strong> $(hostname)</p>
      </div>
    </body>
    </html>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: company-b-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>Company B Dashboard</title>
      <style>
        body { font-family: Arial; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 40px; }
        .container { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
        .logo { font-size: 2em; margin-bottom: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">🏭 Company B</div>
        <h1>Company B Dashboard</h1>
        <p>Welcome to Company B's enterprise dashboard.</p>
        <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
          <h3>Dashboard Widgets:</h3>
          <ul>
            <li>Sales Analytics</li>
            <li>Inventory Management</li>
            <li>Customer Support</li>
          </ul>
        </div>
        <p><strong>Served by pod:</strong> $(hostname)</p>
      </div>
    </body>
    </html>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: blog-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>Tech Blog</title>
      <style>
        body { font-family: Arial; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 40px; }
        .container { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
        .logo { font-size: 2em; margin-bottom: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">📝 Tech Blog</div>
        <h1>Technology Blog</h1>
        <p>Latest articles about cloud computing and DevOps.</p>
        <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
          <h3>Recent Posts:</h3>
          <ul>
            <li>Kubernetes Networking Deep Dive</li>
            <li>CI/CD Best Practices</li>
            <li>Microservices Architecture</li>
          </ul>
        </div>
        <p><strong>Served by pod:</strong> $(hostname)</p>
      </div>
    </body>
    </html>
```

### Task 2: Create Services

```yaml
# tenant-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: company-a-service
spec:
  selector:
    tenant: company-a
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: company-b-service
spec:
  selector:
    tenant: company-b
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: blog-service
spec:
  selector:
    app: blog
  ports:
  - port: 80
    targetPort: 80
```

### Task 3: Host-based Routing Ingress

Create an Ingress with multiple host rules:

```yaml
# host-based-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    # Add custom headers based on host
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Tenant: $host";
spec:
  ingressClassName: nginx
  rules:
  # Company A domain
  - host: company-a.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: company-a-service
            port:
              number: 80
  # Company B domain
  - host: company-b.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: company-b-service
            port:
              number: 80
  # Blog domain
  - host: blog.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: blog-service
            port:
              number: 80
```

### Task 4: Wildcard Host Routing

Create an Ingress with wildcard host matching:

```yaml
# wildcard-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wildcard-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/server-snippet: |
      # Extract subdomain
      if ($host ~ ^([^.]+)\.tenant\.local$) {
        set $subdomain $1;
      }
      # Set header with extracted subdomain
      more_set_headers "X-Subdomain: $subdomain";
spec:
  ingressClassName: nginx
  rules:
  # Wildcard for tenant subdomains
  - host: "*.tenant.local"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: company-a-service  # Default service
            port:
              number: 80
```

### Task 5: Combined Host and Path Routing

Create complex routing with both host and path rules:

```yaml
# combined-routing.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: combined-routing
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  ingressClassName: nginx
  rules:
  # Main domain with different paths
  - host: portal.local
    http:
      paths:
      - path: /company-a(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: company-a-service
            port:
              number: 80
      - path: /company-b(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: company-b-service
            port:
              number: 80
      - path: /blog(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: blog-service
            port:
              number: 80
      # Default path
      - path: /
        pathType: Prefix
        backend:
          service:
            name: company-a-service
            port:
              number: 80
```

### Task 6: Configure DNS and Test

Set up DNS resolution and test routing:

```bash
# Get Ingress IP
INGRESS_IP=$(kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add entries to hosts file
sudo tee -a /etc/hosts << EOF
$INGRESS_IP company-a.local
$INGRESS_IP company-b.local
$INGRESS_IP blog.local
$INGRESS_IP portal.local
$INGRESS_IP subdomain1.tenant.local
$INGRESS_IP subdomain2.tenant.local
EOF

# Test host-based routing
echo "Testing Company A:"
curl -s http://company-a.local | grep -o '<title>.*</title>'

echo "Testing Company B:"
curl -s http://company-b.local | grep -o '<title>.*</title>'

echo "Testing Blog:"
curl -s http://blog.local | grep -o '<title>.*</title>'

# Test wildcard routing
echo "Testing wildcard subdomains:"
curl -H "Host: test1.tenant.local" http://$INGRESS_IP
curl -H "Host: test2.tenant.local" http://$INGRESS_IP

# Test combined routing
echo "Testing combined routing:"
curl http://portal.local/company-a
curl http://portal.local/company-b
curl http://portal.local/blog
```

## ✅ Verification Steps

1. **Host routing works for each domain**:
   ```bash
   curl -s http://company-a.local | grep "Company A"
   curl -s http://company-b.local | grep "Company B"
   curl -s http://blog.local | grep "Tech Blog"
   ```

2. **Headers are set correctly**:
   ```bash
   curl -I http://company-a.local | grep "X-Tenant"
   curl -I http://subdomain1.tenant.local | grep "X-Subdomain"
   ```

3. **Combined routing functions**:
   ```bash
   curl -s http://portal.local/company-a | grep "Company A"
   curl -s http://portal.local/company-b | grep "Company B"
   ```

4. **Load balancing across pods**:
   ```bash
   for i in {1..5}; do
     curl -s http://company-a.local | grep "pod:"
   done
   ```

## 🔧 Advanced Host Configuration

### Server Name Indication (SNI)

```yaml
# sni-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sni-ingress
  annotations:
    nginx.ingress.kubernetes.io/server-alias: "company-a.com,www.company-a.com"
spec:
  ingressClassName: nginx
  rules:
  - host: company-a.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: company-a-service
            port:
              number: 80
```

### Default Backend for Unknown Hosts

```yaml
# default-backend-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: default-backend
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: blog-service
      port:
        number: 80
```

## 🔍 Debugging Host Issues

```bash
# Test with specific Host header
curl -H "Host: company-a.local" http://INGRESS_IP

# Check Ingress controller nginx config
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A 20 server_name

# Test DNS resolution
nslookup company-a.local

# Check Ingress status
kubectl describe ingress host-based-ingress
```

## 🧹 Cleanup

```bash
kubectl delete ingress host-based-ingress wildcard-ingress combined-routing
kubectl delete deployment company-a-app company-b-app blog-app
kubectl delete service company-a-service company-b-service blog-service
kubectl delete configmap company-a-content company-b-content blog-content

# Remove from hosts file
sudo sed -i '/company-a.local\|company-b.local\|blog.local\|portal.local\|tenant.local/d' /etc/hosts
```

## 📚 Key Learnings

- Host-based routing enables multi-tenancy
- Wildcard hosts support dynamic subdomains
- Host and path routing can be combined
- Server aliases allow multiple domains per service
- Default backends handle unknown hosts

## 🔍 Troubleshooting Tips

- Verify DNS resolution or hosts file entries
- Check Host header in requests
- Test with curl -H "Host: domain.com"
- Monitor Ingress controller logs
- Validate Ingress resource configuration

## 📖 Additional Resources

- [Ingress Rules](https://kubernetes.io/docs/concepts/services-networking/ingress/#ingress-rules)
- [NGINX Virtual Hosts](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#server-alias)
- [Wildcard Hosts](https://kubernetes.github.io/ingress-nginx/user-guide/ingress-path-matching/)