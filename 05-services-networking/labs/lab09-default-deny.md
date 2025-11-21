# Lab 9: Default Deny Network Policy

**Learning Objective**: Implement a default deny network policy to restrict all pod-to-pod communication by default.

**Time**: 20 minutes

## 📋 Prerequisites
- Kubernetes cluster running
- kubectl configured
- Network plugin supporting NetworkPolicy (Calico, Cilium, etc.)

## 🎯 Lab Overview
A default deny policy blocks all ingress and egress traffic to pods in a namespace unless explicitly allowed. This is a security best practice for zero-trust networking.

## 📝 Tasks

### Task 1: Create a Namespace and Deployment
```bash
kubectl create namespace secure-apps
kubectl run test-app --image=nginx --namespace=secure-apps --labels="app=test"
```

### Task 2: Apply Default Deny Policy
```yaml
# default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: secure-apps
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```
Apply the policy:
```bash
kubectl apply -f default-deny.yaml
```

### Task 3: Test Connectivity
- Try to connect to the pod from another pod in the same namespace:
```bash
kubectl run busybox --rm -it --image=busybox --namespace=secure-apps -- sh
wget -O- http://test-app
```
- Connection should fail.

### Task 4: Allow Specific Traffic (Optional)
Add a rule to allow traffic from a specific pod or namespace.

## ✅ Verification Steps
- Confirm no pod-to-pod traffic is allowed by default.
- Check `kubectl describe networkpolicy default-deny -n secure-apps`.

## 🧹 Cleanup
```bash
kubectl delete namespace secure-apps
```

## 📚 Key Learnings
- Default deny policies enforce zero-trust networking.
- Only explicitly allowed traffic is permitted.
- Essential for security-sensitive workloads.

## 📖 Additional Resources
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)