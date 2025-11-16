# Lab 09: Permission Testing

## Objective
Learn to test and validate RBAC permissions systematically to ensure security policies are working correctly.

## Tasks

### Task 1: Basic Permission Testing Setup

```bash
# Create test namespaces
kubectl create namespace permission-test
kubectl create namespace restricted-zone
kubectl create namespace public-zone
```

```yaml
# test-service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: developer-sa
  namespace: permission-test
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: viewer-sa
  namespace: permission-test
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-sa
  namespace: permission-test
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: restricted-sa
  namespace: permission-test
```

### Task 2: Create Test Roles and Bindings

```yaml
# test-roles.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: permission-test
  name: developer-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: permission-test
  name: viewer-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: restricted-zone
  name: restricted-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
  resourceNames: ["allowed-pod-1", "allowed-pod-2"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-viewer-role
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
# RoleBindings
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: permission-test
subjects:
- kind: ServiceAccount
  name: developer-sa
  namespace: permission-test
roleRef:
  kind: Role
  name: developer-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: viewer-binding
  namespace: permission-test
subjects:
- kind: ServiceAccount
  name: viewer-sa
  namespace: permission-test
roleRef:
  kind: Role
  name: viewer-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: restricted-binding
  namespace: restricted-zone
subjects:
- kind: ServiceAccount
  name: restricted-sa
  namespace: permission-test
roleRef:
  kind: Role
  name: restricted-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-viewer-binding
subjects:
- kind: ServiceAccount
  name: admin-sa
  namespace: permission-test
roleRef:
  kind: ClusterRole
  name: cluster-viewer-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 3: Permission Testing Scripts

```yaml
# permission-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: permission-tester
  namespace: permission-test
spec:
  serviceAccountName: developer-sa
  containers:
  - name: tester
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "=== Permission Testing for developer-sa ==="
      echo "Namespace: $(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
      echo ""
      
      echo "Testing basic permissions:"
      echo "Can I get pods? $(kubectl auth can-i get pods && echo 'YES' || echo 'NO')"
      echo "Can I create pods? $(kubectl auth can-i create pods && echo 'YES' || echo 'NO')"
      echo "Can I delete pods? $(kubectl auth can-i delete pods && echo 'YES' || echo 'NO')"
      echo "Can I get secrets? $(kubectl auth can-i get secrets && echo 'YES' || echo 'NO')"
      echo "Can I create secrets? $(kubectl auth can-i create secrets && echo 'YES' || echo 'NO')"
      echo ""
      
      echo "Testing cross-namespace permissions:"
      echo "Can I get pods in default? $(kubectl auth can-i get pods -n default && echo 'YES' || echo 'NO')"
      echo "Can I get pods in restricted-zone? $(kubectl auth can-i get pods -n restricted-zone && echo 'YES' || echo 'NO')"
      echo ""
      
      echo "Testing cluster-level permissions:"
      echo "Can I get nodes? $(kubectl auth can-i get nodes && echo 'YES' || echo 'NO')"
      echo "Can I get namespaces? $(kubectl auth can-i get namespaces && echo 'YES' || echo 'NO')"
      echo ""
      
      echo "Listing all permissions:"
      kubectl auth can-i --list
      
      sleep 3600
```

### Task 4: Comprehensive Permission Testing

```bash
# Create a script for systematic testing
cat > test-permissions.sh << 'EOF'
#!/bin/bash

# Function to test permissions for a service account
test_permissions() {
    local sa_name=$1
    local namespace=${2:-permission-test}
    
    echo "=== Testing permissions for $sa_name in $namespace ==="
    
    # Basic resource operations
    resources=("pods" "services" "configmaps" "secrets" "deployments")
    verbs=("get" "list" "create" "update" "delete")
    
    for resource in "${resources[@]}"; do
        echo "Testing $resource:"
        for verb in "${verbs[@]}"; do
            result=$(kubectl auth can-i $verb $resource --as=system:serviceaccount:$namespace:$sa_name -n $namespace 2>/dev/null && echo "✓" || echo "✗")
            printf "  %-8s: %s\n" "$verb" "$result"
        done
        echo ""
    done
    
    # Cross-namespace testing
    echo "Cross-namespace permissions:"
    echo "  default namespace:"
    echo "    get pods: $(kubectl auth can-i get pods --as=system:serviceaccount:$namespace:$sa_name -n default 2>/dev/null && echo "✓" || echo "✗")"
    echo "  restricted-zone namespace:"
    echo "    get pods: $(kubectl auth can-i get pods --as=system:serviceaccount:$namespace:$sa_name -n restricted-zone 2>/dev/null && echo "✓" || echo "✗")"
    
    # Cluster-level permissions
    echo "Cluster-level permissions:"
    echo "    get nodes: $(kubectl auth can-i get nodes --as=system:serviceaccount:$namespace:$sa_name 2>/dev/null && echo "✓" || echo "✗")"
    echo "    get namespaces: $(kubectl auth can-i get namespaces --as=system:serviceaccount:$namespace:$sa_name 2>/dev/null && echo "✓" || echo "✗")"
    
    echo "================================================"
    echo ""
}

# Test all service accounts
test_permissions "developer-sa"
test_permissions "viewer-sa"
test_permissions "admin-sa"
test_permissions "restricted-sa"
