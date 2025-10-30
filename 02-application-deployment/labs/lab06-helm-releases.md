# Lab 6: Helm Release Management

**Objective**: Master advanced Helm release management and operational patterns
**Time**: 40 minutes
**Difficulty**: Advanced

## Learning Goals

- Manage complex release lifecycles
- Implement release strategies with Helm
- Use Helm in CI/CD pipelines
- Handle release secrets and security
- Monitor and troubleshoot releases
- Implement GitOps patterns with Helm

## Exercise 1: Advanced Release Operations (15 minutes)

### Task 1.1: Multi-Environment Release Management

```bash
# Create multiple environments
kubectl create namespace production
kubectl create namespace staging
kubectl create namespace development

# Create environment-specific values files
cat << EOF > values-production.yaml
replicaCount: 5

image:
  repository: nginx
  tag: "1.21-alpine"
  pullPolicy: Always

service:
  type: LoadBalancer
  port: 80

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

nodeSelector:
  node-type: production

tolerations:
- key: "production"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"

env:
  APP_ENV: production
  LOG_LEVEL: warn
  CACHE_TTL: "3600"
EOF

cat << EOF > values-staging.yaml
replicaCount: 2

image:
  repository: nginx
  tag: "1.21-alpine"
  pullPolicy: Always

service:
  type: ClusterIP
  port: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

autoscaling:
  enabled: false

env:
  APP_ENV: staging
  LOG_LEVEL: info
  CACHE_TTL: "1800"
EOF

cat << EOF > values-development.yaml
replicaCount: 1

image:
  repository: nginx
  tag: "1.20-alpine"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  limits:
    cpu: 50m
    memory: 64Mi
  requests:
    cpu: 25m
    memory: 32Mi

autoscaling:
  enabled: false

env:
  APP_ENV: development
  LOG_LEVEL: debug
  CACHE_TTL: "300"
EOF
```

### Task 1.2: Deploy to Multiple Environments

```bash
# Deploy to development
helm install webapp-dev bitnami/nginx \
  --namespace development \
  --values values-development.yaml \
  --set fullnameOverride=webapp-dev

# Deploy to staging
helm install webapp-staging bitnami/nginx \
  --namespace staging \
  --values values-staging.yaml \
  --set fullnameOverride=webapp-staging

# Deploy to production
helm install webapp-prod bitnami/nginx \
  --namespace production \
  --values values-production.yaml \
  --set fullnameOverride=webapp-prod

# Check all deployments
helm list --all-namespaces
```

### Task 1.3: Release Promotion Strategy

```bash
# Simulate promotion from dev to staging
DEV_IMAGE_TAG=$(helm get values webapp-dev -n development -o json | jq -r '.image.tag // "1.20-alpine"')
echo "Promoting image tag: $DEV_IMAGE_TAG"

# Update staging with dev image
helm upgrade webapp-staging bitnami/nginx \
  --namespace staging \
  --values values-staging.yaml \
  --set image.tag=$DEV_IMAGE_TAG \
  --set fullnameOverride=webapp-staging

# Check rollout status
kubectl rollout status deployment/webapp-staging -n staging

# Promote to production (with additional validation)
helm upgrade webapp-prod bitnami/nginx \
  --namespace production \
  --values values-production.yaml \
  --set image.tag=$DEV_IMAGE_TAG \
  --set fullnameOverride=webapp-prod \
  --dry-run  # First do a dry run

# If dry run is successful, apply the change
helm upgrade webapp-prod bitnami/nginx \
  --namespace production \
  --values values-production.yaml \
  --set image.tag=$DEV_IMAGE_TAG \
  --set fullnameOverride=webapp-prod
```

## Exercise 2: Release Security and Secrets (10 minutes)

### Task 2.1: Working with Helm Secrets

```bash
# Create secrets for different environments
kubectl create secret generic webapp-secrets \
  --from-literal=db-password=prod-secret-pass \
  --from-literal=api-key=prod-api-key-12345 \
  --namespace production

kubectl create secret generic webapp-secrets \
  --from-literal=db-password=staging-secret-pass \
  --from-literal=api-key=staging-api-key-67890 \
  --namespace staging

kubectl create secret generic webapp-secrets \
  --from-literal=db-password=dev-simple-pass \
  --from-literal=api-key=dev-api-key-abcde \
  --namespace development
```

### Task 2.2: Create Chart with Secret Integration

