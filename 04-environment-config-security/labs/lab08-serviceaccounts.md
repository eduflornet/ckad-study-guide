# Lab 08: ServiceAccount Management

## Objective
Learn to create, configure, and manage ServiceAccounts for pod authentication and API access.

## Tasks

### Task 1: Basic ServiceAccount Creation

```bash
# Create ServiceAccounts using kubectl
kubectl create serviceaccount app-service-account
kubectl create serviceaccount monitoring-service-account
kubectl create serviceaccount backup-service-account
```

```yaml
# service-account-yaml.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: custom-service-account
  namespace: default
  labels:
    app: custom-app
  annotations:
    description: "Custom service account for application pods"
automountServiceAccountToken: true
```

### Task 2: ServiceAccount with Secrets

```yaml
# service-account-with-secret.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-with-secret
secrets:
- name: custom-secret-token
---
apiVersion: v1
kind: Secret
metadata:
  name: custom-secret-token
  annotations:
    kubernetes.io/service-account.name: sa-with-secret
type: kubernetes.io/service-account-token
data:
  extra-key: dmFsdWU=  # base64 encoded 'value'
```

### Task 3: ServiceAccount with imagePullSecrets

```bash
# Create docker registry secret
kubectl create secret docker-registry private-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=myemail@example.com
```

```yaml
# service-account-image-pull.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-with-image-pull
imagePullSecrets:
- name: private-registry-secret
```

### Task 4: Pod using ServiceAccount

```yaml
# pod-with-service-account.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-sa
spec:
  serviceAccountName: app-service-account
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "ServiceAccount information:"
      echo "Namespace: $(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
      echo "Token exists: $(test -f /var/run/secrets/kubernetes.io/serviceaccount/token && echo 'YES' || echo 'NO')"
      echo "CA cert exists: $(test -f /var/run/secrets/kubernetes.io/serviceaccount/ca.crt && echo 'YES' || echo 'NO')"
      ls -la /var/run/secrets/kubernetes.io/serviceaccount/
      sleep 3600
```

### Task 5: Disable Token Auto-mounting

```yaml
# pod-no-token.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-token
spec:
  serviceAccountName: app-service-account
  automountServiceAccountToken: false  # Disable token mounting
  containers:
  - name: app
    image: nginx:alpine
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Checking for service account token..."
      ls -la /var/run/secrets/kubernetes.io/serviceaccount/ 2>/dev/null || echo "No service account directory found"
      sleep 3600
```

### Task 6: ServiceAccount in Deployment

```yaml
# deployment-with-sa.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-sa
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-with-sa
  template:
    metadata:
      labels:
        app: app-with-sa
    spec:
      serviceAccountName: monitoring-service-account
      containers:
      - name: app
        image: nginx:alpine
        env:
        - name: SERVICE_ACCOUNT_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.serviceAccountName
        command: ["/bin/sh"]
        args:
        - -c
        - |
          echo "Pod using ServiceAccount: $SERVICE_ACCOUNT_NAME"
          echo "Namespace: $(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
          nginx -g 'daemon off;'
        ports:
        - containerPort: 80
```

### Task 7: ServiceAccount with RBAC

```yaml
# service-account-with-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-manager-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "create", "delete"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-manager-binding
subjects:
- kind: ServiceAccount
  name: pod-manager-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-manager-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 8: ServiceAccount API Access Test

```yaml
# api-access-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-access-test
spec:
  serviceAccountName: pod-manager-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Testing API access with ServiceAccount..."
      
      # Get current namespace
      NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
      echo "Current namespace: $NAMESPACE"
      
      # Test permissions
      echo "Testing permissions:"
      kubectl auth can-i get pods
      kubectl auth can-i create pods
      kubectl auth can-i delete pods
      kubectl auth can-i get secrets
      
      # List pods if allowed
      echo "Attempting to list pods:"
      kubectl get pods || echo "Failed to list pods"
      
      sleep 3600
```

### Task 9: Cross-namespace ServiceAccount Access

```bash
# Create test namespaces
kubectl create namespace namespace-a
kubectl create namespace namespace-b
```

```yaml
# cross-namespace-sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cross-namespace-sa
  namespace: namespace-a
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cross-namespace-role
  namespace: namespace-b
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cross-namespace-binding
  namespace: namespace-b
subjects:
- kind: ServiceAccount
  name: cross-namespace-sa
  namespace: namespace-a  # ServiceAccount from different namespace
roleRef:
  kind: Role
  name: cross-namespace-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Pod
metadata:
  name: cross-namespace-test
  namespace: namespace-a
spec:
  serviceAccountName: cross-namespace-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Testing cross-namespace access..."
      kubectl auth can-i get pods -n namespace-a
      kubectl auth can-i get pods -n namespace-b
      kubectl get pods -n namespace-b || echo "Access denied to namespace-b"
      sleep 3600
```

### Task 10: ServiceAccount Token Management

```yaml
# manual-token-creation.yaml
apiVersion: v1
kind: Secret
metadata:
  name: manual-sa-token
  annotations:
    kubernetes.io/service-account.name: backup-service-account
type: kubernetes.io/service-account-token
---
apiVersion: v1
kind: Pod
metadata:
  name: manual-token-pod
