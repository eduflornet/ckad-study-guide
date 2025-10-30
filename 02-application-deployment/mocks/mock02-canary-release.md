# Mock Scenario 2: Canary Release Strategy

**Objective**: Implement a sophisticated Canary release strategy with automated validation and progressive traffic shifting
**Time**: 55 minutes
**Difficulty**: Advanced

---

## Scenario Overview

You work for a financial services company that processes millions of transactions daily. The company needs to deploy a critical API update that includes new fraud detection algorithms. Due to the sensitive nature of financial transactions, you must implement a Canary release strategy that:

- Gradually shifts traffic to the new version
- Monitors key metrics during deployment
- Automatically rolls back if issues are detected
- Validates transaction processing integrity
- Maintains audit trails for compliance

## Application Architecture

The system consists of:

1. **Payment API**: Core transaction processing service
2. **Fraud Detection Service**: ML-based fraud detection
3. **Database**: Transaction logs and user data
4. **Monitoring**: Metrics collection and alerting
5. **Load Balancer**: Traffic distribution control

## Implementation Tasks

### Task 1: Setup Monitoring and Base Infrastructure (15 minutes)

Create the foundation with monitoring capabilities:

```bash
# Create namespace
kubectl create namespace canary-release

# Create monitoring and shared resources
cat << EOF > base-infrastructure.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: canary-release
data:
  DATABASE_URL: "postgresql://finapp:password@postgres-service:5432/transactions"
  REDIS_URL: "redis://redis-service:6379"
  LOG_LEVEL: "info"
  API_VERSION: "v1"
  FRAUD_DETECTION_ENABLED: "true"
  TRANSACTION_LIMIT: "10000"
  MONITORING_ENABLED: "true"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: canary-release
type: Opaque
data:
  # echo -n 'secure-db-password' | base64
  db_password: c2VjdXJlLWRiLXBhc3N3b3Jk
  # echo -n 'fraud-ml-api-key' | base64
  fraud_api_key: ZnJhdWQtbWwtYXBpLWtleQ==
  # echo -n 'jwt-signing-secret' | base64
  jwt_secret: and0LXNpZ25pbmctc2VjcmV0
---
# PostgreSQL Database
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: canary-release
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "transactions"
        - name: POSTGRES_USER
          value: "finapp"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: postgres-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: canary-release
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
# Redis for caching
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: canary-release
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: canary-release
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
---
# Metrics collection service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-collector
  namespace: canary-release
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-collector
  template:
    metadata:
      labels:
        app: metrics-collector
    spec:
      containers:
      - name: metrics
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting metrics collector..."
          while true; do
            echo "$(date): Collecting metrics..."
            # Simulate metrics collection
            echo "Transaction rate: $((RANDOM % 1000 + 100))/sec"
            echo "Error rate: $((RANDOM % 5))%"
            echo "Response time: $((RANDOM % 200 + 50))ms"
            sleep 30
          done
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-service
  namespace: canary-release
spec:
  selector:
    app: metrics-collector
  ports:
  - port: 8080
    targetPort: 8080
EOF

kubectl apply -f base-infrastructure.yaml
```

### Task 2: Deploy Stable Version (10 minutes)

Deploy the current stable version of the payment API:

```yaml
cat << EOF > stable-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api-stable
  namespace: canary-release
  labels:
    app: payment-api
    version: stable
    track: stable
spec:
  replicas: 9  # 90% of traffic initially
  selector:
    matchLabels:
      app: payment-api
      version: stable
  template:
    metadata:
      labels:
        app: payment-api
        version: stable
        track: stable
    spec:
      containers:
      - name: payment-api
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: PORT
          value: "3000"
        - name: NODE_ENV
          value: "production"
        - name: API_VERSION
          value: "stable-v1.5.0"
        - name: DEPLOYMENT_TRACK
          value: "stable"
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: REDIS_URL
        - name: FRAUD_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: fraud_api_key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt_secret
        command:
        - sh
        - -c
        - |
          cat << 'NODEAPP' > app.js
          const express = require('express');
          const crypto = require('crypto');
          const app = express();
          const port = process.env.PORT || 3000;
          
          app.use(express.json());
          
          // Global metrics
          let metrics = {
            totalTransactions: 0,
            successfulTransactions: 0,
            failedTransactions: 0,
            fraudDetected: 0,
            avgResponseTime: 0,
            uptime: Date.now()
          };
          
          // Simulate fraud detection (stable version)
          function detectFraud(transaction) {
            // Simple rule-based fraud detection
            const riskFactors = [];
            
            if (transaction.amount > 10000) {
              riskFactors.push('high_amount');
            }
            
            if (transaction.merchant === 'suspicious_merchant') {
              riskFactors.push('suspicious_merchant');
            }
            
            // 2% fraud rate in stable version
            const isFraud = Math.random() < 0.02;
            
            return {
              isFraud,
              riskScore: isFraud ? Math.random() * 0.3 + 0.7 : Math.random() * 0.3,
              riskFactors,
              algorithm: 'rule_based_v1',
              version: process.env.API_VERSION
            };
          }
          
          // Health check
          app.get('/health', (req, res) => {
            const health = {
              status: 'healthy',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString(),
              uptime: Date.now() - metrics.uptime,
              metrics: {
                totalTransactions: metrics.totalTransactions,
                successRate: metrics.totalTransactions > 0 
                  ? (metrics.successfulTransactions / metrics.totalTransactions * 100).toFixed(2) + '%'
                  : '0%',
                fraudDetectionRate: metrics.totalTransactions > 0
                  ? (metrics.fraudDetected / metrics.totalTransactions * 100).toFixed(2) + '%'
                  : '0%'
              }
            };
            res.json(health);
          });
          
          // Readiness check
          app.get('/ready', (req, res) => {
            res.json({
              status: 'ready',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString()
            });
          });
          
          // Main API endpoint
          app.get('/', (req, res) => {
            res.json({
              service: 'Payment API',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              environment: process.env.NODE_ENV,
              features: {
                fraudDetection: 'rule_based_v1',
                encryption: 'AES256',
                compliance: 'PCI_DSS',
                monitoring: 'basic'
              },
              timestamp: new Date().toISOString()
            });
          });
          
          // Process payment endpoint
          app.post('/api/payments', (req, res) => {
            const startTime = Date.now();
            metrics.totalTransactions++;
            
            try {
              const transaction = req.body;
              
              // Validate transaction
              if (!transaction.amount || !transaction.merchant || !transaction.cardNumber) {
                metrics.failedTransactions++;
                return res.status(400).json({
                  error: 'Invalid transaction data',
                  version: process.env.API_VERSION,
                  track: process.env.DEPLOYMENT_TRACK
                });
              }
              
              // Fraud detection
              const fraudCheck = detectFraud(transaction);
              
              if (fraudCheck.isFraud) {
                metrics.fraudDetected++;
                return res.status(403).json({
                  error: 'Transaction blocked - fraud detected',
                  riskScore: fraudCheck.riskScore,
                  riskFactors: fraudCheck.riskFactors,
                  version: process.env.API_VERSION,
                  track: process.env.DEPLOYMENT_TRACK
                });
              }
              
              // Simulate payment processing
              const processingTime = Math.random() * 1000 + 500; // 500-1500ms
              
              setTimeout(() => {
                // 98% success rate
                const isSuccess = Math.random() > 0.02;
                
                if (isSuccess) {
                  metrics.successfulTransactions++;
                  
                  const responseTime = Date.now() - startTime;
                  metrics.avgResponseTime = (metrics.avgResponseTime + responseTime) / 2;
                  
                  res.json({
                    transactionId: crypto.randomUUID(),
                    status: 'approved',
                    amount: transaction.amount,
                    merchant: transaction.merchant,
                    processedAt: new Date().toISOString(),
                    fraudCheck: {
                      riskScore: fraudCheck.riskScore,
                      algorithm: fraudCheck.algorithm
                    },
                    version: process.env.API_VERSION,
                    track: process.env.DEPLOYMENT_TRACK,
                    responseTime: responseTime + 'ms'
                  });
                } else {
                  metrics.failedTransactions++;
                  res.status(500).json({
                    error: 'Payment processing failed',
                    version: process.env.API_VERSION,
                    track: process.env.DEPLOYMENT_TRACK
                  });
                }
              }, processingTime);
              
            } catch (error) {
              metrics.failedTransactions++;
              res.status(500).json({
                error: 'Internal server error',
                version: process.env.API_VERSION,
                track: process.env.DEPLOYMENT_TRACK
              });
            }
          });
          
          // Metrics endpoint
          app.get('/metrics', (req, res) => {
            res.json({
              ...metrics,
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString()
            });
          });
          
          app.listen(port, () => {
            console.log(\`Payment API (stable) listening on port \${port}\`);
            console.log(\`Version: \${process.env.API_VERSION}\`);
          });
          NODEAPP
          
          npm init -y
          npm install express
          node app.js
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: payment-api-stable-service
  namespace: canary-release
  labels:
    app: payment-api
    version: stable
spec:
  selector:
    app: payment-api
    version: stable
  ports:
  - port: 80
    targetPort: 3000
---
# Main service that will distribute traffic
apiVersion: v1
kind: Service
metadata:
  name: payment-api-service
  namespace: canary-release
  labels:
    app: payment-api
spec:
  selector:
    app: payment-api  # Initially serves all versions
  ports:
  - port: 80
    targetPort: 3000
EOF

kubectl apply -f stable-deployment.yaml
```

