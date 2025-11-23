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

### Labs: Health Probes
- [1. Configure liveness probes](labs/lab01-liveness-probes.md)
- [2. Set up readiness probes](labs/lab02-readiness-probes.md)
- [3. Implement startup probes](labs/lab03-startup-probes.md)

### Labs: Monitoring
- [4. Container log analysis](labs/lab04-log-analysis.md)
- [5. Resource monitoring](labs/lab05-resource-monitoring.md)
- [6. Application metrics](labs/lab06-metrics.md)

### Labs: Troubleshooting
- [7. Debug failing pods](labs/lab07-pod-debugging.md)
- [8. Network troubleshooting](labs/lab08-network-debug.md)
- [9. Performance issues](labs/lab09-performance-debug.md)

## ⚡ Quick Drills

```bash

🔹 Logs

# View logs of a pod
kubectl logs mypod

# View logs of a specific container
kubectl logs <pod-name> -c <container-name>

# Track logs in real time
kubectl logs -f mypod

# View logs
kubectl logs <pod-name> --previous

🔹 Exec (debugging within Pod)
# Execute a command within a Pod:
kubectl exec mypod -- ls /app

# Enter interactive shell:
kubectl exec -it <pod-name> -- /bin/sh
kubectl exec -it  -- /bin/bash

# Debug pods
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp

🔹 Port-forwarding
# Redirect local port to Pod
kubectl port-forward pod/mypod 8080:80

# Redirect to a Service
kubectl port-forward svc/myservice 8080:80

🔹 Probes (liveness/readiness)

# Although they are usually defined in YAML, you can use imperative overrides:

# Create a Pod with a liveness probe:

kubectl run liveness-pod --image=nginx \
  --overrides='{"spec":{"containers":[{"name":"nginx","image":"nginx","livenessProbe":{"httpGet":{"path":"/","port":80}}}]}}'

🔹 Resource Management
# Scaling a Deployment

kubectl scale deployment myapp --replicas=5

# View resource usage (if metrics-server is installed):

kubectl top pod
kubectl top node
kubectl describe node <node-name>

🔹 Maintenance

# Eliminate problematic Pod:
kubectl delete pod mypod


# Restart Deployment
kubectl rollout restart deployment myapp


# View deployment history
kubectl rollout history deployment myapp

```

This part of the exam measures your ability to monitor, debug, and maintain applications in Kubernetes, and imperatives are your best ally for reacting quickly without writing YAML.

Memorize the most commonly used imperatives: logs, exec, port-forward, scale, rollout, and restart.

Practice quick debugging: enter a Pod (exec -it), review logs, and scale Deployments.

Remember that probes and overrides can be defined imperatively, although the exam will often require YAML.

Use kubectl explain if you need to remember configuration fields.

✅ In summary: The most important imperatives are kubectl logs, kubectl exec, kubectl port-forward, kubectl scale, kubectl rollout restart, along with kubectl top for metrics and kubectl delete for quick maintenance.



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