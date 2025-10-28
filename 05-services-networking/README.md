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

### Lab 1: Services
- [ClusterIP service](labs/lab01-clusterip-service.md)
- [NodePort service](labs/lab02-nodeport-service.md)
- [LoadBalancer service](labs/lab03-loadbalancer-service.md)
- [Headless service](labs/lab04-headless-service.md)

### Lab 2: Ingress
- [Basic Ingress setup](labs/lab05-basic-ingress.md)
- [Path-based routing](labs/lab06-path-routing.md)
- [Host-based routing](labs/lab07-host-routing.md)
- [TLS configuration](labs/lab08-tls-ingress.md)

### Lab 3: Network Policies
- [Default deny policy](labs/lab09-default-deny.md)
- [Allow specific traffic](labs/lab10-allow-traffic.md)
- [Namespace isolation](labs/lab11-namespace-isolation.md)

## ⚡ Quick Drills

```bash
# Services
kubectl expose deployment nginx --port=80 --type=ClusterIP
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl create service clusterip my-service --tcp=80:8080

# Check service endpoints
kubectl get endpoints
kubectl describe service nginx

# Ingress
kubectl create ingress simple --rule="foo.com/bar*=service1:8080"

# Network policies
kubectl label namespace default name=default
kubectl apply -f network-policy.yaml

# Service discovery
kubectl run test-pod --image=busybox -it --rm -- nslookup nginx
```

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