### Task 3: Deploy Canary Version (10 minutes)

Deploy the new canary version with enhanced fraud detection:

```yaml
cat << EOF > canary-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api-canary
  namespace: canary-release
  labels:
    app: payment-api
    version: canary
    track: canary
spec:
  replicas: 1  # 10% of traffic initially
  selector:
    matchLabels:
      app: payment-api
      version: canary
  template:
    metadata:
      labels:
        app: payment-api
        version: canary
        track: canary
    spec:
      containers:
      - name: payment-api
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: PORT
          value: "3000"
        - name: NODE_ENV
          value: "production"
        - name: API_VERSION
          value: "canary-v2.0.0"
        - name: DEPLOYMENT_TRACK
          value: "canary"
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: REDIS_URL
        - name: FRAUD_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: fraud_api_key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt_secret
        command:
        - sh
        - -c
        - |
          cat << 'NODEAPP' > app.js
          const express = require('express');
          const crypto = require('crypto');
          const app = express();
          const port = process.env.PORT || 3000;
          
          app.use(express.json());
          
          // Enhanced metrics for canary
          let metrics = {
            totalTransactions: 0,
            successfulTransactions: 0,
            failedTransactions: 0,
            fraudDetected: 0,
            avgResponseTime: 0,
            uptime: Date.now(),
            mlModelAccuracy: 0.97,
            falsePositiveRate: 0.01
          };
          
          // Enhanced ML-based fraud detection (canary version)
          function detectFraudML(transaction) {
            // Advanced ML-based fraud detection
            const features = {
              amount: transaction.amount,
              merchant: transaction.merchant,
              time: new Date().getHours(),
              dayOfWeek: new Date().getDay()
            };
            
            const riskFactors = [];
            let riskScore = 0;
            
            // Amount-based risk
            if (transaction.amount > 10000) {
              riskFactors.push('high_amount');
              riskScore += 0.3;
            } else if (transaction.amount > 5000) {
              riskFactors.push('moderate_amount');
              riskScore += 0.1;
            }
            
            // Merchant-based risk
            if (transaction.merchant === 'suspicious_merchant') {
              riskFactors.push('suspicious_merchant');
              riskScore += 0.4;
            }
            
            // Time-based risk (late night transactions)
            if (features.time < 6 || features.time > 22) {
              riskFactors.push('unusual_time');
              riskScore += 0.2;
            }
            
            // Weekend transactions
            if (features.dayOfWeek === 0 || features.dayOfWeek === 6) {
              riskFactors.push('weekend_transaction');
              riskScore += 0.1;
            }
            
            // Enhanced ML model - 1.5% fraud rate but better accuracy
            const mlPrediction = Math.random() < 0.015;
            
            // Combine rule-based and ML predictions
            const isFraud = mlPrediction || riskScore > 0.6;
            
            return {
              isFraud,
              riskScore: Math.min(riskScore + (Math.random() * 0.2), 1.0),
              riskFactors,
              algorithm: 'ml_enhanced_v2',
              confidence: 0.95 + (Math.random() * 0.05),
              version: process.env.API_VERSION
            };
          }
          
          // Health check with enhanced metrics
          app.get('/health', (req, res) => {
            const health = {
              status: 'healthy',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString(),
              uptime: Date.now() - metrics.uptime,
              metrics: {
                totalTransactions: metrics.totalTransactions,
                successRate: metrics.totalTransactions > 0 
                  ? (metrics.successfulTransactions / metrics.totalTransactions * 100).toFixed(2) + '%'
                  : '0%',
                fraudDetectionRate: metrics.totalTransactions > 0
                  ? (metrics.fraudDetected / metrics.totalTransactions * 100).toFixed(2) + '%'
                  : '0%',
                mlModelAccuracy: (metrics.mlModelAccuracy * 100).toFixed(1) + '%',
                falsePositiveRate: (metrics.falsePositiveRate * 100).toFixed(2) + '%'
              },
              features: {
                enhancedFraudDetection: true,
                mlModel: true,
                realTimeAnalytics: true
              }
            };
            res.json(health);
          });
          
          // Readiness check
          app.get('/ready', (req, res) => {
            res.json({
              status: 'ready',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString(),
              mlModelLoaded: true
            });
          });
          
          // Main API endpoint with enhanced features
          app.get('/', (req, res) => {
            res.json({
              service: 'Payment API - Enhanced',
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              environment: process.env.NODE_ENV,
              features: {
                fraudDetection: 'ml_enhanced_v2',
                encryption: 'AES256',
                compliance: 'PCI_DSS',
                monitoring: 'advanced',
                realTimeAnalytics: true,
                enhancedSecurity: true
              },
              improvements: {
                fraudAccuracy: '+15%',
                responseTime: '-20%',
                falsePositives: '-50%'
              },
              timestamp: new Date().toISOString()
            });
          });
          
          // Enhanced payment processing endpoint
          app.post('/api/payments', (req, res) => {
            const startTime = Date.now();
            metrics.totalTransactions++;
            
            try {
              const transaction = req.body;
              
              // Enhanced validation
              if (!transaction.amount || !transaction.merchant || !transaction.cardNumber) {
                metrics.failedTransactions++;
                return res.status(400).json({
                  error: 'Invalid transaction data',
                  version: process.env.API_VERSION,
                  track: process.env.DEPLOYMENT_TRACK
                });
              }
              
              // Enhanced fraud detection
              const fraudCheck = detectFraudML(transaction);
              
              if (fraudCheck.isFraud) {
                metrics.fraudDetected++;
                return res.status(403).json({
                  error: 'Transaction blocked - fraud detected',
                  riskScore: fraudCheck.riskScore,
                  riskFactors: fraudCheck.riskFactors,
                  confidence: fraudCheck.confidence,
                  algorithm: fraudCheck.algorithm,
                  version: process.env.API_VERSION,
                  track: process.env.DEPLOYMENT_TRACK
                });
              }
              
              // Faster processing in canary (20% improvement)
              const processingTime = Math.random() * 800 + 400; // 400-1200ms
              
              setTimeout(() => {
                // 98.5% success rate (improved)
                const isSuccess = Math.random() > 0.015;
                
                if (isSuccess) {
                  metrics.successfulTransactions++;
                  
                  const responseTime = Date.now() - startTime;
                  metrics.avgResponseTime = (metrics.avgResponseTime + responseTime) / 2;
                  
                  res.json({
                    transactionId: crypto.randomUUID(),
                    status: 'approved',
                    amount: transaction.amount,
                    merchant: transaction.merchant,
                    processedAt: new Date().toISOString(),
                    fraudCheck: {
                      riskScore: fraudCheck.riskScore,
                      algorithm: fraudCheck.algorithm,
                      confidence: fraudCheck.confidence,
                      enhancedSecurity: true
                    },
                    version: process.env.API_VERSION,
                    track: process.env.DEPLOYMENT_TRACK,
                    responseTime: responseTime + 'ms',
                    features: ['enhanced_fraud_detection', 'faster_processing']
                  });
                } else {
                  metrics.failedTransactions++;
                  res.status(500).json({
                    error: 'Payment processing failed',
                    version: process.env.API_VERSION,
                    track: process.env.DEPLOYMENT_TRACK
                  });
                }
              }, processingTime);
              
            } catch (error) {
              metrics.failedTransactions++;
              res.status(500).json({
                error: 'Internal server error',
                version: process.env.API_VERSION,
                track: process.env.DEPLOYMENT_TRACK
              });
            }
          });
          
          // Enhanced metrics endpoint
          app.get('/metrics', (req, res) => {
            res.json({
              ...metrics,
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK,
              timestamp: new Date().toISOString(),
              enhanced: true
            });
          });
          
          // New analytics endpoint
          app.get('/api/analytics', (req, res) => {
            res.json({
              fraudPrevention: {
                totalBlocked: metrics.fraudDetected,
                accuracy: metrics.mlModelAccuracy,
                falsePositiveRate: metrics.falsePositiveRate
              },
              performance: {
                avgResponseTime: metrics.avgResponseTime + 'ms',
                successRate: metrics.totalTransactions > 0 
                  ? (metrics.successfulTransactions / metrics.totalTransactions * 100).toFixed(2) + '%'
                  : '0%'
              },
              version: process.env.API_VERSION,
              track: process.env.DEPLOYMENT_TRACK
            });
          });
          
          app.listen(port, () => {
            console.log(\`Payment API (canary) listening on port \${port}\`);
            console.log(\`Version: \${process.env.API_VERSION}\`);
            console.log('Enhanced ML fraud detection enabled');
          });
          NODEAPP
          
          npm init -y
          npm install express
          node app.js
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: payment-api-canary-service
  namespace: canary-release
  labels:
    app: payment-api
    version: canary
spec:
  selector:
    app: payment-api
    version: canary
  ports:
  - port: 80
    targetPort: 3000
EOF

kubectl apply -f canary-deployment.yaml
```

