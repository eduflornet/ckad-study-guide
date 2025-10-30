# Mock Scenario 3: Complex Helm Deployment

**Objective**: Deploy and manage a complex multi-service application using advanced Helm features
**Time**: 60 minutes
**Difficulty**: Expert

---

## Scenario Overview

You work for an e-commerce platform that needs to deploy a complete microservices architecture for their holiday sale. The system must be:

- **Highly available** with zero-downtime deployments
- **Scalable** to handle traffic spikes
- **Configurable** across multiple environments
- **Secure** with proper secrets management
- **Observable** with comprehensive monitoring

The architecture includes:
- **Frontend**: React-based web application
- **API Gateway**: NGINX reverse proxy with rate limiting
- **User Service**: Authentication and user management
- **Product Service**: Product catalog and inventory
- **Order Service**: Order processing and fulfillment
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster for session storage
- **Message Queue**: RabbitMQ for async processing
- **Monitoring**: Prometheus and Grafana stack

## Implementation Tasks

### Task 1: Create Helm Chart Structure (10 minutes)

Create a complex Helm chart with dependencies:

```bash
# Create namespace
kubectl create namespace ecommerce-prod

# Create the main Helm chart
helm create ecommerce-platform
cd ecommerce-platform

# Clean up default files and create structure
rm -rf templates/*
rm values.yaml

# Create chart structure
cat << 'EOF' > Chart.yaml
apiVersion: v2
name: ecommerce-platform
description: Complete e-commerce microservices platform
type: application
version: 0.2.0
appVersion: "2.1.0"
keywords:
  - ecommerce
  - microservices
  - kubernetes
  - helm
home: https://ecommerce-platform.example.com
sources:
  - https://github.com/company/ecommerce-platform
maintainers:
  - name: DevOps Team
    email: devops@company.com

dependencies:
  - name: postgresql
    version: "12.1.9"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
    tags:
      - database
  - name: redis
    version: "17.3.7"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
    tags:
      - cache
  - name: rabbitmq
    version: "11.1.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: rabbitmq.enabled
    tags:
      - messaging
  - name: prometheus
    version: "15.16.1"
    repository: "https://prometheus-community.github.io/helm-charts"
    condition: monitoring.prometheus.enabled
    tags:
      - monitoring
  - name: grafana
    version: "6.44.11"
    repository: "https://grafana.github.io/helm-charts"
    condition: monitoring.grafana.enabled
    tags:
      - monitoring
EOF

# Create comprehensive values.yaml
cat << 'EOF' > values.yaml
# Global configuration
global:
  imageRegistry: "docker.io"
  imagePullSecrets: []
  storageClass: "standard"
  
# Environment configuration
environment: production
region: us-west-2

# Application configuration
replicaCount:
  frontend: 3
  apiGateway: 2
  userService: 3
  productService: 4
  orderService: 3

image:
  registry: docker.io
  pullPolicy: Always
  tag: "latest"

# Service-specific configurations
frontend:
  enabled: true
  image:
    repository: nginx
    tag: "1.21-alpine"
  service:
    type: ClusterIP
    port: 80
  ingress:
    enabled: true
    className: "nginx"
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
    hosts:
      - host: ecommerce.local
        paths:
          - path: /
            pathType: Prefix
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

apiGateway:
  enabled: true
  image:
    repository: nginx
    tag: "1.21-alpine"
  service:
    type: ClusterIP
    port: 8080
  config:
    rateLimit: "100r/m"
    maxBodySize: "10m"
    timeout: "30s"
  resources:
    limits:
      cpu: 300m
      memory: 512Mi
    requests:
      cpu: 150m
      memory: 256Mi

userService:
  enabled: true
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3001
  env:
    JWT_SECRET: ""
    SESSION_TIMEOUT: "3600"
    PASSWORD_SALT_ROUNDS: "12"
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 512Mi

productService:
  enabled: true
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3002
  env:
    CACHE_TTL: "300"
    ELASTICSEARCH_URL: ""
    IMAGE_RESIZE_QUALITY: "85"
  resources:
    limits:
      cpu: 800m
      memory: 1.5Gi
    requests:
      cpu: 400m
      memory: 768Mi

orderService:
  enabled: true
  image:
    repository: node
    tag: "18-alpine"
  service:
    type: ClusterIP
    port: 3003
  env:
    PAYMENT_GATEWAY_URL: ""
    ORDER_TIMEOUT: "1800"
    INVENTORY_CHECK_ENABLED: "true"
  resources:
    limits:
      cpu: 600m
      memory: 1Gi
    requests:
      cpu: 300m
      memory: 512Mi

# Database configuration
postgresql:
  enabled: true
  auth:
    enablePostgresUser: true
    postgresPassword: "securepassword"
    username: "ecommerce"
    password: "ecommerce123"
    database: "ecommerce"
  primary:
    persistence:
      enabled: true
      size: 50Gi
  readReplicas:
    replicaCount: 2
    persistence:
      enabled: true
      size: 50Gi

# Cache configuration
redis:
  enabled: true
  auth:
    enabled: true
    password: "redis123"
  master:
    persistence:
      enabled: true
      size: 10Gi
  replica:
    replicaCount: 2
    persistence:
      enabled: true
      size: 10Gi

# Message queue configuration
rabbitmq:
  enabled: true
  auth:
    username: "ecommerce"
    password: "rabbitmq123"
  persistence:
    enabled: true
    size: 20Gi
  replicaCount: 3

# Monitoring configuration
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
    admin:
      password: "grafana123"

# Security configuration
security:
  networkPolicies:
    enabled: true
  podSecurityContext:
    fsGroup: 1001
    runAsNonRoot: true
    runAsUser: 1001
  securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop:
        - ALL
    readOnlyRootFilesystem: true

# Autoscaling configuration
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Service mesh configuration (optional)
serviceMesh:
  enabled: false
  istio:
    enabled: false
  linkerd:
    enabled: false

# Backup configuration
backup:
  enabled: true
  schedule: "0 2 * * *"
  retention: "30d"
  storage:
    size: "100Gi"
    storageClass: "gp2"
EOF

# Create templates directory structure
mkdir -p templates/{frontend,api-gateway,user-service,product-service,order-service,monitoring,security}
```

