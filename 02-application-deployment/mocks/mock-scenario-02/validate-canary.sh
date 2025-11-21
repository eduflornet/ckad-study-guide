#!/bin/bash

NAMESPACE="canary-release"

echo "=== Canary Release Validation ==="

# Check deployments
echo "1. Deployment Status:"
kubectl get deployments -n $NAMESPACE
echo

# Check services
echo "2. Service Status:"
kubectl get services -n $NAMESPACE
echo

# Check pod distribution
echo "3. Pod Distribution:"
kubectl get pods -n $NAMESPACE -l app=payment-api --show-labels
echo

# Test traffic distribution
echo "4. Testing Traffic Distribution:"
./manage-canary.sh status
echo

# Health checks
echo "5. Health Checks:"
kubectl port-forward -n $NAMESPACE svc/payment-api-service 8080:80 &
PF_PID=$!
sleep 3

echo "Overall service health:"
curl -s http://localhost:8080/health | jq '.status, .version, .track'

kill $PF_PID
echo

# Test rollback capability
echo "6. Testing Rollback Capability:"
current_canary=$(kubectl get deployment payment-api-canary -n $NAMESPACE -o jsonpath='{.spec.replicas}')
echo "Current canary replicas: $current_canary"

./manage-canary.sh rollback
sleep 10

echo "After rollback:"
./manage-canary.sh status

# Restore canary for final state
./manage-canary.sh set 25
sleep 10

echo -e "\n✅ Canary release validation completed!"