### Task 4: Create Canary Management Scripts (10 minutes)

Create scripts to manage the canary deployment:

```bash
# Create canary management script
cat << 'EOF' > manage-canary.sh
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
EOF

chmod +x manage-canary.sh

# Create automated canary progression script
cat << 'EOF' > auto-canary.sh
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
EOF

chmod +x auto-canary.sh
```

### Task 5: Execute Canary Deployment (10 minutes)

Run the progressive canary deployment:

```bash
# Check initial status
echo "Initial deployment status:"
kubectl get deployments -n canary-release
./manage-canary.sh status

# Start with 10% canary traffic
echo -e "\nStarting canary with 10% traffic:"
./manage-canary.sh set 10

# Wait for deployment to stabilize
sleep 30

# Monitor initial metrics
echo -e "\nMonitoring initial canary metrics:"
./manage-canary.sh monitor

# Test different endpoints
echo -e "\nTesting canary features:"
kubectl port-forward -n canary-release svc/payment-api-canary-service 8082:80 &
CANARY_PF_PID=$!
sleep 3

echo "Testing enhanced analytics endpoint (canary only):"
curl -s http://localhost:8082/api/analytics | jq '.'

echo -e "\nTesting main endpoint:"
curl -s http://localhost:8082/ | jq '.improvements'

kill $CANARY_PF_PID

# Increase to 25% traffic
echo -e "\nIncreasing canary traffic to 25%:"
./manage-canary.sh set 25

# Run some load to test
kubectl port-forward -n canary-release svc/payment-api-service 8080:80 &
MAIN_PF_PID=$!
sleep 3

echo "Running sample transactions..."
for i in {1..10}; do
    curl -s -X POST http://localhost:8080/api/payments \
        -H "Content-Type: application/json" \
        -d '{"amount": '$((RANDOM % 2000 + 100))', "merchant": "test_merchant_'$i'", "cardNumber": "****1234"}' | jq '.track' &
done

wait
kill $MAIN_PF_PID

# Check metrics after load
echo -e "\nMetrics after load test:"
./manage-canary.sh monitor
```