### Task 2: Create Advanced Templates (15 minutes)

Create sophisticated Helm templates with conditionals and loops:

```yaml
# Create helper template
cat << 'EOF' > templates/_helpers.tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "ecommerce.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ecommerce.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ecommerce.labels" -}}
helm.sh/chart: {{ include "ecommerce.chart" . }}
{{ include "ecommerce.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ecommerce-platform
environment: {{ .Values.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ecommerce.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ecommerce.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ecommerce.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ecommerce.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate database connection string
*/}}
{{- define "ecommerce.databaseUrl" -}}
{{- if .Values.postgresql.enabled }}
postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "ecommerce.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.externalDatabase.url }}
{{- end }}
{{- end }}

{{/*
Generate Redis connection string
*/}}
{{- define "ecommerce.redisUrl" -}}
{{- if .Values.redis.enabled }}
redis://:{{ .Values.redis.auth.password }}@{{ include "ecommerce.fullname" . }}-redis-master:6379
{{- else }}
{{- .Values.externalRedis.url }}
{{- end }}
{{- end }}

{{/*
Generate RabbitMQ connection string
*/}}
{{- define "ecommerce.rabbitmqUrl" -}}
{{- if .Values.rabbitmq.enabled }}
amqp://{{ .Values.rabbitmq.auth.username }}:{{ .Values.rabbitmq.auth.password }}@{{ include "ecommerce.fullname" . }}-rabbitmq:5672
{{- else }}
{{- .Values.externalRabbitmq.url }}
{{- end }}
{{- end }}

{{/*
Generate microservice labels
*/}}
{{- define "ecommerce.microserviceLabels" -}}
{{ include "ecommerce.labels" . }}
app.kubernetes.io/component: {{ .component }}
tier: {{ .tier | default "backend" }}
{{- end }}

{{/*
Generate security context
*/}}
{{- define "ecommerce.securityContext" -}}
{{- if .Values.security.securityContext }}
securityContext:
  {{- toYaml .Values.security.securityContext | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Generate pod security context
*/}}
{{- define "ecommerce.podSecurityContext" -}}
{{- if .Values.security.podSecurityContext }}
securityContext:
  {{- toYaml .Values.security.podSecurityContext | nindent 2 }}
{{- end }}
{{- end }}
EOF

# Create ConfigMap template
cat << 'EOF' > templates/configmap.yaml
{{- if or .Values.userService.enabled .Values.productService.enabled .Values.orderService.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ecommerce.fullname" . }}-config
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
data:
  # Database configuration
  DATABASE_URL: {{ include "ecommerce.databaseUrl" . | quote }}
  REDIS_URL: {{ include "ecommerce.redisUrl" . | quote }}
  RABBITMQ_URL: {{ include "ecommerce.rabbitmqUrl" . | quote }}
  
  # Application configuration
  ENVIRONMENT: {{ .Values.environment | quote }}
  REGION: {{ .Values.region | quote }}
  
  # Service discovery
  USER_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-user-service:{{ .Values.userService.service.port }}"
  PRODUCT_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-product-service:{{ .Values.productService.service.port }}"
  ORDER_SERVICE_URL: "http://{{ include "ecommerce.fullname" . }}-order-service:{{ .Values.orderService.service.port }}"
  
  # User Service specific
  {{- if .Values.userService.enabled }}
  SESSION_TIMEOUT: {{ .Values.userService.env.SESSION_TIMEOUT | quote }}
  PASSWORD_SALT_ROUNDS: {{ .Values.userService.env.PASSWORD_SALT_ROUNDS | quote }}
  {{- end }}
  
  # Product Service specific
  {{- if .Values.productService.enabled }}
  CACHE_TTL: {{ .Values.productService.env.CACHE_TTL | quote }}
  IMAGE_RESIZE_QUALITY: {{ .Values.productService.env.IMAGE_RESIZE_QUALITY | quote }}
  {{- end }}
  
  # Order Service specific
  {{- if .Values.orderService.enabled }}
  ORDER_TIMEOUT: {{ .Values.orderService.env.ORDER_TIMEOUT | quote }}
  INVENTORY_CHECK_ENABLED: {{ .Values.orderService.env.INVENTORY_CHECK_ENABLED | quote }}
  {{- end }}
{{- end }}
EOF

# Create Secrets template
cat << 'EOF' > templates/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "ecommerce.fullname" . }}-secrets
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
type: Opaque
data:
  {{- if .Values.userService.enabled }}
  JWT_SECRET: {{ .Values.userService.env.JWT_SECRET | default (randAlphaNum 32) | b64enc | quote }}
  {{- end }}
  
  {{- if .Values.productService.enabled }}
  ELASTICSEARCH_URL: {{ .Values.productService.env.ELASTICSEARCH_URL | default "" | b64enc | quote }}
  {{- end }}
  
  {{- if .Values.orderService.enabled }}
  PAYMENT_GATEWAY_URL: {{ .Values.orderService.env.PAYMENT_GATEWAY_URL | default "" | b64enc | quote }}
  {{- end }}
  
  # External service credentials
  DATABASE_PASSWORD: {{ .Values.postgresql.auth.password | b64enc | quote }}
  REDIS_PASSWORD: {{ .Values.redis.auth.password | b64enc | quote }}
  RABBITMQ_PASSWORD: {{ .Values.rabbitmq.auth.password | b64enc | quote }}
EOF
```

