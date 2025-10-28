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

### Lab 1: ConfigMaps and Secrets
- [Create and use ConfigMaps](labs/lab01-configmaps.md)
- [Manage Secrets securely](labs/lab02-secrets.md)
- [Environment variable injection](labs/lab03-env-variables.md)

### Lab 2: Security
- [Configure security contexts](labs/lab04-security-context.md)
- [Non-root containers](labs/lab05-non-root.md)
- [Pod security standards](labs/lab06-pod-security.md)

### Lab 3: RBAC
- [Create roles and bindings](labs/lab07-rbac-basics.md)
- [ServiceAccount management](labs/lab08-serviceaccounts.md)
- [Permission testing](labs/lab09-permission-testing.md)

### Lab 4: Resources
- [Set resource limits](labs/lab10-resource-limits.md)
- [Configure resource quotas](labs/lab11-resource-quotas.md)
- [QoS classes](labs/lab12-qos-classes.md)

## ⚡ Quick Drills

```bash
# ConfigMaps
kubectl create configmap app-config --from-literal=key1=value1
kubectl create configmap app-config --from-file=config.properties

# Secrets
kubectl create secret generic db-secret --from-literal=username=admin
kubectl create secret docker-registry regcred --docker-username=user

# Security Context
kubectl run secure-pod --image=nginx --dry-run=client -o yaml > pod.yaml
# Edit to add securityContext

# RBAC
kubectl create role pod-reader --verb=get,list --resource=pods
kubectl create rolebinding read-pods --role=pod-reader --user=jane

# Resource management
kubectl set resources deployment nginx --limits=cpu=200m,memory=512Mi
```

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