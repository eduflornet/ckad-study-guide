# Lab 8: TLS Ingress Configuration

**Learning Objective**: Configure HTTPS/TLS termination using Ingress resources with SSL certificates.

**Time**: 40 minutes

## 📋 Prerequisites

- Kubernetes cluster with Ingress controller
- kubectl configured
- OpenSSL for certificate generation
- Understanding of TLS/SSL concepts

## 🎯 Lab Overview

TLS termination at the Ingress level provides HTTPS access to your applications while keeping internal communication unencrypted, improving performance and simplifying certificate management.

## 📝 Tasks

### Task 1: Create Sample Applications

Deploy applications that will be served over HTTPS:

```yaml
# secure-apps.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-web-app
  labels:
    app: secure-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-web
  template:
    metadata:
      labels:
        app: secure-web
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: content
        configMap:
          name: secure-web-content
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-app
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
apiVersion: v1
kind: ConfigMap
metadata:
  name: secure-web-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>Secure Web Application</title>
      <style>
        body { 
          font-family: Arial; 
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
          color: white; 
          padding: 40px; 
          margin: 0;
        }
        .container { 
          background: rgba(255,255,255,0.1); 
          padding: 30px; 
          border-radius: 15px; 
          max-width: 800px;
          margin: 0 auto;
        }
        .secure-badge { 
          background: #4CAF50; 
          padding: 5px 15px; 
          border-radius: 20px; 
          display: inline-block; 
          margin-bottom: 20px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="secure-badge">🔒 SECURE</div>
        <h1>Secure Web Application</h1>
        <p>This application is served over HTTPS with TLS termination at the Ingress.</p>
        <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0;">
          <h3>Security Features:</h3>
          <ul>
            <li>TLS 1.2/1.3 encryption</li>
            <li>Certificate-based authentication</li>
            <li>Secure headers configuration</li>
            <li>HTTP to HTTPS redirection</li>
          </ul>
        </div>
        <p><strong>Pod:</strong> $(hostname)</p>
        <p><strong>Protocol:</strong> <span id="protocol"></span></p>
        <script>
          document.getElementById('protocol').textContent = location.protocol;
        </script>
      </div>
    </body>
    </html>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-content
data:
  index.html: |
    {
      "status": "success",
      "message": "Secure API endpoint",
      "encryption": "TLS enabled",
      "pod": "$(hostname)",
      "endpoints": [
        "/api/users",
        "/api/orders",
        "/api/auth"
      ]
    }
```

### Task 2: Create Services

```yaml
# secure-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: secure-web-service
spec:
  selector:
    app: secure-web
  ports:
  - port: 80
    targetPort: 80
---
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
```

### Task 3: Generate Self-Signed Certificates

Create TLS certificates for testing:

```bash
# Create certificates directory
mkdir -p ./certs
cd certs

# Generate private key
openssl genrsa -out tls.key 2048

# Generate certificate signing request
openssl req -new -key tls.key -out tls.csr -subj "/CN=secure.local/O=MyOrg"

# Generate self-signed certificate
openssl x509 -req -in tls.csr -signkey tls.key -out tls.crt -days 365

# Create Kubernetes TLS secret
kubectl create secret tls secure-tls-secret --cert=tls.crt --key=tls.key

# Generate certificate for API
openssl genrsa -out api-tls.key 2048
openssl req -new -key api-tls.key -out api-tls.csr -subj "/CN=api.local/O=MyOrg"
openssl x509 -req -in api-tls.csr -signkey api-tls.key -out api-tls.crt -days 365
kubectl create secret tls api-tls-secret --cert=api-tls.crt --key=api-tls.key

# Wildcard certificate
openssl genrsa -out wildcard-tls.key 2048
openssl req -new -key wildcard-tls.key -out wildcard-tls.csr -subj "/CN=*.example.local/O=MyOrg"
openssl x509 -req -in wildcard-tls.csr -signkey wildcard-tls.key -out wildcard-tls.crt -days 365
kubectl create secret tls wildcard-tls-secret --cert=wildcard-tls.crt --key=wildcard-tls.key

cd ..
```

### Task 4: Create TLS Ingress

Create an Ingress with TLS configuration:

```yaml
# tls-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains";
      more_set_headers "X-Frame-Options: SAMEORIGIN";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.local
    secretName: secure-tls-secret
  - hosts:
    - api.local
    secretName: api-tls-secret
  rules:
  - host: secure.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-web-service
            port:
              number: 80
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### Task 5: Wildcard TLS Certificate

Create an Ingress using wildcard certificates:

```yaml
# wildcard-tls-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wildcard-tls-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Additional TLS configuration
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-RSA-AES128-GCM-SHA256,ECDHE-RSA-AES256-GCM-SHA384"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - "*.example.local"
    secretName: wildcard-tls-secret
  rules:
  - host: app1.example.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-web-service
            port:
              number: 80
  - host: app2.example.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### Task 6: Configure DNS and Test HTTPS

