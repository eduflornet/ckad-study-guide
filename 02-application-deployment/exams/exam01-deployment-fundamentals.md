# Mock Exam 1: Application Deployment (CKAD)

**Exam Duration**: 45 minutes  
**Total Questions**: 15  
**Passing Score**: 80% (12/15 correct)  
**Exam Focus**: Application Deployment (20% of CKAD)

---

## Instructions

- You have 45 minutes to complete 15 questions
- Each question is worth equal points
- You may use the official Kubernetes documentation
- All work must be done in the provided cluster environment
- Save your YAML files as requested for verification
- Partial credit may be awarded for partially correct solutions

---

## Question 1 (4 points)
**Topic**: Basic Deployments  
**Time**: 3 minutes

Create a deployment named `web-app` in the namespace `production` with the following specifications:
- Image: `nginx:1.20`
- Replicas: 3
- Labels: `app=web-app`, `environment=prod`
- Container port: 80
- Resource limits: CPU 200m, Memory 256Mi
- Resource requests: CPU 100m, Memory 128Mi

Save the deployment YAML to `/tmp/web-app-deployment.yaml`.

<details>
<summary>Solution</summary>

```yaml
# Create namespace first
kubectl create namespace production

# Create deployment YAML
cat << EOF > /tmp/web-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web-app
    environment: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        environment: prod
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
EOF

# Apply the deployment
kubectl apply -f /tmp/web-app-deployment.yaml
```

**Verification Commands:**
```bash
kubectl get deployment web-app -n production
kubectl get pods -n production -l app=web-app
```
</details>

---

## Question 2 (5 points)
**Topic**: Rolling Updates  
**Time**: 4 minutes

You have a deployment named `api-server` running in the `default` namespace. Perform the following operations:

1. Update the deployment to use image `nginx:1.21`
2. Set the rolling update strategy to update a maximum of 2 pods at a time
3. Ensure zero unavailable pods during the update
4. Record the update in the deployment history
5. View the rollout status

<details>
<summary>Solution</summary>

```bash
# First create the base deployment (if not exists)
kubectl create deployment api-server --image=nginx:1.20 --replicas=5

# Configure rolling update strategy
kubectl patch deployment api-server -p='{"spec":{"strategy":{"rollingUpdate":{"maxSurge":2,"maxUnavailable":0},"type":"RollingUpdate"}}}'

# Update the image with record
kubectl set image deployment/api-server nginx=nginx:1.21 --record

# Check rollout status
kubectl rollout status deployment/api-server

# Verify the update
kubectl get deployment api-server -o yaml | grep -A5 strategy
kubectl rollout history deployment/api-server
```
</details>

---

## Question 3 (4 points)
**Topic**: Deployment Rollback  
**Time**: 3 minutes

Your deployment `payment-service` in namespace `finance` has been updated with a problematic image. Perform the following:

1. Check the rollout history
2. Rollback to the previous version
3. Verify the rollback was successful
4. Save the current deployment spec to `/tmp/payment-service-rollback.yaml`

<details>
<summary>Solution</summary>

```bash
# Create namespace and sample deployment for demo
kubectl create namespace finance
kubectl create deployment payment-service --image=nginx:1.20 -n finance
kubectl set image deployment/payment-service nginx=nginx:broken --record -n finance

# Check rollout history
kubectl rollout history deployment/payment-service -n finance

# Rollback to previous version
kubectl rollout undo deployment/payment-service -n finance

# Verify rollback
kubectl rollout status deployment/payment-service -n finance
kubectl get deployment payment-service -n finance

# Save current spec
kubectl get deployment payment-service -n finance -o yaml > /tmp/payment-service-rollback.yaml
```
</details>

---

## Question 4 (6 points)
**Topic**: Scaling and ReplicaSets  
**Time**: 4 minutes

Working with a deployment named `worker-service`:

1. Scale the deployment to 8 replicas
2. Create an additional ReplicaSet manually with 3 replicas using the same pod template
3. List all ReplicaSets and their managed pods
4. Scale down the deployment to 2 replicas
5. Verify that only the deployment's ReplicaSet scales down

<details>
<summary>Solution</summary>

