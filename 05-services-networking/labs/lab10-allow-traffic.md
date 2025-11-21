# Lab 10: Allow Traffic with NetworkPolicy

**Learning Objective**: Create a NetworkPolicy to allow specific traffic between pods and namespaces.

**Time**: 20 minutes

## 📋 Prerequisites
- Kubernetes cluster running
- kubectl configured
- Network plugin supporting NetworkPolicy

## 🎯 Lab Overview
You will create a policy that allows traffic only from selected pods or namespaces, demonstrating fine-grained access control.

## 📝 Tasks

### Task 1: Setup Namespaces and Deployments
```bash
kubectl create namespace frontend
kubectl create namespace backend
kubectl run web --image=nginx --namespace=frontend --labels="app=web"
kubectl run api --image=nginx --namespace=backend --labels="app=api"
```

### Task 2: Create NetworkPolicy to Allow Traffic
```yaml
# allow-frontend-to-backend.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
```
Apply the policy:
```bash
kubectl apply -f allow-frontend-to-backend.yaml
```

### Task 3: Test Connectivity
- From a pod in `frontend`, try to access the `api` pod in `backend`.
- From other namespaces, access should be denied.

### Task 4: Expand Policy (Optional)
- Allow traffic from additional namespaces or pods as needed.

## ✅ Verification Steps
- Confirm only allowed traffic is permitted.
- Use `kubectl describe networkpolicy allow-frontend-to-backend -n backend`.

## 🧹 Cleanup
```bash
kubectl delete namespace frontend
kubectl delete namespace backend
```

## 📚 Key Learnings
- NetworkPolicy enables fine-grained access control.
- Use selectors to define allowed sources.

## 📖 Additional Resources
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)