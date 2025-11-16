#!/bin/bash

echo "=== Helm Release Monitoring ==="
echo

# Get all releases across namespaces
echo "All Helm Releases:"
helm list --all-namespaces --output table

echo
echo "=== Release Status Details ==="

# Check each release status
for namespace in development staging production; do
    echo
    echo "--- $namespace environment ---"
    
    releases=$(helm list -n $namespace --short)
    
    if [ -n "$releases" ]; then
        for release in $releases; do
            echo "Release: $release"
            helm status $release -n $namespace --show-desc
            
            # Check deployment status
            deployment=$(kubectl get deployment -n $namespace -l app.kubernetes.io/instance=$release -o name 2>/dev/null)
            if [ -n "$deployment" ]; then
                echo "Deployment Status:"
                kubectl rollout status $deployment -n $namespace --timeout=10s
            fi
            
            echo "---"
        done
    else
        echo "No releases found in $namespace"
    fi
done

echo
echo "=== Resource Health Check ==="

# Check pod health across environments
for namespace in development staging production; do
    echo
    echo "Pods in $namespace:"
    kubectl get pods -n $namespace --show-labels
done