### Task 3: Create Microservices Deployments (15 minutes)

Create deployment templates for each microservice:

```yaml
# Create User Service deployment
cat << 'EOF' > templates/user-service/deployment.yaml
{{- if .Values.userService.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ecommerce.fullname" . }}-user-service
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "user-service" "tier" "backend") | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount.userService }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "ecommerce.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
      app.kubernetes.io/component: user-service
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "ecommerce.name" . }}
        app.kubernetes.io/instance: {{ .Release.Name }}
        app.kubernetes.io/component: user-service
        version: {{ .Chart.AppVersion }}
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secrets.yaml") . | sha256sum }}
    spec:
      {{- include "ecommerce.podSecurityContext" . | nindent 6 }}
      serviceAccountName: {{ include "ecommerce.serviceAccountName" . }}
      containers:
      - name: user-service
        {{- include "ecommerce.securityContext" . | nindent 8 }}
        image: "{{ .Values.userService.image.repository }}:{{ .Values.userService.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.userService.service.port }}
          protocol: TCP
        env:
        - name: PORT
          value: {{ .Values.userService.service.port | quote }}
        - name: NODE_ENV
          value: {{ .Values.environment }}
        - name: SERVICE_NAME
          value: "user-service"
        envFrom:
        - configMapRef:
            name: {{ include "ecommerce.fullname" . }}-config
        - secretRef:
            name: {{ include "ecommerce.fullname" . }}-secrets
        command:
        - sh
        - -c
        - |
          cat << 'USERAPP' > app.js
          const express = require('express');
          const crypto = require('crypto');
          const app = express();
          const port = process.env.PORT || 3001;
          
          app.use(express.json());
          
          // Mock user database
          const users = new Map();
          const sessions = new Map();
          
          // Service health and metrics
          let serviceMetrics = {
            totalRequests: 0,
            successfulRequests: 0,
            activeUsers: 0,
            registrations: 0,
            startTime: Date.now()
          };
          
          // Middleware
          app.use((req, res, next) => {
            serviceMetrics.totalRequests++;
            res.on('finish', () => {
              if (res.statusCode < 400) {
                serviceMetrics.successfulRequests++;
              }
            });
            next();
          });
          
          // Health check
          app.get('/health', (req, res) => {
            res.json({
              status: 'healthy',
              service: 'user-service',
              version: process.env.npm_package_version || '1.0.0',
              timestamp: new Date().toISOString(),
              uptime: Date.now() - serviceMetrics.startTime,
              environment: process.env.NODE_ENV
            });
          });
          
          // Service info
          app.get('/', (req, res) => {
            res.json({
              service: 'User Service',
              version: '2.1.0',
              features: ['authentication', 'user_management', 'jwt_tokens', 'session_management'],
              endpoints: ['/register', '/login', '/profile', '/logout'],
              metrics: serviceMetrics
            });
          });
          
          // User registration
          app.post('/register', (req, res) => {
            const { username, email, password } = req.body;
            
            if (!username || !email || !password) {
              return res.status(400).json({ error: 'Missing required fields' });
            }
            
            if (users.has(email)) {
              return res.status(409).json({ error: 'User already exists' });
            }
            
            const userId = crypto.randomUUID();
            const hashedPassword = crypto.pbkdf2Sync(password, 'salt', 10000, 64, 'sha512').toString('hex');
            
            users.set(email, {
              id: userId,
              username,
              email,
              password: hashedPassword,
              createdAt: new Date().toISOString(),
              isActive: true
            });
            
            serviceMetrics.registrations++;
            
            res.status(201).json({
              message: 'User created successfully',
              userId,
              username,
              email
            });
          });
          
          // User login
          app.post('/login', (req, res) => {
            const { email, password } = req.body;
            
            if (!email || !password) {
              return res.status(400).json({ error: 'Email and password required' });
            }
            
            const user = users.get(email);
            if (!user) {
              return res.status(401).json({ error: 'Invalid credentials' });
            }
            
            const hashedPassword = crypto.pbkdf2Sync(password, 'salt', 10000, 64, 'sha512').toString('hex');
            if (user.password !== hashedPassword) {
              return res.status(401).json({ error: 'Invalid credentials' });
            }
            
            const sessionId = crypto.randomUUID();
            const expiresAt = Date.now() + (parseInt(process.env.SESSION_TIMEOUT) * 1000);
            
            sessions.set(sessionId, {
              userId: user.id,
              email: user.email,
              expiresAt
            });
            
            serviceMetrics.activeUsers++;
            
            res.json({
              message: 'Login successful',
              sessionId,
              user: {
                id: user.id,
                username: user.username,
                email: user.email
              },
              expiresAt: new Date(expiresAt).toISOString()
            });
          });
          
          // Get user profile
          app.get('/profile/:userId', (req, res) => {
            const userId = req.params.userId;
            const user = Array.from(users.values()).find(u => u.id === userId);
            
            if (!user) {
              return res.status(404).json({ error: 'User not found' });
            }
            
            res.json({
              id: user.id,
              username: user.username,
              email: user.email,
              createdAt: user.createdAt,
              isActive: user.isActive
            });
          });
          
          // Metrics endpoint
          app.get('/metrics', (req, res) => {
            res.json({
              ...serviceMetrics,
              activeUsers: sessions.size,
              timestamp: new Date().toISOString()
            });
          });
          
          app.listen(port, () => {
            console.log(\`User Service listening on port \${port}\`);
          });
          USERAPP
          
          npm init -y
          npm install express
          node app.js
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.userService.resources | nindent 10 }}
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
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
{{- end }}
EOF

# Create corresponding service
cat << 'EOF' > templates/user-service/service.yaml
{{- if .Values.userService.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ecommerce.fullname" . }}-user-service
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "user-service") | nindent 4 }}
spec:
  type: {{ .Values.userService.service.type }}
  ports:
    - port: {{ .Values.userService.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: {{ include "ecommerce.name" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/component: user-service
{{- end }}
EOF

# Create Product Service deployment
cat << 'EOF' > templates/product-service/deployment.yaml
{{- if .Values.productService.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ecommerce.fullname" . }}-product-service
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "product-service") | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount.productService }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "ecommerce.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
      app.kubernetes.io/component: product-service
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "ecommerce.name" . }}
        app.kubernetes.io/instance: {{ .Release.Name }}
        app.kubernetes.io/component: product-service
        version: {{ .Chart.AppVersion }}
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      {{- include "ecommerce.podSecurityContext" . | nindent 6 }}
      containers:
      - name: product-service
        {{- include "ecommerce.securityContext" . | nindent 8 }}
        image: "{{ .Values.productService.image.repository }}:{{ .Values.productService.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.productService.service.port }}
          protocol: TCP
        envFrom:
        - configMapRef:
            name: {{ include "ecommerce.fullname" . }}-config
        env:
        - name: PORT
          value: {{ .Values.productService.service.port | quote }}
        - name: SERVICE_NAME
          value: "product-service"
        command:
        - sh
        - -c
        - |
          cat << 'PRODUCTAPP' > app.js
          const express = require('express');
          const app = express();
          const port = process.env.PORT || 3002;
          
          app.use(express.json());
          
          // Mock product database
          const products = new Map([
            ['1', { id: '1', name: 'Laptop Pro', price: 1299.99, category: 'Electronics', stock: 50 }],
            ['2', { id: '2', name: 'Coffee Maker', price: 89.99, category: 'Appliances', stock: 25 }],
            ['3', { id: '3', name: 'Book: JavaScript Guide', price: 29.99, category: 'Books', stock: 100 }],
            ['4', { id: '4', name: 'Wireless Headphones', price: 199.99, category: 'Electronics', stock: 30 }],
            ['5', { id: '5', name: 'Running Shoes', price: 129.99, category: 'Sports', stock: 75 }]
          ]);
          
          let serviceMetrics = {
            totalRequests: 0,
            productViews: 0,
            searches: 0,
            inventoryChecks: 0,
            startTime: Date.now()
          };
          
          app.use((req, res, next) => {
            serviceMetrics.totalRequests++;
            next();
          });
          
          app.get('/health', (req, res) => {
            res.json({
              status: 'healthy',
              service: 'product-service',
              version: '2.1.0',
              timestamp: new Date().toISOString(),
              productCount: products.size
            });
          });
          
          app.get('/', (req, res) => {
            res.json({
              service: 'Product Service',
              version: '2.1.0',
              features: ['product_catalog', 'inventory_management', 'search', 'categories'],
              productCount: products.size,
              metrics: serviceMetrics
            });
          });
          
          // Get all products
          app.get('/products', (req, res) => {
            serviceMetrics.productViews += products.size;
            res.json(Array.from(products.values()));
          });
          
          // Get product by ID
          app.get('/products/:id', (req, res) => {
            const product = products.get(req.params.id);
            if (!product) {
              return res.status(404).json({ error: 'Product not found' });
            }
            serviceMetrics.productViews++;
            res.json(product);
          });
          
          // Search products
          app.get('/search', (req, res) => {
            const { q, category } = req.query;
            serviceMetrics.searches++;
            
            let results = Array.from(products.values());
            
            if (q) {
              results = results.filter(p => 
                p.name.toLowerCase().includes(q.toLowerCase())
              );
            }
            
            if (category) {
              results = results.filter(p => 
                p.category.toLowerCase() === category.toLowerCase()
              );
            }
            
            res.json(results);
          });
          
          // Check inventory
          app.get('/inventory/:id', (req, res) => {
            const product = products.get(req.params.id);
            if (!product) {
              return res.status(404).json({ error: 'Product not found' });
            }
            
            serviceMetrics.inventoryChecks++;
            res.json({
              productId: product.id,
              name: product.name,
              stock: product.stock,
              available: product.stock > 0
            });
          });
          
          app.get('/metrics', (req, res) => {
            res.json(serviceMetrics);
          });
          
          app.listen(port, () => {
            console.log(\`Product Service listening on port \${port}\`);
          });
          PRODUCTAPP
          
          npm init -y
          npm install express
          node app.js
        resources:
          {{- toYaml .Values.productService.resources | nindent 10 }}
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
{{- end }}
EOF

# Create Product Service service
cat << 'EOF' > templates/product-service/service.yaml
{{- if .Values.productService.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ecommerce.fullname" . }}-product-service
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "product-service") | nindent 4 }}
spec:
  type: {{ .Values.productService.service.type }}
  ports:
    - port: {{ .Values.productService.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: {{ include "ecommerce.name" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/component: product-service
{{- end }}
EOF
```

