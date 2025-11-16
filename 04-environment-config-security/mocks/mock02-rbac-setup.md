# Mock 02: RBAC Configuration

## 🎯 Scenario Description
You are the platform engineer for a multi-tenant Kubernetes cluster. Three teams (development, testing, and operations) need different levels of access to cluster resources. You must implement a comprehensive RBAC strategy that provides appropriate permissions while maintaining security boundaries.

## 📋 Requirements

### Task 1: Namespace and Team Setup (10 minutes)
Create the following namespaces and team structure:

1. **Namespaces**: 
   - `team-development`
   - `team-testing` 
   - `team-operations`
   - `shared-services`

2. **ServiceAccounts** (one per team):
   - `dev-team-sa` in `team-development`
   - `test-team-sa` in `team-testing`
   - `ops-team-sa` in `team-operations`

### Task 2: Development Team Permissions (15 minutes)
Configure RBAC for the development team:

**Permissions in `team-development` namespace**:
- Full access to: pods, services, configmaps, secrets, deployments, replicasets
- Read-only access to: events, endpoints

**Permissions in `shared-services` namespace**:
- Read-only access to: services, endpoints

**Cluster-level permissions**:
- Read-only access to: nodes (to check resource availability)

### Task 3: Testing Team Permissions (15 minutes)
Configure RBAC for the testing team:

**Permissions in `team-testing` namespace**:
- Full access to: pods, services, configmaps, deployments, replicasets
- Read-only access to: secrets, events

**Permissions in `team-development` namespace**:
- Read-only access to: deployments, services (to test integration)

**Cross-namespace permissions**:
- Read access to specific ConfigMaps in `shared-services`

### Task 4: Operations Team Permissions (15 minutes)
Configure RBAC for the operations team:

**Cluster-wide permissions**:
- Full access to: nodes, namespaces, persistentvolumes
- Read access to: all pods, services, deployments across all namespaces
- Ability to create/delete namespaces

**Monitoring permissions**:
- Access to metrics and logs (if monitoring tools are deployed)

**Emergency permissions**:
- Ability to delete any pod in any namespace (for incident response)

### Task 5: Permission Testing and Validation (5 minutes)
Create test pods for each team to validate their permissions:

1. Verify each team can only access their intended resources
2. Test cross-namespace permissions work correctly
3. Confirm operations team has cluster-wide access
4. Validate that restricted operations fail as expected

## 🚀 Solution

### Step 1: Create Namespaces and ServiceAccounts

```bash
# Create namespaces
kubectl create namespace team-development
kubectl create namespace team-testing
kubectl create namespace team-operations
kubectl create namespace shared-services

# Create ServiceAccounts
kubectl create serviceaccount dev-team-sa -n team-development
kubectl create serviceaccount test-team-sa -n team-testing
kubectl create serviceaccount ops-team-sa -n team-operations
```

### Step 2: Development Team RBAC

```yaml
# dev-team-rbac.yaml
# Role for development namespace - full access
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: team-development
  name: dev-team-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "endpoints"]
  verbs: ["get", "list", "create", "update", "patch", "delete", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete", "watch"]
---
# Role for shared-services - read-only
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: shared-services
  name: dev-shared-services-role
rules:
- apiGroups: [""]
  resources: ["services", "endpoints"]
  verbs: ["get", "list", "watch"]
---
# ClusterRole for node access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dev-nodes-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
---
# RoleBindings
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-team-binding
  namespace: team-development
subjects:
- kind: ServiceAccount
  name: dev-team-sa
  namespace: team-development
roleRef:
  kind: Role
  name: dev-team-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-shared-binding
  namespace: shared-services
subjects:
- kind: ServiceAccount
  name: dev-team-sa
  namespace: team-development
roleRef:
  kind: Role
  name: dev-shared-services-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dev-nodes-binding
subjects:
- kind: ServiceAccount
  name: dev-team-sa
  namespace: team-development
roleRef:
  kind: ClusterRole
  name: dev-nodes-reader
  apiGroup: rbac.authorization.k8s.io
```

### Step 3: Testing Team RBAC

