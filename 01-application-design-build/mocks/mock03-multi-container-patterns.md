# Mock Exam: Multi-Container Pod Design Patterns

**Domain**: Application Design and Build (20%)  
**Topic**: Understand multi-container Pod design patterns  
**Time Limit**: 35 minutes  
**Questions**: 4  

---

## [Question 1: Sidecar Pattern Implementation (10 minutes)](/01-application-design-build/mocks/mock-exam-03/q01/)
**Points**: 25%

Create a multi-container Pod that implements the sidecar pattern for log processing.

**Scenario**: You have a web application that writes logs to a shared volume. You need a sidecar container to process and forward these logs.

**Requirements**:

**Main Application Container**:
- Name: `web-app`
- Image: `nginx:1.24-alpine`
- Generates access logs to `/var/log/nginx/access.log`
- Serves content from `/usr/share/nginx/html`

**Sidecar Container**:
- Name: `log-processor`
- Image: `busybox:1.35`
- Reads logs from shared volume and processes them
- Command: `["sh", "-c", "while true; do if [ -f /shared-logs/access.log ]; then echo '[PROCESSED]' $(tail -n 1 /shared-logs/access.log); fi; sleep 10; done"]`

**Shared Storage**:
- Volume name: `log-volume`
- Mount path in web-app: `/var/log/nginx`
- Mount path in sidecar: `/shared-logs`
- Use `emptyDir` volume

**Tasks**:
1. Create the Pod manifest in `/tmp/sidecar-pod.yaml`
2. Apply the Pod and verify both containers are running
3. Generate some traffic to create logs: `kubectl exec -it <pod-name> -c web-app -- curl localhost`
4. Check the sidecar container logs to verify log processing
5. Document the sidecar pattern benefits in `/tmp/sidecar-benefits.txt`

---

## [Question 2: Init Containers for Dependency Management (8 minutes)](/01-application-design-build/mocks/mock-exam-03/q02/)
**Points**: 22%

Create a Pod with init containers that handle service dependencies before the main application starts.

**Scenario**: Deploy a database application that requires:
1. Database schema initialization
2. Configuration file setup
3. Network connectivity verification

**Init Container Specifications**:

**Init Container 1** - Schema Setup:
- Name: `init-schema`
- Image: `busybox:1.35`
- Purpose: Create database schema files
- Command: `["sh", "-c", "echo 'CREATE TABLE users (id INT, name VARCHAR(50));' > /shared-data/schema.sql; echo 'Schema file created'"]`

**Init Container 2** - Config Setup:
- Name: `init-config`
- Image: `busybox:1.35`
- Purpose: Generate configuration files
- Command: `["sh", "-c", "echo 'port=5432\nmax_connections=100\nshared_buffers=256MB' > /shared-config/postgresql.conf; echo 'Config file created'"]`

**Init Container 3** - Network Check:
- Name: `network-check`
- Image: `busybox:1.35`
- Purpose: Verify network connectivity
- Command: `["sh", "-c", "nslookup kubernetes.default.svc.cluster.local; echo 'Network connectivity verified'"]`

**Main Container**:
- Name: `database`
- Image: `postgres:15-alpine`
- Environment variables: `POSTGRES_DB=testdb`, `POSTGRES_USER=admin`, `POSTGRES_PASSWORD=secret`
- Mount both shared volumes

**Volumes**:
- `data-volume`: Mount at `/shared-data` (init containers) and `/docker-entrypoint-initdb.d` (main container)
- `config-volume`: Mount at `/shared-config` (init containers) and `/etc/postgresql` (main container)

**Tasks**:
1. Create the Pod manifest in `/tmp/init-containers-pod.yaml`
2. Apply the Pod and monitor the init container execution order
3. Verify all init containers complete successfully before the main container starts
4. Check the main container has access to files created by init containers

---

## [Question 3: Ambassador Pattern for External Service Access (8 minutes)](/01-application-design-build/mocks/mock-exam-03/q03/)
**Points**: 25%

Implement the ambassador pattern to manage external database connections through a proxy container.

**Scenario**: Your application needs to connect to an external database, but you want to abstract the connection logic and provide connection pooling.

