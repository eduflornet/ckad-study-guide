# Application Environment, Configuration and Security (25%)

## 📚 Topics Covered

### ConfigMaps and Secrets
- Configuration management
- Environment variables
- Volume mounts
- Secret handling best practices

### Security Contexts
- Pod security context
- Container security context
- User and group IDs
- Capabilities and privileges

### RBAC (Role-Based Access Control)
- Roles and ClusterRoles
- RoleBindings and ClusterRoleBindings
- ServiceAccounts
- Permission management

### Resource Management
- Resource requests and limits
- Quality of Service classes
- LimitRanges and ResourceQuotas

## 🛠️ Practice Labs

### Labs: ConfigMaps and Secrets
- [1. Create and use ConfigMaps](labs/lab01-configmaps.md)
- [2. Manage Secrets securely](labs/lab02-secrets.md)
- [3. Environment variable injection](labs/lab03-environment-variables.md)

### Labs: Security
- [4. Configure security contexts](labs/lab04-security-context.md)
- [5. Non-root containers](labs/lab05-non-root.md)
- [6. Pod security standards](labs/lab06-pod-security.md)

### Labs: RBAC
- [7. Create roles and bindings](labs/lab07-rbac-basics.md)
- [8. ServiceAccount management](labs/lab08-serviceaccounts.md)
- [9. Permission testing](labs/lab09-permission-testing.md)

### Labs: Resources
- [10. Set resource limits](labs/lab10-resource-limits.md)
- [11. Configure resource quotas](labs/lab11-resource-quotas.md)
- [12. QoS classes](labs/lab12-qos-classes.md)

## ⚡ Quick Drills

```bash
🔹 ConfigMaps

# Create ConfigMap from literal values:
kubectl create configmap app-config --from-literal=key1=value1 --from-literal=key2=value2

# Create ConfigMap from file:
kubectl create configmap app-config --from-file=config.properties

# View content configmap
kubectl get configmap app-config -o yaml

🔹 Secrets

# Create generic secret
kubectl create secret generic db-secret --from-literal=username=admin

# Create generic secret from file
kubectl create secret generic mysecret --from-file=./secret.txt

# Decode secret value
kubectl get secret mysecret -o jsonpath='{.data.password}' | base64 --decode

# Create docker registry secret
kubectl create secret docker-registry regcred --docker-username=user

🔹 Service Accounts

# Create ServiceAccount
kubectl create serviceaccount mysa

# Using SA in a Pod:
kubectl run mypod --image=nginx --serviceaccount=mysa


🔹 Security Context

# Get yaml manifest
kubectl run secure-pod --image=nginx --dry-run=client -o yaml > pod.yaml

#Pod with specific user
kubectl run secpod --image=nginx --overrides='{"spec":{"securityContext":{"runAsUser":1000}}}'

🔹 Resource Quotas & LimitRanges

# Create ResourceQuota
kubectl create quota myquota --hard=cpu=2,memory=1Gi,pods=10

# Create LimitRange
kubectl create limitrange mylimits --default-cpu=200m --default-memory=512Mi --max-cpu=1 --max-memory=1Gi

# Edit to add securityContext

# RBAC
kubectl create role pod-reader --verb=get,list --resource=pods
kubectl create rolebinding read-pods --role=pod-reader --user=jane

# Resource management
kubectl set resources deployment nginx --limits=cpu=200m,memory=512Mi
```

🎯 Exam Strategy
Memorize key flags: --from-literal, --from-file, --serviceaccount, --hard, --default-cpu, --default-memory.

Practice with `kubectl create` and `kubectl run`, as these are the ones that appear most frequently in practical scenarios.

Use `kubectl explain <resource>` to remember YAML fields if you need to convert imperatives into manifests.

Think about speed: imperatives are your shortcut to avoid wasting time writing long YAML statements.

✅ In summary: the most important imperatives are kubectl create configmap, kubectl create secret, kubectl create serviceaccount, kubectl create quota, kubectl create limitrange, along with kubectl run for Pods with quick configurations.

## 🎯 Mock Scenarios

- [Mock 1: Secure application deployment](mocks/mock01-secure-deployment.md)
- [Mock 2: RBAC configuration](mocks/mock02-rbac-setup.md)
- [Mock 3: Resource management](mocks/mock03-resource-management.md)

## 🔑 Key Concepts to Master

- [ ] Create and consume ConfigMaps and Secrets
- [ ] Configure pod and container security contexts
- [ ] Implement RBAC policies
- [ ] Set appropriate resource requests and limits
- [ ] Use ServiceAccounts effectively
- [ ] Understand security best practices

## 📝 Common Exam Tasks

1. "Create a ConfigMap and mount it as a volume"
2. "Configure a pod to run as non-root user"
3. "Create a ServiceAccount with specific permissions"
4. "Set resource limits for a deployment"
5. "Create a Secret and use it as environment variables"