### Task 4: Create Advanced Features (10 minutes)

Add autoscaling, ingress, and monitoring:

```yaml
# Create HPA template
cat << 'EOF' > templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
{{- $services := list "userService" "productService" "orderService" }}
{{- range $service := $services }}
{{- $serviceConfig := index $.Values $service }}
{{- if $serviceConfig.enabled }}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ecommerce.fullname" $ }}-{{ $service | kebabcase }}
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" $.Chart "Release" $.Release "Values" $.Values "component" ($service | kebabcase)) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "ecommerce.fullname" $ }}-{{ $service | kebabcase }}
  minReplicas: {{ $.Values.autoscaling.minReplicas }}
  maxReplicas: {{ $.Values.autoscaling.maxReplicas }}
  metrics:
  {{- if $.Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ $.Values.autoscaling.targetCPUUtilizationPercentage }}
  {{- end }}
  {{- if $.Values.autoscaling.targetMemoryUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ $.Values.autoscaling.targetMemoryUtilizationPercentage }}
  {{- end }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
{{- end }}
{{- end }}
{{- end }}
EOF

# Create Ingress template
cat << 'EOF' > templates/frontend/ingress.yaml
{{- if and .Values.frontend.enabled .Values.frontend.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "ecommerce.fullname" . }}-frontend
  labels:
    {{- include "ecommerce.microserviceLabels" (dict "Chart" .Chart "Release" .Release "Values" .Values "component" "frontend") | nindent 4 }}
  {{- with .Values.frontend.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.frontend.ingress.className }}
  ingressClassName: {{ .Values.frontend.ingress.className }}
  {{- end }}
  rules:
    {{- range .Values.frontend.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "ecommerce.fullname" $ }}-frontend
                port:
                  number: {{ $.Values.frontend.service.port }}
          {{- end }}
    {{- end }}
EOF

# Create ServiceMonitor for Prometheus
cat << 'EOF' > templates/monitoring/servicemonitor.yaml
{{- if and .Values.monitoring.prometheus.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "ecommerce.fullname" . }}-services
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "ecommerce.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
  endpoints:
  {{- if .Values.userService.enabled }}
  - port: http
    path: /metrics
    targetPort: {{ .Values.userService.service.port }}
    interval: 30s
    scrapeTimeout: 10s
  {{- end }}
  {{- if .Values.productService.enabled }}
  - port: http
    path: /metrics
    targetPort: {{ .Values.productService.service.port }}
    interval: 30s
    scrapeTimeout: 10s
  {{- end }}
  {{- if .Values.orderService.enabled }}
  - port: http
    path: /metrics
    targetPort: {{ .Values.orderService.service.port }}
    interval: 30s
    scrapeTimeout: 10s
  {{- end }}
{{- end }}
EOF

# Create NetworkPolicy
cat << 'EOF' > templates/security/networkpolicy.yaml
{{- if .Values.security.networkPolicies.enabled }}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "ecommerce.fullname" . }}-default-deny
  labels:
    {{- include "ecommerce.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: {{ include "ecommerce.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: {{ include "ecommerce.name" . }}
          app.kubernetes.io/instance: {{ .Release.Name }}
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: {{ include "ecommerce.name" . }}
          app.kubernetes.io/instance: {{ .Release.Name }}
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 443
{{- end }}
EOF
```

