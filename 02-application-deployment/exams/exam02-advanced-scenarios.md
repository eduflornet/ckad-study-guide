# Mock Exam 2: Advanced Application Deployment

**Exam Duration**: 50 minutes  
**Total Questions**: 12  
**Passing Score**: 75% (9/12 correct)  
**Exam Focus**: Advanced Application Deployment Scenarios

---

## Instructions

- You have 50 minutes to complete 12 questions
- Each question varies in complexity and point value
- Use official Kubernetes and Helm documentation as needed
- All work must be performed in the provided cluster
- Save YAML files as requested for verification
- Some questions build upon previous answers

---

## Question 1 (6 points)
**Topic**: Multi-Environment Deployment Strategy  
**Time**: 5 minutes

Create a deployment strategy that supports multiple environments using labels and namespaces:

1. Create namespaces: `development`, `staging`, `production`
2. Deploy the same application (`webapp`) in all three environments with different configurations:
   - **Development**: 1 replica, image `nginx:1.20-alpine`, resources requests: 50m CPU, 64Mi memory
   - **Staging**: 2 replicas, image `nginx:1.21-alpine`, resources requests: 100m CPU, 128Mi memory  
   - **Production**: 5 replicas, image `nginx:1.21`, resources requests: 200m CPU, 256Mi memory
3. Add environment-specific labels and annotations
4. Create a script that can deploy to any environment with parameters

Save all files to `/tmp/multi-env/`

<details>
<summary>Solution</summary>

```bash
# Create directory structure
mkdir -p /tmp/multi-env/{development,staging,production}

# Create namespaces
kubectl create namespace development
kubectl create namespace staging  
kubectl create namespace production

# Create base deployment template
cat << 'EOF' > /tmp/multi-env/webapp-template.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: ${ENVIRONMENT}
  labels:
    app: webapp
    environment: ${ENVIRONMENT}
    version: ${VERSION}
  annotations:
    deployment.kubernetes.io/revision: "1"
    meta.helm.sh/release-name: webapp-${ENVIRONMENT}
spec:
  replicas: ${REPLICAS}
  selector:
    matchLabels:
      app: webapp
      environment: ${ENVIRONMENT}
  template:
    metadata:
      labels:
        app: webapp
        environment: ${ENVIRONMENT}
        version: ${VERSION}
    spec:
      containers:
      - name: webapp
        image: ${IMAGE}
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: ${CPU_REQUEST}
            memory: ${MEMORY_REQUEST}
          limits:
            cpu: ${CPU_LIMIT}
            memory: ${MEMORY_LIMIT}
        env:
        - name: ENVIRONMENT
          value: ${ENVIRONMENT}
        - name: VERSION
          value: ${VERSION}
EOF

# Create environment-specific deployments
# Development
cat << EOF > /tmp/multi-env/development/webapp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: development
  labels:
    app: webapp
    environment: development
    version: v1.20
  annotations:
    deployment.kubernetes.io/revision: "1"
    meta.helm.sh/release-name: webapp-development
spec:
  replicas: 1
  selector:
    matchLabels:
      app: webapp
      environment: development
  template:
    metadata:
      labels:
        app: webapp
        environment: development
        version: v1.20
    spec:
      containers:
      - name: webapp
        image: nginx:1.20-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
        env:
        - name: ENVIRONMENT
          value: development
        - name: VERSION
          value: v1.20
        - name: DEBUG
          value: "true"
EOF

# Staging
cat << EOF > /tmp/multi-env/staging/webapp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: staging
  labels:
    app: webapp
    environment: staging
    version: v1.21
  annotations:
    deployment.kubernetes.io/revision: "1"
    meta.helm.sh/release-name: webapp-staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
      environment: staging
  template:
    metadata:
      labels:
        app: webapp
        environment: staging
        version: v1.21
    spec:
      containers:
      - name: webapp
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        env:
        - name: ENVIRONMENT
          value: staging
        - name: VERSION
          value: v1.21
        - name: DEBUG
          value: "false"
EOF

# Production
cat << EOF > /tmp/multi-env/production/webapp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: production
  labels:
    app: webapp
    environment: production
    version: v1.21
  annotations:
    deployment.kubernetes.io/revision: "1"
    meta.helm.sh/release-name: webapp-production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: webapp
      environment: production
  template:
    metadata:
      labels:
        app: webapp
        environment: production
        version: v1.21
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 400m
            memory: 512Mi
        env:
        - name: ENVIRONMENT
          value: production
        - name: VERSION
          value: v1.21
        - name: DEBUG
          value: "false"
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
EOF

# Create deployment script
cat << 'EOF' > /tmp/multi-env/deploy.sh
#!/bin/bash

ENVIRONMENT=$1
ACTION=${2:-apply}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [apply|delete]"
    echo "Environments: development, staging, production"
    exit 1
fi

if [ ! -d "$ENVIRONMENT" ]; then
    echo "Environment '$ENVIRONMENT' not found"
    exit 1
fi

echo "Performing $ACTION on $ENVIRONMENT environment..."

if [ "$ACTION" = "apply" ]; then
    kubectl apply -f $ENVIRONMENT/
    kubectl rollout status deployment/webapp -n $ENVIRONMENT
elif [ "$ACTION" = "delete" ]; then
    kubectl delete -f $ENVIRONMENT/
else
    echo "Invalid action: $ACTION"
    exit 1
fi

echo "Operation completed for $ENVIRONMENT"
EOF

chmod +x /tmp/multi-env/deploy.sh

# Deploy to all environments
/tmp/multi-env/deploy.sh development
/tmp/multi-env/deploy.sh staging
/tmp/multi-env/deploy.sh production

# Verify deployments
kubectl get deployments -A | grep webapp
kubectl get pods -A | grep webapp
```
</details>