**Ambassador Container**:
- Name: `db-ambassador`
- Image: `haproxy:2.8-alpine`
- Purpose: Proxy connections to external database
- Config: Create HAProxy configuration to forward traffic from port 5432 to external service
- Port: Listen on `5432`

**Application Container**:
- Name: `app`
- Image: `busybox:1.35`
- Purpose: Application that connects to database through ambassador
- Command: `["sh", "-c", "while true; do echo 'Connecting to database via ambassador on localhost:5432'; nc -z localhost 5432 && echo 'Connection successful' || echo 'Connection failed'; sleep 30; done"]`

**Configuration Requirements**:
1. Create a ConfigMap with HAProxy configuration
2. Ambassador container mounts the config and uses it
3. Both containers share the network namespace (they can communicate via localhost)
4. Application connects to ambassador on localhost:5432
5. Ambassador forwards to external service `external-db.example.com:5432`

**Tasks**:
1. Create the ConfigMap for HAProxy configuration
2. Create the Pod manifest in `/tmp/ambassador-pod.yaml`
3. Apply both resources
4. Verify the ambassador container is listening on port 5432
5. Check application container logs for connection attempts

**HAProxy Config Template**:
```
global
    daemon

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend db_frontend
    bind *:5432
    default_backend db_backend

backend db_backend
    server external_db external-db.example.com:5432 check
```

---

## [Question 4: Adapter Pattern for Log Format Standardization (9 minutes)](/01-application-design-build/mocks/mock-exam-03/q04/)
**Points**: 28%

Create a multi-container Pod using the adapter pattern to standardize log formats from different applications.

**Scenario**: You have multiple applications with different log formats that need to be standardized before being sent to a centralized logging system.

**Application Containers**:

**App Container 1**:
- Name: `app-nginx`
- Image: `nginx:1.24-alpine`
- Generates access logs in nginx format
- Log location: `/var/log/nginx/access.log`

**App Container 2**:
- Name: `app-apache`
- Image: `httpd:2.4-alpine`
- Generates access logs in Apache format
- Log location: `/usr/local/apache2/logs/access_log`

**Adapter Container**:
- Name: `log-adapter`
- Image: `busybox:1.35`
- Purpose: Read logs from both applications and convert to JSON format
- Output: Standardized JSON logs to stdout for log collection

**Adapter Logic**:
```bash
# Continuously monitor both log files and convert to JSON
while true; do
  if [ -f /nginx-logs/access.log ]; then
    tail -n 0 -f /nginx-logs/access.log | while read line; do
      echo "{\"source\":\"nginx\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
    done &
  fi
  
  if [ -f /apache-logs/access_log ]; then
    tail -n 0 -f /apache-logs/access_log | while read line; do
      echo "{\"source\":\"apache\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
    done &
  fi
  
  sleep 60
done
```

**Volume Configuration**:
- `nginx-logs`: Shared between nginx and adapter
- `apache-logs`: Shared between apache and adapter

**Tasks**:
1. Create the Pod manifest in `/tmp/adapter-pod.yaml`
2. Apply the Pod and wait for all containers to be ready
3. Generate traffic to both web servers:
   - nginx: `kubectl exec -it <pod> -c app-nginx -- curl localhost`
   - apache: `kubectl exec -it <pod> -c app-apache -- curl localhost`
4. Check adapter container logs to verify JSON format conversion
5. Save a sample of the standardized output to `/tmp/adapter-output.json`
6. Create a comparison document showing original vs adapted log formats in `/tmp/log-comparison.txt`

---

## Answer Key & Solutions

### Question 1: Sidecar Pattern Implementation

<details>
<summary>Solution</summary>

**sidecar-pod.yaml**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-logging
  labels:
    app: web-with-sidecar
spec:
  containers:
  - name: web-app
    image: nginx:1.24-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/nginx
  - name: log-processor
    image: busybox:1.35
    command: 
    - "sh"
    - "-c"
    - "while true; do if [ -f /shared-logs/access.log ]; then echo '[PROCESSED]' $(tail -n 1 /shared-logs/access.log); fi; sleep 10; done"
    volumeMounts:
    - name: log-volume
      mountPath: /shared-logs
  volumes:
  - name: log-volume
    emptyDir: {}