```yaml
# test-team-rbac.yaml
# Role for testing namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: team-testing
  name: test-team-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "create", "update", "patch", "delete", "watch"]
- apiGroups: [""]
  resources: ["secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete", "watch"]
---
# Role for development namespace - read-only
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: team-development
  name: test-dev-reader-role
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list", "watch"]
---
# Role for shared-services - specific ConfigMaps
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: shared-services
  name: test-shared-config-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["test-config", "integration-config"]
  verbs: ["get", "list", "watch"]
---
# RoleBindings
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-team-binding
  namespace: team-testing
subjects:
- kind: ServiceAccount
  name: test-team-sa
  namespace: team-testing
roleRef:
  kind: Role
  name: test-team-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-dev-reader-binding
  namespace: team-development
subjects:
- kind: ServiceAccount
  name: test-team-sa
  namespace: team-testing
roleRef:
  kind: Role
  name: test-dev-reader-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-shared-config-binding
  namespace: shared-services
subjects:
- kind: ServiceAccount
  name: test-team-sa
  namespace: team-testing
roleRef:
  kind: Role
  name: test-shared-config-role
  apiGroup: rbac.authorization.k8s.io
```

### Step 4: Operations Team RBAC

```yaml
# ops-team-rbac.yaml
# ClusterRole for operations team
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ops-team-cluster-role
rules:
# Full access to cluster resources
- apiGroups: [""]
  resources: ["nodes", "namespaces", "persistentvolumes", "persistentvolumeclaims"]
  verbs: ["get", "list", "create", "update", "patch", "delete", "watch"]
# Read access to all workloads
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
# Emergency pod deletion
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["delete"]
# Namespace management
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["create", "delete"]
# Monitoring access (metrics)
- apiGroups: ["metrics.k8s.io"]
  resources: ["pods", "nodes"]
  verbs: ["get", "list"]
---
# Additional role for logs access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ops-logs-reader
rules:
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
---
# ClusterRoleBindings
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ops-team-cluster-binding
subjects:
- kind: ServiceAccount
  name: ops-team-sa
  namespace: team-operations
roleRef:
  kind: ClusterRole
  name: ops-team-cluster-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ops-logs-binding
subjects:
- kind: ServiceAccount
  name: ops-team-sa
  namespace: team-operations
roleRef:
  kind: ClusterRole
  name: ops-logs-reader
  apiGroup: rbac.authorization.k8s.io
```

### Step 5: Create Test Resources

```yaml
# test-resources.yaml
# ConfigMaps for testing
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
  namespace: shared-services
data:
  test.property: "allowed-access"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: integration-config
  namespace: shared-services
data:
  integration.endpoint: "http://api.example.com"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: restricted-config
  namespace: shared-services
data:
  secret.key: "not-accessible-to-test-team"
---
# Sample deployment in development
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: team-development
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
      - name: app
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: sample-service
  namespace: team-development
spec:
  selector:
    app: sample-app
  ports:
  - port: 80
    targetPort: 80
```

### Step 6: Permission Testing Pods

```yaml
# permission-test-pods.yaml
# Development team test pod
apiVersion: v1
kind: Pod
metadata:
  name: dev-team-test
  namespace: team-development
spec:
  serviceAccountName: dev-team-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== Development Team Permission Test ==="
      echo "Testing permissions in team-development namespace:"
      kubectl auth can-i create pods
      kubectl auth can-i delete secrets
      kubectl auth can-i get nodes
      
      echo "Testing permissions in shared-services namespace:"
      kubectl auth can-i get services -n shared-services
      kubectl auth can-i create pods -n shared-services
      
      echo "Testing forbidden operations:"
      kubectl auth can-i delete namespaces
      kubectl auth can-i get pods -n team-testing
      
      sleep 3600
---
# Testing team test pod
apiVersion: v1
kind: Pod
metadata:
  name: test-team-test
  namespace: team-testing
spec:
  serviceAccountName: test-team-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== Testing Team Permission Test ==="
      echo "Testing permissions in team-testing namespace:"
      kubectl auth can-i create pods
      kubectl auth can-i delete secrets
      kubectl auth can-i get secrets
      
      echo "Testing cross-namespace permissions:"
      kubectl auth can-i get deployments -n team-development
      kubectl auth can-i get configmaps -n shared-services
      
      echo "Testing specific ConfigMap access:"
      kubectl get configmap test-config -n shared-services || echo "Access denied"
      kubectl get configmap restricted-config -n shared-services || echo "Access denied as expected"
      
      sleep 3600
---
# Operations team test pod
apiVersion: v1
kind: Pod
metadata:
  name: ops-team-test
  namespace: team-operations
spec:
  serviceAccountName: ops-team-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== Operations Team Permission Test ==="
      echo "Testing cluster-wide permissions:"
      kubectl auth can-i get nodes
      kubectl auth can-i create namespaces
      kubectl auth can-i delete pods --all-namespaces
      
      echo "Testing monitoring access:"
      kubectl auth can-i get pods --all-namespaces
      kubectl auth can-i get pods/log --all-namespaces
      
      echo "Listing resources across namespaces:"
      kubectl get pods --all-namespaces | head -10
      kubectl get nodes
      
      sleep 3600
```