---

## Question 2 (8 points)
**Topic**: Advanced Helm Chart with Dependencies  
**Time**: 7 minutes

Create a complex Helm chart for a microservices e-commerce application:

1. Chart name: `ecommerce-stack`
2. Include dependencies: PostgreSQL, Redis, and RabbitMQ from Bitnami
3. Create three microservices: `user-service`, `product-service`, `order-service`
4. Each service should have configurable replicas, resources, and environment variables
5. Add conditional deployment based on feature flags
6. Include proper service discovery configuration
7. Add ingress configuration for external access

Save chart to `/tmp/ecommerce-stack/`

<details>
<summary>Solution</summary>

```bash
# Create Helm chart
mkdir -p /tmp/ecommerce-stack
cd /tmp/ecommerce-stack
helm create ecommerce-stack

# Clean up default files
rm -rf ecommerce-stack/templates/*
rm ecommerce-stack/values.yaml

# Create Chart.yaml with dependencies
cat << EOF > ecommerce-stack/Chart.yaml
apiVersion: v2
name: ecommerce-stack
description: Complete e-commerce microservices stack
type: application
version: 0.2.0
appVersion: "2.0"
keywords:
  - ecommerce
  - microservices
  - kubernetes

dependencies:
  - name: postgresql
    version: "12.1.9"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
  - name: redis
    version: "17.3.7"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
  - name: rabbitmq
    version: "11.1.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: rabbitmq.enabled
EOF

# Create comprehensive values.yaml
cat << EOF > ecommerce-stack/values.yaml
# Global configuration
global:
  imageRegistry: docker.io
  imagePullSecrets: []

# Feature flags
features:
  userService: true
  productService: true
  orderService: true
  ingress: true
  monitoring: false

# Service configurations
userService:
  enabled: true
  replicaCount: 3
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3001
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  env:
    NODE_ENV: production
    JWT_SECRET: supersecretkey
    DATABASE_URL: ""

productService:
  enabled: true
  replicaCount: 4
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3002
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 800m
      memory: 1Gi
  env:
    NODE_ENV: production
    REDIS_URL: ""
    ELASTICSEARCH_URL: ""

orderService:
  enabled: true
  replicaCount: 3
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3003
  resources:
    requests:
      cpu: 150m
      memory: 256Mi
    limits:
      cpu: 600m
      memory: 768Mi
  env:
    NODE_ENV: production
    RABBITMQ_URL: ""
    PAYMENT_GATEWAY_URL: ""

# Dependencies configuration
postgresql:
  enabled: true
  auth:
    postgresPassword: "postgres123"
    username: "ecommerce"
    password: "ecommerce123"
    database: "ecommerce"

redis:
  enabled: true
  auth:
    enabled: true
    password: "redis123"

rabbitmq:
  enabled: true
  auth:
    username: "ecommerce"
    password: "rabbitmq123"

# Ingress configuration
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
  hosts:
    - host: ecommerce.local
      paths:
        - path: /api/users
          pathType: Prefix
          service: user-service
        - path: /api/products
          pathType: Prefix
          service: product-service
        - path: /api/orders
          pathType: Prefix
          service: order-service
EOF

# Create helper templates
cat << 'EOF' > ecommerce-stack/templates/_helpers.tpl
{{- define "ecommerce.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ecommerce.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "ecommerce.labels" -}}
helm.sh/chart: {{ include "ecommerce.chart" . }}
{{ include "ecommerce.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "ecommerce.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ecommerce.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "ecommerce.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ecommerce.serviceLabels" -}}
{{ include "ecommerce.labels" . }}
app.kubernetes.io/component: {{ .component }}
{{- end }}
EOF

# Create ConfigMap
cat << 'EOF' > ecommerce-stack/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ecommerce.fullname" . }}-config
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
data:
  {{- if .Values.postgresql.enabled }}
  DATABASE_URL: "postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "ecommerce.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}"
  {{- end }}
  {{- if .Values.redis.enabled }}
  REDIS_URL: "redis://:{{ .Values.redis.auth.password }}@{{ include "ecommerce.fullname" . }}-redis-master:6379"
  {{- end }}
  {{- if .Values.rabbitmq.enabled }}
  RABBITMQ_URL: "amqp://{{ .Values.rabbitmq.auth.username }}:{{ .Values.rabbitmq.auth.password }}@{{ include "ecommerce.fullname" . }}-rabbitmq:5672"
  {{- end }}
  USER_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-user-service:{{ .Values.userService.service.port }}"
  PRODUCT_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-product-service:{{ .Values.productService.service.port }}"
  ORDER_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-order-service:{{ .Values.orderService.service.port }}"
EOF

# Create User Service deployment
cat << 'EOF' > ecommerce-stack/templates/user-service.yaml
{{- if and .Values.features.userService .Values.userService.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ecommerce.fullname" . }}-user-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "user-service") | nindent 4 }}
spec:
  replicas: {{ .Values.userService.replicaCount }}
  selector:
    matchLabels:
      {{- include "ecommerce.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: user-service
  template:
    metadata:
      labels:
        {{- include "ecommerce.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: user-service
    spec:
      containers:
      - name: user-service
        image: "{{ .Values.userService.image.repository }}:{{ .Values.userService.image.tag }}"
        ports:
        - name: http
          containerPort: {{ .Values.userService.service.port }}
        env:
        {{- range $key, $value := .Values.userService.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        envFrom:
        - configMapRef:
            name: {{ include "ecommerce.fullname" . }}-config
        resources:
          {{- toYaml .Values.userService.resources | nindent 10 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ecommerce.fullname" . }}-user-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "user-service") | nindent 4 }}
spec:
  type: {{ .Values.userService.service.type }}
  ports:
  - port: {{ .Values.userService.service.port }}
    targetPort: http
    name: http
  selector:
    {{- include "ecommerce.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: user-service
{{- end }}
EOF

# Create Product Service deployment
cat << 'EOF' > ecommerce-stack/templates/product-service.yaml
{{- if and .Values.features.productService .Values.productService.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ecommerce.fullname" . }}-product-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "product-service") | nindent 4 }}
spec:
  replicas: {{ .Values.productService.replicaCount }}
  selector:
    matchLabels:
      {{- include "ecommerce.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: product-service
  template:
    metadata:
      labels:
        {{- include "ecommerce.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: product-service
    spec:
      containers:
      - name: product-service
        image: "{{ .Values.productService.image.repository }}:{{ .Values.productService.image.tag }}"
        ports:
        - name: http
          containerPort: {{ .Values.productService.service.port }}
        env:
        {{- range $key, $value := .Values.productService.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        envFrom:
        - configMapRef:
            name: {{ include "ecommerce.fullname" . }}-config
        resources:
          {{- toYaml .Values.productService.resources | nindent 10 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ecommerce.fullname" . }}-product-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "product-service") | nindent 4 }}
spec:
  type: {{ .Values.productService.service.type }}
  ports:
  - port: {{ .Values.productService.service.port }}
    targetPort: http
    name: http
  selector:
    {{- include "ecommerce.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: product-service
{{- end }}
EOF

# Create Order Service deployment
cat << 'EOF' > ecommerce-stack/templates/order-service.yaml
{{- if and .Values.features.orderService .Values.orderService.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ecommerce.fullname" . }}-order-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "order-service") | nindent 4 }}
spec:
  replicas: {{ .Values.orderService.replicaCount }}
  selector:
    matchLabels:
      {{- include "ecommerce.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: order-service
  template:
    metadata:
      labels:
        {{- include "ecommerce.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: order-service
    spec:
      containers:
      - name: order-service
        image: "{{ .Values.orderService.image.repository }}:{{ .Values.orderService.image.tag }}"
        ports:
        - name: http
          containerPort: {{ .Values.orderService.service.port }}
        env:
        {{- range $key, $value := .Values.orderService.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        envFrom:
        - configMapRef:
            name: {{ include "ecommerce.fullname" . }}-config
        resources:
          {{- toYaml .Values.orderService.resources | nindent 10 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ecommerce.fullname" . }}-order-service
  labels:
    {{- include "ecommerce.serviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "order-service") | nindent 4 }}
spec:
  type: {{ .Values.orderService.service.type }}
  ports:
  - port: {{ .Values.orderService.service.port }}
    targetPort: http
    name: http
  selector:
    {{- include "ecommerce.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: order-service
{{- end }}
EOF

# Create Ingress
cat << 'EOF' > ecommerce-stack/templates/ingress.yaml
{{- if and .Values.features.ingress .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "ecommerce.fullname" . }}-ingress
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  rules:
  {{- range .Values.ingress.hosts }}
  - host: {{ .host | quote }}
    http:
      paths:
      {{- range .paths }}
      - path: {{ .path }}
        pathType: {{ .pathType }}
        backend:
          service:
            name: {{ include "ecommerce.fullname" $ }}-{{ .service }}
            port:
              number: {{ index $.Values (.service | replace "-" "" | lower) "service" "port" }}
      {{- end }}
  {{- end }}
{{- end }}
EOF

# Add repositories and update dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Build dependencies
helm dependency build ecommerce-stack

# Install the chart
helm install ecommerce-stack ./ecommerce-stack --create-namespace --namespace ecommerce

# Verify installation
helm list -n ecommerce
kubectl get all -n ecommerce
```
</details>

