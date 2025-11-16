#!/bin/bash

# Simulate GitOps deployment pattern
ENVIRONMENT=$1
IMAGE_TAG=$2
CHART_VERSION=${3:-"0.1.0"}

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <environment> <image-tag> [chart-version]"
    echo "Example: $0 staging v1.2.3"
    exit 1
fi

echo "=== GitOps Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Image Tag: $IMAGE_TAG"
echo "Chart Version: $CHART_VERSION"
echo

# 1. Validate environment
case $ENVIRONMENT in
    development|staging|production)
        echo "✅ Valid environment: $ENVIRONMENT"
        ;;
    *)
        echo "❌ Invalid environment. Must be: development, staging, or production"
        exit 1
        ;;
esac

# 2. Check if namespace exists
if ! kubectl get namespace $ENVIRONMENT >/dev/null 2>&1; then
    echo "Creating namespace $ENVIRONMENT..."
    kubectl create namespace $ENVIRONMENT
fi

# 3. Determine values file
VALUES_FILE="values-${ENVIRONMENT}.yaml"
if [ ! -f "$VALUES_FILE" ]; then
    echo "❌ Values file $VALUES_FILE not found"
    exit 1
fi

# 4. Deploy or upgrade
RELEASE_NAME="webapp-${ENVIRONMENT}"

if helm status $RELEASE_NAME -n $ENVIRONMENT >/dev/null 2>&1; then
    echo "Upgrading existing release..."
    helm upgrade $RELEASE_NAME bitnami/nginx \
        --namespace $ENVIRONMENT \
        --values $VALUES_FILE \
        --set image.tag=$IMAGE_TAG \
        --set fullnameOverride=$RELEASE_NAME \
        --wait \
        --timeout=300s
else
    echo "Installing new release..."
    helm install $RELEASE_NAME bitnami/nginx \
        --namespace $ENVIRONMENT \
        --values $VALUES_FILE \
        --set image.tag=$IMAGE_TAG \
        --set fullnameOverride=$RELEASE_NAME \
        --wait \
        --timeout=300s
fi

# 5. Validate deployment
echo "Validating deployment..."
./validate-release.sh $RELEASE_NAME $ENVIRONMENT

echo "🎉 GitOps deployment completed!"