### Task 5: Deploy and Test the Application (10 minutes)

Deploy the complete Helm chart:

```bash
# Go back to parent directory
cd ..

# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install dependencies
cd ecommerce-platform
helm dependency build

# Create custom values for production deployment
cat << 'EOF' > values-prod.yaml
environment: production
region: us-west-2

# Scale for production
replicaCount:
  frontend: 3
  apiGateway: 2
  userService: 3
  productService: 4
  orderService: 3

# Database configuration for production
postgresql:
  enabled: true
  auth:
    postgresPassword: "prod-secure-password"
    password: "prod-ecommerce-password"
  primary:
    persistence:
      size: 100Gi
  readReplicas:
    replicaCount: 2

redis:
  enabled: true
  auth:
    password: "prod-redis-password"
  master:
    persistence:
      size: 20Gi
  replica:
    replicaCount: 3

rabbitmq:
  enabled: true
  auth:
    password: "prod-rabbitmq-password"
  persistence:
    size: 50Gi
  replicaCount: 3

# Enable monitoring
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

# Enable security features
security:
  networkPolicies:
    enabled: true

# Enable autoscaling
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10

# Frontend ingress
frontend:
  ingress:
    enabled: true
    hosts:
    - host: ecommerce-prod.local
      paths:
      - path: /
        pathType: Prefix
EOF

# Deploy the application
helm install ecommerce-prod ./ecommerce-platform \
  --namespace ecommerce-prod \
  --values values-prod.yaml \
  --timeout 10m \
  --wait

# Check deployment status
kubectl get pods -n ecommerce-prod
kubectl get services -n ecommerce-prod
kubectl get ingress -n ecommerce-prod
```