---

## Question 3 (7 points)
**Topic**: Automated Deployment Pipeline  
**Time**: 6 minutes

Create an automated deployment pipeline using Kubernetes Jobs:

1. Create a Job that builds and deploys an application
2. Job should validate the previous deployment before deploying new version
3. Include rollback capability if validation fails
4. Add notification mechanisms (using ConfigMap for webhook URLs)
5. Create a CronJob that performs regular health checks
6. Implement progressive deployment (10% -> 50% -> 100% traffic)

Save all resources to `/tmp/deployment-pipeline/`

<details>
<summary>Solution</summary>

```bash
# Create directory
mkdir -p /tmp/deployment-pipeline

# Create namespace
kubectl create namespace deployment-pipeline

# Create notification ConfigMap
cat << EOF > /tmp/deployment-pipeline/notification-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: notification-config
  namespace: deployment-pipeline
data:
  slack_webhook: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  email_smtp: "smtp.company.com:587"
  deployment_channel: "#deployments"
  alert_channel: "#alerts"
EOF

# Create deployment validation Job
cat << EOF > /tmp/deployment-pipeline/validation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: deployment-validator
  namespace: deployment-pipeline
  labels:
    app: deployment-pipeline
    component: validator
spec:
  template:
    metadata:
      labels:
        app: deployment-pipeline
        component: validator
    spec:
      restartPolicy: Never
      containers:
      - name: validator
        image: curlimages/curl:latest
        command:
        - sh
        - -c
        - |
          echo "Starting deployment validation..."
          
          # Check if previous deployment exists
          if kubectl get deployment webapp -n deployment-pipeline 2>/dev/null; then
            echo "Previous deployment found, validating health..."
            
            # Port forward to test the service
            kubectl port-forward svc/webapp-service 8080:80 -n deployment-pipeline &
            PF_PID=\$!
            sleep 5
            
            # Health check
            if curl -f http://localhost:8080/health; then
              echo "Previous deployment is healthy"
              kill \$PF_PID
              exit 0
            else
              echo "Previous deployment failed health check"
              kill \$PF_PID
              exit 1
            fi
          else
            echo "No previous deployment found, proceeding..."
            exit 0
          fi
      serviceAccountName: deployment-pipeline-sa
EOF

# Create progressive deployment Job
cat << EOF > /tmp/deployment-pipeline/progressive-deploy-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: progressive-deployer
  namespace: deployment-pipeline
  labels:
    app: deployment-pipeline
    component: deployer
spec:
  template:
    metadata:
      labels:
        app: deployment-pipeline
        component: deployer
    spec:
      restartPolicy: Never
      containers:
      - name: deployer
        image: bitnami/kubectl:latest
        command:
        - sh
        - -c
        - |
          echo "Starting progressive deployment..."
          
          NEW_VERSION=\${NEW_VERSION:-v2.0}
          STAGES=(10 50 100)
          
          # Create or update canary deployment
          cat << CANARY_EOF | kubectl apply -f -
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: webapp-canary
            namespace: deployment-pipeline
            labels:
              app: webapp
              version: canary
          spec:
            replicas: 1
            selector:
              matchLabels:
                app: webapp
                version: canary
            template:
              metadata:
                labels:
                  app: webapp
                  version: canary
              spec:
                containers:
                - name: webapp
                  image: nginx:\$NEW_VERSION
                  ports:
                  - containerPort: 80
                  readinessProbe:
                    httpGet:
                      path: /
                      port: 80
                    initialDelaySeconds: 5
                    periodSeconds: 5
          CANARY_EOF
          
          # Wait for canary to be ready
          kubectl wait --for=condition=available deployment/webapp-canary -n deployment-pipeline --timeout=120s
          
          # Progressive traffic shifting
          for stage in "\${STAGES[@]}"; do
            echo "Shifting \$stage% traffic to canary..."
            
            # Calculate replicas (total 10 replicas for easy percentage)
            canary_replicas=\$((10 * stage / 100))
            stable_replicas=\$((10 - canary_replicas))
            
            # Scale deployments
            kubectl scale deployment webapp-canary --replicas=\$canary_replicas -n deployment-pipeline
            if kubectl get deployment webapp -n deployment-pipeline 2>/dev/null; then
              kubectl scale deployment webapp --replicas=\$stable_replicas -n deployment-pipeline
            fi
            
            # Wait and validate
            sleep 30
            
            # Health check canary
            kubectl port-forward svc/webapp-service 8080:80 -n deployment-pipeline &
            PF_PID=\$!
            sleep 5
            
            if curl -f http://localhost:8080/; then
              echo "Stage \$stage% validation passed"
              kill \$PF_PID
            else
              echo "Stage \$stage% validation failed, rolling back..."
              kubectl scale deployment webapp-canary --replicas=0 -n deployment-pipeline
              if kubectl get deployment webapp -n deployment-pipeline 2>/dev/null; then
                kubectl scale deployment webapp --replicas=10 -n deployment-pipeline
              fi
              kill \$PF_PID
              exit 1
            fi
            
            if [ "\$stage" = "100" ]; then
              echo "Deployment successful, promoting canary..."
              # Replace stable with canary
              kubectl delete deployment webapp -n deployment-pipeline --ignore-not-found
              kubectl patch deployment webapp-canary -n deployment-pipeline -p '{"metadata":{"name":"webapp"}}'
            fi
          done
          
          echo "Progressive deployment completed successfully"
        env:
        - name: NEW_VERSION
          value: "1.21"
      serviceAccountName: deployment-pipeline-sa
EOF

# Create health check CronJob
cat << EOF > /tmp/deployment-pipeline/health-check-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: health-checker
  namespace: deployment-pipeline
  labels:
    app: deployment-pipeline
    component: health-checker
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: deployment-pipeline
            component: health-checker
        spec:
          restartPolicy: Never
          containers:
          - name: health-checker
            image: curlimages/curl:latest
            command:
            - sh
            - -c
            - |
              echo "Running scheduled health check..."
              
              # Check if webapp service exists
              if kubectl get service webapp-service -n deployment-pipeline 2>/dev/null; then
                # Port forward and test
                kubectl port-forward svc/webapp-service 8080:80 -n deployment-pipeline &
                PF_PID=\$!
                sleep 5
                
                if curl -f http://localhost:8080/; then
                  echo "Health check passed at \$(date)"
                  # Send success notification (webhook simulation)
                  echo "Sending success notification to webhook..."
                else
                  echo "Health check failed at \$(date)"
                  # Send alert notification
                  echo "Sending alert notification to webhook..."
                  exit 1
                fi
                
                kill \$PF_PID
              else
                echo "No webapp service found, skipping health check"
              fi
          serviceAccountName: deployment-pipeline-sa
EOF

# Create notification Job
cat << EOF > /tmp/deployment-pipeline/notification-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: deployment-notifier
  namespace: deployment-pipeline
  labels:
    app: deployment-pipeline
    component: notifier
spec:
  template:
    metadata:
      labels:
        app: deployment-pipeline
        component: notifier
    spec:
      restartPolicy: Never
      containers:
      - name: notifier
        image: curlimages/curl:latest
        command:
        - sh
        - -c
        - |
          echo "Sending deployment notifications..."
          
          DEPLOYMENT_STATUS=\${DEPLOYMENT_STATUS:-success}
          MESSAGE="Deployment \$DEPLOYMENT_STATUS at \$(date)"
          
          # Simulate webhook notification
          echo "Notification: \$MESSAGE"
          echo "Webhook URL: \$SLACK_WEBHOOK"
          
          # In real scenario, would send actual HTTP request:
          # curl -X POST \$SLACK_WEBHOOK -d "{\"text\":\"\$MESSAGE\"}"
          
          echo "Notification sent successfully"
        envFrom:
        - configMapRef:
            name: notification-config
        env:
        - name: DEPLOYMENT_STATUS
          value: "success"
      serviceAccountName: deployment-pipeline-sa
EOF

# Create ServiceAccount and RBAC
cat << EOF > /tmp/deployment-pipeline/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: deployment-pipeline-sa
  namespace: deployment-pipeline
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: deployment-pipeline
  name: deployment-pipeline-role
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services", "pods", "configmaps"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployment-pipeline-binding
  namespace: deployment-pipeline
subjects:
- kind: ServiceAccount
  name: deployment-pipeline-sa
  namespace: deployment-pipeline
roleRef:
  kind: Role
  name: deployment-pipeline-role
  apiGroup: rbac.authorization.k8s.io
EOF

# Create pipeline orchestrator script
cat << 'EOF' > /tmp/deployment-pipeline/deploy-pipeline.sh
#!/bin/bash

NAMESPACE="deployment-pipeline"
NEW_VERSION=${1:-"1.21"}

echo "Starting deployment pipeline for version $NEW_VERSION..."

# Apply RBAC
kubectl apply -f rbac.yaml

# Apply notification config
kubectl apply -f notification-config.yaml

# Run validation
echo "Step 1: Validating current deployment..."
kubectl apply -f validation-job.yaml
kubectl wait --for=condition=complete job/deployment-validator -n $NAMESPACE --timeout=120s

if kubectl get job deployment-validator -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q True; then
    echo "Validation passed, proceeding with deployment..."
    
    # Run progressive deployment
    echo "Step 2: Starting progressive deployment..."
    sed "s/value: \"1.21\"/value: \"$NEW_VERSION\"/" progressive-deploy-job.yaml | kubectl apply -f -
    kubectl wait --for=condition=complete job/progressive-deployer -n $NAMESPACE --timeout=600s
    
    if kubectl get job progressive-deployer -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q True; then
        echo "Progressive deployment completed successfully"
        
        # Send success notification
        echo "Step 3: Sending success notification..."
        kubectl apply -f notification-job.yaml
        
        # Set up health monitoring
        echo "Step 4: Setting up health monitoring..."
        kubectl apply -f health-check-cronjob.yaml
        
        echo "Deployment pipeline completed successfully!"
    else
        echo "Progressive deployment failed"
        exit 1
    fi
else
    echo "Validation failed, aborting deployment"
    exit 1
fi

# Cleanup old jobs
kubectl delete job deployment-validator progressive-deployer deployment-notifier -n $NAMESPACE --ignore-not-found
EOF

chmod +x /tmp/deployment-pipeline/deploy-pipeline.sh

# Apply all resources
cd /tmp/deployment-pipeline
kubectl apply -f rbac.yaml
kubectl apply -f notification-config.yaml

# Run the pipeline
./deploy-pipeline.sh 1.21

# Verify pipeline components
kubectl get jobs,cronjobs -n deployment-pipeline
kubectl get pods -n deployment-pipeline
```
</details>