Set up DNS and test TLS functionality:

```bash
# Get Ingress IP
INGRESS_IP=$(kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add entries to hosts file
sudo tee -a /etc/hosts << EOF
$INGRESS_IP secure.local
$INGRESS_IP api.local
$INGRESS_IP app1.example.local
$INGRESS_IP app2.example.local
EOF

# Test HTTPS access (ignore certificate warnings for self-signed certs)
echo "Testing HTTPS access:"
curl -k https://secure.local
curl -k https://api.local

# Test HTTP to HTTPS redirect
echo "Testing HTTP redirect:"
curl -I http://secure.local  # Should return 301/302 redirect

# Test certificate details
echo "Certificate information:"
openssl s_client -connect secure.local:443 -servername secure.local < /dev/null 2>/dev/null | openssl x509 -noout -subject -dates

# Test wildcard certificates
echo "Testing wildcard certificates:"
curl -k https://app1.example.local
curl -k https://app2.example.local
```

### Task 7: Let's Encrypt with cert-manager (Optional)

If you want to use real certificates, install cert-manager:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

Create a ClusterIssuer for Let's Encrypt:

```yaml
# letsencrypt-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

Ingress with automatic certificate generation:

```yaml
# letsencrypt-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: letsencrypt-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - your-domain.com  # Replace with your actual domain
    secretName: letsencrypt-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-web-service
            port:
              number: 80
```

## ✅ Verification Steps

1. **HTTPS access works**:
   ```bash
   curl -k -I https://secure.local | grep "HTTP/2 200"
   curl -k -I https://api.local | grep "HTTP/2 200"
   ```

2. **HTTP redirects to HTTPS**:
   ```bash
   curl -I http://secure.local | grep "301\|302"
   ```

3. **Security headers present**:
   ```bash
   curl -k -I https://secure.local | grep -E "Strict-Transport-Security|X-Frame-Options"
   ```

4. **TLS certificate valid**:
   ```bash
   echo | openssl s_client -connect secure.local:443 -servername secure.local 2>/dev/null | openssl x509 -noout -subject
   ```

5. **Wildcard certificate works**:
   ```bash
   curl -k https://app1.example.local | grep "Secure Web"
   curl -k https://app2.example.local | grep "Secure API"
   ```

## 🔧 Advanced TLS Configuration

### Custom TLS Settings

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-RSA-AES128-GCM-SHA256"
    nginx.ingress.kubernetes.io/ssl-prefer-server-ciphers: "true"
    nginx.ingress.kubernetes.io/ssl-session-cache: "shared:SSL:10m"
    nginx.ingress.kubernetes.io/ssl-session-timeout: "10m"
```

### Client Certificate Authentication

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "default/ca-secret"
    nginx.ingress.kubernetes.io/auth-tls-verify-depth: "1"
```

## 🔍 Debugging TLS Issues

```bash
# Check TLS secret exists
kubectl get secret secure-tls-secret -o yaml

# Verify certificate in secret
kubectl get secret secure-tls-secret -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text

# Test TLS handshake
openssl s_client -connect secure.local:443 -servername secure.local

# Check Ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller | grep -i tls

# Validate certificate chain
curl -k -v https://secure.local 2>&1 | grep -E "SSL|TLS"
```

## 🧹 Cleanup

```bash
kubectl delete ingress tls-ingress wildcard-tls-ingress
kubectl delete deployment secure-web-app api-app
kubectl delete service secure-web-service api-service
kubectl delete configmap secure-web-content api-content
kubectl delete secret secure-tls-secret api-tls-secret wildcard-tls-secret

# Clean up certificate files
rm -rf ./certs

# Remove from hosts file
sudo sed -i '/secure.local\|api.local\|example.local/d' /etc/hosts
```

## 📚 Key Learnings

- TLS termination at Ingress provides centralized certificate management
- Self-signed certificates work for testing but show browser warnings
- Let's Encrypt provides free automated certificates for production
- Security headers enhance HTTPS protection
- Wildcard certificates can serve multiple subdomains

## 🔍 Troubleshooting Tips

- Verify certificate matches hostname
- Check certificate expiration dates
- Ensure TLS secret is in correct namespace
- Validate certificate chain completeness
- Monitor cert-manager logs for automatic certificates

## 📖 Additional Resources

- [Ingress TLS](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [NGINX TLS Configuration](https://kubernetes.github.io/ingress-nginx/user-guide/tls/)