```

**Commands**:
```bash
kubectl apply -f /tmp/sidecar-pod.yaml
kubectl get pods sidecar-logging
kubectl exec -it sidecar-logging -c web-app -- curl localhost
kubectl logs sidecar-logging -c log-processor
```

**sidecar-benefits.txt**:
```
Sidecar Pattern Benefits:
1. Separation of Concerns - Log processing is isolated from main application
2. Reusability - Same sidecar can be used with different applications
3. Independent Scaling - Can optimize resources for each container separately
4. Independent Updates - Can update log processing logic without touching main app
5. Shared Resources - Efficient sharing of storage and network without tight coupling
```
</details>

### Question 2: Init Containers for Dependency Management

<details>
<summary>Solution</summary>

**init-containers-pod.yaml**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database-with-init
  labels:
    app: database
spec:
  initContainers:
  - name: init-schema
    image: busybox:1.35
    command:
    - "sh"
    - "-c"
    - "echo 'CREATE TABLE users (id INT, name VARCHAR(50));' > /shared-data/schema.sql; echo 'Schema file created'"
    volumeMounts:
    - name: data-volume
      mountPath: /shared-data
  - name: init-config
    image: busybox:1.35
    command:
    - "sh"
    - "-c"
    - "echo 'port=5432\nmax_connections=100\nshared_buffers=256MB' > /shared-config/postgresql.conf; echo 'Config file created'"
    volumeMounts:
    - name: config-volume
      mountPath: /shared-config
  - name: network-check
    image: busybox:1.35
    command:
    - "sh"
    - "-c"
    - "nslookup kubernetes.default.svc.cluster.local; echo 'Network connectivity verified'"
  containers:
  - name: database
    image: postgres:15-alpine
    env:
    - name: POSTGRES_DB
      value: "testdb"
    - name: POSTGRES_USER
      value: "admin"
    - name: POSTGRES_PASSWORD
      value: "secret"
    ports:
    - containerPort: 5432
    volumeMounts:
    - name: data-volume
      mountPath: /docker-entrypoint-initdb.d
    - name: config-volume
      mountPath: /etc/postgresql
  volumes:
  - name: data-volume
    emptyDir: {}
  - name: config-volume
    emptyDir: {}
```

**Commands**:
```bash
kubectl apply -f /tmp/init-containers-pod.yaml
kubectl get pods database-with-init -w
kubectl logs database-with-init -c init-schema
kubectl logs database-with-init -c init-config
kubectl logs database-with-init -c network-check
kubectl exec -it database-with-init -- ls -la /docker-entrypoint-initdb.d/
```
</details>

### Question 3: Ambassador Pattern for External Service Access

<details>
<summary>Solution</summary>

**HAProxy ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
data:
  haproxy.cfg: |
    global
        daemon

    defaults
        mode tcp
        timeout connect 5000ms
        timeout client 50000ms
        timeout server 50000ms

    frontend db_frontend
        bind *:5432
        default_backend db_backend

    backend db_backend
        server external_db external-db.example.com:5432 check
```

**ambassador-pod.yaml**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pattern
  labels:
    app: database-proxy
spec:
  containers:
  - name: db-ambassador
    image: haproxy:2.8-alpine
    ports:
    - containerPort: 5432
    volumeMounts:
    - name: haproxy-config
      mountPath: /usr/local/etc/haproxy/haproxy.cfg
      subPath: haproxy.cfg
  - name: app
    image: busybox:1.35
    command:
    - "sh"
    - "-c"
    - "while true; do echo 'Connecting to database via ambassador on localhost:5432'; nc -z localhost 5432 && echo 'Connection successful' || echo 'Connection failed'; sleep 30; done"
  volumes:
  - name: haproxy-config
    configMap:
      name: haproxy-config
```

**Commands**:
```bash
kubectl apply -f haproxy-configmap.yaml
kubectl apply -f /tmp/ambassador-pod.yaml
kubectl get pods ambassador-pattern
kubectl logs ambassador-pattern -c app
kubectl exec -it ambassador-pattern -c db-ambassador -- netstat -ln
```
</details>

### Question 4: Adapter Pattern for Log Format Standardization

<details>
<summary>Solution</summary>