Test the deployment:

```bash
# Port forward to test services
kubectl port-forward -n ecommerce-prod svc/ecommerce-prod-ecommerce-platform-user-service 3001:3001 &
USER_SERVICE_PID=$!

kubectl port-forward -n ecommerce-prod svc/ecommerce-prod-ecommerce-platform-product-service 3002:3002 &
PRODUCT_SERVICE_PID=$!

sleep 5

# Test User Service
echo "Testing User Service:"
curl -s http://localhost:3001/ | jq '.'

echo -e "\nRegistering a user:"
curl -s -X POST http://localhost:3001/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}' | jq '.'

# Test Product Service
echo -e "\nTesting Product Service:"
curl -s http://localhost:3002/ | jq '.'

echo -e "\nGetting products:"
curl -s http://localhost:3002/products | jq '.[0:2]'

echo -e "\nSearching products:"
curl -s "http://localhost:3002/search?q=laptop" | jq '.'

# Clean up port forwards
kill $USER_SERVICE_PID $PRODUCT_SERVICE_PID
```

## Final Validation and Management

Create management and testing scripts:

```bash
# Create comprehensive testing script
cat << 'EOF' > test-ecommerce.sh
#!/bin/bash

NAMESPACE="ecommerce-prod"
RELEASE_NAME="ecommerce-prod"

echo "=== E-commerce Platform Test Suite ==="

# Check Helm release status
echo "1. Helm Release Status:"
helm status $RELEASE_NAME -n $NAMESPACE
echo

# Check all resources
echo "2. Resource Status:"
kubectl get all -n $NAMESPACE
echo

# Check ConfigMaps and Secrets
echo "3. Configuration Status:"
kubectl get configmaps,secrets -n $NAMESPACE
echo

# Test database connectivity
echo "4. Database Connectivity Test:"
kubectl run db-test --rm -i --tty --restart=Never \
  --image=postgres:14-alpine \
  --env="PGPASSWORD=prod-ecommerce-password" \
  -n $NAMESPACE -- psql -h ecommerce-prod-postgresql -U ecommerce -d ecommerce -c "\dt"
echo

# Test each microservice
echo "5. Microservice Health Checks:"

# User Service
kubectl port-forward -n $NAMESPACE svc/ecommerce-prod-ecommerce-platform-user-service 3001:3001 &
USER_PID=$!
sleep 3
echo "User Service Health:"
curl -s http://localhost:3001/health | jq '.status, .service, .uptime'
kill $USER_PID

# Product Service
kubectl port-forward -n $NAMESPACE svc/ecommerce-prod-ecommerce-platform-product-service 3002:3002 &
PRODUCT_PID=$!
sleep 3
echo "Product Service Health:"
curl -s http://localhost:3002/health | jq '.status, .service, .productCount'
kill $PRODUCT_PID

echo -e "\n6. Autoscaling Status:"
kubectl get hpa -n $NAMESPACE

echo -e "\n7. Network Policies:"
kubectl get networkpolicies -n $NAMESPACE

echo -e "\n✅ E-commerce platform test completed!"
EOF

chmod +x test-ecommerce.sh

# Create upgrade script
cat << 'EOF' > upgrade-ecommerce.sh
#!/bin/bash

NAMESPACE="ecommerce-prod"
RELEASE_NAME="ecommerce-prod"

echo "=== Upgrading E-commerce Platform ==="

# Backup current values
helm get values $RELEASE_NAME -n $NAMESPACE > current-values.yaml

# Create new values with updates
cat << 'NEWVALUES' > values-upgrade.yaml
# Inherit from production values
environment: production
region: us-west-2

# Increased capacity for holiday sales
replicaCount:
  frontend: 5
  apiGateway: 3
  userService: 5
  productService: 6
  orderService: 4

# Enhanced autoscaling
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

# Database scaling
postgresql:
  enabled: true
  auth:
    postgresPassword: "prod-secure-password"
    password: "prod-ecommerce-password"
  primary:
    persistence:
      size: 200Gi
  readReplicas:
    replicaCount: 3

redis:
  enabled: true
  auth:
    password: "prod-redis-password"
  master:
    persistence:
      size: 40Gi
  replica:
    replicaCount: 4

# Enhanced monitoring
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

security:
  networkPolicies:
    enabled: true

frontend:
  ingress:
    enabled: true
    hosts:
    - host: ecommerce-prod.local
      paths:
      - path: /
        pathType: Prefix
NEWVALUES

# Perform dry-run first
echo "Performing dry-run upgrade..."
helm upgrade $RELEASE_NAME ./ecommerce-platform \
  --namespace $NAMESPACE \
  --values values-upgrade.yaml \
  --dry-run --debug

read -p "Proceed with actual upgrade? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Performing upgrade..."
    helm upgrade $RELEASE_NAME ./ecommerce-platform \
      --namespace $NAMESPACE \
      --values values-upgrade.yaml \
      --timeout 15m \
      --wait
    
    echo "Upgrade completed! New status:"
    helm status $RELEASE_NAME -n $NAMESPACE
else
    echo "Upgrade cancelled."
fi
EOF

chmod +x upgrade-ecommerce.sh

# Run the test suite
./test-ecommerce.sh
```

