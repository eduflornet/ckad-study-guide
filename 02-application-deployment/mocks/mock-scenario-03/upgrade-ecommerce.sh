#!/bin/bash

NAMESPACE="ecommerce-prod"
RELEASE_NAME="ecommerce-prod"

echo "=== Upgrading E-commerce Platform ==="

# Backup current values
helm get values $RELEASE_NAME -n $NAMESPACE > current-values.yaml

# Create new values with updates
cat << 'NEWVALUES' > values-upgrade.yaml
# Inherit from production values
environment: production
region: us-west-2

# Increased capacity for holiday sales
replicaCount:
  frontend: 5
  apiGateway: 3
  userService: 5
  productService: 6
  orderService: 4

# Enhanced autoscaling
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

# Database scaling
postgresql:
  enabled: true
  auth:
    postgresPassword: "prod-secure-password"
    password: "prod-ecommerce-password"
  primary:
    persistence:
      size: 200Gi
  readReplicas:
    replicaCount: 3

redis:
  enabled: true
  auth:
    password: "prod-redis-password"
  master:
    persistence:
      size: 40Gi
  replica:
    replicaCount: 4

# Enhanced monitoring
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

security:
  networkPolicies:
    enabled: true

frontend:
  ingress:
    enabled: true
    hosts:
    - host: ecommerce-prod.local
      paths:
      - path: /
        pathType: Prefix
NEWVALUES

# Perform dry-run first
echo "Performing dry-run upgrade..."
helm upgrade $RELEASE_NAME ./ecommerce-platform \
  --namespace $NAMESPACE \
  --values values-upgrade.yaml \
  --dry-run --debug

read -p "Proceed with actual upgrade? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Performing upgrade..."
    helm upgrade $RELEASE_NAME ./ecommerce-platform \
      --namespace $NAMESPACE \
      --values values-upgrade.yaml \
      --timeout 15m \
      --wait
    
    echo "Upgrade completed! New status:"
    helm status $RELEASE_NAME -n $NAMESPACE
else
    echo "Upgrade cancelled."
fi