---

## Question 4 (5 points)
**Topic**: Rolling Updates with Constraints  
**Time**: 4 minutes

Configure a deployment with specific rolling update constraints:

1. Deployment name: `constrained-app`, image: `nginx:1.20`, replicas: 12
2. Rolling update strategy: maximum 25% unavailable, maximum 50% surge
3. Minimum ready seconds: 45
4. Progress deadline: 300 seconds
5. Update to image `nginx:1.21` and monitor the rollout
6. If rollout fails or takes too long, perform automatic rollback

<details>
<summary>Solution</summary>

```yaml
# Create deployment with rolling update constraints
cat << EOF > constrained-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: constrained-app
  labels:
    app: constrained-app
spec:
  replicas: 12
  minReadySeconds: 45
  progressDeadlineSeconds: 300
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
      maxSurge: 50%
  selector:
    matchLabels:
      app: constrained-app
  template:
    metadata:
      labels:
        app: constrained-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
EOF

# Apply initial deployment
kubectl apply -f constrained-deployment.yaml

# Wait for initial deployment
kubectl rollout status deployment/constrained-app --timeout=600s

# Update with record
kubectl set image deployment/constrained-app nginx=nginx:1.21 --record

# Monitor rollout in background
(
  echo "Monitoring rollout progress..."
  if ! kubectl rollout status deployment/constrained-app --timeout=400s; then
    echo "Rollout failed or timed out, performing automatic rollback..."
    kubectl rollout undo deployment/constrained-app
    kubectl rollout status deployment/constrained-app --timeout=300s
    echo "Rollback completed"
  else
    echo "Rollout completed successfully"
  fi
) &

# Show rollout details
kubectl describe deployment constrained-app
kubectl get pods -l app=constrained-app --watch --timeout=60s &

# Check rollout history
kubectl rollout history deployment/constrained-app

# Verify final state
wait  # Wait for background monitoring to complete
kubectl get deployment constrained-app
kubectl get pods -l app=constrained-app
```
</details>

