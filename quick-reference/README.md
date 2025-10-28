# CKAD Quick Reference Guide

Essential commands, YAML templates, and troubleshooting tips for the CKAD exam.

## 📚 Table of Contents

1. [Essential kubectl Commands](#essential-kubectl-commands)
2. [YAML Templates](#yaml-templates)
3. [Troubleshooting Guide](#troubleshooting-guide)
4. [Time-Saving Tips](#time-saving-tips)
5. [Common Ports and Values](#common-ports-and-values)

---

## Essential kubectl Commands

### Basic Operations
```bash
# Setup aliases (run at start of exam)
alias k=kubectl
complete -F __start_kubectl k

# Context and namespace
kubectl config get-contexts
kubectl config set-context --current --namespace=<namespace>
kubectl config current-context

# Quick resource creation
kubectl run <pod-name> --image=<image> --restart=Never
kubectl create deployment <name> --image=<image> --replicas=3
kubectl create service clusterip <name> --tcp=80:8080

# Generators with dry-run
kubectl run pod-name --image=nginx --dry-run=client -o yaml > pod.yaml
kubectl create deployment web --image=nginx --dry-run=client -o yaml > deploy.yaml
kubectl expose deployment web --port=80 --dry-run=client -o yaml > service.yaml
```

### Resource Management
```bash
# Scale resources
kubectl scale deployment web --replicas=5
kubectl autoscale deployment web --cpu-percent=80 --min=1 --max=10

# Update resources
kubectl set image deployment/web nginx=nginx:1.21
kubectl set resources deployment web --limits=cpu=200m,memory=512Mi
kubectl set env deployment/web DB_HOST=postgresql

# Rollout management
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
kubectl rollout restart deployment/web
```

### Inspection and Debugging
```bash
# Get resources
kubectl get pods -o wide
kubectl get all --all-namespaces
kubectl get events --sort-by=.metadata.creationTimestamp

# Describe and logs
kubectl describe pod <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous
kubectl logs -f deployment/web

# Execute commands
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec <pod-name> -c <container> -- command
kubectl port-forward <pod-name> 8080:80

# Resource usage
kubectl top nodes
kubectl top pods
kubectl top pods --containers
```

### ConfigMaps and Secrets
```bash
# ConfigMaps
kubectl create configmap app-config --from-literal=key1=value1 --from-literal=key2=value2
kubectl create configmap app-config --from-file=config.properties
kubectl create configmap app-config --from-env-file=config.env

# Secrets
kubectl create secret generic db-secret --from-literal=username=admin --from-literal=password=secret123
kubectl create secret docker-registry regcred --docker-username=user --docker-password=pass --docker-email=email@example.com
kubectl create secret tls tls-secret --cert=tls.crt --key=tls.key
```

### Jobs and CronJobs
```bash
# Jobs
kubectl create job pi --image=perl -- perl -Mbignum=bpi -wle 'print bpi(2000)'
kubectl create job hello --image=busybox -- echo "Hello World"

# CronJobs
kubectl create cronjob hello --image=busybox --schedule="*/1 * * * *" -- echo "Hello World"
kubectl create cronjob backup --image=busybox --schedule="0 2 * * *" -- backup.sh
```

### Network and Services
```bash
# Services
kubectl expose pod web --port=80 --target-port=8080
kubectl expose deployment web --port=80 --type=NodePort
kubectl expose deployment web --port=80 --type=LoadBalancer

# Ingress
kubectl create ingress simple --rule="foo.com/bar*=service1:8080"
kubectl create ingress tls --rule="foo.com/*=service1:8080" --tls=tls-secret

# Network testing
kubectl run test --image=busybox -it --rm -- nslookup service-name
kubectl run test --image=busybox -it --rm -- wget -qO- http://service-name
```

---

## YAML Templates

### Pod Template
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  containers:
  - name: container-name
    image: nginx:1.20
    ports:
    - containerPort: 80
    env:
    - name: ENV_VAR
      value: "value"
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
```

### Deployment Template
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: container-name
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### Service Templates
```yaml
# ClusterIP Service
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---
# NodePort Service
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport-service
spec:
  selector:
    app: my-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
    nodePort: 30080
  type: NodePort
```

### ConfigMap and Secret Usage
```yaml
# Pod using ConfigMap and Secret
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    env:
    - name: CONFIG_VALUE
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: config-key
    - name: SECRET_VALUE
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: secret-key
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secret
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: secret-volume
      mountPath: /etc/secret
  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: secret-volume
    secret:
      secretName: app-secret
```

### Multi-Container Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: main-app
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: log-sidecar
    image: busybox
    command: ["tail", "-f", "/var/log/nginx/access.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  initContainers:
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo "Setting up..." && sleep 10']
  volumes:
  - name: shared-logs
    emptyDir: {}
```

### Job and CronJob Templates
```yaml
# Job
apiVersion: batch/v1
kind: Job
metadata:
  name: my-job
spec:
  template:
    spec:
      containers:
      - name: job-container
        image: busybox
        command: ["echo", "Hello from Job"]
      restartPolicy: Never
  backoffLimit: 4
  ttlSecondsAfterFinished: 300

---
# CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-cronjob
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cronjob-container
            image: busybox
            command: ["echo", "Hello from CronJob"]
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### Security Context Template
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
```

### Network Policy Template
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-network-policy
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    - namespaceSelector:
        matchLabels:
          name: allowed-namespace
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

---

## Troubleshooting Guide

### Pod Not Starting
```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# Common issues:
# 1. Image pull errors
kubectl get events --sort-by=.metadata.creationTimestamp

# 2. Resource constraints
kubectl describe node <node-name>
kubectl top nodes
kubectl top pods

# 3. Configuration errors
kubectl logs <pod-name> --previous
kubectl get pod <pod-name> -o yaml
```

### Service Not Accessible
```bash
# Check service and endpoints
kubectl get service
kubectl get endpoints
kubectl describe service <service-name>

# Test service connectivity
kubectl run test --image=busybox -it --rm -- nslookup <service-name>
kubectl run test --image=busybox -it --rm -- wget -qO- http://<service-name>

# Check selectors
kubectl get pods --show-labels
kubectl get service <service-name> -o yaml
```

### Application Errors
```bash
# Check application logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs -f deployment/<deployment-name>

# Execute into container
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec <pod-name> -- ps aux
kubectl exec <pod-name> -- netstat -tulpn

# Check environment variables
kubectl exec <pod-name> -- env
kubectl describe pod <pod-name>
```

### Networking Issues
```bash
# Test pod-to-pod connectivity
kubectl exec -it <pod1> -- ping <pod2-ip>
kubectl exec -it <pod1> -- nslookup <service-name>
kubectl exec -it <pod1> -- curl http://<service-name>

# Check network policies
kubectl get networkpolicy
kubectl describe networkpolicy <policy-name>

# Check DNS
kubectl exec -it <pod> -- nslookup kubernetes.default
kubectl get pods -n kube-system | grep dns
```

---

## Time-Saving Tips

### Vim Configuration
```bash
# Add to ~/.vimrc for faster YAML editing
set tabstop=2
set shiftwidth=2
set expandtab
set number
```

### Bash Aliases
```bash
# Add to ~/.bashrc
alias k=kubectl
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deployment'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'

export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"
```

### kubectl Shortcuts
```bash
# Use short forms
k get po          # instead of kubectl get pods
k get svc         # instead of kubectl get services
k get deploy      # instead of kubectl get deployments
k get ing         # instead of kubectl get ingress

# Use dry-run for templates
k run test --image=nginx $do > pod.yaml
k create deploy web --image=nginx $do > deploy.yaml
k expose deploy web --port=80 $do > service.yaml
```

### Fast YAML Creation
```bash
# Start with generators, then edit
kubectl create deployment web --image=nginx --dry-run=client -o yaml > deploy.yaml
kubectl expose deployment web --port=80 --dry-run=client -o yaml > service.yaml
kubectl create configmap config --from-literal=key=value --dry-run=client -o yaml > cm.yaml
kubectl create secret generic secret --from-literal=key=value --dry-run=client -o yaml > secret.yaml
```

---

## Common Ports and Values

### Application Ports
- HTTP: 80, 8080, 3000
- HTTPS: 443, 8443
- Database: PostgreSQL (5432), MySQL (3306), Redis (6379), MongoDB (27017)
- Application servers: Tomcat (8080), Node.js (3000), Python Flask (5000)

### Resource Values
- CPU: 100m, 250m, 500m, 1000m (1 core)
- Memory: 64Mi, 128Mi, 256Mi, 512Mi, 1Gi
- Storage: 1Gi, 5Gi, 10Gi, 20Gi

### Common Images
- Web servers: nginx:1.20, httpd:2.4, nginx:alpine
- Databases: postgres:13, mysql:8.0, redis:6.2
- Utilities: busybox:1.35, alpine:3.14, ubuntu:20.04
- Applications: node:16-alpine, python:3.9-slim, openjdk:11-jre-slim

### Schedule Formats (Cron)
- Every minute: `* * * * *`
- Every hour: `0 * * * *`
- Daily at 2 AM: `0 2 * * *`
- Weekly (Sunday): `0 0 * * 0`
- Monthly (1st): `0 0 1 * *`

---

*Keep this reference handy during practice and the exam!*