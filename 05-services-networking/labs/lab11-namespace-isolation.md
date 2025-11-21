# Lab 11: Namespace Isolation with NetworkPolicy

**Learning Objective**: Isolate namespaces using NetworkPolicy to prevent cross-namespace communication.

**Time**: 20 minutes

## 📋 Prerequisites
- Kubernetes cluster running
- kubectl configured
- Network plugin supporting NetworkPolicy

## 🎯 Lab Overview
You will create policies to ensure pods in one namespace cannot communicate with pods in another, enforcing strict isolation.

## 📝 Tasks

### Task 1: Create Namespaces and Deployments
```bash
kubectl create namespace team-a
kubectl create namespace team-b
kubectl run app-a --image=nginx --namespace=team-a --labels="app=a"
kubectl run app-b --image=nginx --namespace=team-b --labels="app=b"
```

### Task 2: Apply Namespace Isolation Policy
```yaml
# namespace-isolation.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-cross-namespace
  namespace: team-a
spec:
  podSelector: {}
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: team-a
```
Apply the policy:
```bash
kubectl apply -f namespace-isolation.yaml
```

### Task 3: Test Isolation
- Try to access `app-a` from `team-b` (should fail).
- Access within `team-a` should succeed.

### Task 4: Repeat for Other Namespace (Optional)
- Apply similar policy in `team-b` for full isolation.

## ✅ Verification Steps
- Confirm cross-namespace traffic is blocked.
- Use `kubectl describe networkpolicy deny-cross-namespace -n team-a`.

## 🧹 Cleanup
```bash
kubectl delete namespace team-a
kubectl delete namespace team-b
```

## 📚 Key Learnings
- Namespace isolation is critical for multi-team clusters.
- NetworkPolicy can enforce strict boundaries.

## 📖 Additional Resources
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)