```bash
# Create a custom chart for secure application
helm create secure-webapp

# Update values.yaml
cat << EOF > secure-webapp/values.yaml
replicaCount: 1

image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: "1.21"

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

service:
  type: ClusterIP
  port: 80

secrets:
  existingSecret: "webapp-secrets"
  
database:
  host: "postgres.example.com"
  port: 5432
  name: "webapp"
  username: "webapp_user"

security:
  podSecurityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  
  securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop:
      - ALL
    readOnlyRootFilesystem: true

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
EOF

# Update deployment template
cat << 'EOF' > secure-webapp/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "secure-webapp.fullname" . }}
  labels:
    {{- include "secure-webapp.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "secure-webapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "secure-webapp.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "secure-webapp.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.security.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.security.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          env:
            - name: DB_HOST
              value: {{ .Values.database.host | quote }}
            - name: DB_PORT
              value: {{ .Values.database.port | quote }}
            - name: DB_NAME
              value: {{ .Values.database.name | quote }}
            - name: DB_USER
              value: {{ .Values.database.username | quote }}
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secrets.existingSecret }}
                  key: db-password
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.secrets.existingSecret }}
                  key: api-key
          livenessProbe:
            httpGet:
              path: /
              port: http
          readinessProbe:
            httpGet:
              path: /
              port: http
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
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
EOF
```

### Task 2.3: Deploy Secure Application

```bash
# Deploy to each environment
helm install secure-app secure-webapp/ \
  --namespace development \
  --set replicaCount=1

helm install secure-app secure-webapp/ \
  --namespace staging \
  --set replicaCount=2

helm install secure-app secure-webapp/ \
  --namespace production \
  --set replicaCount=3

# Verify secrets are properly mounted
kubectl describe pod -n production -l app.kubernetes.io/name=secure-webapp
```

## Exercise 3: Release Monitoring and Troubleshooting (10 minutes)

### Task 3.1: Release Status Monitoring

```bash
# Create a comprehensive monitoring script
cat << 'EOF' > monitor-releases.sh
#!/bin/bash

echo "=== Helm Release Monitoring ==="
echo

# Get all releases across namespaces
echo "All Helm Releases:"
helm list --all-namespaces --output table

echo
echo "=== Release Status Details ==="

# Check each release status
for namespace in development staging production; do
    echo
    echo "--- $namespace environment ---"
    
    releases=$(helm list -n $namespace --short)
    
    if [ -n "$releases" ]; then
        for release in $releases; do
            echo "Release: $release"
            helm status $release -n $namespace --show-desc
            
            # Check deployment status
            deployment=$(kubectl get deployment -n $namespace -l app.kubernetes.io/instance=$release -o name 2>/dev/null)
            if [ -n "$deployment" ]; then
                echo "Deployment Status:"
                kubectl rollout status $deployment -n $namespace --timeout=10s
            fi
            
            echo "---"
        done
    else
        echo "No releases found in $namespace"
    fi
done

echo
echo "=== Resource Health Check ==="

# Check pod health across environments
for namespace in development staging production; do
    echo
    echo "Pods in $namespace:"
    kubectl get pods -n $namespace --show-labels
done
EOF

chmod +x monitor-releases.sh
./monitor-releases.sh
```

### Task 3.2: Release Troubleshooting

```bash
# Create a troubleshooting toolkit
cat << 'EOF' > troubleshoot-release.sh
#!/bin/bash

RELEASE_NAME=$1
NAMESPACE=$2

if [ -z "$RELEASE_NAME" ] || [ -z "$NAMESPACE" ]; then
    echo "Usage: $0 <release-name> <namespace>"
    exit 1
fi

echo "=== Troubleshooting Release: $RELEASE_NAME in $NAMESPACE ==="
echo

# 1. Check release status
echo "1. Release Status:"
helm status $RELEASE_NAME -n $NAMESPACE

echo
echo "2. Release History:"
helm history $RELEASE_NAME -n $NAMESPACE

echo
echo "3. Release Values:"
helm get values $RELEASE_NAME -n $NAMESPACE

echo
echo "4. Release Manifest:"
helm get manifest $RELEASE_NAME -n $NAMESPACE

echo
echo "5. Kubernetes Resources:"
kubectl get all -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo
echo "6. Pod Descriptions:"
kubectl describe pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo
echo "7. Recent Events:"
kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp | tail -20

echo
echo "8. Pod Logs (if available):"
pods=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)
for pod in $pods; do
    echo "--- Logs for $pod ---"
    kubectl logs $pod -n $NAMESPACE --tail=50
done
EOF

chmod +x troubleshoot-release.sh

# Test the troubleshooting script
./troubleshoot-release.sh webapp-prod production
```

### Task 3.3: Automated Release Validation

