# Lab 02: Secrets

## Objective
Learn to create and manage Secrets securely for sensitive data like passwords, tokens, and certificates.

## Tasks

### Task 1: Create Secrets using different methods

1. **Create a Secret from literal values:**
```bash
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123 \
  --from-literal=host=db.example.com
```

2. **Create a Secret from files:**

Create credential files:
```bash
echo -n 'admin' > username.txt
echo -n 'topsecret' > password.txt
echo -n 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' > token.txt

kubectl create secret generic api-credentials \
  --from-file=username.txt \
  --from-file=password.txt \
  --from-file=token.txt
```

3. **Create a TLS Secret:**
```bash
# Generate self-signed certificate (for demo purposes)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=myapp.example.com/O=myapp"

kubectl create secret tls tls-secret --key tls.key --cert tls.crt
```

4. **Create Docker registry Secret:**
```bash
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=myemail@example.com
```

### Task 2: Use Secrets as Environment Variables

```yaml
# pod-env-secret.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-secret-env
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
    envFrom:
    - secretRef:
        name: db-credentials
        prefix: DB_
```

### Task 3: Mount Secrets as Volumes

```yaml
# pod-volume-secret.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-secret-volume
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
    - name: tls-volume
      mountPath: /etc/tls
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: api-credentials
      defaultMode: 0400
  - name: tls-volume
    secret:
      secretName: tls-secret
```

### Task 4: Use imagePullSecrets

```yaml
# pod-with-image-pull-secret.yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-image-pod
spec:
  containers:
  - name: app
    image: nginx:alpine  # Replace with private image
  imagePullSecrets:
  - name: regcred
```

### Task 5: Create Secret using YAML (with base64 encoding)

```yaml
# manual-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: manual-secret
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded 'admin'
  password: cGFzc3dvcmQxMjM=  # base64 encoded 'password123'
stringData:
  config.yaml: |
    database:
      host: localhost
      port: 5432
    api:
      endpoint: https://api.example.com
```

## Verification Commands

```bash
# List Secrets
kubectl get secrets

# Describe Secret (note: data is not shown)
kubectl describe secret db-credentials

# View Secret data (base64 encoded)
kubectl get secret db-credentials -o yaml

# Decode Secret data
kubectl get secret db-credentials -o jsonpath='{.data.username}' | base64 --decode
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 --decode

# Check environment variables in pod
kubectl exec app-secret-env -- env | grep DB_

# Check mounted secret files
kubectl exec app-secret-volume -- ls -la /etc/secrets
kubectl exec app-secret-volume -- cat /etc/secrets/username
```

## Security Best Practices

### Task 6: Implement Secret Security Best Practices

1. **Use proper RBAC for Secrets:**
```yaml
# secret-reader-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: secret-reader-binding
subjects:
- kind: User
  name: developer
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

2. **Use specific file permissions:**
```yaml
# secure-secret-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-secret-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: api-credentials
      defaultMode: 0400  # Read-only for owner only
      items:
      - key: username
        path: db-username
        mode: 0400
      - key: password
        path: db-password
        mode: 0400
```

## Cleanup

```bash
kubectl delete pod app-secret-env app-secret-volume private-image-pod secure-secret-pod
kubectl delete secret db-credentials api-credentials tls-secret regcred manual-secret
kubectl delete role secret-reader
kubectl delete rolebinding secret-reader-binding
rm -f username.txt password.txt token.txt tls.key tls.crt
```

## 🎯 Key Learning Points

- Secrets are base64 encoded, not encrypted at rest by default
- Use stringData for plain text in YAML manifests
- Environment variables expose secrets to process lists
- Volume mounts are more secure than environment variables
- Use proper file permissions (0400) for secret files
- Implement RBAC to control Secret access
- Use imagePullSecrets for private registries
- Never commit Secrets to version control
- Consider using external secret management systems for production