```bash
# Create initial deployment
kubectl create deployment worker-service --image=nginx:1.20 --replicas=3

# Scale deployment to 8 replicas
kubectl scale deployment worker-service --replicas=8

# Get the deployment's pod template to create manual ReplicaSet
kubectl get deployment worker-service -o yaml > temp-deployment.yaml

# Create manual ReplicaSet
cat << EOF > manual-replicaset.yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: worker-service-manual
  labels:
    app: worker-service-manual
spec:
  replicas: 3
  selector:
    matchLabels:
      app: worker-service-manual
  template:
    metadata:
      labels:
        app: worker-service-manual
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
EOF

kubectl apply -f manual-replicaset.yaml

# List all ReplicaSets
kubectl get replicasets
kubectl get pods -l app=worker-service
kubectl get pods -l app=worker-service-manual

# Scale down deployment
kubectl scale deployment worker-service --replicas=2

# Verify only deployment scaled down
kubectl get replicasets
kubectl get pods --show-labels
```
</details>

---

## Question 5 (5 points)
**Topic**: Deployment Strategies  
**Time**: 4 minutes

Create a deployment that implements a Blue-Green deployment pattern:

1. Create deployment `app-blue` with image `nginx:1.20`, 3 replicas, label `version=blue`
2. Create service `app-service` that routes to `version=blue`
3. Create deployment `app-green` with image `nginx:1.21`, 3 replicas, label `version=green`  
4. Switch service to route to `version=green`
5. Verify the switch was successful

Save all YAML files to `/tmp/blue-green/`

<details>
<summary>Solution</summary>

```bash
# Create directory
mkdir -p /tmp/blue-green

# Create Blue deployment
cat << EOF > /tmp/blue-green/app-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    app: myapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

# Create service pointing to blue
cat << EOF > /tmp/blue-green/app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    version: blue
  ports:
  - port: 80
    targetPort: 80
EOF

# Create Green deployment
cat << EOF > /tmp/blue-green/app-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    app: myapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
EOF

# Apply blue and service
kubectl apply -f /tmp/blue-green/app-blue.yaml
kubectl apply -f /tmp/blue-green/app-service.yaml

# Apply green
kubectl apply -f /tmp/blue-green/app-green.yaml

# Wait for green to be ready
kubectl wait --for=condition=available deployment/app-green --timeout=60s

# Switch service to green
kubectl patch service app-service -p '{"spec":{"selector":{"version":"green"}}}'

# Verify switch
kubectl get service app-service -o yaml | grep -A2 selector
kubectl get endpoints app-service
```
</details>

---

## Question 6 (4 points)
**Topic**: Helm Basics  
**Time**: 3 minutes

Using Helm:

1. Add the official Bitnami repository
2. Search for nginx charts in the Bitnami repository  
3. Install nginx chart with release name `my-nginx` in namespace `web`
4. List all Helm releases across all namespaces

<details>
<summary>Solution</summary>

```bash
# Add Bitnami repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update repositories
helm repo update

# Search for nginx charts
helm search repo bitnami/nginx

# Create namespace
kubectl create namespace web

# Install nginx chart
helm install my-nginx bitnami/nginx --namespace web

# List all releases
helm list --all-namespaces
```
</details>

---

## Question 7 (6 points)
**Topic**: Helm Custom Values  
**Time**: 5 minutes

Create a custom values file for an nginx Helm chart with the following specifications:

1. Set replica count to 4
2. Enable ingress with host `myapp.local`
3. Set resource limits: CPU 300m, Memory 512Mi
4. Set resource requests: CPU 150m, Memory 256Mi
5. Install the chart with these custom values as release `custom-nginx`
6. Save the values file as `/tmp/custom-values.yaml`

<details>
<summary>Solution</summary>

```yaml
# Create custom values file
cat << EOF > /tmp/custom-values.yaml
replicaCount: 4

ingress:
  enabled: true
  hosts:
    - host: myapp.local
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 300m
    memory: 512Mi
  requests:
    cpu: 150m
    memory: 256Mi
EOF

# Install with custom values
helm install custom-nginx bitnami/nginx -f /tmp/custom-values.yaml --namespace web --create-namespace

# Verify installation
helm get values custom-nginx -n web
kubectl get pods -n web -l app.kubernetes.io/instance=custom-nginx
kubectl get ingress -n web
```
</details>

---

