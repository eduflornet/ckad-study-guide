# Lab 05: Non-root Containers

## Objective
Learn to create and run containers as non-root users to enhance security and follow best practices.

## Tasks

### Task 1: Basic Non-root Configuration

```yaml
# basic-nonroot-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: basic-nonroot
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 2000
    runAsNonRoot: true
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args: ["-c", "whoami; id; echo 'Running as non-root'; sleep 3600"]
```

### Task 2: Non-root with Custom User

```yaml
# custom-user-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-user-pod
spec:
  securityContext:
    runAsUser: 5000
    runAsGroup: 5000
    runAsNonRoot: true
    fsGroup: 5000
  containers:
  - name: app
    image: alpine:latest
    command: ["/bin/sh"]
    args: ["-c", "adduser -D -u 5000 appuser; whoami; id; ls -la /home; sleep 3600"]
    volumeMounts:
    - name: app-data
      mountPath: /app/data
  volumes:
  - name: app-data
    emptyDir: {}
```

### Task 3: Non-root Nginx with Custom Configuration

First, create a custom nginx configuration that runs on non-privileged port:

```bash
kubectl create configmap nginx-nonroot-config --from-literal=nginx.conf='
user nobody;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    access_log /var/log/nginx/access.log;
    
    sendfile on;
    keepalive_timeout 65;
    
    server {
        listen 8080;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        location / {
            try_files $uri $uri/ =404;
        }
    }
}
'
```

```yaml
# nonroot-nginx-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-nginx
spec:
  securityContext:
    runAsUser: 65534  # nobody user
    runAsGroup: 65534
    runAsNonRoot: true
    fsGroup: 65534
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
    - name: tmp-volume
      mountPath: /tmp
    - name: var-cache
      mountPath: /var/cache/nginx
    - name: var-log
      mountPath: /var/log/nginx
    command: ["nginx", "-g", "daemon off;"]
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-nonroot-config
  - name: tmp-volume
    emptyDir: {}
  - name: var-cache
    emptyDir: {}
  - name: var-log
    emptyDir: {}
```

### Task 4: Non-root Application with File Permissions

```yaml
# file-permissions-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: file-permissions-pod
spec:
  securityContext:
    runAsUser: 1001
    runAsGroup: 2001
    runAsNonRoot: true
    fsGroup: 3001  # Files created in volumes will have this group
  containers:
  - name: app
    image: alpine:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Current user: $(whoami)"
      echo "Current groups: $(id)"
      echo "Creating files in different locations..."
      
      # This should work (volume with fsGroup)
      echo "test data" > /shared/test.txt
      ls -la /shared/
      
      # This should work (tmp is writable)
      echo "temp data" > /tmp/temp.txt
      ls -la /tmp/temp.txt
      
      # Keep container running
      sleep 3600
    volumeMounts:
    - name: shared-volume
      mountPath: /shared
  volumes:
  - name: shared-volume
    emptyDir: {}
```

### Task 5: Non-root Deployment with Init Container

```yaml
# nonroot-deployment-with-init.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nonroot-web-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nonroot-web-app
  template:
    metadata:
      labels:
        app: nonroot-web-app
    spec:
      securityContext:
        runAsUser: 1000
        runAsGroup: 2000
        runAsNonRoot: true
        fsGroup: 3000
      initContainers:
      - name: setup
        image: alpine:latest
        securityContext:
          runAsUser: 1000
          runAsNonRoot: true
        command: ["/bin/sh"]
        args:
        - -c
        - |
          echo "Setting up application..."
          echo "<h1>Hello from Non-root App!</h1>" > /shared/index.html
          echo "<p>Running as user $(whoami) with ID $(id)</p>" >> /shared/index.html
          ls -la /shared/
        volumeMounts:
        - name: web-content
          mountPath: /shared
      containers:
      - name: web
        image: nginx:alpine
        ports:
        - containerPort: 8080
        securityContext:
          runAsUser: 1000
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        volumeMounts:
        - name: web-content
          mountPath: /usr/share/nginx/html
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: default.conf
        - name: tmp-volume
          mountPath: /tmp
        - name: var-cache
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
      volumes:
      - name: web-content
        emptyDir: {}
      - name: nginx-config
        configMap:
          name: nginx-port-config
      - name: tmp-volume
        emptyDir: {}
      - name: var-cache
        emptyDir: {}
      - name: var-run
        emptyDir: {}
```

