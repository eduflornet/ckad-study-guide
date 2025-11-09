# Lab 7: Sidecar Logging Container

**Objective**: Implement the sidecar pattern for log collection and processing

**Time**: 35 minutes

**Prerequisites**: Kubernetes cluster access, understanding of multi-container pods

---

## [Exercise 1: Basic Sidecar Pattern (15 minutes)](/01-application-design-build/labs/lab07-solution/exercise-01/)

Create a web application with a sidecar container for log processing.

### Step 1: Simple Sidecar Configuration

Create `basic-sidecar.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-sidecar
  labels:
    app: sidecar-demo
spec:
  containers:
  # Main application container
  - name: web-app
    image: nginx:1.24-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
    - name: web-content
      mountPath: /usr/share/nginx/html
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
      limits:
        memory: "64Mi"
        cpu: "100m"
  
  # Sidecar logging container
  - name: log-sidecar
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Log sidecar starting..."
      
      # Wait for nginx to create log files
      while [ ! -f /shared-logs/access.log ]; do
        echo "Waiting for access.log to be created..."
        sleep 2
      done
      
      echo "Starting to monitor access.log"
      tail -F /shared-logs/access.log | while read line; do
        echo "[PROCESSED] $(date '+%Y-%m-%d %H:%M:%S') - $line"
      done
    volumeMounts:
    - name: shared-logs
      mountPath: /shared-logs
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
      limits:
        memory: "32Mi"
        cpu: "50m"
  
  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: web-content
    configMap:
      name: web-content
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-content
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sidecar Demo</title>
    </head>
    <body>
        <h1>Web Application with Sidecar Logging</h1>
        <p>This application demonstrates the sidecar pattern for log processing.</p>
        <p>Every request is logged and processed by the sidecar container.</p>
        <p>Current time: <span id="time"></span></p>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
```

Deploy and test:
```bash
# Apply the configuration
kubectl apply -f basic-sidecar.yaml

# Check pod status
kubectl get pods web-with-sidecar

# Wait for both containers to be ready
kubectl wait --for=condition=Ready pod/web-with-sidecar --timeout=60s

# Generate some traffic
kubectl exec -it web-with-sidecar -c web-app -- curl localhost

# Check sidecar logs to see processed log entries
kubectl logs web-with-sidecar -c log-sidecar

# Generate more traffic
for i in {1..5}; do
  kubectl exec -it web-with-sidecar -c web-app -- curl localhost/
  sleep 1
done

# Check sidecar logs again
kubectl logs web-with-sidecar -c log-sidecar --tail=10

# Cleanup
kubectl delete -f basic-sidecar.yaml
```

---

## [Exercise 2: Advanced Log Processing Sidecar (15 minutes)](/01-application-design-build/labs/lab07-solution/exercise-02/)

Create a more sophisticated sidecar that processes and enriches logs.

### Step 1: Log Processing Sidecar