## Question 8 (5 points)
**Topic**: Helm Chart Creation  
**Time**: 4 minutes

Create a basic Helm chart:

1. Create a new chart named `webapp`
2. Modify the default deployment to use image `httpd:2.4`
3. Set default replica count to 2
4. Package the chart
5. Install it as release `my-webapp`

Save chart in `/tmp/charts/`

<details>
<summary>Solution</summary>

```bash
# Create directory and chart
mkdir -p /tmp/charts
cd /tmp/charts
helm create webapp

# Modify values.yaml
sed -i 's/repository: nginx/repository: httpd/' webapp/values.yaml
sed -i 's/tag: ""/tag: "2.4"/' webapp/values.yaml
sed -i 's/replicaCount: 1/replicaCount: 2/' webapp/values.yaml

# Package the chart
helm package webapp

# Install the chart
helm install my-webapp ./webapp

# Verify installation
helm list
kubectl get pods -l app.kubernetes.io/name=webapp
```
</details>

---

## Question 9 (5 points)
**Topic**: Helm Upgrades  
**Time**: 4 minutes

Working with an existing Helm release `api-app`:

1. Upgrade the release to use image tag `v2.0`
2. Increase replica count to 5 during the upgrade
3. View the upgrade history
4. Rollback to the previous version if the upgrade fails
5. Check the final status

<details>
<summary>Solution</summary>

```bash
# First create a sample release
helm install api-app bitnami/nginx --set image.tag=1.20

# Upgrade with new values
helm upgrade api-app bitnami/nginx --set image.tag=v2.0 --set replicaCount=5

# View upgrade history
helm history api-app

# If upgrade fails, rollback
helm rollback api-app 1

# Check final status
helm status api-app
kubectl get pods -l app.kubernetes.io/instance=api-app
```
</details>

---

## Question 10 (4 points)
**Topic**: Deployment Troubleshooting  
**Time**: 3 minutes

A deployment named `broken-app` in namespace `debug` is failing to start. Investigate and fix the issues:

1. Identify why pods are not starting
2. Fix the deployment
3. Ensure all pods are running
4. Document the issue and fix in `/tmp/troubleshooting-report.txt`

<details>
<summary>Solution</summary>

```bash
# Create broken deployment for demo
kubectl create namespace debug
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-app
  namespace: debug
spec:
  replicas: 3
  selector:
    matchLabels:
      app: broken-app
  template:
    metadata:
      labels:
        app: broken-app
    spec:
      containers:
      - name: app
        image: nonexistent:latest
        resources:
          requests:
            memory: "10Gi"  # Unrealistic memory request
EOF

# Investigate the issues
kubectl get pods -n debug
kubectl describe deployment broken-app -n debug
kubectl describe pods -n debug
kubectl get events -n debug --sort-by='.lastTimestamp'

# Fix the deployment
kubectl patch deployment broken-app -n debug -p='{"spec":{"template":{"spec":{"containers":[{"name":"app","image":"nginx:1.20","resources":{"requests":{"memory":"128Mi"}}}]}}}}'

# Verify fix
kubectl get pods -n debug
kubectl rollout status deployment/broken-app -n debug

# Document findings
cat << EOF > /tmp/troubleshooting-report.txt
Issues Found:
1. Invalid container image: nonexistent:latest
2. Unrealistic memory request: 10Gi

Fixes Applied:
1. Changed image to nginx:1.20
2. Reduced memory request to 128Mi

Result: All pods are now running successfully
EOF
```
</details>

---

## Question 11 (5 points)
**Topic**: Advanced Deployment Configuration  
**Time**: 4 minutes

Create a deployment with advanced configuration:

1. Name: `advanced-app`, namespace: `apps`
2. Image: `nginx:1.21`
3. Replicas: 3
4. Rolling update: max 1 unavailable, max 2 surge
5. Readiness probe: HTTP GET on port 80, path `/ready`
6. Liveness probe: HTTP GET on port 80, path `/health`
7. Init container that runs `busybox:1.35` and sleeps for 10 seconds

Save to `/tmp/advanced-deployment.yaml`

<details>
<summary>Solution</summary>