### Task 6: Automated Testing and Validation (Bonus)

Run the automated canary progression:

```bash
# Run automated canary deployment (optional - takes ~6 minutes)
echo "Running automated canary deployment..."
echo "This will progressively shift traffic: 10% -> 25% -> 50% -> 100%"
echo "Press Ctrl+C to skip automated deployment"

read -t 10 -p "Continue with automated deployment? (y/N): " response
if [[ $response =~ ^[Yy]$ ]]; then
    ./auto-canary.sh
else
    echo "Skipping automated deployment. You can run it manually with: ./auto-canary.sh"
fi

# Manual validation
echo -e "\nManual validation - testing both versions:"

# Test stable version
kubectl port-forward -n canary-release svc/payment-api-stable-service 8081:80 &
STABLE_PF_PID=$!

# Test canary version  
kubectl port-forward -n canary-release svc/payment-api-canary-service 8082:80 &
CANARY_PF_PID=$!

sleep 3

echo "Stable version features:"
curl -s http://localhost:8081/ | jq '.features'

echo -e "\nCanary version improvements:"
curl -s http://localhost:8082/ | jq '.improvements'

kill $STABLE_PF_PID $CANARY_PF_PID
```

## Validation and Testing

### Final Validation

```bash
# Create comprehensive validation script
cat << 'EOF' > validate-canary.sh
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
EOF

chmod +x validate-canary.sh
./validate-canary.sh
```