```bash
# Create release validation script
cat << 'EOF' > validate-release.sh
#!/bin/bash

RELEASE_NAME=$1
NAMESPACE=$2
TIMEOUT=${3:-300}  # 5 minutes default timeout

if [ -z "$RELEASE_NAME" ] || [ -z "$NAMESPACE" ]; then
    echo "Usage: $0 <release-name> <namespace> [timeout-seconds]"
    exit 1
fi

echo "=== Validating Release: $RELEASE_NAME in $NAMESPACE ==="

# 1. Check Helm release status
echo "1. Checking Helm release status..."
if ! helm status $RELEASE_NAME -n $NAMESPACE >/dev/null 2>&1; then
    echo "❌ Release $RELEASE_NAME not found in namespace $NAMESPACE"
    exit 1
fi

release_status=$(helm status $RELEASE_NAME -n $NAMESPACE -o json | jq -r '.info.status')
if [ "$release_status" != "deployed" ]; then
    echo "❌ Release status is $release_status (expected: deployed)"
    exit 1
fi
echo "✅ Release status: $release_status"

# 2. Check deployment rollout
echo "2. Checking deployment rollout..."
deployments=$(kubectl get deployment -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)

for deployment in $deployments; do
    echo "Checking $deployment..."
    if ! kubectl rollout status $deployment -n $NAMESPACE --timeout=${TIMEOUT}s; then
        echo "❌ Deployment rollout failed for $deployment"
        exit 1
    fi
    echo "✅ Deployment $deployment is ready"
done

# 3. Check pod readiness
echo "3. Checking pod readiness..."
pods=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)

for pod in $pods; do
    if ! kubectl wait $pod -n $NAMESPACE --for=condition=Ready --timeout=${TIMEOUT}s; then
        echo "❌ Pod $pod is not ready"
        exit 1
    fi
done
echo "✅ All pods are ready"

# 4. Run Helm tests if available
echo "4. Running Helm tests..."
if helm test $RELEASE_NAME -n $NAMESPACE --timeout=${TIMEOUT}s; then
    echo "✅ Helm tests passed"
else
    echo "⚠️ Helm tests failed or not available"
fi

echo
echo "🎉 Release validation completed successfully!"
EOF

chmod +x validate-release.sh

# Test validation
./validate-release.sh webapp-prod production
```

## Exercise 4: CI/CD Integration Patterns (5 minutes)

### Task 4.1: GitOps Style Release Management

```bash
# Create GitOps simulation script
cat << 'EOF' > gitops-deploy.sh
#!/bin/bash

# Simulate GitOps deployment pattern
ENVIRONMENT=$1
IMAGE_TAG=$2
CHART_VERSION=${3:-"0.1.0"}

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <environment> <image-tag> [chart-version]"
    echo "Example: $0 staging v1.2.3"
    exit 1
fi

echo "=== GitOps Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Image Tag: $IMAGE_TAG"
echo "Chart Version: $CHART_VERSION"
echo

# 1. Validate environment
case $ENVIRONMENT in
    development|staging|production)
        echo "✅ Valid environment: $ENVIRONMENT"
        ;;
    *)
        echo "❌ Invalid environment. Must be: development, staging, or production"
        exit 1
        ;;
esac

# 2. Check if namespace exists
if ! kubectl get namespace $ENVIRONMENT >/dev/null 2>&1; then
    echo "Creating namespace $ENVIRONMENT..."
    kubectl create namespace $ENVIRONMENT
fi

# 3. Determine values file
VALUES_FILE="values-${ENVIRONMENT}.yaml"
if [ ! -f "$VALUES_FILE" ]; then
    echo "❌ Values file $VALUES_FILE not found"
    exit 1
fi

# 4. Deploy or upgrade
RELEASE_NAME="webapp-${ENVIRONMENT}"

if helm status $RELEASE_NAME -n $ENVIRONMENT >/dev/null 2>&1; then
    echo "Upgrading existing release..."
    helm upgrade $RELEASE_NAME bitnami/nginx \
        --namespace $ENVIRONMENT \
        --values $VALUES_FILE \
        --set image.tag=$IMAGE_TAG \
        --set fullnameOverride=$RELEASE_NAME \
        --wait \
        --timeout=300s
else
    echo "Installing new release..."
    helm install $RELEASE_NAME bitnami/nginx \
        --namespace $ENVIRONMENT \
        --values $VALUES_FILE \
        --set image.tag=$IMAGE_TAG \
        --set fullnameOverride=$RELEASE_NAME \
        --wait \
        --timeout=300s
fi

# 5. Validate deployment
echo "Validating deployment..."
./validate-release.sh $RELEASE_NAME $ENVIRONMENT

echo "🎉 GitOps deployment completed!"
EOF

chmod +x gitops-deploy.sh

# Test GitOps deployment
./gitops-deploy.sh development 1.22-alpine
```

### Task 4.2: Blue-Green Deployment with Helm