```bash
# Create nginx configuration for port 8080
kubectl create configmap nginx-port-config --from-literal=default.conf='
server {
    listen 8080;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
'
```

### Task 6: Non-root with Service Account

```yaml
# nonroot-serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: nonroot-sa
automountServiceAccountToken: true
---
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-with-sa
spec:
  serviceAccountName: nonroot-sa
  securityContext:
    runAsUser: 2000
    runAsGroup: 3000
    runAsNonRoot: true
  containers:
  - name: app
    image: alpine:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "User: $(whoami)"
      echo "Service Account Token:"
      ls -la /var/run/secrets/kubernetes.io/serviceaccount/
      cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
      echo ""
      sleep 3600
```

### Task 7: Testing Root Prevention

```yaml
# root-prevention-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: root-prevention-test
spec:
  securityContext:
    runAsNonRoot: true  # This will prevent the container from starting if it tries to run as root
  containers:
  - name: should-fail
    image: nginx:alpine  # This image typically runs as root by default
    command: ["/bin/sh"]
    args: ["-c", "whoami; sleep 3600"]
```

## Verification Commands

```bash
# Check user IDs in pods
kubectl exec basic-nonroot -- whoami
kubectl exec basic-nonroot -- id

kubectl exec custom-user-pod -- whoami
kubectl exec custom-user-pod -- id

# Check nginx non-root setup
kubectl exec nonroot-nginx -- whoami
kubectl exec nonroot-nginx -- ps aux
kubectl port-forward nonroot-nginx 8080:8080 &
curl http://localhost:8080
pkill -f "port-forward"

# Check file permissions
kubectl exec file-permissions-pod -- ls -la /shared/
kubectl exec file-permissions-pod -- stat /shared/test.txt

# Check deployment
kubectl get pods -l app=nonroot-web-app
kubectl exec deployment/nonroot-web-app -- whoami
kubectl exec deployment/nonroot-web-app -- id

# Check service account
kubectl exec nonroot-with-sa -- whoami
kubectl exec nonroot-with-sa -- cat /var/run/secrets/kubernetes.io/serviceaccount/namespace

# Test root prevention (should fail to create or start)
kubectl apply -f root-prevention-test.yaml
kubectl describe pod root-prevention-test
```

## Security Best Practices

### Task 8: Comprehensive Non-root Security

```yaml
# comprehensive-nonroot-security.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-nonroot-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-nonroot-app
  template:
    metadata:
      labels:
        app: secure-nonroot-app
    spec:
      securityContext:
        runAsUser: 10001
        runAsGroup: 10001
        runAsNonRoot: true
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: nginx:alpine
        ports:
        - containerPort: 8080
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 10001
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-cache
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: default.conf
      volumes:
      - name: tmp
        emptyDir: {}
      - name: var-cache
        emptyDir: {}
      - name: var-run
        emptyDir: {}
      - name: nginx-config
        configMap:
          name: nginx-port-config
```

## Cleanup

```bash
kubectl delete pod basic-nonroot custom-user-pod nonroot-nginx file-permissions-pod nonroot-with-sa root-prevention-test
kubectl delete deployment nonroot-web-app secure-nonroot-app
kubectl delete serviceaccount nonroot-sa
kubectl delete configmap nginx-nonroot-config nginx-port-config
```

## 🎯 Key Learning Points

- **runAsNonRoot: true** prevents containers from running as root (UID 0)
- **fsGroup** sets group ownership for volume mounts
- Non-privileged ports (> 1024) don't require root privileges
- Use **nobody** user (UID 65534) for maximum compatibility
- Init containers can run setup tasks as non-root
- **readOnlyRootFilesystem** + writable volumes for necessary directories
- Service account tokens are accessible to non-root users
- Some images require configuration changes to run as non-root
- File permissions matter - use fsGroup for shared volumes
- Combine with other security measures (capabilities, seccomp, etc.)
- Test your applications thoroughly when switching to non-root
- Document the required UIDs/GIDs for your applications