---

## Question 5 (8 points)
**Topic**: Blue-Green Deployment with Database Migration  
**Time**: 7 minutes

Implement a blue-green deployment that includes database schema migration:

1. Create blue environment with PostgreSQL database and application
2. Create green environment with updated application and database schema
3. Implement database migration job that runs before traffic switch
4. Create traffic switching mechanism using service label selectors
5. Add validation tests for both environments
6. Implement rollback capability that preserves data integrity

Save all manifests to `/tmp/blue-green-db/`

<details>
<summary>Solution</summary>

```bash
# Create directory
mkdir -p /tmp/blue-green-db/{blue,green,migrations,scripts}

# Create namespace
kubectl create namespace blue-green-db

# Create Blue Environment - Database
cat << EOF > /tmp/blue-green-db/blue/database.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-blue
  namespace: blue-green-db
  labels:
    app: postgres
    environment: blue
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
      environment: blue
  template:
    metadata:
      labels:
        app: postgres
        environment: blue
    spec:
      containers:
      - name: postgres
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: "appdb"
        - name: POSTGRES_USER
          value: "appuser"
        - name: POSTGRES_PASSWORD
          value: "apppass"
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: postgres-storage
        emptyDir: {}
      - name: init-scripts
        configMap:
          name: db-init-scripts
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-blue-service
  namespace: blue-green-db
  labels:
    app: postgres
    environment: blue
spec:
  selector:
    app: postgres
    environment: blue
  ports:
  - port: 5432
    targetPort: 5432
EOF

# Create Blue Environment - Application
cat << EOF > /tmp/blue-green-db/blue/application.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-blue
  namespace: blue-green-db
  labels:
    app: webapp
    environment: blue
    version: v1.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      environment: blue
  template:
    metadata:
      labels:
        app: webapp
        environment: blue
        version: v1.0
    spec:
      containers:
      - name: webapp
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          value: "postgresql://appuser:apppass@postgres-blue-service:5432/appdb"
        - name: ENVIRONMENT
          value: "blue"
        - name: VERSION
          value: "v1.0"
        command:
        - sh
        - -c
        - |
          cat << 'NODEAPP' > app.js
          const express = require('express');
          const app = express();
          const port = 3000;
          
          app.use(express.json());
          
          app.get('/', (req, res) => {
            res.json({
              environment: process.env.ENVIRONMENT,
              version: process.env.VERSION,
              database: process.env.DATABASE_URL.split('@')[1],
              timestamp: new Date().toISOString()
            });
          });
          
          app.get('/health', (req, res) => {
            res.json({ status: 'healthy', environment: process.env.ENVIRONMENT });
          });
          
          // Legacy API endpoint
          app.get('/api/users', (req, res) => {
            res.json([
              { id: 1, name: 'John Doe', email: 'john@example.com' },
              { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
            ]);
          });
          
          app.listen(port, () => {
            console.log(\`Blue app listening on port \${port}\`);
          });
          NODEAPP
          
          npm init -y
          npm install express
          node app.js
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-blue-service
  namespace: blue-green-db
  labels:
    app: webapp
    environment: blue
spec:
  selector:
    app: webapp
    environment: blue
  ports:
  - port: 80
    targetPort: 3000
EOF

# Create database initialization scripts
cat << EOF > /tmp/blue-green-db/db-init-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-init-scripts
  namespace: blue-green-db
data:
  01-init.sql: |
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      name VARCHAR(100) NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com')
    ON CONFLICT (email) DO NOTHING;
  
  02-schema-v1.sql: |
    -- Version 1 schema
    CREATE TABLE IF NOT EXISTS app_config (
      key VARCHAR(50) PRIMARY KEY,
      value TEXT,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO app_config (key, value) VALUES
    ('schema_version', '1.0'),
    ('app_name', 'Blue-Green Demo')
    ON CONFLICT (key) DO NOTHING;
EOF

# Create Green Environment - Database Migration
cat << EOF > /tmp/blue-green-db/migrations/migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-v2
  namespace: blue-green-db
  labels:
    app: migration
    version: v2.0
spec:
  template:
    metadata:
      labels:
        app: migration
        version: v2.0
    spec:
      restartPolicy: Never
      containers:
      - name: migrator
        image: postgres:14
        env:
        - name: PGHOST
          value: "postgres-blue-service"
        - name: PGDATABASE
          value: "appdb"
        - name: PGUSER
          value: "appuser"
        - name: PGPASSWORD
          value: "apppass"
        command:
        - sh
        - -c
        - |
          echo "Starting database migration to v2.0..."
          
          # Check current schema version
          CURRENT_VERSION=\$(psql -t -c "SELECT value FROM app_config WHERE key='schema_version';" | xargs)
          echo "Current schema version: \$CURRENT_VERSION"
          
          if [ "\$CURRENT_VERSION" = "1.0" ]; then
            echo "Migrating from v1.0 to v2.0..."
            
            # Add new columns
            psql -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);"
            psql -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';"
            
            # Create new table
            psql -c "CREATE TABLE IF NOT EXISTS user_profiles (
              id SERIAL PRIMARY KEY,
              user_id INTEGER REFERENCES users(id),
              bio TEXT,
              preferences JSONB,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"
            
            # Update schema version
            psql -c "UPDATE app_config SET value='2.0', updated_at=CURRENT_TIMESTAMP WHERE key='schema_version';"
            
            echo "Migration completed successfully"
          else
            echo "Schema is already at version \$CURRENT_VERSION or higher"
          fi
          
          # Verify migration
          psql -c "SELECT * FROM app_config WHERE key='schema_version';"
          psql -c "\d users"
EOF

# Create Green Environment - Updated Application
cat << EOF > /tmp/blue-green-db/green/application.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-green
  namespace: blue-green-db
  labels:
    app: webapp
    environment: green
    version: v2.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      environment: green
  template:
    metadata:
      labels:
        app: webapp
        environment: green
        version: v2.0
    spec:
      containers:
      - name: webapp
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          value: "postgresql://appuser:apppass@postgres-blue-service:5432/appdb"
        - name: ENVIRONMENT
          value: "green"
        - name: VERSION
          value: "v2.0"
        command:
        - sh
        - -c
        - |
          cat << 'NODEAPP' > app.js
          const express = require('express');
          const app = express();
          const port = 3000;
          
          app.use(express.json());
          
          app.get('/', (req, res) => {
            res.json({
              environment: process.env.ENVIRONMENT,
              version: process.env.VERSION,
              database: process.env.DATABASE_URL.split('@')[1],
              timestamp: new Date().toISOString(),
              features: ['enhanced_api', 'user_profiles', 'phone_support']
            });
          });
          
          app.get('/health', (req, res) => {
            res.json({ 
              status: 'healthy', 
              environment: process.env.ENVIRONMENT,
              version: process.env.VERSION
            });
          });
          
          // Enhanced API endpoints
          app.get('/api/users', (req, res) => {
            res.json([
              { 
                id: 1, 
                name: 'John Doe', 
                email: 'john@example.com',
                phone: '+1234567890',
                status: 'active'
              },
              { 
                id: 2, 
                name: 'Jane Smith', 
                email: 'jane@example.com',
                phone: '+1234567891',
                status: 'active'
              }
            ]);
          });
          
          // New endpoint
          app.get('/api/users/:id/profile', (req, res) => {
            res.json({
              userId: req.params.id,
              bio: 'Sample user bio',
              preferences: { theme: 'dark', notifications: true }
            });
          });
          
          app.listen(port, () => {
            console.log(\`Green app listening on port \${port}\`);
          });
          NODEAPP
          
          npm init -y
          npm install express
          node app.js
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-green-service
  namespace: blue-green-db
  labels:
    app: webapp
    environment: green
spec:
  selector:
    app: webapp
    environment: green
  ports:
  - port: 80
    targetPort: 3000
EOF

# Create main service for traffic switching
cat << EOF > /tmp/blue-green-db/main-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-main-service
  namespace: blue-green-db
  labels:
    app: webapp
    role: main
spec:
  selector:
    app: webapp
    environment: blue  # Initially pointing to blue
  ports:
  - port: 80
    targetPort: 3000
EOF

# Create validation tests
cat << EOF > /tmp/blue-green-db/validation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: environment-validator
  namespace: blue-green-db
  labels:
    app: validator
spec:
  template:
    metadata:
      labels:
        app: validator
    spec:
      restartPolicy: Never
      containers:
      - name: validator
        image: curlimages/curl:latest
        env:
        - name: TARGET_ENV
          value: "green"  # Change this to test different environments
        command:
        - sh
        - -c
        - |
          echo "Validating \$TARGET_ENV environment..."
          
          SERVICE_NAME="webapp-\$TARGET_ENV-service"
          
          # Basic health check
          if curl -f http://\$SERVICE_NAME/health; then
            echo "✓ Health check passed"
          else
            echo "✗ Health check failed"
            exit 1
          fi
          
          # API functionality test
          if curl -f http://\$SERVICE_NAME/api/users | grep -q "John Doe"; then
            echo "✓ API functionality test passed"
          else
            echo "✗ API functionality test failed"
            exit 1
          fi
          
          # Version-specific tests
          if [ "\$TARGET_ENV" = "green" ]; then
            # Test new endpoint
            if curl -f http://\$SERVICE_NAME/api/users/1/profile | grep -q "preferences"; then
              echo "✓ New API endpoint test passed"
            else
              echo "✗ New API endpoint test failed"
              exit 1
            fi
          fi
          
          echo "All validation tests passed for \$TARGET_ENV environment"
EOF

# Create traffic switching script
cat << 'EOF' > /tmp/blue-green-db/scripts/switch-traffic.sh
#!/bin/bash

NAMESPACE="blue-green-db"
TARGET_ENV=${1:-green}

if [ "$TARGET_ENV" != "blue" ] && [ "$TARGET_ENV" != "green" ]; then
    echo "Usage: $0 [blue|green]"
    exit 1
fi

echo "Switching traffic to $TARGET_ENV environment..."

# Update service selector
kubectl patch service webapp-main-service -n $NAMESPACE -p "{\"spec\":{\"selector\":{\"environment\":\"$TARGET_ENV\"}}}"

# Verify the switch
echo "Verifying traffic switch..."
sleep 5

kubectl port-forward svc/webapp-main-service 8080:80 -n $NAMESPACE &
PF_PID=$!
sleep 3

RESPONSE=$(curl -s http://localhost:8080/ | grep -o '"environment":"[^"]*"')
echo "Current environment: $RESPONSE"

kill $PF_PID

if echo "$RESPONSE" | grep -q "$TARGET_ENV"; then
    echo "✓ Traffic successfully switched to $TARGET_ENV"
else
    echo "✗ Traffic switch failed"
    exit 1
fi
EOF

chmod +x /tmp/blue-green-db/scripts/switch-traffic.sh

# Create deployment orchestration script
cat << 'EOF' > /tmp/blue-green-db/scripts/deploy-blue-green.sh
#!/bin/bash

NAMESPACE="blue-green-db"

echo "Starting Blue-Green deployment with database migration..."

# Step 1: Deploy Blue environment
echo "Step 1: Deploying Blue environment..."
kubectl apply -f ../db-init-configmap.yaml
kubectl apply -f ../blue/
kubectl apply -f ../main-service.yaml

# Wait for Blue to be ready
kubectl wait --for=condition=available deployment/webapp-blue -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=available deployment/postgres-blue -n $NAMESPACE --timeout=120s

echo "Blue environment is ready"

# Step 2: Run database migration
echo "Step 2: Running database migration..."
kubectl apply -f ../migrations/migration-job.yaml
kubectl wait --for=condition=complete job/db-migration-v2 -n $NAMESPACE --timeout=300s

if kubectl get job db-migration-v2 -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q True; then
    echo "Database migration completed successfully"
else
    echo "Database migration failed"
    exit 1
fi

# Step 3: Deploy Green environment
echo "Step 3: Deploying Green environment..."
kubectl apply -f ../green/

# Wait for Green to be ready
kubectl wait --for=condition=available deployment/webapp-green -n $NAMESPACE --timeout=120s

echo "Green environment is ready"

# Step 4: Validate Green environment
echo "Step 4: Validating Green environment..."
kubectl apply -f ../validation-job.yaml
kubectl wait --for=condition=complete job/environment-validator -n $NAMESPACE --timeout=120s

if kubectl get job environment-validator -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q True; then
    echo "Green environment validation passed"
    
    # Step 5: Switch traffic
    echo "Step 5: Switching traffic to Green..."
    ./switch-traffic.sh green
    
    echo "Blue-Green deployment completed successfully!"
    echo "Current environment: Green (v2.0)"
    echo "Database schema: v2.0"
    
else
    echo "Green environment validation failed, staying on Blue"
    exit 1
fi
EOF

chmod +x /tmp/blue-green-db/scripts/deploy-blue-green.sh

# Execute the deployment
cd /tmp/blue-green-db/scripts
./deploy-blue-green.sh

# Verify deployment
kubectl get all -n blue-green-db
kubectl get jobs -n blue-green-db
```
</details>

---

## Continue with remaining questions...

The exam continues with 7 more questions covering:
- Question 6: Helm Chart Testing and Hooks
- Question 7: Multi-Region Deployment Strategy  
- Question 8: Advanced Scaling with Custom Metrics
- Question 9: Deployment Security and Compliance
- Question 10: Disaster Recovery and Backup
- Question 11: Service Mesh Integration
- Question 12: Performance Optimization

Would you like me to continue with the remaining questions?