# Services and Networking (20%)

## 📚 Topics Covered

### Services
- ClusterIP, NodePort, LoadBalancer
- Service discovery
- Endpoints and EndpointSlices
- Headless services

### Ingress
- Ingress controllers
- Path-based routing
- Host-based routing
- TLS termination

### Network Policies
- Pod-to-pod communication
- Ingress and egress rules
- Namespace isolation
- Label selectors

## 🛠️ Practice Labs

### Labs: Services
- [1. ClusterIP service](labs/lab01-clusterip-service.md)
- [2. NodePort service](labs/lab02-nodeport-service.md)
- [3. LoadBalancer service](labs/lab03-loadbalancer-service.md)
- [4. Headless service](labs/lab04-headless-service.md)

### Labs: Ingress
- [5. Basic Ingress setup](labs/lab05-basic-ingress.md)
- [6. Path-based routing](labs/lab06-path-routing.md)
- [7. Host-based routing](labs/lab07-host-routing.md)
- [8. TLS configuration](labs/lab08-tls-ingress.md)

### Labs: Network Policies
- [9. Default deny policy](labs/lab09-default-deny.md)
- [10. Allow specific traffic](labs/lab10-allow-traffic.md)
- [11. Namespace isolation](labs/lab11-namespace-isolation.md)

## ⚡ Quick Drills

```bash
🔹 Services
kubectl expose deployment nginx --port=80 --type=ClusterIP
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl create service clusterip my-service --tcp=80:8080

# Create a ClusterIP Service (default):
kubectl expose pod mypod --port=80 --target-port=8080

# Create a Deployment Service:
kubectl expose deployment myapp --port=80 --target-port=8080

# NodePort Service:
kubectl expose deployment myapp --port=80 --target-port=8080 --type=NodePort

# View Details:
kubectl get svc
kubectl describe svc myapp


# Check service endpoints
kubectl get endpoints
kubectl describe service nginx

🔹 Networking (Ingress)

# Create an basic ingress
kubectl create ingress simple --rule="myapp.example.com/*=myapp:80"

# Edit inmgress rules:
kubectl edit ingress myingress

🔹 Network Policies
# Create an imperative NetworkPolicy (example: deny all incoming traffic)
kubectl create networkpolicy deny-all --pod-selector=app=myapp --policy-types=Ingress

# Add ingress rules
kubectl create networkpolicy allow-nginx --pod-selector=app=nginx \
  --ingress --from-pod-selector=app=frontend

# Network policies
kubectl label namespace default name=default
kubectl apply -f network-policy.yaml

# Service discovery
kubectl run test-pod --image=busybox -it --rm -- nslookup nginx
```
🎯 Recommended approach for the exam
Memorize the key flags: --port, --target-port, --type, --rule, --pod-selector, --policy-types.

Practice with `kubectl expose` and `kubectl create ingress/networkpolicy`, as these are the most frequently used in exam scenarios.

Supplement your practice with `kubectl run` and `kubectl create deployment`, because the exam often requires you to start a pod or deployment and then expose it.

Use `kubectl explain <resource>` during the exam to remember YAML fields if you decide to convert imperatives into manifests.

## 🎯 Mock Scenarios

- [Mock 1: Multi-tier application networking](mocks/mock01-multi-tier-networking.md)
- [Mock 2: Ingress with multiple backends](mocks/mock02-complex-ingress.md)
- [Mock 3: Network security policies](mocks/mock03-network-security.md)

## 🔑 Key Concepts to Master

- [ ] Understand different service types
- [ ] Configure Ingress for HTTP routing
- [ ] Implement network policies for security
- [ ] Use service discovery mechanisms
- [ ] Debug networking issues
- [ ] Configure TLS termination

## 📝 Common Exam Tasks

1. "Expose a deployment as a LoadBalancer service"
2. "Create an Ingress with path-based routing"
3. "Implement a network policy to isolate pods"
4. "Configure a headless service for StatefulSet"
5. "Set up TLS termination on Ingress"