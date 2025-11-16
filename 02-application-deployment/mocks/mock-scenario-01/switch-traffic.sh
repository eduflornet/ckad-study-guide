#!/bin/bash

COLOR=$1
NAMESPACE="blue-green-prod"

if [ "$COLOR" != "blue" ] && [ "$COLOR" != "green" ]; then
    echo "Usage: $0 [blue|green]"
    exit 1
fi

echo "Switching traffic to $COLOR environment..."

# Update main service selector
kubectl patch service webapp-service -n $NAMESPACE \
    -p '{"spec":{"selector":{"version":"'$COLOR'"}}}'

echo "Traffic switched to $COLOR"

# Verify the switch
echo "Verifying switch..."
kubectl describe service webapp-service -n $NAMESPACE | grep Selector

# Test the switch
echo "Testing switched environment..."
kubectl port-forward -n $NAMESPACE svc/webapp-service 8080:80 &
sleep 3

response=$(curl -s http://localhost:8080/ | jq -r '.color')
echo "Active environment: $response"

pkill -f "kubectl port-forward"

if [ "$response" = "$COLOR" ]; then
    echo "✅ Traffic successfully switched to $COLOR"
else
    echo "❌ Traffic switch failed. Expected: $COLOR, Got: $response"
    exit 1
fi
