# Mock Scenario 1: Blue-Green Deployment

**Objective**: Implement a complete Blue-Green deployment strategy for a web application
**Time**: 50 minutes
**Difficulty**: Advanced

---

## Scenario Overview

You work for an e-commerce company that needs to deploy a critical web application with zero downtime. The application serves thousands of customers, and any downtime during deployment would result in significant revenue loss. You need to implement a Blue-Green deployment strategy that allows:

- Zero-downtime deployments
- Instant rollback capability
- Traffic validation before switching
- Database migration coordination
- Health monitoring and validation

## Application Architecture

The system consists of:

1. **Web Application**: Node.js/Express API with Redis session store
2. **Database**: PostgreSQL with migration scripts
3. **Load Balancer**: NGINX ingress controller
4. **Monitoring**: Health checks and metrics collection
5. **Cache Layer**: Redis for session management

## Implementation Tasks

### Task 1: Setup Blue-Green Infrastructure (15 minutes)

Create the namespace and base infrastructure:

```bash
# Create namespace for blue-green deployment
kubectl create namespace blue-green-prod

# Create shared resources (database, redis, etc.)
cat << EOF > shared-resources.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: blue-green-prod
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  SESSION_TIMEOUT: "3600"
  API_VERSION: "v1"
  FEATURE_FLAGS: "analytics:true,notifications:true"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: blue-green-prod
type: Opaque
data:
  # echo -n 'super-secret-db-password' | base64
  db_password: c3VwZXItc2VjcmV0LWRiLXBhc3N3b3Jk
  # echo -n 'redis-secret-password' | base64  
  redis_password: cmVkaXMtc2VjcmV0LXBhc3N3b3Jk
  # echo -n 'jwt-secret-key-12345' | base64
  jwt_secret: and0LXNlY3JldC1rZXktMTIzNDU=
---
# PostgreSQL Database
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-db
  namespace: blue-green-prod
  labels:
    app: postgres
    tier: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
        tier: database
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "ecommerce"
        - name: POSTGRES_USER
          value: "webapp"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - webapp
            - -d
            - ecommerce
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - webapp
            - -d
            - ecommerce
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: blue-green-prod
  labels:
    app: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
# Redis Cache
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
  namespace: blue-green-prod
  labels:
    app: redis
    tier: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
        tier: cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --requirepass
        - \$(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis_password
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: blue-green-prod
  labels:
    app: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
EOF

kubectl apply -f shared-resources.yaml
```

### Task 2: Create Blue Environment (10 minutes)

Deploy the initial "Blue" version of the application:

```yaml
cat << EOF > blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-blue
  namespace: blue-green-prod
  labels:
    app: webapp
    version: blue
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: blue
  template:
    metadata:
      labels:
        app: webapp
        version: blue
        environment: production
    spec:
      initContainers:
      - name: db-migration
        image: node:18-alpine
        command:
        - sh
        - -c
        - |
          echo "Running database migrations for Blue deployment..."
          echo "Connecting to database..."
          # Simulate migration
          sleep 10
          echo "Migration completed successfully"
        env:
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_USER
          value: "webapp"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        - name: DB_NAME
          value: "ecommerce"
      containers:
      - name: webapp
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: PORT
          value: "3000"
        - name: NODE_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: NODE_ENV
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL
        - name: APP_VERSION
          value: "blue-v1.0.0"
        - name: DEPLOYMENT_COLOR
          value: "blue"
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_USER
          value: "webapp"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        - name: DB_NAME
          value: "ecommerce"
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis_password
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
          const redis = require('redis');
          const { Pool } = require('pg');
          
          const app = express();
          const port = process.env.PORT || 3000;
          
          // Database connection
          const pool = new Pool({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME,
            port: 5432,
          });
          
          // Redis connection
          const redisClient = redis.createClient({
            host: process.env.REDIS_HOST,
            port: 6379,
            password: process.env.REDIS_PASSWORD
          });
          
          // Health check endpoint
          app.get('/health', async (req, res) => {
            try {
              // Check database
              await pool.query('SELECT 1');
              
              // Check Redis
              await redisClient.ping();
              
              res.json({
                status: 'healthy',
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR,
                timestamp: new Date().toISOString(),
                environment: process.env.NODE_ENV,
                checks: {
                  database: 'ok',
                  redis: 'ok'
                }
              });
            } catch (error) {
              res.status(500).json({
                status: 'unhealthy',
                error: error.message,
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR
              });
            }
          });
          
          // Readiness check
          app.get('/ready', (req, res) => {
            res.json({
              status: 'ready',
              version: process.env.APP_VERSION,
              color: process.env.DEPLOYMENT_COLOR,
              timestamp: new Date().toISOString()
            });
          });
          
          // Main application endpoint
          app.get('/', (req, res) => {
            res.json({
              message: 'E-commerce Application',
              version: process.env.APP_VERSION,
              color: process.env.DEPLOYMENT_COLOR,
              environment: process.env.NODE_ENV,
              timestamp: new Date().toISOString(),
              features: {
                analytics: true,
                notifications: true,
                newFeature: false
              }
            });
          });
          
          // API endpoint with database interaction
          app.get('/api/products', async (req, res) => {
            try {
              const result = await pool.query('SELECT 1 as id, \'Sample Product\' as name, 29.99 as price');
              res.json({
                products: result.rows,
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR,
                cached: false
              });
            } catch (error) {
              res.status(500).json({ error: error.message });
            }
          });
          
          // User session endpoint with Redis
          app.get('/api/session/:userId', async (req, res) => {
            try {
              const userId = req.params.userId;
              const sessionData = {
                userId: userId,
                loginTime: new Date().toISOString(),
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR
              };
              
              await redisClient.setex(\`session:\${userId}\`, 3600, JSON.stringify(sessionData));
              
              res.json({
                message: 'Session created',
                session: sessionData
              });
            } catch (error) {
              res.status(500).json({ error: error.message });
            }
          });
          
          // Graceful shutdown
          process.on('SIGTERM', () => {
            console.log('Received SIGTERM, closing connections...');
            redisClient.quit();
            pool.end();
            process.exit(0);
          });
          
          app.listen(port, () => {
            console.log(\`Blue app listening on port \${port}\`);
            console.log(\`Version: \${process.env.APP_VERSION}\`);
            console.log(\`Environment: \${process.env.NODE_ENV}\`);
          });
          NODEAPP
          
          # Install dependencies and start app
          npm init -y
          npm install express redis pg
          node app.js
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
        lifecycle:
          preStop:
            exec:
              command:
              - sh
              - -c
              - "sleep 15"  # Grace period for connections to drain
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-blue-service
  namespace: blue-green-prod
  labels:
    app: webapp
    version: blue
spec:
  selector:
    app: webapp
    version: blue
  ports:
  - port: 80
    targetPort: 3000
    name: http
  type: ClusterIP
---
# Main service that will switch between blue and green
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
  namespace: blue-green-prod
  labels:
    app: webapp
spec:
  selector:
    app: webapp
    version: blue  # Initially pointing to blue
  ports:
  - port: 80
    targetPort: 3000
    name: http
  type: ClusterIP
EOF

kubectl apply -f blue-deployment.yaml
```

### Task 3: Verify Blue Deployment (5 minutes)

```bash
# Wait for blue deployment to be ready
kubectl rollout status deployment/webapp-blue -n blue-green-prod

# Check all pods are running
kubectl get pods -n blue-green-prod

# Test blue environment
kubectl port-forward -n blue-green-prod svc/webapp-service 8080:80 &

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/api/products
curl http://localhost:8080/api/session/user123

# Kill port forward
pkill -f "kubectl port-forward"
```

### Task 4: Deploy Green Environment (10 minutes)

Deploy the new "Green" version with updates:

```yaml
cat << EOF > green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-green
  namespace: blue-green-prod
  labels:
    app: webapp
    version: green
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: green
  template:
    metadata:
      labels:
        app: webapp
        version: green
        environment: production
    spec:
      initContainers:
      - name: db-migration
        image: node:18-alpine
        command:
        - sh
        - -c
        - |
          echo "Running database migrations for Green deployment..."
          echo "Checking database compatibility..."
          # Simulate migration with new features
          sleep 12
          echo "New feature migration completed successfully"
        env:
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_USER
          value: "webapp"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        - name: DB_NAME
          value: "ecommerce"
      containers:
      - name: webapp
        image: node:18-alpine
        ports:
        - containerPort: 3000
        env:
        - name: PORT
          value: "3000"
        - name: NODE_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: NODE_ENV
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL
        - name: APP_VERSION
          value: "green-v2.0.0"  # Updated version
        - name: DEPLOYMENT_COLOR
          value: "green"
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_USER
          value: "webapp"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        - name: DB_NAME
          value: "ecommerce"
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis_password
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
          const redis = require('redis');
          const { Pool } = require('pg');
          
          const app = express();
          const port = process.env.PORT || 3000;
          
          // Database connection
          const pool = new Pool({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME,
            port: 5432,
          });
          
          // Redis connection
          const redisClient = redis.createClient({
            host: process.env.REDIS_HOST,
            port: 6379,
            password: process.env.REDIS_PASSWORD
          });
          
          // Health check endpoint
          app.get('/health', async (req, res) => {
            try {
              // Check database
              await pool.query('SELECT 1');
              
              // Check Redis
              await redisClient.ping();
              
              res.json({
                status: 'healthy',
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR,
                timestamp: new Date().toISOString(),
                environment: process.env.NODE_ENV,
                checks: {
                  database: 'ok',
                  redis: 'ok',
                  newFeatureHealth: 'ok'  // New health check
                }
              });
            } catch (error) {
              res.status(500).json({
                status: 'unhealthy',
                error: error.message,
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR
              });
            }
          });
          
          // Enhanced readiness check
          app.get('/ready', (req, res) => {
            res.json({
              status: 'ready',
              version: process.env.APP_VERSION,
              color: process.env.DEPLOYMENT_COLOR,
              timestamp: new Date().toISOString(),
              capabilities: ['api', 'database', 'cache', 'newFeature']
            });
          });
          
          // Main application endpoint with new features
          app.get('/', (req, res) => {
            res.json({
              message: 'E-commerce Application - Enhanced Version',
              version: process.env.APP_VERSION,
              color: process.env.DEPLOYMENT_COLOR,
              environment: process.env.NODE_ENV,
              timestamp: new Date().toISOString(),
              features: {
                analytics: true,
                notifications: true,
                newFeature: true,  // New feature enabled
                enhancedSearch: true,
                realTimeUpdates: true
              },
              performance: {
                optimized: true,
                cacheEnabled: true
              }
            });
          });
          
          // Enhanced API endpoint
          app.get('/api/products', async (req, res) => {
            try {
              const result = await pool.query('SELECT 1 as id, \'Enhanced Product\' as name, 24.99 as price, \'New features available\' as description');
              res.json({
                products: result.rows,
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR,
                cached: true,  // Enhanced caching
                totalProducts: result.rows.length,
                apiVersion: 'v2'
              });
            } catch (error) {
              res.status(500).json({ error: error.message });
            }
          });
          
          // New feature endpoint
          app.get('/api/features/new', (req, res) => {
            res.json({
              feature: 'Enhanced Product Recommendations',
              version: process.env.APP_VERSION,
              color: process.env.DEPLOYMENT_COLOR,
              enabled: true,
              description: 'AI-powered product recommendations',
              performance: '50% faster response time'
            });
          });
          
          // Enhanced session endpoint
          app.get('/api/session/:userId', async (req, res) => {
            try {
              const userId = req.params.userId;
              const sessionData = {
                userId: userId,
                loginTime: new Date().toISOString(),
                version: process.env.APP_VERSION,
                color: process.env.DEPLOYMENT_COLOR,
                features: ['newFeature', 'enhancedUI'],
                sessionType: 'enhanced'
              };
              
              await redisClient.setex(\`session:\${userId}\`, 3600, JSON.stringify(sessionData));
              
              res.json({
                message: 'Enhanced session created',
                session: sessionData
              });
            } catch (error) {
              res.status(500).json({ error: error.message });
            }
          });
          
          // Graceful shutdown
          process.on('SIGTERM', () => {
            console.log('Received SIGTERM, closing connections...');
            redisClient.quit();
            pool.end();
            process.exit(0);
          });
          
          app.listen(port, () => {
            console.log(\`Green app listening on port \${port}\`);
            console.log(\`Version: \${process.env.APP_VERSION}\`);
            console.log(\`Environment: \${process.env.NODE_ENV}\`);
            console.log('New features enabled!');
          });
          NODEAPP
          
          # Install dependencies and start app
          npm init -y
          npm install express redis pg
          node app.js
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
        lifecycle:
          preStop:
            exec:
              command:
              - sh
              - -c
              - "sleep 15"
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-green-service
  namespace: blue-green-prod
  labels:
    app: webapp
    version: green
spec:
  selector:
    app: webapp
    version: green
  ports:
  - port: 80
    targetPort: 3000
    name: http
  type: ClusterIP
EOF

kubectl apply -f green-deployment.yaml
```

