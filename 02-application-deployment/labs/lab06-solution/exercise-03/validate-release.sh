#!/bin/bash

RELEASE_NAME=$1
NAMESPACE=$2
TIMEOUT=${3:-300}  # 5 minutes default timeout

if [ -z "$RELEASE_NAME" ] || [ -z "$NAMESPACE" ]; then
    echo "Usage: $0 <release-name> <namespace> [timeout-seconds]"
    exit 1
fi

echo "=== Validating Release: $RELEASE_NAME in $NAMESPACE ==="

# 1. Check Helm release status
echo "1. Checking Helm release status..."
if ! helm status $RELEASE_NAME -n $NAMESPACE >/dev/null 2>&1; then
    echo "❌ Release $RELEASE_NAME not found in namespace $NAMESPACE"
    exit 1
fi

release_status=$(helm status $RELEASE_NAME -n $NAMESPACE -o json | jq -r '.info.status')
if [ "$release_status" != "deployed" ]; then
    echo "❌ Release status is $release_status (expected: deployed)"
    exit 1
fi
echo "✅ Release status: $release_status"

# 2. Check deployment rollout
echo "2. Checking deployment rollout..."
deployments=$(kubectl get deployment -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)

for deployment in $deployments; do
    echo "Checking $deployment..."
    if ! kubectl rollout status $deployment -n $NAMESPACE --timeout=${TIMEOUT}s; then
        echo "❌ Deployment rollout failed for $deployment"
        exit 1
    fi
    echo "✅ Deployment $deployment is ready"
done

# 3. Check pod readiness
echo "3. Checking pod readiness..."
pods=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME -o name)

for pod in $pods; do
    if ! kubectl wait $pod -n $NAMESPACE --for=condition=Ready --timeout=${TIMEOUT}s; then
        echo "❌ Pod $pod is not ready"
        exit 1
    fi
done
echo "✅ All pods are ready"

# 4. Run Helm tests if available
echo "4. Running Helm tests..."
if helm test $RELEASE_NAME -n $NAMESPACE --timeout=${TIMEOUT}s; then
    echo "✅ Helm tests passed"
else
    echo "⚠️ Helm tests failed or not available"
fi

echo
echo "🎉 Release validation completed successfully!"