## ✅ Verification Commands

```bash
# Apply all RBAC configurations
kubectl apply -f dev-team-rbac.yaml
kubectl apply -f test-team-rbac.yaml
kubectl apply -f ops-team-rbac.yaml
kubectl apply -f test-resources.yaml
kubectl apply -f permission-test-pods.yaml

# Check RBAC objects
kubectl get roles,rolebindings --all-namespaces | grep -E "(dev-team|test-team|ops-team)"
kubectl get clusterroles,clusterrolebindings | grep -E "(dev-|test-|ops-)"

# Test development team permissions
kubectl auth can-i create pods --as=system:serviceaccount:team-development:dev-team-sa -n team-development
kubectl auth can-i get nodes --as=system:serviceaccount:team-development:dev-team-sa
kubectl auth can-i delete namespaces --as=system:serviceaccount:team-development:dev-team-sa

# Test testing team permissions
kubectl auth can-i get deployments --as=system:serviceaccount:team-testing:test-team-sa -n team-development
kubectl auth can-i create secrets --as=system:serviceaccount:team-testing:test-team-sa -n team-testing
kubectl auth can-i get configmaps --as=system:serviceaccount:team-testing:test-team-sa -n shared-services

# Test operations team permissions
kubectl auth can-i delete pods --as=system:serviceaccount:team-operations:ops-team-sa --all-namespaces
kubectl auth can-i create namespaces --as=system:serviceaccount:team-operations:ops-team-sa
kubectl auth can-i get nodes --as=system:serviceaccount:team-operations:ops-team-sa

# Check test pod logs
kubectl logs dev-team-test -n team-development
kubectl logs test-team-test -n team-testing
kubectl logs ops-team-test -n team-operations

# Verify specific resource access
kubectl get configmap test-config -n shared-services --as=system:serviceaccount:team-testing:test-team-sa
kubectl get configmap restricted-config -n shared-services --as=system:serviceaccount:team-testing:test-team-sa || echo "Access denied as expected"
```

## 🎯 Success Criteria

- ✅ Development team has full access to their namespace and read access to nodes
- ✅ Testing team can read dev deployments and specific shared ConfigMaps
- ✅ Operations team has cluster-wide monitoring and emergency deletion rights
- ✅ Cross-namespace permissions work as specified
- ✅ Forbidden operations are properly blocked
- ✅ Resource-specific permissions (ConfigMap names) are enforced
- ✅ All teams can only access their intended resources

## 🧹 Cleanup

```bash
kubectl delete namespace team-development team-testing team-operations shared-services
kubectl delete clusterrole dev-nodes-reader ops-team-cluster-role ops-logs-reader
kubectl delete clusterrolebinding dev-nodes-binding ops-team-cluster-binding ops-logs-binding
```

## 📚 Key Learning Points

- **Namespace Isolation**: Each team has their own namespace with appropriate permissions
- **Cross-namespace Access**: Controlled access between teams using RoleBindings
- **Cluster-level Permissions**: Operations team needs ClusterRole/ClusterRoleBinding
- **Resource-specific Access**: Testing team limited to specific ConfigMap names
- **Principle of Least Privilege**: Each team gets minimum necessary permissions
- **Permission Testing**: Systematic validation of RBAC policies
- **Role Composition**: Combining multiple roles for complex permission sets
- **Security Boundaries**: Clear separation between team capabilities