```yaml
cat << EOF > /tmp/advanced-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: advanced-app
  namespace: apps
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 2
  selector:
    matchLabels:
      app: advanced-app
  template:
    metadata:
      labels:
        app: advanced-app
    spec:
      initContainers:
      - name: init-setup
        image: busybox:1.35
        command: ['sh', '-c', 'sleep 10']
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
EOF

# Apply the deployment
kubectl create namespace apps
kubectl apply -f /tmp/advanced-deployment.yaml

# Verify
kubectl get deployment advanced-app -n apps
kubectl describe deployment advanced-app -n apps
```
</details>

---

## Question 12 (6 points)
**Topic**: Multi-Container Deployments  
**Time**: 5 minutes

Create a deployment with multiple containers:

1. Name: `multi-app`, namespace: `multicontainer`
2. Container 1: `web` using `nginx:1.20`, port 80
3. Container 2: `sidecar` using `busybox:1.35`, command: `sleep 3600`
4. Shared volume: `shared-data` mounted at `/usr/share/nginx/html` in web container and `/data` in sidecar
5. Environment variable in web container: `ENVIRONMENT=production`
6. 2 replicas

Create a service to expose the web container on port 80.

<details>
<summary>Solution</summary>

```yaml
# Create namespace
kubectl create namespace multicontainer

# Create deployment
cat << EOF > multi-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-app
  namespace: multicontainer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: multi-app
  template:
    metadata:
      labels:
        app: multi-app
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: ENVIRONMENT
          value: "production"
        volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
      - name: sidecar
        image: busybox:1.35
        command: ["sleep", "3600"]
        volumeMounts:
        - name: shared-data
          mountPath: /data
      volumes:
      - name: shared-data
        emptyDir: {}
EOF

# Create service
cat << EOF > multi-app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-app-service
  namespace: multicontainer
spec:
  selector:
    app: multi-app
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f multi-app-deployment.yaml
kubectl apply -f multi-app-service.yaml

# Verify
kubectl get pods -n multicontainer
kubectl describe deployment multi-app -n multicontainer
kubectl get service -n multicontainer
```
</details>

---

## Question 13 (5 points)
**Topic**: Helm Dependencies  
**Time**: 4 minutes

Create a Helm chart that depends on external charts:

1. Create chart named `fullstack-app`
2. Add dependency on `bitnami/postgresql` version `12.1.9`
3. Add dependency on `bitnami/redis` version `17.3.7`
4. Configure postgresql with database name `appdb`
5. Install the chart with dependencies

<details>
<summary>Solution</summary>

```bash
# Create chart
helm create fullstack-app

# Create Chart.yaml with dependencies
cat << EOF > fullstack-app/Chart.yaml
apiVersion: v2
name: fullstack-app
description: A Helm chart for fullstack application
type: application
version: 0.1.0
appVersion: "1.0"

dependencies:
  - name: postgresql
    version: "12.1.9"
    repository: "https://charts.bitnami.com/bitnami"
  - name: redis
    version: "17.3.7"
    repository: "https://charts.bitnami.com/bitnami"
EOF

# Configure postgresql in values.yaml
cat << EOF >> fullstack-app/values.yaml

postgresql:
  auth:
    database: appdb
    username: appuser
    password: apppassword

redis:
  auth:
    enabled: false
EOF

# Update dependencies
helm dependency update fullstack-app

# Install chart
helm install fullstack-app ./fullstack-app

# Verify installation
helm list
kubectl get pods
kubectl get pvc
```
</details>

---

## Question 14 (6 points)
**Topic**: Canary Deployment  
**Time**: 5 minutes

Implement a canary deployment strategy:

1. Create stable deployment `api-stable` with 9 replicas, image `nginx:1.20`, label `version=stable`
2. Create canary deployment `api-canary` with 1 replica, image `nginx:1.21`, label `version=canary`  
3. Create service that routes to both versions based on labels `app=api`
4. Verify traffic distribution (90% stable, 10% canary)
5. Scale canary to 3 replicas and stable to 7 replicas
6. Show the new traffic distribution

<details>
<summary>Solution</summary>

