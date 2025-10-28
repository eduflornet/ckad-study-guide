# kubectl Cheat Sheet for CKAD

Quick reference for essential kubectl commands organized by exam domains.

## Basic Setup
```bash
# Essential aliases
alias k=kubectl
complete -F __start_kubectl k

# Context management
k config get-contexts
k config current-context
k config set-context --current --namespace=<namespace>

# Quick environment variables
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"
```

## Pod Management
```bash
# Create pods
k run nginx --image=nginx --restart=Never
k run nginx --image=nginx --restart=Never --port=80
k run nginx --image=nginx --restart=Never --labels="app=web,env=dev"
k run nginx --image=nginx --restart=Never $do > pod.yaml

# Pod operations
k get pods
k get pods -o wide
k get pods --show-labels
k get pods -l app=web
k describe pod nginx
k delete pod nginx
k delete pod nginx $now

# Execute into pods
k exec -it nginx -- /bin/bash
k exec nginx -- ls /
k exec nginx -c container-name -- command

# Port forwarding
k port-forward nginx 8080:80
k port-forward service/nginx 8080:80
```

## Deployments
```bash
# Create deployments
k create deployment nginx --image=nginx
k create deployment nginx --image=nginx --replicas=3
k create deployment nginx --image=nginx $do > deploy.yaml

# Scale deployments
k scale deployment nginx --replicas=5
k autoscale deployment nginx --cpu-percent=80 --min=1 --max=10

# Update deployments
k set image deployment/nginx nginx=nginx:1.21
k set resources deployment nginx --limits=cpu=200m,memory=512Mi
k set env deployment/nginx DB_HOST=postgresql

# Rollout management
k rollout status deployment/nginx
k rollout history deployment/nginx
k rollout undo deployment/nginx
k rollout restart deployment/nginx
```

## Services
```bash
# Create services
k expose pod nginx --port=80 --target-port=80
k expose deployment nginx --port=80 --type=ClusterIP
k expose deployment nginx --port=80 --type=NodePort
k expose deployment nginx --port=80 --type=LoadBalancer
k create service clusterip nginx --tcp=80:80

# Service operations
k get services
k get svc
k describe service nginx
k get endpoints
```

## ConfigMaps and Secrets
```bash
# ConfigMaps
k create configmap app-config --from-literal=key1=value1 --from-literal=key2=value2
k create configmap app-config --from-file=config.properties
k create configmap app-config --from-env-file=.env
k get configmaps
k describe configmap app-config

# Secrets
k create secret generic app-secret --from-literal=username=admin --from-literal=password=secret
k create secret docker-registry regcred --docker-username=user --docker-password=pass
k create secret tls tls-secret --cert=tls.crt --key=tls.key
k get secrets
k describe secret app-secret
```

## Jobs and CronJobs
```bash
# Jobs
k create job pi --image=perl -- perl -Mbignum=bpi -wle 'print bpi(2000)'
k create job hello --image=busybox -- echo "Hello World"
k get jobs
k describe job hello
k logs job/hello

# CronJobs
k create cronjob hello --image=busybox --schedule="*/1 * * * *" -- echo "Hello World"
k create cronjob backup --image=busybox --schedule="0 2 * * *" -- backup.sh
k get cronjobs
k get cronjob hello -o yaml
```

## Ingress
```bash
# Create Ingress
k create ingress simple --rule="foo.com/bar*=service1:8080"
k create ingress multi --rule="foo.com/api*=api-service:80" --rule="foo.com/web*=web-service:8080"
k create ingress tls --rule="secure.com/*=web:80" --tls=my-tls-secret
k get ingress
k describe ingress simple
```

## Debugging and Troubleshooting
```bash
# View resources
k get all
k get all --all-namespaces
k get events --sort-by=.metadata.creationTimestamp
k get events --field-selector involvedObject.name=nginx

# Logs
k logs nginx
k logs nginx -c container-name
k logs nginx --previous
k logs -f deployment/nginx
k logs -l app=nginx

# Describe resources
k describe pod nginx
k describe service nginx
k describe deployment nginx
k describe node node-name

# Resource usage
k top nodes
k top pods
k top pods --containers
k top pods --sort-by=cpu
k top pods --sort-by=memory
```

## Network Policies
```bash
# Get network policies
k get networkpolicy
k get netpol
k describe networkpolicy deny-all

# Test network connectivity
k run test --image=busybox -it --rm -- nslookup service-name
k run test --image=busybox -it --rm -- wget -qO- http://service-name:80
k run test --image=busybox -it --rm -- ping pod-ip
```

## Resource Management
```bash
# Set resources
k set resources deployment nginx --requests=cpu=100m,memory=128Mi --limits=cpu=500m,memory=512Mi
k set env deployment/nginx DATABASE_URL=postgresql://db:5432/app
k patch deployment nginx -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","resources":{"limits":{"cpu":"500m"}}}]}}}}'

# Labels and annotations
k label pod nginx env=production
k label pod nginx app-
k annotate pod nginx description="Web server"
k get pods --show-labels
k get pods -l env=production
```

## YAML Output and Manipulation
```bash
# Generate YAML
k run nginx --image=nginx $do > pod.yaml
k create deployment nginx --image=nginx $do > deployment.yaml
k expose deployment nginx --port=80 $do > service.yaml
k create configmap config --from-literal=key=value $do > configmap.yaml

# Edit resources
k edit pod nginx
k edit deployment nginx
k edit service nginx

# Apply and delete
k apply -f pod.yaml
k delete -f pod.yaml
k replace -f pod.yaml --force
```

## Namespaces
```bash
# Namespace operations
k get namespaces
k create namespace dev
k delete namespace dev
k config set-context --current --namespace=dev

# Cross-namespace access
k get pods --all-namespaces
k get pods -n kube-system
k describe pod nginx -n production
```

## Helpful Shortcuts
```bash
# Resource short names
po = pods
svc = services
deploy = deployments
rs = replicasets
cm = configmaps
ns = namespaces
ing = ingress
netpol = networkpolicies
pv = persistentvolumes
pvc = persistentvolumeclaims

# Examples
k get po
k get svc
k get deploy
k describe po nginx
k delete svc nginx
```

## One-Liners for Common Tasks
```bash
# Quick pod with command
k run debug --image=busybox -it --rm -- sh

# Check if service is accessible
k run test --image=busybox -it --rm -- wget -qO- http://service-name

# Get pod IPs
k get pods -o wide

# Get all pod logs
k logs -l app=myapp --tail=100

# Force delete stuck pod
k delete pod nginx --grace-period=0 --force

# Quick deployment with service
k create deployment web --image=nginx && k expose deployment web --port=80

# Scale to zero
k scale deployment web --replicas=0

# Restart deployment
k rollout restart deployment/web
```

## Quick YAML Snippets

### Basic Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
```

### Pod with ConfigMap
```yaml
spec:
  containers:
  - name: app
    image: nginx
    envFrom:
    - configMapRef:
        name: app-config
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

### Pod with Secret
```yaml
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```

### Pod with Probes
```yaml
spec:
  containers:
  - name: nginx
    image: nginx
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