### Task 5: Test Green Environment (5 minutes)

```bash
# Wait for green deployment to be ready
kubectl rollout status deployment/webapp-green -n blue-green-prod

# Test green environment separately
kubectl port-forward -n blue-green-prod svc/webapp-green-service 8081:80 &

# Test green endpoints
echo "Testing Green Environment:"
curl http://localhost:8081/
curl http://localhost:8081/health
curl http://localhost:8081/api/features/new
curl http://localhost:8081/api/session/user456

# Compare with blue (still active)
echo -e "\nTesting Blue Environment (still active):"
kubectl port-forward -n blue-green-prod svc/webapp-service 8080:80 &
curl http://localhost:8080/

# Kill port forwards
pkill -f "kubectl port-forward"
```

### Task 6: Traffic Switch and Validation (5 minutes)

```bash
# Create traffic switch script
cat << 'EOF' > switch-traffic.sh
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
EOF

chmod +x switch-traffic.sh

# Switch traffic to green
./switch-traffic.sh green

# Verify new features are available
kubectl port-forward -n blue-green-prod svc/webapp-service 8080:80 &
sleep 3

echo "Testing new features after switch:"
curl http://localhost:8080/api/features/new

pkill -f "kubectl port-forward"
```

### Task 7: Rollback Scenario (5 minutes)

```bash
# Create rollback script
cat << 'EOF' > rollback.sh
#!/bin/bash

NAMESPACE="blue-green-prod"

echo "=== EMERGENCY ROLLBACK TO BLUE ==="

# Switch traffic back to blue
echo "Switching traffic back to blue environment..."
kubectl patch service webapp-service -n $NAMESPACE \
    -p '{"spec":{"selector":{"version":"blue"}}}'

# Verify rollback
echo "Verifying rollback..."
kubectl port-forward -n $NAMESPACE svc/webapp-service 8080:80 &
sleep 3

response=$(curl -s http://localhost:8080/ | jq -r '.color')
echo "Active environment after rollback: $response"

if [ "$response" = "blue" ]; then
    echo "✅ Rollback successful - traffic restored to blue"
    
    # Test that old stable version is working
    echo "Testing rolled-back environment:"
    curl -s http://localhost:8080/ | jq '.features'
else
    echo "❌ Rollback failed"
    exit 1
fi

pkill -f "kubectl port-forward"

# Optionally remove green deployment
echo "Green deployment can be safely removed now"
echo "Run: kubectl delete deployment webapp-green -n $NAMESPACE"
EOF

chmod +x rollback.sh

# Test rollback capability
./rollback.sh

# Switch back to green for final testing
./switch-traffic.sh green
```

## Validation and Testing

### Comprehensive Validation