spec:
  serviceAccountName: backup-service-account
  containers:
  - name: app
    image: alpine:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Manual token information:"
      echo "Token from default mount:"
      ls -la /var/run/secrets/kubernetes.io/serviceaccount/
      echo ""
      echo "Manual token mount:"
      ls -la /var/run/secrets/manual-token/
      echo ""
      echo "Comparing tokens:"
      echo "Default token (first 20 chars):"
      head -c 20 /var/run/secrets/kubernetes.io/serviceaccount/token
      echo ""
      echo "Manual token (first 20 chars):"
      head -c 20 /var/run/secrets/manual-token/token
      sleep 3600
    volumeMounts:
    - name: manual-token
      mountPath: /var/run/secrets/manual-token
      readOnly: true
  volumes:
  - name: manual-token
    secret:
      secretName: manual-sa-token
```

### Task 11: ServiceAccount with Annotations and Labels

```yaml
# annotated-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: annotated-sa
  labels:
    app: web-application
    version: v1.0
    environment: production
  annotations:
    description: "Production web application service account"
    owner: "platform-team"
    contact: "platform-team@company.com"
    created-by: "kubectl"
    compliance.company.com/required: "true"
automountServiceAccountToken: true
imagePullSecrets:
- name: private-registry-secret
---
apiVersion: v1
kind: Pod
metadata:
  name: annotated-sa-pod
spec:
  serviceAccountName: annotated-sa
  containers:
  - name: web
    image: nginx:alpine
    ports:
    - containerPort: 80
```

## Verification Commands

```bash
# List ServiceAccounts
kubectl get serviceaccounts
kubectl get sa  # Short form

# Describe ServiceAccount details
kubectl describe serviceaccount app-service-account
kubectl describe sa monitoring-service-account

# Check ServiceAccount secrets
kubectl get serviceaccount app-service-account -o yaml
kubectl get secrets | grep service-account-token

# Check pod ServiceAccount usage
kubectl get pods -o custom-columns=NAME:.metadata.name,SERVICE_ACCOUNT:.spec.serviceAccountName

# Verify ServiceAccount token mounting
kubectl exec pod-with-sa -- ls -la /var/run/secrets/kubernetes.io/serviceaccount/
kubectl exec pod-with-sa -- cat /var/run/secrets/kubernetes.io/serviceaccount/namespace

# Test API access
kubectl logs api-access-test
kubectl exec api-access-test -- kubectl auth can-i get pods

# Check cross-namespace access
kubectl exec cross-namespace-test -n namespace-a -- kubectl auth can-i get pods -n namespace-b

# View ServiceAccount annotations and labels
kubectl get sa annotated-sa -o yaml | grep -A 10 -E "(annotations|labels):"

# Check imagePullSecrets
kubectl get sa sa-with-image-pull -o jsonpath='{.imagePullSecrets[*].name}'
```

## Troubleshooting ServiceAccounts

### Task 12: Common ServiceAccount Issues

```yaml
# troubleshooting-examples.yaml
apiVersion: v1
kind: Pod
metadata:
  name: sa-troubleshooting
spec:
  serviceAccountName: non-existent-sa  # This will cause issues
  containers:
  - name: app
    image: nginx:alpine
```

```bash
# Debug ServiceAccount issues
kubectl describe pod sa-troubleshooting
kubectl get events --sort-by='.lastTimestamp' | grep ServiceAccount

# Check if ServiceAccount exists
kubectl get sa non-existent-sa || echo "ServiceAccount does not exist"

# Verify RBAC permissions
kubectl auth can-i get pods --as=system:serviceaccount:default:pod-manager-sa
kubectl auth can-i create secrets --as=system:serviceaccount:default:pod-manager-sa

# Check token expiration (if applicable)
kubectl get secrets | grep service-account-token
kubectl describe secret <token-name>
```

## Cleanup

```bash
kubectl delete pod pod-with-sa pod-no-token api-access-test manual-token-pod annotated-sa-pod sa-troubleshooting cross-namespace-test
kubectl delete deployment app-with-sa
kubectl delete serviceaccount app-service-account monitoring-service-account backup-service-account custom-service-account sa-with-secret sa-with-image-pull pod-manager-sa cross-namespace-sa annotated-sa
kubectl delete secret private-registry-secret custom-secret-token manual-sa-token
kubectl delete role pod-manager-role cross-namespace-role
kubectl delete rolebinding pod-manager-binding cross-namespace-binding
kubectl delete namespace namespace-a namespace-b
```

## 🎯 Key Learning Points

- **Default ServiceAccount**: Every namespace has a 'default' ServiceAccount
- **Token Mounting**: Tokens are automatically mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`
- **automountServiceAccountToken**: Can be disabled at ServiceAccount or Pod level
- **imagePullSecrets**: Automatically added to pods using the ServiceAccount
- **RBAC Integration**: ServiceAccounts are subjects in RoleBindings/ClusterRoleBindings
- **Cross-namespace**: RoleBindings can reference ServiceAccounts from other namespaces
- **Annotations/Labels**: Use for metadata, ownership, and compliance tracking
- **Token Types**: Automatically generated vs manually created tokens
- **Security**: Use dedicated ServiceAccounts with minimal required permissions
- **API Access**: ServiceAccount tokens enable pod-to-API communication
- **Troubleshooting**: Check pod events, RBAC permissions, and token mounting
- **Best Practices**: One ServiceAccount per application/purpose, disable auto-mounting when not needed
