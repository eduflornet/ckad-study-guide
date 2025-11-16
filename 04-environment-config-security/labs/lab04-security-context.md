# Lab 04: Security Context

## Objective
Learn to configure pod and container security contexts to implement security best practices and control permissions.

## Tasks

### Task 1: Pod-level Security Context

```yaml
# pod-security-context.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-security-context
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    runAsNonRoot: true
    fsGroup: 2000
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args: ["-c", "while true; do whoami; id; ls -la /tmp; sleep 30; done"]
    volumeMounts:
    - name: test-volume
      mountPath: /tmp/test
  volumes:
  - name: test-volume
    emptyDir: {}
```

### Task 2: Container-level Security Context

```yaml
# container-security-context.yaml
apiVersion: v1
kind: Pod
metadata:
  name: container-security-context
spec:
  containers:
  - name: secure-container
    image: nginx:alpine
    securityContext:
      runAsUser: 1001
      runAsGroup: 2001
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'User: $(whoami), ID: $(id)'; sleep 30; done"]
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: cache-volume
      mountPath: /var/cache/nginx
    - name: run-volume
      mountPath: /var/run
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: cache-volume
    emptyDir: {}
  - name: run-volume
    emptyDir: {}
```

### Task 3: Security Context Override

```yaml
# security-context-override.yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-override
spec:
  securityContext:
    runAsUser: 1000  # Pod-level setting
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: container1
    image: nginx:alpine
    # Inherits pod-level security context
    command: ["/bin/sh"]
    args: ["-c", "echo 'Container 1:'; whoami; id; sleep 3600"]
  - name: container2
    image: nginx:alpine
    securityContext:
      runAsUser: 2000  # Overrides pod-level setting
      runAsGroup: 4000
    command: ["/bin/sh"]
    args: ["-c", "echo 'Container 2:'; whoami; id; sleep 3600"]
```

### Task 4: Capabilities Management

```yaml
# capabilities-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: capabilities-demo
spec:
  containers:
  - name: minimal-caps
    image: nginx:alpine
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
    command: ["/bin/sh"]
    args: ["-c", "echo 'Minimal capabilities'; capsh --print; sleep 3600"]
  - name: network-caps
    image: nginx:alpine
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
        - NET_RAW
    command: ["/bin/sh"]
    args: ["-c", "echo 'Network capabilities'; capsh --print; sleep 3600"]
```

### Task 5: Read-only Root Filesystem

```yaml
# readonly-filesystem.yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-filesystem
spec:
  containers:
  - name: readonly-app
    image: nginx:alpine
    securityContext:
      runAsUser: 101
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: var-cache
      mountPath: /var/cache/nginx
    - name: var-run
      mountPath: /var/run
    - name: var-log
      mountPath: /var/log/nginx
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: var-cache
    emptyDir: {}
  - name: var-run
    emptyDir: {}
  - name: var-log
    emptyDir: {}
  - name: nginx-config
    configMap:
      name: nginx-config
```

```bash
# Create nginx configuration
kubectl create configmap nginx-config --from-literal=default.conf='
server {
    listen 8080;
    server_name localhost;
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
}
'
```

### Task 6: Security Context in Deployments

```yaml
# secure-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-web-app
  template:
    metadata:
      labels:
        app: secure-web-app
    spec:
      securityContext:
        runAsUser: 1000
        runAsGroup: 2000
        runAsNonRoot: true
        fsGroup: 3000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: web
        image: nginx:alpine
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-cache
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
      volumes:
      - name: tmp
        emptyDir: {}
      - name: var-cache
        emptyDir: {}
      - name: var-run
        emptyDir: {}
```

### Task 7: SecurityContext with SELinux

```yaml
# selinux-context.yaml
apiVersion: v1
kind: Pod
metadata:
  name: selinux-context
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 2000
    seLinuxOptions:
      level: "s0:c123,c456"
      role: "object_r"
      type: "container_t"
      user: "system_u"
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'SELinux context:'; ls -Z /; sleep 60; done"]
```

## Verification Commands

```bash
# Check running processes and users
kubectl exec pod-security-context -- ps aux
kubectl exec pod-security-context -- whoami
kubectl exec pod-security-context -- id

# Verify file permissions
kubectl exec pod-security-context -- ls -la /tmp/test

# Check container security contexts
kubectl exec container-security-context -- whoami
kubectl exec container-security-context -- id

# Compare security contexts in override example
kubectl exec security-override -c container1 -- id
kubectl exec security-override -c container2 -- id

# Check capabilities
kubectl exec capabilities-demo -c minimal-caps -- capsh --print
kubectl exec capabilities-demo -c network-caps -- capsh --print

# Test read-only filesystem
kubectl exec readonly-filesystem -- touch /test-file  # Should fail
kubectl exec readonly-filesystem -- touch /tmp/test-file  # Should succeed

# Check deployment security
kubectl get pods -l app=secure-web-app
kubectl exec deployment/secure-web-app -- whoami
```

## Security Testing

### Task 8: Test Security Violations

```yaml
# insecure-pod.yaml (This should be rejected by security policies)
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: insecure
    image: nginx:alpine
    securityContext:
      runAsUser: 0  # Running as root
      privileged: true  # Privileged container
      allowPrivilegeEscalation: true
    command: ["/bin/sh"]
    args: ["-c", "whoami; sleep 3600"]
```

```bash
# Test security violations
kubectl apply -f insecure-pod.yaml  # May be rejected by admission controllers

# Check if running as root (security risk)
kubectl exec insecure-pod -- whoami
kubectl exec insecure-pod -- id
```

## Cleanup

```bash
kubectl delete pod pod-security-context container-security-context security-override capabilities-demo readonly-filesystem selinux-context insecure-pod
kubectl delete deployment secure-web-app
kubectl delete configmap nginx-config
```

## 🎯 Key Learning Points

- **Pod vs Container Security Context**: Container-level overrides pod-level
- **runAsUser/runAsGroup**: Control user and group IDs
- **runAsNonRoot**: Prevent running as root (UID 0)
- **fsGroup**: Set group ownership for volumes
- **Capabilities**: Fine-grained permission control (drop ALL, add specific)
- **readOnlyRootFilesystem**: Prevent filesystem modifications
- **allowPrivilegeEscalation**: Control privilege escalation
- **seccompProfile**: Apply seccomp security profiles
- **SELinux**: Additional security labeling (when available)
- Security contexts are inherited: Pod → Container
- Use minimal privileges (principle of least privilege)