## Cleanup

```bash
# Clean up resources
kubectl delete namespace canary-release

# Clean up scripts
rm -f manage-canary.sh auto-canary.sh validate-canary.sh
rm -f base-infrastructure.yaml stable-deployment.yaml canary-deployment.yaml
```

## Success Criteria

- [ ] Stable version deploys successfully with baseline metrics
- [ ] Canary version deploys with enhanced features
- [ ] Traffic can be gradually shifted between versions
- [ ] Both versions handle requests correctly with proper routing
- [ ] Metrics show differences between versions (fraud detection, response time)
- [ ] Health checks validate both deployments
- [ ] Rollback functionality works instantly
- [ ] Progressive traffic shifting maintains service availability
- [ ] Enhanced fraud detection shows improved accuracy in canary
- [ ] Load testing demonstrates version differences

## Key Takeaways

1. **Canary releases** enable safe deployment of new features
2. **Progressive traffic shifting** reduces risk during deployment
3. **Metrics monitoring** is crucial for validating canary success
4. **Automated rollback** protects against failed deployments
5. **Health checks** ensure service reliability during transitions
6. **Load testing** validates performance under realistic conditions

## Best Practices

1. Start with small traffic percentages (5-10%)
2. Monitor key business metrics throughout deployment
3. Implement automated rollback triggers
4. Use feature flags for additional control
5. Test rollback procedures before production deployment
6. Maintain audit trails for compliance requirements