# Lab 06: RBAC Basics

## Objective
Learn to implement Role-Based Access Control (RBAC) in Kubernetes to manage permissions and secure access to resources.

## Tasks

### Task 1: Create Service Accounts

```bash
# Create service accounts for different roles
kubectl create serviceaccount developer-sa
kubectl create serviceaccount viewer-sa
kubectl create serviceaccount admin-sa
kubectl create serviceaccount pod-reader-sa
```

### Task 2: Basic Role and RoleBinding

```yaml
# developer-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: developer-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: developer-sa
  namespace: default
roleRef:
  kind: Role
  name: developer-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 3: Read-only Role

```yaml
# viewer-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: viewer-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: viewer-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: viewer-sa
  namespace: default
roleRef:
  kind: Role
  name: viewer-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 4: Specific Resource Role

```yaml
# pod-reader-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods/status"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: pod-reader-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 5: ClusterRole and ClusterRoleBinding

```yaml
# cluster-admin-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-admin-role
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-binding
subjects:
- kind: ServiceAccount
  name: admin-sa
  namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-admin-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 6: Test Permissions with Pods

```yaml
# test-developer-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-developer-pod
spec:
  serviceAccountName: developer-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Testing developer permissions..."
      kubectl auth can-i create pods
      kubectl auth can-i delete deployments
      kubectl auth can-i get secrets
      kubectl auth can-i create namespaces
      sleep 3600
---
apiVersion: v1
kind: Pod
metadata:
  name: test-viewer-pod
spec:
  serviceAccountName: viewer-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Testing viewer permissions..."
      kubectl auth can-i get pods
      kubectl auth can-i create pods
      kubectl auth can-i delete services
      kubectl auth can-i get secrets
      sleep 3600
---
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-reader-pod
spec:
  serviceAccountName: pod-reader-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Testing pod-reader permissions..."
      kubectl auth can-i get pods
      kubectl auth can-i get pods/log
      kubectl auth can-i create pods
      kubectl auth can-i get services
      sleep 3600
```

### Task 7: Resource-specific Permissions

```yaml
# secret-manager-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: secret-manager-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secret-manager-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: secret-manager-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: secret-manager-sa
  namespace: default
roleRef:
  kind: Role
  name: secret-manager-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 8: Named Resource Permissions

```yaml
# specific-resource-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: specific-resource-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config", "feature-flags"]
  verbs: ["get", "update"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["db-credentials"]
  verbs: ["get"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: specific-resource-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: specific-resource-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: specific-resource-sa
  namespace: default
roleRef:
  kind: Role
  name: specific-resource-role
  apiGroup: rbac.authorization.k8s.io
```

### Task 9: Multiple Namespace Access

```bash
# Create additional namespaces for testing
kubectl create namespace dev
kubectl create namespace staging
```

```yaml
# multi-namespace-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: dev-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: staging
  name: staging-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: multi-namespace-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-binding
  namespace: dev
subjects:
- kind: ServiceAccount
  name: multi-namespace-sa
  namespace: default
roleRef:
  kind: Role
  name: dev-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: staging-binding
  namespace: staging
subjects:
- kind: ServiceAccount
  name: multi-namespace-sa
  namespace: default
roleRef:
  kind: Role
  name: staging-role
  apiGroup: rbac.authorization.k8s.io
```

## Verification Commands

```bash
# Check service accounts
kubectl get serviceaccounts

# Check roles and cluster roles
kubectl get roles
kubectl get clusterroles | grep -E "(cluster-admin-role|developer-role)"

# Check role bindings
kubectl get rolebindings
kubectl get clusterrolebindings | grep cluster-admin-binding

# Describe roles to see permissions
kubectl describe role developer-role
kubectl describe role viewer-role
kubectl describe clusterrole cluster-admin-role

# Test permissions directly
kubectl auth can-i create pods --as=system:serviceaccount:default:developer-sa
kubectl auth can-i delete services --as=system:serviceaccount:default:viewer-sa
kubectl auth can-i get secrets --as=system:serviceaccount:default:pod-reader-sa

# Check what a service account can do
kubectl auth can-i --list --as=system:serviceaccount:default:developer-sa

# Test cross-namespace permissions
kubectl auth can-i create pods --as=system:serviceaccount:default:multi-namespace-sa -n dev
kubectl auth can-i create pods --as=system:serviceaccount:default:multi-namespace-sa -n staging

# Check pod logs for permission tests
kubectl logs test-developer-pod
kubectl logs test-viewer-pod
kubectl logs test-pod-reader-pod
```

## Advanced RBAC Scenarios

### Task 10: Aggregated ClusterRoles

```yaml
# aggregated-cluster-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-reader
  labels:
    rbac.example.com/aggregate-to-monitoring: "true"
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aggregated-monitoring
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.example.com/aggregate-to-monitoring: "true"
rules: [] # Rules are automatically filled in by the controller manager
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: monitoring-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: monitoring-binding
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: default
roleRef:
  kind: ClusterRole
  name: aggregated-monitoring
  apiGroup: rbac.authorization.k8s.io
```

## Cleanup

```bash
kubectl delete pod test-developer-pod test-viewer-pod test-pod-reader-pod
kubectl delete serviceaccount developer-sa viewer-sa admin-sa pod-reader-sa secret-manager-sa specific-resource-sa multi-namespace-sa monitoring-sa
kubectl delete role developer-role viewer-role pod-reader-role secret-manager-role specific-resource-role dev-role staging-role
kubectl delete rolebinding developer-binding viewer-binding pod-reader-binding secret-manager-binding specific-resource-binding dev-binding staging-binding
kubectl delete clusterrole cluster-admin-role monitoring-reader aggregated-monitoring
kubectl delete clusterrolebinding cluster-admin-binding monitoring-binding
kubectl delete namespace dev staging
```

## 🎯 Key Learning Points

- **Role vs ClusterRole**: Role for namespace-scoped, ClusterRole for cluster-wide resources
- **RoleBinding vs ClusterRoleBinding**: Binding determines the scope of access
- **Service Accounts**: Identity for pods to interact with Kubernetes API
- **Verbs**: get, list, watch, create, update, patch, delete
- **API Groups**: Core (""), apps, extensions, etc.
- **Resource Names**: Restrict access to specific resources
- **Aggregation**: Combine multiple ClusterRoles automatically
- **Testing**: Use `kubectl auth can-i` to verify permissions
- **Principle of Least Privilege**: Grant minimum necessary permissions
- **Cross-namespace**: RoleBindings can reference ServiceAccounts from other namespaces
- **Built-in Roles**: system:admin, cluster-admin, edit, view
- **Troubleshooting**: Check RBAC with `kubectl describe` and `kubectl auth can-i`