**adapter-pod.yaml**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter-logging
  labels:
    app: multi-app-logging
spec:
  containers:
  - name: app-nginx
    image: nginx:1.24-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: nginx-logs
      mountPath: /var/log/nginx
  - name: app-apache
    image: httpd:2.4-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: apache-logs
      mountPath: /usr/local/apache2/logs
  - name: log-adapter
    image: busybox:1.35
    command:
    - "sh"
    - "-c"
    - |
      while true; do
        if [ -f /nginx-logs/access.log ]; then
          tail -n 0 -f /nginx-logs/access.log | while read line; do
            echo "{\"source\":\"nginx\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
          done &
        fi
        
        if [ -f /apache-logs/access_log ]; then
          tail -n 0 -f /apache-logs/access_log | while read line; do
            echo "{\"source\":\"apache\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
          done &
        fi
        
        sleep 60
      done
    volumeMounts:
    - name: nginx-logs
      mountPath: /nginx-logs
    - name: apache-logs
      mountPath: /apache-logs
  volumes:
  - name: nginx-logs
    emptyDir: {}
  - name: apache-logs
    emptyDir: {}
```

**Commands**:
```bash
kubectl apply -f /tmp/adapter-pod.yaml
kubectl get pods adapter-logging
kubectl exec -it adapter-logging -c app-nginx -- curl localhost
kubectl exec -it adapter-logging -c app-apache -- curl localhost
kubectl logs adapter-logging -c log-adapter
```

**Sample adapter-output.json**:
```json
{"source":"nginx","timestamp":"2024-01-15T10:30:45+00:00","message":"172.17.0.1 - - [15/Jan/2024:10:30:45 +0000] \"GET / HTTP/1.1\" 200 615 \"-\" \"curl/7.88.1\""}
{"source":"apache","timestamp":"2024-01-15T10:30:50+00:00","message":"172.17.0.1 - - [15/Jan/2024:10:30:50 +0000] \"GET / HTTP/1.1\" 200 45"}
```

**log-comparison.txt**:
```
Original Log Formats:

Nginx (Combined Log Format):
172.17.0.1 - - [15/Jan/2024:10:30:45 +0000] "GET / HTTP/1.1" 200 615 "-" "curl/7.88.1"

Apache (Common Log Format):
172.17.0.1 - - [15/Jan/2024:10:30:50 +0000] "GET / HTTP/1.1" 200 45

Standardized JSON Format:
{
  "source": "nginx|apache",
  "timestamp": "2024-01-15T10:30:45+00:00",
  "message": "original log line"
}

Benefits of Adapter Pattern:
- Consistent log format for centralized processing
- No modification required to existing applications
- Easy to add new log sources
- Centralized format transformation logic
```
</details>

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 90-100% | All patterns correctly implemented with proper container communication and resource sharing |
| 80-89% | Good understanding of patterns, minor configuration issues |
| 70-79% | Basic pattern concepts correct, some issues with volume mounting or communication |
| 60-69% | Limited understanding of multi-container design patterns |
| Below 60% | Poor understanding of container collaboration and shared resources |

## Key Learning Objectives

After completing this mock exam, you should understand:

1. **Sidecar Pattern**: Extending functionality without modifying main application
2. **Init Containers**: Managing dependencies and initialization tasks
3. **Ambassador Pattern**: Abstracting external service communication
4. **Adapter Pattern**: Data transformation and format standardization
5. **Volume Sharing**: Effective communication between containers
6. **Container Lifecycle**: Understanding startup order and dependencies

## Common Mistakes to Avoid

1. **Volume Mount Mismatches**: Ensure consistent paths between containers
2. **Missing Init Container Dependencies**: Order matters for init containers
3. **Network Communication Issues**: Remember containers in same Pod share network
4. **Resource Conflicts**: Avoid port conflicts between containers
5. **Improper Container Roles**: Each container should have a single, clear responsibility

## Design Pattern Best Practices

1. **Single Responsibility**: Each container should have one primary function
2. **Shared Nothing (Except Volumes)**: Minimize dependencies between containers
3. **Graceful Degradation**: Design patterns should handle container failures
4. **Resource Efficiency**: Balance functionality with resource consumption
5. **Monitoring**: Each pattern should be observable and debuggable