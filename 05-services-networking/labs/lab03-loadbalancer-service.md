# Lab 3: LoadBalancer Service Implementation

**Learning Objective**: Deploy and configure LoadBalancer services for external access with cloud provider integration.

**Time**: 30 minutes

## 📋 Prerequisites

- Kubernetes cluster with LoadBalancer support (cloud provider or MetalLB)
- kubectl configured
- Understanding of NodePort services

## 🎯 Lab Overview

LoadBalancer services provide external access through cloud provider load balancers, offering production-ready external connectivity with automatic load balancing.

## 📝 Tasks

### Task 1: Create Application Deployment

Deploy a sample web application:

```yaml
# web-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-application
  labels:
    app: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html-content
          mountPath: /usr/share/nginx/html
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      volumes:
      - name: html-content
        configMap:
          name: webapp-content
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
        <title>LoadBalancer Service Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { background: white; padding: 20px; border-radius: 10px; }
            .hostname { color: #007acc; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LoadBalancer Service Demo</h1>
            <p>This request was served by pod: <span class="hostname">$(hostname)</span></p>
            <p>Timestamp: $(date)</p>
            <p>LoadBalancer services provide external access through cloud provider load balancers.</p>
        </div>
    </body>
    </html>
```

### Task 2: Create LoadBalancer Service

Create a LoadBalancer service:

```yaml
# loadbalancer-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-loadbalancer
  labels:
    app: webapp
  annotations:
    # Cloud provider specific annotations
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
spec:
  type: LoadBalancer
  selector:
    app: webapp
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
  - name: https
    port: 443
    targetPort: 80
    protocol: TCP
  # Optional: Specify load balancer source ranges
  loadBalancerSourceRanges:
  - 0.0.0.0/0  # Allow all IPs (use with caution)
```

### Task 3: Monitor LoadBalancer Provisioning

1. **Watch service creation**:
   ```bash
   kubectl get service webapp-loadbalancer -w
   ```

2. **Check service details**:
   ```bash
   kubectl describe service webapp-loadbalancer
   ```

3. **Get external IP**:
   ```bash
   # Wait for EXTERNAL-IP to be assigned
   kubectl get service webapp-loadbalancer
   
   # Get external IP programmatically
   EXTERNAL_IP=$(kubectl get service webapp-loadbalancer -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
   echo "External IP: $EXTERNAL_IP"
   ```

### Task 4: Test External Access

1. **Test HTTP access**:
   ```bash
   # Replace with actual external IP
   curl http://$EXTERNAL_IP
   
   # Test load balancing
   for i in {1..10}; do
     echo "Request $i:"
     curl -s http://$EXTERNAL_IP | grep hostname
   done
   ```

2. **Test from web browser**:
   ```bash
   echo "Access the application at: http://$EXTERNAL_IP"
   ```

### Task 5: Advanced LoadBalancer Configuration

#### Session Affinity

```yaml
# session-affinity-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sticky-loadbalancer
spec:
  type: LoadBalancer
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 300
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: 80
```

#### Health Check Configuration

```yaml
# health-check-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: health-aware-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-path: "/health"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval: "10"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-timeout: "5"
    service.beta.kubernetes.io/aws-load-balancer-healthy-threshold: "2"
    service.beta.kubernetes.io/aws-load-balancer-unhealthy-threshold: "2"
spec:
  type: LoadBalancer
  selector:
    app: webapp
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: health
    port: 8080
    targetPort: 8080
```

## ✅ Verification Steps

1. **Service has external IP assigned**:
   ```bash
   kubectl get service webapp-loadbalancer
   # EXTERNAL-IP should not be <pending>
   ```

2. **External connectivity works**:
   ```bash
   curl -I http://$EXTERNAL_IP
   # Should return HTTP 200 OK
   ```

3. **Load balancing across pods**:
   ```bash
   # Should see different pod hostnames
   for i in {1..5}; do curl -s http://$EXTERNAL_IP | grep hostname; done
   ```

4. **Health checks working**:
   ```bash
   kubectl get endpoints webapp-loadbalancer
   # Should show all healthy pod IPs
   ```

## 🔧 Cloud Provider Specific Examples

### AWS Annotations

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:..."
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "http"
```

### GCP Annotations

```yaml
metadata:
  annotations:
    cloud.google.com/load-balancer-type: "External"
    cloud.google.com/backend-config: '{"default": "my-backend-config"}'
```

### Azure Annotations

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-resource-group: "my-rg"
    service.beta.kubernetes.io/azure-pip-name: "my-public-ip"
```

## 🔄 MetalLB Configuration (On-Premises)

For bare-metal clusters using MetalLB:

```yaml
# metallb-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - 192.168.1.100-192.168.1.110
```

## 🧹 Cleanup

```bash
kubectl delete deployment web-application
kubectl delete configmap webapp-content
kubectl delete service webapp-loadbalancer sticky-loadbalancer health-aware-lb
```

## 📚 Key Learnings

- LoadBalancer services integrate with cloud provider load balancers
- External IP provisioning depends on cloud provider
- Annotations control cloud-specific load balancer features
- LoadBalancer includes NodePort and ClusterIP functionality
- Session affinity can be configured for sticky sessions

## 🔍 Troubleshooting Tips

- Check cloud provider quotas and permissions
- Verify LoadBalancer controller is running
- Monitor service events for provisioning errors
- Check security groups/firewall rules
- Validate target group health in cloud console

## 📖 Additional Resources

- [LoadBalancer Service Type](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
- [Cloud Provider Integration](https://kubernetes.io/docs/concepts/cluster-administration/cloud-providers/)
- [MetalLB Documentation](https://metallb.universe.tf/)