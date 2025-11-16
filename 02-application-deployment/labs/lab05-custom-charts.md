# Lab 5: Custom Helm Charts

**Objective**: Create, customize, and manage your own Helm charts
**Time**: 45 minutes
**Difficulty**: Intermediate

## Learning Goals

- Create custom Helm charts from scratch
- Understand chart structure and templating
- Work with templates, values, and helpers
- Implement chart hooks and tests
- Package and share charts
- Handle dependencies and subcharts

## [Exercise 1: Creating Your First Chart (15 minutes)](/02-application-deployment/labs/lab05-solution/exercise-01/)

### Task 1.1: Generate Chart Scaffold

```bash
# Create a new chart
helm create my-web-app

# Examine the generated structure
ls -la my-web-app/
tree my-web-app/ || find my-web-app -type f

# Look at the main files
cat my-web-app/Chart.yaml
cat my-web-app/values.yaml
ls my-web-app/templates/
```

### Task 1.2: Understand Chart.yaml

```yaml
# Edit Chart.yaml
cat << EOF > my-web-app/Chart.yaml
apiVersion: v2
name: my-web-app
description: A custom Helm chart for a web application
type: application
version: 0.1.0
appVersion: "1.0.0"
home: https://github.com/mycompany/my-web-app
sources:
  - https://github.com/mycompany/my-web-app
maintainers:
  - name: Your Name
    email: your.email@company.com
keywords:
  - web
  - application
  - nginx
annotations:
  category: Infrastructure
EOF
```

### Task 1.3: Customize Default Values

```yaml
# Replace values.yaml with custom values
cat << EOF > my-web-app/values.yaml
# Default values for my-web-app
replicaCount: 2

image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: "1.21"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations: {}

podSecurityContext:
  fsGroup: 2000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: my-web-app.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 100
  targetCPUUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}

# Custom application configuration
app:
  environment: production
  debug: false
  features:
    enableMetrics: true
    enableHealthCheck: true

# Database configuration
database:
  enabled: false
  host: ""
  port: 5432
  name: myapp
  username: myuser
  password: ""
  existingSecret: ""

# Redis configuration  
redis:
  enabled: false
  host: ""
  port: 6379
  password: ""
EOF
```

### Task 1.4: Test Initial Chart

```bash
# Validate the chart
helm lint my-web-app/

# Render templates to see output
helm template my-web-app my-web-app/

# Install the chart
kubectl create namespace custom-charts
helm install my-web-app my-web-app/ --namespace custom-charts

# Check deployment
kubectl get all -n custom-charts
```

## [Exercise 2: Advanced Templating (15 minutes)](/02-application-deployment/labs/lab05-solution/exercise-02/)

### Task 2.1: Create ConfigMap Template

```yaml
# Create templates/configmap.yaml
cat << 'EOF' > my-web-app/templates/configmap.yaml
{{- if .Values.app }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "my-web-app.fullname" . }}-config
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
data:
  # Application configuration
  environment: {{ .Values.app.environment | quote }}
  debug: {{ .Values.app.debug | quote }}
  
  # Feature flags
  {{- if .Values.app.features }}
  enable-metrics: {{ .Values.app.features.enableMetrics | quote }}
  enable-health-check: {{ .Values.app.features.enableHealthCheck | quote }}
  {{- end }}
  
  # Database configuration
  {{- if .Values.database.enabled }}
  database-host: {{ .Values.database.host | quote }}
  database-port: {{ .Values.database.port | quote }}
  database-name: {{ .Values.database.name | quote }}
  {{- end }}
  
  # Redis configuration
  {{- if .Values.redis.enabled }}
  redis-host: {{ .Values.redis.host | quote }}
  redis-port: {{ .Values.redis.port | quote }}
  {{- end }}
{{- end }}
EOF
```

### Task 2.2: Create Secret Template

```yaml
# Create templates/secret.yaml
cat << 'EOF' > my-web-app/templates/secret.yaml
{{- if or .Values.database.enabled .Values.redis.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "my-web-app.fullname" . }}-secret
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
type: Opaque
data:
  {{- if and .Values.database.enabled .Values.database.password }}
  database-password: {{ .Values.database.password | b64enc }}
  {{- end }}
  {{- if and .Values.redis.enabled .Values.redis.password }}
  redis-password: {{ .Values.redis.password | b64enc }}
  {{- end }}
{{- end }}
EOF
```

