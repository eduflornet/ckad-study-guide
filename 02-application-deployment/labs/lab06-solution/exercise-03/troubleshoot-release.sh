#!/bin/bash

RELEASE_NAME=$1
NAMESPACE=$2

if [ -z "$RELEASE_NAME" ] || [ -z "$NAMESPACE" ]; then
    echo "Usage: $0 <release-name> <namespace>"
    exit 1
fi

echo "=== Troubleshooting Release: $RELEASE_NAME in $NAMESPACE ==="
echo

# 1. Check release status
echo "1. Release Status:"
helm status $RELEASE_NAME -n $NAMESPACE

echo
echo "2. Release History:"
helm history $RELEASE_NAME -n $NAMESPACE

echo
echo "3. Release Values:"
helm get values $RELEASE_NAME -n $NAMESPACE

echo
echo "4. Release Manifest:"
helm get manifest $RELEASE_NAME -n $NAMESPACE

echo
echo "5. Kubernetes Resources:"
kubectl get all -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo
echo "6. Pod Descriptions:"
kubectl describe pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo
echo "7. Recent Events:"
kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp | tail -20

echo
echo "8. Pod Logs (if available):"
pods=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)
for pod in $pods; do
    echo "--- Logs for $pod ---"
    kubectl logs $pod -n $NAMESPACE --tail=50
done
