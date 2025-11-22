#!/bin/bash

NAMESPACE="canary-release"
ACTION=$1
PERCENTAGE=${2:-10}

function get_current_distribution() {
    local stable_replicas=$(kubectl get deployment payment-api-stable -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    local canary_replicas=$(kubectl get deployment payment-api-canary -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    local total=$((stable_replicas + canary_replicas))
    
    if [ $total -gt 0 ]; then
        local stable_percent=$((stable_replicas * 100 / total))
        local canary_percent=$((canary_replicas * 100 / total))
        echo "Current distribution: Stable: ${stable_percent}%, Canary: ${canary_percent}%"
    else
        echo "No active deployments found"
    fi
}

function set_traffic_distribution() {
    local canary_percent=$1
    local stable_percent=$((100 - canary_percent))
    
    # Calculate target replicas (assuming 10 total for easy percentage calculation)
    local total_replicas=10
    local canary_replicas=$((total_replicas * canary_percent / 100))
    local stable_replicas=$((total_replicas - canary_replicas))
    
    # Ensure at least 1 replica for non-zero percentages
    if [ $canary_percent -gt 0 ] && [ $canary_replicas -eq 0 ]; then
        canary_replicas=1
        stable_replicas=$((total_replicas - 1))
    fi
    
    echo "Setting traffic distribution: Stable: ${stable_percent}% ($stable_replicas replicas), Canary: ${canary_percent}% ($canary_replicas replicas)"
    
    kubectl scale deployment payment-api-stable --replicas=$stable_replicas -n $NAMESPACE
    kubectl scale deployment payment-api-canary --replicas=$canary_replicas -n $NAMESPACE
    
    # Wait for deployments to be ready
    kubectl rollout status deployment/payment-api-stable -n $NAMESPACE --timeout=120s
    kubectl rollout status deployment/payment-api-canary -n $NAMESPACE --timeout=120s
}

function monitor_metrics() {
    echo "Monitoring canary metrics..."
    
    # Get metrics from both versions
    kubectl port-forward -n $NAMESPACE svc/payment-api-service 8080:80 &
    PORT_FORWARD_PID=$!
    sleep 3
    
    echo "=== Stable Version Metrics ==="
    kubectl port-forward -n $NAMESPACE svc/payment-api-stable-service 8081:80 &
    STABLE_PF_PID=$!
    sleep 2
    curl -s http://localhost:8081/metrics | jq '.'
    kill $STABLE_PF_PID
    
    echo -e "\n=== Canary Version Metrics ==="
    kubectl port-forward -n $NAMESPACE svc/payment-api-canary-service 8082:80 &
    CANARY_PF_PID=$!
    sleep 2
    curl -s http://localhost:8082/metrics | jq '.'
    kill $CANARY_PF_PID
    
    echo -e "\n=== Overall Service Health ==="
    curl -s http://localhost:8080/health | jq '.'
    
    kill $PORT_FORWARD_PID
}

function rollback_canary() {
    echo "Rolling back canary deployment..."
    set_traffic_distribution 0
    echo "Canary rollback completed - all traffic routed to stable version"
}

function promote_canary() {
    echo "Promoting canary to stable..."
    set_traffic_distribution 100
    echo "Canary promoted - all traffic routed to canary version"
    
    # Update labels to make canary the new stable
    kubectl patch deployment payment-api-canary -n $NAMESPACE -p '{"metadata":{"labels":{"track":"stable"}}}'
    echo "Canary is now the stable version"
}

case $ACTION in
    "status")
        get_current_distribution
        ;;
    "set")
        if [ -z "$PERCENTAGE" ]; then
            echo "Usage: $0 set <percentage>"
            exit 1
        fi
        set_traffic_distribution $PERCENTAGE
        ;;
    "monitor")
        monitor_metrics
        ;;
    "rollback")
        rollback_canary
        ;;
    "promote")
        promote_canary
        ;;
    *)
        echo "Usage: $0 {status|set <percentage>|monitor|rollback|promote}"
        echo "Examples:"
        echo "  $0 status                 # Show current traffic distribution"
        echo "  $0 set 20                # Set canary to 20% traffic"
        echo "  $0 monitor               # Monitor metrics from both versions"
        echo "  $0 rollback              # Rollback to stable version"
        echo "  $0 promote               # Promote canary to stable"
        exit 1
        ;;
esac