### Task 2.3: Update Deployment Template

```yaml
# Replace templates/deployment.yaml
cat << 'EOF' > my-web-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-web-app.fullname" . }}
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "my-web-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "my-web-app.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "my-web-app.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          env:
            - name: APP_ENV
              valueFrom:
                configMapKeyRef:
                  name: {{ include "my-web-app.fullname" . }}-config
                  key: environment
            - name: DEBUG
              valueFrom:
                configMapKeyRef:
                  name: {{ include "my-web-app.fullname" . }}-config
                  key: debug
            {{- if .Values.database.enabled }}
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: {{ include "my-web-app.fullname" . }}-config
                  key: database-host
            - name: DB_USER
              value: {{ .Values.database.username | quote }}
            {{- if .Values.database.password }}
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ include "my-web-app.fullname" . }}-secret
                  key: database-password
            {{- end }}
            {{- end }}
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
EOF
```

### Task 2.4: Create HPA Template

```yaml
# Create templates/hpa.yaml
cat << 'EOF' > my-web-app/templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "my-web-app.fullname" . }}
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "my-web-app.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
EOF
```

## [Exercise 3: Chart Hooks and Tests (10 minutes)](/02-application-deployment/labs/lab05-solution/exercise-03/)

### Task 3.1: Create Pre-Install Hook

```yaml
# Create templates/pre-install-job.yaml
cat << 'EOF' > my-web-app/templates/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "my-web-app.fullname" . }}-pre-install
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: {{ include "my-web-app.fullname" . }}-pre-install
      labels:
        {{- include "my-web-app.selectorLabels" . | nindent 8 }}
    spec:
      restartPolicy: Never
      containers:
      - name: pre-install
        image: busybox:1.35
        command:
        - /bin/sh
        - -c
        - |
          echo "Pre-install hook: Preparing environment..."
          echo "Checking prerequisites..."
          echo "Environment: {{ .Values.app.environment }}"
          {{- if .Values.database.enabled }}
          echo "Database will be configured"
          {{- end }}
          {{- if .Values.redis.enabled }}
          echo "Redis will be configured"
          {{- end }}
          echo "Pre-install hook completed successfully"
EOF
```

### Task 3.2: Create Test Hook

```yaml
# Create templates/tests/test-connection.yaml
mkdir -p my-web-app/templates/tests

cat << 'EOF' > my-web-app/templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "my-web-app.fullname" . }}-test-connection"
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
spec:
  restartPolicy: Never
  containers:
    - name: wget
      image: busybox:1.35
      command: ['wget']
      args: ['{{ include "my-web-app.fullname" . }}:{{ .Values.service.port }}']
    - name: curl-test
      image: curlimages/curl:latest
      command: ['curl']
      args: 
        - --fail
        - --retry
        - "3"
        - http://{{ include "my-web-app.fullname" . }}:{{ .Values.service.port }}/
EOF
```

### Task 3.3: Create Post-Install Hook

```yaml
# Create templates/post-install-job.yaml
cat << 'EOF' > my-web-app/templates/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "my-web-app.fullname" . }}-post-install
  labels:
    {{- include "my-web-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "1"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: {{ include "my-web-app.fullname" . }}-post-install
      labels:
        {{- include "my-web-app.selectorLabels" . | nindent 8 }}
    spec:
      restartPolicy: Never
      containers:
      - name: post-install
        image: curlimages/curl:latest
        command:
        - /bin/sh
        - -c
        - |
          echo "Post-install hook: Verifying deployment..."
          
          # Wait for service to be ready
          sleep 30
          
          # Test application health
          if curl -f http://{{ include "my-web-app.fullname" . }}:{{ .Values.service.port }}/; then
            echo "Application is responding correctly"
          else
            echo "Application health check failed"
            exit 1
          fi
          
          echo "Post-install hook completed successfully"
EOF
```

## [Exercise 4: Chart Dependencies and Packaging (5 minutes)](/02-application-deployment/labs/lab05-solution/exercise-04/)

### Task 4.1: Add Chart Dependencies