```bash
# Create blue-green deployment script
cat << 'EOF' > blue-green-helm.sh
#!/bin/bash

ENVIRONMENT=${1:-"staging"}
NEW_VERSION=$2
CURRENT_COLOR=""
NEW_COLOR=""

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 [environment] <new-version>"
    echo "Example: $0 staging v1.2.3"
    exit 1
fi

echo "=== Blue-Green Deployment with Helm ==="

# 1. Determine current color
if helm status webapp-blue -n $ENVIRONMENT >/dev/null 2>&1; then
    CURRENT_COLOR="blue"
    NEW_COLOR="green"
elif helm status webapp-green -n $ENVIRONMENT >/dev/null 2>&1; then
    CURRENT_COLOR="green"
    NEW_COLOR="blue"
else
    echo "No existing deployment found. Starting with blue."
    CURRENT_COLOR=""
    NEW_COLOR="blue"
fi

echo "Current Color: ${CURRENT_COLOR:-none}"
echo "New Color: $NEW_COLOR"

# 2. Deploy new version
echo "Deploying $NEW_COLOR version..."
helm install webapp-$NEW_COLOR bitnami/nginx \
    --namespace $ENVIRONMENT \
    --values values-${ENVIRONMENT}.yaml \
    --set image.tag=$NEW_VERSION \
    --set fullnameOverride=webapp-$NEW_COLOR \
    --wait

# 3. Validate new deployment
echo "Validating new deployment..."
./validate-release.sh webapp-$NEW_COLOR $ENVIRONMENT

# 4. Switch traffic (simulate by updating service selector)
echo "Switching traffic to $NEW_COLOR..."
if kubectl get service webapp-service -n $ENVIRONMENT >/dev/null 2>&1; then
    kubectl patch service webapp-service -n $ENVIRONMENT \
        -p '{"spec":{"selector":{"app.kubernetes.io/instance":"webapp-'$NEW_COLOR'"}}}'
else
    # Create service pointing to new color
    kubectl expose deployment webapp-$NEW_COLOR \
        --name=webapp-service \
        --port=80 \
        --target-port=80 \
        --namespace=$ENVIRONMENT
fi

# 5. Clean up old version (optional)
if [ -n "$CURRENT_COLOR" ]; then
    echo "Removing old $CURRENT_COLOR deployment..."
    helm uninstall webapp-$CURRENT_COLOR -n $ENVIRONMENT
fi

echo "🎉 Blue-Green deployment completed!"
echo "Active version: $NEW_COLOR ($NEW_VERSION)"
EOF

chmod +x blue-green-helm.sh

# Test blue-green deployment
./blue-green-helm.sh staging 1.23-alpine
```

## Lab Validation

### Comprehensive Release Check

```bash
# Final validation of all releases
echo "=== Final Release Validation ==="

# Check all releases
helm list --all-namespaces

# Validate each environment
for env in development staging production; do
    echo
    echo "=== Environment: $env ==="
    kubectl get all -n $env
    
    # Check if validation script works
    releases=$(helm list -n $env --short)
    for release in $releases; do
        if [ -f "./validate-release.sh" ]; then
            ./validate-release.sh $release $env
        fi
    done
done
```

### Performance Testing

```bash
# Test release performance
kubectl run perf-test --image=busybox:1.35 --rm -it --restart=Never -- sh

# Inside the pod, test each environment:
# while true; do wget -qO- webapp-service.production.svc.cluster.local && sleep 1; done
```

## Cleanup

```bash
# Uninstall all releases
for env in development staging production; do
    releases=$(helm list -n $env --short)
    for release in $releases; do
        helm uninstall $release -n $env
    done
done

# Delete namespaces
kubectl delete namespace development staging production

# Clean up files
rm -f values-*.yaml
rm -f *.sh
rm -rf secure-webapp/
```

## Key Takeaways

1. **Environment separation** is crucial for release management
2. **Values files** enable environment-specific configurations
3. **Release promotion** should be automated and validated
4. **Security** must be built into the deployment process
5. **Monitoring** and troubleshooting are essential operations
6. **GitOps patterns** improve deployment reliability

## Best Practices

1. Use separate namespaces for different environments
2. Implement proper RBAC for release management
3. Always validate deployments before promoting
4. Keep secrets separate from charts
5. Monitor release health continuously
6. Implement automated rollback strategies
7. Use semantic versioning for releases
8. Document deployment procedures

## Common CKAD Scenarios

```bash
# 1. Multi-environment deployment
helm install app chart/ -n production --values production-values.yaml

# 2. Release promotion
helm upgrade app chart/ -n staging --set image.tag=v1.2.3

# 3. Rollback release
helm rollback app 2 -n production

# 4. Release validation
helm test app -n production

# 5. Release monitoring
helm status app -n production

# 6. Secret management
kubectl create secret generic app-secrets --from-literal=key=value
helm install app chart/ --set secrets.existingSecret=app-secrets
```

## Advanced Patterns

- **Canary deployments** with Helm and Flagger
- **Progressive delivery** with Argo Rollouts
- **Multi-cluster** release management
- **Helm plugins** for extended functionality
- **Policy enforcement** with OPA Gatekeeper