Create `advanced-sidecar.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-processor-config
data:
  processor.py: |
    import re
    import json
    import time
    import sys
    from datetime import datetime
    
    def parse_nginx_log(line):
        """Parse nginx access log line into structured data"""
        # Nginx log format: IP - - [timestamp] "method path protocol" status size "referer" "user-agent"
        pattern = r'(\S+) - - \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+) "([^"]*)" "([^"]*)"'
        match = re.match(pattern, line.strip())
        
        if match:
            return {
                "timestamp": datetime.now().isoformat(),
                "client_ip": match.group(1),
                "request_time": match.group(2),
                "method": match.group(3),
                "path": match.group(4),
                "protocol": match.group(5),
                "status_code": int(match.group(6)),
                "response_size": int(match.group(7)),
                "referer": match.group(8),
                "user_agent": match.group(9),
                "severity": "INFO" if int(match.group(6)) < 400 else "WARN" if int(match.group(6)) < 500 else "ERROR"
            }
        return None
    
    def process_logs():
        """Main log processing function"""
        print("Advanced log processor starting...")
        
        log_file = "/shared-logs/access.log"
        
        # Wait for log file
        while True:
            try:
                with open(log_file, 'r') as f:
                    break
            except FileNotFoundError:
                print("Waiting for log file...")
                time.sleep(2)
        
        print(f"Monitoring {log_file}")
        
        # Follow the log file
        with open(log_file, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    parsed = parse_nginx_log(line)
                    if parsed:
                        # Output structured JSON log
                        print(json.dumps(parsed))
                        
                        # Alert on errors
                        if parsed['status_code'] >= 500:
                            alert = {
                                "alert": "HTTP_5XX_ERROR",
                                "timestamp": datetime.now().isoformat(),
                                "details": parsed
                            }
                            print(f"ALERT: {json.dumps(alert)}", file=sys.stderr)
                else:
                    time.sleep(0.1)
    
    if __name__ == "__main__":
        process_logs()
---
apiVersion: v1
kind: Pod
metadata:
  name: advanced-sidecar-demo
  labels:
    app: advanced-sidecar
spec:
  containers:
  # Main application
  - name: web-app
    image: nginx:1.24-alpine
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Advanced log processing sidecar
  - name: log-processor
    image: python:3.11-alpine
    command:
    - python
    - /scripts/processor.py
    volumeMounts:
    - name: shared-logs
      mountPath: /shared-logs
    - name: log-processor-config
      mountPath: /scripts
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
  
  # Log forwarder sidecar
  - name: log-forwarder
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Log forwarder starting..."
      
      # Simulate forwarding structured logs to external system
      while true; do
        if [ -f /shared-logs/access.log ]; then
          # Count log entries
          CURRENT_LINES=$(wc -l < /shared-logs/access.log 2>/dev/null || echo 0)
          LAST_LINES=${LAST_LINES:-0}
          
          if [ $CURRENT_LINES -gt $LAST_LINES ]; then
            NEW_ENTRIES=$((CURRENT_LINES - LAST_LINES))
            echo "Forwarding $NEW_ENTRIES new log entries to external system"
            echo "Total entries processed: $CURRENT_LINES"
            LAST_LINES=$CURRENT_LINES
          fi
        fi
        sleep 5
      done
    volumeMounts:
    - name: shared-logs
      mountPath: /shared-logs
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: log-processor-config
    configMap:
      name: log-processor-config
      defaultMode: 0755
  - name: nginx-config
    configMap:
      name: nginx-custom-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-custom-config
data:
  nginx.conf: |
    server {
        listen 80;
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /api {
            return 200 '{"status":"ok","timestamp":"${time_iso8601}"}';
            add_header Content-Type application/json;
        }
        
        location /error {
            return 500 '{"error":"Internal Server Error"}';
            add_header Content-Type application/json;
        }
        
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
    }
```

Deploy and test advanced sidecar:
```bash
# Apply the advanced configuration
kubectl apply -f advanced-sidecar.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/advanced-sidecar-demo --timeout=60s

# Test different endpoints to generate various log types
kubectl exec -it advanced-sidecar-demo -c web-app -- curl localhost/
kubectl exec -it advanced-sidecar-demo -c web-app -- curl localhost/api
kubectl exec -it advanced-sidecar-demo -c web-app -- curl localhost/error

# Check structured logs from processor
kubectl logs advanced-sidecar-demo -c log-processor

# Check forwarder logs
kubectl logs advanced-sidecar-demo -c log-forwarder

# Generate more traffic and errors
for i in {1..3}; do
  kubectl exec -it advanced-sidecar-demo -c web-app -- curl localhost/
  kubectl exec -it advanced-sidecar-demo -c web-app -- curl localhost/error
  sleep 1
done

# Check for alerts on errors
kubectl logs advanced-sidecar-demo -c log-processor --tail=20

# Cleanup
kubectl delete -f advanced-sidecar.yaml
```

---

## [Exercise 3: Sidecar with Persistent Storage (5 minutes)](/01-application-design-build/labs/lab07-solution/exercise-03/)

Create a sidecar pattern that persists processed logs.

### Step 1: Persistent Log Storage

Create `persistent-sidecar.yaml`:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: log-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: persistent-log-demo
spec:
  containers:
  # Application container
  - name: app
    image: python:3.11-alpine
    command:
    - python
    - -c
    - |
      import time
      import random
      import logging
      
      # Configure logging
      logging.basicConfig(
          filename='/app-logs/application.log',
          level=logging.INFO,
          format='%(asctime)s - %(levelname)s - %(message)s'
      )
      
      logger = logging.getLogger(__name__)
      
      print("Application starting...")
      
      counter = 0
      while True:
          counter += 1
          
          # Generate different types of log entries
          if counter % 10 == 0:
              logger.error(f"Error event #{counter}")
          elif counter % 5 == 0:
              logger.warning(f"Warning event #{counter}")
          else:
              logger.info(f"Info event #{counter}")
          
          print(f"Generated log entry #{counter}")
          time.sleep(random.uniform(2, 5))
    volumeMounts:
    - name: app-logs
      mountPath: /app-logs
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Log aggregator sidecar
  - name: log-aggregator
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Log aggregator starting..."
      
      while true; do
        if [ -f /app-logs/application.log ]; then
          echo "=== Processing application logs ==="
          
          # Count different log levels
          INFO_COUNT=$(grep -c "INFO" /app-logs/application.log 2>/dev/null || echo 0)
          WARN_COUNT=$(grep -c "WARNING" /app-logs/application.log 2>/dev/null || echo 0)
          ERROR_COUNT=$(grep -c "ERROR" /app-logs/application.log 2>/dev/null || echo 0)
          
          # Create summary
          echo "$(date): INFO:$INFO_COUNT, WARN:$WARN_COUNT, ERROR:$ERROR_COUNT" >> /persistent-logs/summary.log
          
          # Archive errors to separate file
          grep "ERROR" /app-logs/application.log > /persistent-logs/errors.log 2>/dev/null || true
          
          echo "Log summary updated: INFO=$INFO_COUNT, WARN=$WARN_COUNT, ERROR=$ERROR_COUNT"
        fi
        
        sleep 10
      done
    volumeMounts:
    - name: app-logs
      mountPath: /app-logs
    - name: persistent-logs
      mountPath: /persistent-logs
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  volumes:
  - name: app-logs
    emptyDir: {}
  - name: persistent-logs
    persistentVolumeClaim:
      claimName: log-storage