```yaml
# Update Chart.yaml with dependencies
cat << EOF >> my-web-app/Chart.yaml

dependencies:
  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: database.enabled
    alias: postgres
EOF
```

### Task 4.2: Update Dependencies

```bash
# Add Bitnami repository if not already added
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Update chart dependencies
helm dependency update my-web-app/

# Check downloaded dependencies
ls my-web-app/charts/
```

### Task 4.3: Package the Chart

```bash
# Lint the chart
helm lint my-web-app/

# Package the chart
helm package my-web-app/

# List packaged chart
ls *.tgz
```

## [Exercise 5: Testing Custom Chart (Bonus)](/02-application-deployment/labs/lab05-solution/exercise-05/)

### Task 5.1: Test with Custom Values

```yaml
# Create test values
cat << EOF > custom-test-values.yaml
replicaCount: 3

app:
  environment: testing
  debug: true
  features:
    enableMetrics: true
    enableHealthCheck: true

database:
  enabled: true
  host: postgres-service
  name: testdb
  username: testuser
  password: testpass

redis:
  enabled: true
  host: redis-service

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
EOF
```

### Task 5.2: Deploy with Dependencies

```bash
# Install with dependencies
helm install my-test-app my-web-app/ \
  --namespace custom-charts \
  --values custom-test-values.yaml

# Check all resources
kubectl get all -n custom-charts

# Check configmaps and secrets
kubectl get configmaps -n custom-charts
kubectl get secrets -n custom-charts

# Check dependency deployments
kubectl get deployments -n custom-charts
```

### Task 5.3: Run Chart Tests

```bash
# Run chart tests
helm test my-test-app --namespace custom-charts

# Check test results
kubectl get pods -n custom-charts -l "helm.sh/hook=test"

# View test logs
kubectl logs -n custom-charts -l "helm.sh/hook=test"
```

## Lab Validation

### Validation Commands

```bash
# Check chart structure
helm lint my-web-app/

# Verify templates render correctly
helm template test-release my-web-app/ --values custom-test-values.yaml

# Check deployed resources
kubectl get all -n custom-charts

# Verify hooks executed
kubectl get events -n custom-charts --sort-by=.metadata.creationTimestamp

# Check application logs
kubectl logs -n custom-charts deployment/my-test-app-my-web-app
```

### Template Testing

```bash
# Test specific template rendering
helm template my-web-app my-web-app/ \
  --show-only templates/configmap.yaml \
  --values custom-test-values.yaml

# Test with different value combinations
helm template my-web-app my-web-app/ \
  --set app.environment=production \
  --set database.enabled=false \
  --set redis.enabled=false
```

## Troubleshooting

### Common Template Issues

```bash
# Debug template rendering
helm template my-web-app my-web-app/ --debug

# Check for syntax errors
helm lint my-web-app/

# Validate against Kubernetes
helm template my-web-app my-web-app/ | kubectl apply --dry-run=client -f -
```

### Dependency Issues

```bash
# Clean dependencies
rm -rf my-web-app/charts/
rm my-web-app/Chart.lock

# Re-download dependencies
helm dependency update my-web-app/
```

## Cleanup

```bash
# Uninstall releases
helm uninstall my-web-app --namespace custom-charts
helm uninstall my-test-app --namespace custom-charts

# Delete namespace
kubectl delete namespace custom-charts

# Clean up files
rm -rf my-web-app/
rm *.tgz
rm custom-test-values.yaml
```

## Key Takeaways

1. **Chart structure** follows a standard directory layout
2. **Templates** use Go templating with Sprig functions
3. **Values** provide configuration abstraction
4. **Hooks** enable lifecycle management
5. **Dependencies** allow chart composition
6. **Testing** ensures chart reliability

## Best Practices

1. Use semantic versioning for charts
2. Document all values in comments
3. Include helpful defaults
4. Use hooks for setup/teardown tasks
5. Test charts thoroughly
6. Include meaningful labels and annotations

## Common CKAD Tasks

```bash
# 1. Create chart
helm create myapp

# 2. Add template logic
# Edit templates with {{ if .Values.feature.enabled }}

# 3. Package chart
helm package myapp/

# 4. Install custom chart
helm install release ./myapp

# 5. Upgrade with values
helm upgrade release ./myapp --values custom-values.yaml

# 6. Test chart
helm test release
```