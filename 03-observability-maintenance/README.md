# Application Observability and Maintenance (15%)

## 📚 Topics Covered

### Health Probes
- Liveness probes
- Readiness probes
- Startup probes
- Probe configuration

### Monitoring and Logging
- Container logs
- Application metrics
- Resource monitoring
- Debugging techniques

### Troubleshooting
- Pod debugging
- Network issues
- Resource problems
- Application failures

## 🛠️ Practice Labs

### Lab 1: Health Probes
- [Configure liveness probes](labs/lab01-liveness-probes.md)
- [Set up readiness probes](labs/lab02-readiness-probes.md)
- [Implement startup probes](labs/lab03-startup-probes.md)

### Lab 2: Monitoring
- [Container log analysis](labs/lab04-log-analysis.md)
- [Resource monitoring](labs/lab05-resource-monitoring.md)
- [Application metrics](labs/lab06-metrics.md)

### Lab 3: Troubleshooting
- [Debug failing pods](labs/lab07-pod-debugging.md)
- [Network troubleshooting](labs/lab08-network-debug.md)
- [Performance issues](labs/lab09-performance-debug.md)

## ⚡ Quick Drills

```bash
# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous

# Debug pods
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl exec -it <pod-name> -- /bin/bash

# Resource usage
kubectl top pods
kubectl top nodes
kubectl describe node <node-name>

# Port forwarding for debugging
kubectl port-forward <pod-name> 8080:80
```

## 🎯 Mock Scenarios

- [Mock 1: Debug failing application](mocks/mock01-debug-failing-app.md)
- [Mock 2: Configure health checks](mocks/mock02-health-checks.md)
- [Mock 3: Monitor resource usage](mocks/mock03-resource-monitoring.md)

## 🔑 Key Concepts to Master

- [ ] Configure all three types of probes
- [ ] Analyze container logs effectively
- [ ] Debug pod startup issues
- [ ] Monitor resource consumption
- [ ] Troubleshoot network connectivity
- [ ] Use kubectl for debugging

## 📝 Common Exam Tasks

1. "Add a liveness probe to check application health"
2. "Configure readiness probe for a web application"
3. "Debug why a pod is not starting"
4. "Find and analyze logs from a failed container"
5. "Monitor CPU and memory usage of pods"