```yaml
# Create stable deployment
cat << EOF > api-stable.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-stable
  labels:
    app: api
    version: stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: api
      version: stable
  template:
    metadata:
      labels:
        app: api
        version: stable
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

# Create canary deployment
cat << EOF > api-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-canary
  labels:
    app: api
    version: canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
      version: canary
  template:
    metadata:
      labels:
        app: api
        version: canary
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
EOF

# Create service
cat << EOF > api-service.yaml
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
EOF

# Apply all resources
kubectl apply -f api-stable.yaml
kubectl apply -f api-canary.yaml
kubectl apply -f api-service.yaml

# Verify initial distribution
kubectl get pods -l app=api --show-labels
echo "Initial distribution: 9 stable (90%), 1 canary (10%)"

# Scale for new distribution
kubectl scale deployment api-stable --replicas=7
kubectl scale deployment api-canary --replicas=3

# Verify new distribution
kubectl get pods -l app=api --show-labels
echo "New distribution: 7 stable (70%), 3 canary (30%)"

# Show endpoints
kubectl get endpoints api-service
```
</details>

---

## Question 15 (5 points)
**Topic**: Helm Testing and Validation  
**Time**: 4 minutes

Working with Helm chart testing:

1. Create a simple Helm chart named `test-app`
2. Add a test that verifies the service responds correctly
3. Add a test that checks if the deployment has the correct number of replicas
4. Run the tests after installation
5. Show test results

Save test files in `/tmp/helm-tests/`

<details>
<summary>Solution</summary>

```bash
# Create chart
mkdir -p /tmp/helm-tests
cd /tmp/helm-tests
helm create test-app

# Create service test
mkdir -p test-app/templates/tests
cat << EOF > test-app/templates/tests/service-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "test-app.fullname" . }}-service-test"
  labels:
    {{- include "test-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  containers:
  - name: service-test
    image: curlimages/curl:latest
    command: ['curl']
    args: ['{{ include "test-app.fullname" . }}:{{ .Values.service.port }}']
EOF

# Create replica test
cat << EOF > test-app/templates/tests/replica-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "test-app.fullname" . }}-replica-test"
  labels:
    {{- include "test-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  containers:
  - name: replica-test
    image: bitnami/kubectl:latest
    command: ['/bin/bash']
    args:
      - -c
      - |
        REPLICAS=\$(kubectl get deployment {{ include "test-app.fullname" . }} -o jsonpath='{.status.readyReplicas}')
        if [ "\$REPLICAS" = "{{ .Values.replicaCount }}" ]; then
          echo "Replica count test passed: \$REPLICAS replicas"
          exit 0
        else
          echo "Replica count test failed: expected {{ .Values.replicaCount }}, got \$REPLICAS"
          exit 1
        fi
  serviceAccountName: {{ include "test-app.serviceAccountName" . }}
EOF

# Install chart
helm install test-app ./test-app

# Wait for deployment
kubectl wait --for=condition=available deployment/test-app --timeout=60s

# Run tests
helm test test-app

# Show test results
kubectl logs -l "helm.sh/hook=test"
```
</details>

---

## Scoring Guide

**Excellent (90-100%)**: 14-15 correct answers
- Deep understanding of all deployment concepts
- Efficient use of kubectl and Helm commands
- Clean, well-structured YAML files
- Proper troubleshooting methodology

**Good (80-89%)**: 12-13 correct answers  
- Solid grasp of most deployment concepts
- Minor syntax errors or inefficiencies
- Generally correct approach to problems

**Satisfactory (70-79%)**: 11 correct answers
- Basic understanding of deployments
- Some gaps in advanced concepts
- Functional but not optimal solutions

**Needs Improvement (<70%)**: 10 or fewer correct answers
- Significant gaps in understanding
- Frequent syntax errors
- Inability to complete complex scenarios

## Key Topics Covered

1. **Basic Deployments** - Creation, configuration, resource management
2. **Rolling Updates** - Update strategies, rollbacks, history management  
3. **Scaling** - Manual scaling, ReplicaSet management
4. **Deployment Strategies** - Blue-Green, Canary deployments
5. **Helm Basics** - Repository management, chart installation
6. **Helm Advanced** - Custom values, chart creation, dependencies
7. **Troubleshooting** - Problem identification and resolution
8. **Multi-container** - Sidecar patterns, shared volumes
9. **Testing** - Helm tests, validation procedures

This exam comprehensively tests the Application Deployment domain of the CKAD certification, covering 20% of the exam content with practical, hands-on scenarios.