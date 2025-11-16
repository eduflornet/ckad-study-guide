# Lab 01: ConfigMaps

## Objective
Learn to create and use ConfigMaps for application configuration management.

## Tasks

### Task 1: Create ConfigMaps using different methods

1. **Create a ConfigMap from literal values:**
```bash
kubectl create configmap app-config \
  --from-literal=DATABASE_URL=postgres://localhost:5432/mydb \
  --from-literal=API_KEY=abc123 \
  --from-literal=DEBUG=true
```

2. **Create a ConfigMap from a file:**

Create a properties file:
```properties
# config.properties
app.name=my-application
app.version=1.0.0
app.environment=production
database.host=db.example.com
database.port=5432
cache.enabled=true
cache.ttl=3600
```

```bash
kubectl create configmap file-config --from-file=config.properties
```

3. **Create a ConfigMap from a directory:**
```bash
mkdir config-files
echo "user=admin" > config-files/database.conf
echo "timeout=30" > config-files/app.conf
kubectl create configmap dir-config --from-file=config-files/
```

### Task 2: Use ConfigMaps as Environment Variables

Create a pod that uses ConfigMap as environment variables:

```yaml
# pod-env-configmap.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_URL
    - name: API_KEY
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: API_KEY
    envFrom:
    - configMapRef:
        name: app-config
```

### Task 3: Mount ConfigMaps as Volumes

```yaml
# pod-volume-configmap.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-volume-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: single-config
      mountPath: /etc/single
      subPath: config.properties
  volumes:
  - name: config-volume
    configMap:
      name: file-config
  - name: single-config
    configMap:
      name: file-config
```

### Task 4: Update ConfigMaps and observe behavior

1. Update the ConfigMap:
```bash
kubectl patch configmap app-config -p '{"data":{"DEBUG":"false"}}'
```

2. Verify the change propagation (note: environment variables don't update automatically, but mounted files do)

## Verification Commands

```bash
# List ConfigMaps
kubectl get configmaps

# Describe ConfigMap
kubectl describe configmap app-config

# Check environment variables in pod
kubectl exec app-env-pod -- env | grep -E "(DATABASE_URL|API_KEY|DEBUG)"

# Check mounted files
kubectl exec app-volume-pod -- ls -la /etc/config
kubectl exec app-volume-pod -- cat /etc/config/config.properties
```

## Cleanup

```bash
kubectl delete pod app-env-pod app-volume-pod
kubectl delete configmap app-config file-config dir-config
rm -rf config-files
rm config.properties
```

## 🎯 Key Learning Points

- ConfigMaps store non-confidential configuration data
- Multiple ways to create ConfigMaps (literal, file, directory)
- Environment variables vs volume mounts for configuration
- Volume-mounted configs update automatically, env vars don't
- Use meaningful names and organize configurations logically