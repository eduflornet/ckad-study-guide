# Lab 4: Headless Service Configuration

**Learning Objective**: Implement headless services for direct pod communication and StatefulSet integration.

**Time**: 25 minutes

## 📋 Prerequisites

- Kubernetes cluster running
- kubectl configured
- Understanding of DNS and service discovery

## 🎯 Lab Overview

Headless services don't provide load balancing or a single service IP. Instead, they return DNS records pointing directly to pod IPs, enabling direct pod-to-pod communication.

## 📝 Tasks

### Task 1: Create a Regular Deployment

First, create a deployment to understand the difference:

```yaml
# web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deployment
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
            cpu: "50m"
```

### Task 2: Create Headless Service

Create a headless service by setting `clusterIP: None`:

```yaml
# headless-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-headless
  labels:
    app: web
spec:
  clusterIP: None  # This makes it headless
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
```

### Task 3: Compare Regular vs Headless Services

Create a regular service for comparison:

```yaml
# regular-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-regular
  labels:
    app: web
spec:
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
```

Test DNS resolution:

```bash
# Test regular service DNS
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-regular

# Test headless service DNS
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-headless
```

### Task 4: StatefulSet with Headless Service

Create a StatefulSet that uses the headless service:

```yaml
# database-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database
spec:
  serviceName: database-headless  # Links to headless service
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: database
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "admin"
        - name: POSTGRES_PASSWORD
          value: "password"
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        ports:
        - containerPort: 5432
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: database-headless
  labels:
    app: database
spec:
  clusterIP: None
  selector:
    app: database
  ports:
  - name: postgres
    port: 5432
    targetPort: 5432
```

### Task 5: Test Pod-Specific DNS

Test individual pod DNS records:

```bash
# Get pod names
kubectl get pods -l app=database

# Test individual pod DNS (StatefulSet creates predictable names)
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup database-0.database-headless.default.svc.cluster.local

kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup database-1.database-headless.default.svc.cluster.local

# Test service DNS (returns all pod IPs)
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup database-headless.default.svc.cluster.local
```

### Task 6: Application Using Headless Service

Create an application that connects to specific pods:

```yaml
# client-application.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: db-client
spec:
  replicas: 1
  selector:
    matchLabels:
      app: db-client
  template:
    metadata:
      labels:
        app: db-client
    spec:
      containers:
      - name: client
        image: postgres:13
        command:
        - /bin/bash
        - -c
        - |
          while true; do
            echo "Connecting to database-0..."
            PGPASSWORD=password psql -h database-0.database-headless.default.svc.cluster.local -U admin -d testdb -c "SELECT current_database(), inet_server_addr();"
            
            echo "Connecting to database-1..."
            PGPASSWORD=password psql -h database-1.database-headless.default.svc.cluster.local -U admin -d testdb -c "SELECT current_database(), inet_server_addr();"
            
            echo "Sleeping for 30 seconds..."
            sleep 30
          done
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
```

## ✅ Verification Steps

1. **Headless service has no ClusterIP**:
   ```bash
   kubectl get service web-headless
   # ClusterIP should show "None"
   ```

2. **DNS returns pod IPs directly**:
   ```bash
   kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-headless
   # Should return individual pod IPs, not a single cluster IP
   ```

3. **StatefulSet pods have predictable DNS names**:
   ```bash
   kubectl run dns-test --image=busybox --rm -it --restart=Never -- \
     nslookup database-0.database-headless.default.svc.cluster.local
   # Should resolve to specific pod IP
   ```

4. **Endpoints show all pod IPs**:
   ```bash
   kubectl get endpoints database-headless
   # Should list all database pod IPs
   ```

## 🔧 Advanced Use Cases

### Database Master-Slave Setup

```yaml
# master-slave-headless.yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-master
spec:
  clusterIP: None
  selector:
    app: mysql
    role: master  # Only master pods
  ports:
  - port: 3306
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-slave
spec:
  clusterIP: None
  selector:
    app: mysql
    role: slave  # Only slave pods
  ports:
  - port: 3306
```

### Service Discovery Without Load Balancing

```yaml
# discovery-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: service-discovery
  annotations:
    service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
spec:
  clusterIP: None
  publishNotReadyAddresses: true  # Include unready pods in DNS
  selector:
    app: discovery-app
  ports:
  - port: 8080
```

## 🔍 DNS Resolution Patterns

```bash
# Regular service DNS
<service-name>.<namespace>.svc.cluster.local
# Returns: Single cluster IP

# Headless service DNS
<service-name>.<namespace>.svc.cluster.local
# Returns: All pod IPs

# StatefulSet pod DNS (with headless service)
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
# Returns: Specific pod IP
```

## 🧹 Cleanup

```bash
kubectl delete deployment web-deployment db-client
kubectl delete statefulset database
kubectl delete service web-headless web-regular database-headless
kubectl delete pvc -l app=database  # Clean up StatefulSet PVCs
```

## 📚 Key Learnings

- Headless services don't provide load balancing or cluster IP
- DNS queries return pod IPs directly
- Essential for StatefulSets and direct pod communication
- Enables service discovery without load balancing
- StatefulSet pods get predictable DNS names

## 🔍 Troubleshooting Tips

- Verify `clusterIP: None` in service definition
- Check DNS resolution from within cluster
- Ensure pods are ready for DNS records to appear
- StatefulSet requires `serviceName` to match headless service
- Use `publishNotReadyAddresses: true` if needed

## 📖 Additional Resources

- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [StatefulSet DNS](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#stable-network-id)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)