```

Test persistent logging:
```bash
# Apply the persistent configuration
kubectl apply -f persistent-sidecar.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/persistent-log-demo --timeout=60s

# Monitor both containers
kubectl logs persistent-log-demo -c app &
kubectl logs persistent-log-demo -c log-aggregator &

# Wait a bit for logs to be generated
sleep 30

# Check persistent log files
kubectl exec -it persistent-log-demo -c log-aggregator -- ls -la /persistent-logs/
kubectl exec -it persistent-log-demo -c log-aggregator -- cat /persistent-logs/summary.log
kubectl exec -it persistent-log-demo -c log-aggregator -- head -5 /persistent-logs/errors.log

# Simulate pod restart (logs should persist)
kubectl delete pod persistent-log-demo

# Recreate with same PVC
kubectl apply -f persistent-sidecar.yaml

# Check that logs persisted across restart
kubectl wait --for=condition=Ready pod/persistent-log-demo --timeout=60s
kubectl exec -it persistent-log-demo -c log-aggregator -- cat /persistent-logs/summary.log

# Cleanup
kubectl delete -f persistent-sidecar.yaml
```

---

## 🎯 Sidecar Pattern Benefits

### Separation of Concerns
- Main application focuses on business logic
- Sidecar handles cross-cutting concerns (logging, monitoring, security)
- Independent scaling and updates

### Reusability
- Same sidecar can be used with different applications
- Standardized logging/monitoring patterns
- Easier maintenance and updates

### Resource Efficiency
- Shared storage and network
- Optimal resource allocation per container
- Better resource utilization

## 🔍 Common Sidecar Use Cases

### 1. Log Processing
```yaml
# Log collector, parser, forwarder
- name: log-collector
  image: fluentd:latest
  volumeMounts:
  - name: logs
    mountPath: /var/log
```

### 2. Service Mesh
```yaml
# Envoy proxy sidecar
- name: envoy-proxy
  image: envoyproxy/envoy:latest
  ports:
  - containerPort: 15001
```

### 3. Monitoring
```yaml
# Metrics exporter
- name: metrics-exporter
  image: prom/node-exporter:latest
  ports:
  - containerPort: 9100
```

### 4. Security
```yaml
# Auth proxy
- name: auth-proxy
  image: oauth2-proxy:latest
  ports:
  - containerPort: 4180
```

## 📝 Best Practices

1. **Resource Management**: Set appropriate resource requests and limits
2. **Volume Sharing**: Use appropriate volume types for sharing data
3. **Health Checks**: Implement health checks for both containers
4. **Lifecycle Management**: Handle container startup dependencies
5. **Error Handling**: Implement proper error handling and retries
6. **Monitoring**: Monitor both application and sidecar metrics

## 🔍 Troubleshooting Commands

```bash
# Check all containers in pod
kubectl get pods <pod-name> -o jsonpath='{.spec.containers[*].name}'

# Check container status
kubectl describe pod <pod-name>

# View logs from specific container
kubectl logs <pod-name> -c <container-name>

# Follow logs from all containers
kubectl logs <pod-name> --all-containers -f

# Execute into specific container
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh

# Check volume mounts
kubectl describe pod <pod-name> | grep -A 10 "Mounts"

# Check resource usage
kubectl top pod <pod-name> --containers
```

## 🎯 Key Takeaways

- Sidecar pattern enables separation of concerns in multi-container pods
- Shared volumes facilitate communication between containers
- Proper resource management is crucial for sidecar containers
- Sidecar containers can be standardized and reused across applications
- Monitor both application and sidecar performance

## 📚 Additional Resources

- [Multi-Container Pod Patterns](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/)
- [Istio Service Mesh](https://istio.io/latest/docs/concepts/what-is-istio/)
- [Fluentd Logging](https://docs.fluentd.org/container-deployment/kubernetes)