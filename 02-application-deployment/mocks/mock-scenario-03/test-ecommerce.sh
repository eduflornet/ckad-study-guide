#!/bin/bash

NAMESPACE="ecommerce-prod"
RELEASE_NAME="ecommerce-prod"

echo "=== E-commerce Platform Test Suite ==="

# Check Helm release status
echo "1. Helm Release Status:"
helm status $RELEASE_NAME -n $NAMESPACE
echo

# Check all resources
echo "2. Resource Status:"
kubectl get all -n $NAMESPACE
echo

# Check ConfigMaps and Secrets
echo "3. Configuration Status:"
kubectl get configmaps,secrets -n $NAMESPACE
echo

# Test database connectivity
echo "4. Database Connectivity Test:"
kubectl run db-test --rm -i --tty --restart=Never \
  --image=postgres:14-alpine \
  --env="PGPASSWORD=prod-ecommerce-password" \
  -n $NAMESPACE -- psql -h ecommerce-prod-postgresql -U ecommerce -d ecommerce -c "\dt"
echo

# Test each microservice
echo "5. Microservice Health Checks:"

# User Service
kubectl port-forward -n $NAMESPACE svc/ecommerce-prod-ecommerce-platform-user-service 3001:3001 &
USER_PID=$!
sleep 3
echo "User Service Health:"
curl -s http://localhost:3001/health | jq '.status, .service, .uptime'
kill $USER_PID

# Product Service
kubectl port-forward -n $NAMESPACE svc/ecommerce-prod-ecommerce-platform-product-service 3002:3002 &
PRODUCT_PID=$!
sleep 3
echo "Product Service Health:"
curl -s http://localhost:3002/health | jq '.status, .service, .productCount'
kill $PRODUCT_PID

echo -e "\n6. Autoscaling Status:"
kubectl get hpa -n $NAMESPACE

echo -e "\n7. Network Policies:"
kubectl get networkpolicies -n $NAMESPACE

echo -e "\n✅ E-commerce platform test completed!"