```bash
# Create validation script
cat << 'EOF' > validate-deployment.sh
#!/bin/bash

NAMESPACE="blue-green-prod"

echo "=== Blue-Green Deployment Validation ==="

# Check all deployments
echo "1. Checking deployments:"
kubectl get deployments -n $NAMESPACE

# Check all services
echo -e "\n2. Checking services:"
kubectl get services -n $NAMESPACE

# Check pod health
echo -e "\n3. Checking pod health:"
kubectl get pods -n $NAMESPACE

# Test active environment
echo -e "\n4. Testing active environment:"
kubectl port-forward -n $NAMESPACE svc/webapp-service 8080:80 &
sleep 3

echo "Health check:"
curl -s http://localhost:8080/health | jq '.'

echo -e "\nMain endpoint:"
curl -s http://localhost:8080/ | jq '.'

echo -e "\nNew features:"
curl -s http://localhost:8080/api/features/new | jq '.'

pkill -f "kubectl port-forward"

# Test switch capability
echo -e "\n5. Testing traffic switching:"
current_color=$(kubectl get service webapp-service -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
echo "Current active color: $current_color"

if [ "$current_color" = "green" ]; then
    switch_to="blue"
else
    switch_to="green"
fi

echo "Testing switch to $switch_to..."
./switch-traffic.sh $switch_to

echo "Switching back to $current_color..."
./switch-traffic.sh $current_color

echo -e "\n✅ Blue-Green deployment validation completed!"
EOF

chmod +x validate-deployment.sh
./validate-deployment.sh
```

### Load Testing

```bash
# Create simple load test
cat << 'EOF' > load-test.sh
#!/bin/bash

NAMESPACE="blue-green-prod"
DURATION=${1:-30}  # 30 seconds default

echo "Running load test for $DURATION seconds..."

kubectl port-forward -n $NAMESPACE svc/webapp-service 8080:80 &
PORT_FORWARD_PID=$!
sleep 3

# Simple load test
echo "Starting load test..."
for i in $(seq 1 $DURATION); do
    curl -s http://localhost:8080/ > /dev/null &
    curl -s http://localhost:8080/health > /dev/null &
    curl -s http://localhost:8080/api/products > /dev/null &
    sleep 1
    echo "Requests sent: $((i * 3))"
done

wait

kill $PORT_FORWARD_PID
echo "Load test completed"
EOF

chmod +x load-test.sh

# Run load test during traffic switch
./load-test.sh 10 &
sleep 5
./switch-traffic.sh blue
sleep 5
./switch-traffic.sh green
wait

echo "Load test during traffic switches completed"
```

## Cleanup

```bash
# Clean up all resources
kubectl delete namespace blue-green-prod

# Clean up scripts
rm -f switch-traffic.sh rollback.sh validate-deployment.sh load-test.sh
rm -f shared-resources.yaml blue-deployment.yaml green-deployment.yaml
```

## Success Criteria

- [ ] Blue environment deploys successfully with database and Redis
- [ ] Green environment deploys with new features without affecting blue
- [ ] Traffic can be switched instantly between blue and green
- [ ] Health checks validate application status in both environments
- [ ] Rollback can be executed quickly in case of issues
- [ ] Database migrations run successfully for both environments
- [ ] Zero downtime during traffic switches
- [ ] Both environments can handle concurrent requests
- [ ] Monitoring and validation scripts work correctly

## Key Takeaways

1. **Blue-Green deployment** enables zero-downtime deployments
2. **Shared resources** (database, cache) require careful coordination
3. **Health checks** are critical for validating deployment success
4. **Traffic switching** should be instant and reversible
5. **Database migrations** must be backwards compatible
6. **Monitoring and validation** ensure deployment success
7. **Rollback procedures** must be tested and ready

## Best Practices

1. Use health checks and readiness probes
2. Implement graceful shutdown procedures
3. Test rollback procedures regularly
4. Monitor resource usage during deployments
5. Use database migration strategies that support rollbacks
6. Implement comprehensive validation scripts
7. Coordinate shared resource updates carefully