## Cleanup

```bash
# Uninstall the release
helm uninstall ecommerce-prod -n ecommerce-prod

# Delete namespace
kubectl delete namespace ecommerce-prod

# Clean up files
rm -rf ecommerce-platform values-prod.yaml current-values.yaml values-upgrade.yaml
rm -f test-ecommerce.sh upgrade-ecommerce.sh
```

## Success Criteria

- [ ] Complex Helm chart created with proper structure and dependencies
- [ ] Multiple microservices deployed with individual configurations
- [ ] Database, cache, and message queue dependencies properly configured
- [ ] Advanced Helm features implemented (conditionals, loops, helpers)
- [ ] ConfigMaps and Secrets generated dynamically
- [ ] Autoscaling configured for microservices
- [ ] Network policies and security contexts applied
- [ ] Monitoring and service discovery configured
- [ ] Services communicate properly through service discovery
- [ ] Helm upgrade and rollback procedures tested
- [ ] Dependencies managed through Helm dependency system

## Key Takeaways

1. **Helm charts** can manage complex multi-service applications
2. **Dependencies** simplify external service integration
3. **Templates** provide flexibility with conditionals and loops
4. **Values files** enable environment-specific configurations
5. **Hooks** can manage deployment lifecycle events
6. **Testing** ensures chart reliability and functionality
7. **Security** should be built into chart templates
8. **Monitoring** integration enables observability

## Advanced Features Demonstrated

1. **Chart dependencies** for external services
2. **Complex templating** with conditionals and loops
3. **Multi-environment** configuration management
4. **Service mesh** readiness preparation
5. **Automated scaling** based on metrics
6. **Security policies** at the chart level
7. **Monitoring integration** with Prometheus
8. **Advanced deployment** strategies support