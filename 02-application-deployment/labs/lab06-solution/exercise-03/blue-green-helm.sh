#!/bin/bash

ENVIRONMENT=${1:-"staging"}
NEW_VERSION=$2
CURRENT_COLOR=""
NEW_COLOR=""

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 [environment] <new-version>"
    echo "Example: $0 staging v1.2.3"
    exit 1
fi

echo "=== Blue-Green Deployment with Helm ==="

# 1. Determine current color
if helm status webapp-blue -n $ENVIRONMENT >/dev/null 2>&1; then
    CURRENT_COLOR="blue"
    NEW_COLOR="green"
elif helm status webapp-green -n $ENVIRONMENT >/dev/null 2>&1; then
    CURRENT_COLOR="green"
    NEW_COLOR="blue"
else
    echo "No existing deployment found. Starting with blue."
    CURRENT_COLOR=""
    NEW_COLOR="blue"
fi

echo "Current Color: ${CURRENT_COLOR:-none}"
echo "New Color: $NEW_COLOR"

# 2. Deploy new version
echo "Deploying $NEW_COLOR version..."
helm install webapp-$NEW_COLOR bitnami/nginx \
    --namespace $ENVIRONMENT \
    --values values-${ENVIRONMENT}.yaml \
    --set image.tag=$NEW_VERSION \
    --set fullnameOverride=webapp-$NEW_COLOR \
    --wait

# 3. Validate new deployment
echo "Validating new deployment..."
./validate-release.sh webapp-$NEW_COLOR $ENVIRONMENT

# 4. Switch traffic (simulate by updating service selector)
echo "Switching traffic to $NEW_COLOR..."
if kubectl get service webapp-service -n $ENVIRONMENT >/dev/null 2>&1; then
    kubectl patch service webapp-service -n $ENVIRONMENT \
        -p '{"spec":{"selector":{"app.kubernetes.io/instance":"webapp-'$NEW_COLOR'"}}}'
else
    # Create service pointing to new color
    kubectl expose deployment webapp-$NEW_COLOR \
        --name=webapp-service \
        --port=80 \
        --target-port=80 \
        --namespace=$ENVIRONMENT
fi

# 5. Clean up old version (optional)
if [ -n "$CURRENT_COLOR" ]; then
    echo "Removing old $CURRENT_COLOR deployment..."
    helm uninstall webapp-$CURRENT_COLOR -n $ENVIRONMENT
fi

echo "🎉 Blue-Green deployment completed!"
echo "Active version: $NEW_COLOR ($NEW_VERSION)"
