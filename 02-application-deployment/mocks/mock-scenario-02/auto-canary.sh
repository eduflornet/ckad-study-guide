#!/bin/bash

NAMESPACE="canary-release"

echo "=== Automated Canary Deployment ==="

# Progressive traffic shifting: 10% -> 25% -> 50% -> 100%
STAGES=(10 25 50 100)
STAGE_DURATION=60  # seconds

function check_canary_health() {
    local health_endpoint="http://localhost:8082/health"
    local metrics_endpoint="http://localhost:8082/metrics"
    
    # Port forward to canary service
    kubectl port-forward -n $NAMESPACE svc/payment-api-canary-service 8082:80 &
    local pf_pid=$!
    sleep 3
    
    # Check health
    local health_status=$(curl -s $health_endpoint | jq -r '.status')
    local success_rate=$(curl -s $metrics_endpoint | jq -r '.successfulTransactions, .totalTransactions' | paste -sd, | awk -F, '{if($2>0) print ($1/$2)*100; else print 0}')
    
    kill $pf_pid
    
    # Health criteria
    if [ "$health_status" = "healthy" ] && [ "$(echo "$success_rate > 95" | bc -l)" -eq 1 ]; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

function run_load_test() {
    local duration=$1
    echo "Running load test for $duration seconds..."
    
    kubectl port-forward -n $NAMESPACE svc/payment-api-service 8080:80 &
    local pf_pid=$!
    sleep 3
    
    # Generate load
    for i in $(seq 1 $duration); do
        # Simulate various transactions
        curl -s -X POST http://localhost:8080/api/payments \
            -H "Content-Type: application/json" \
            -d '{"amount": '$((RANDOM % 5000 + 100))', "merchant": "test_merchant_'$i'", "cardNumber": "****1234"}' > /dev/null &
        
        # Health checks
        curl -s http://localhost:8080/health > /dev/null &
        
        sleep 1
    done
    
    wait  # Wait for all background requests
    kill $pf_pid
}

echo "Starting automated canary progression..."

for stage in "${STAGES[@]}"; do
    echo -e "\n=== Stage: ${stage}% Canary Traffic ==="
    
    # Set traffic distribution
    ./manage-canary.sh set $stage
    
    # Wait for deployment to stabilize
    sleep 30
    
    # Run load test
    run_load_test $STAGE_DURATION
    
    # Check canary health
    if check_canary_health; then
        echo "✅ Canary health check passed at ${stage}%"
        
        # Monitor metrics
        echo "Monitoring metrics for ${stage}% traffic..."
        ./manage-canary.sh monitor
        
        if [ $stage -eq 100 ]; then
            echo "🎉 Canary deployment completed successfully!"
            echo "Promoting canary to stable..."
            ./manage-canary.sh promote
        else
            echo "Proceeding to next stage..."
        fi
    else
        echo "❌ Canary health check failed at ${stage}%"
        echo "Rolling back to stable version..."
        ./manage-canary.sh rollback
        exit 1
    fi
    
    # Wait before next stage
    if [ $stage -ne 100 ]; then
        echo "Waiting before next stage..."
        sleep 30
    fi
done

echo "Automated canary deployment completed!"
