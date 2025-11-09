# Lab 9: Shared Volume Communication

**Objective**: Master inter-container communication using shared volumes in multi-container pods

**Time**: 35 minutes

**Prerequisites**: Kubernetes cluster access, understanding of volumes and multi-container pods

---

## [Exercise 1: Basic Volume Sharing (10 minutes)](/01-application-design-build/labs/lab09-solution/exercise-01/)

Learn fundamental concepts of volume sharing between containers.

### Step 1: Simple Data Sharing

Create `basic-volume-sharing.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-sharing-demo
  labels:
    app: volume-demo
spec:
  containers:
  # Producer container
  - name: data-producer
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Data producer starting..."
      counter=0
      
      while true; do
        counter=$((counter + 1))
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Write data to shared volume
        echo "$timestamp - Data entry #$counter" >> /shared-data/producer.log
        echo "Producer: Generated entry #$counter"
        
        # Create structured data file
        cat > /shared-data/current-data.json << EOF
      {
        "timestamp": "$timestamp",
        "counter": $counter,
        "status": "active",
        "producer_id": "$HOSTNAME"
      }
      EOF
        
        sleep 5
      done
    volumeMounts:
    - name: shared-storage
      mountPath: /shared-data
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  # Consumer container
  - name: data-consumer
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Data consumer starting..."
      
      # Wait for producer to create initial data
      while [ ! -f /shared-data/producer.log ]; do
        echo "Waiting for producer data..."
        sleep 2
      done
      
      echo "Producer data found, starting consumption..."
      
      while true; do
        # Count total entries
        if [ -f /shared-data/producer.log ]; then
          TOTAL_ENTRIES=$(wc -l < /shared-data/producer.log)
          echo "Consumer: Total entries processed: $TOTAL_ENTRIES"
        fi
        
        # Read current data
        if [ -f /shared-data/current-data.json ]; then
          echo "Current data:"
          cat /shared-data/current-data.json
        fi
        
        # Create processed data
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Processed batch with $TOTAL_ENTRIES entries" >> /shared-data/consumer.log
        
        sleep 10
      done
    volumeMounts:
    - name: shared-storage
      mountPath: /shared-data
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  # Monitor container
  - name: data-monitor
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Data monitor starting..."
      sleep 10  # Let other containers start
      
      while true; do
        echo "=== Data Monitor Report ==="
        echo "Timestamp: $(date)"
        
        if [ -f /shared-data/producer.log ]; then
          PRODUCER_ENTRIES=$(wc -l < /shared-data/producer.log)
          echo "Producer entries: $PRODUCER_ENTRIES"
        fi
        
        if [ -f /shared-data/consumer.log ]; then
          CONSUMER_ENTRIES=$(wc -l < /shared-data/consumer.log)
          echo "Consumer entries: $CONSUMER_ENTRIES"
        fi
        
        echo "Disk usage:"
        du -h /shared-data/*
        
        echo "========================="
        sleep 15
      done
    volumeMounts:
    - name: shared-storage
      mountPath: /shared-data
    resources:
      requests:
        memory: "16Mi"
        cpu: "25m"
  
  volumes:
  - name: shared-storage
    emptyDir: {}
```

Deploy and monitor:
```bash
# Apply the configuration
kubectl apply -f basic-volume-sharing.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/volume-sharing-demo --timeout=60s

# Check logs from different containers
kubectl logs volume-sharing-demo -c data-producer --tail=5
kubectl logs volume-sharing-demo -c data-consumer --tail=5
kubectl logs volume-sharing-demo -c data-monitor --tail=10

# Verify file sharing by checking shared directory
kubectl exec volume-sharing-demo -c data-producer -- ls -la /shared-data/
kubectl exec volume-sharing-demo -c data-consumer -- cat /shared-data/current-data.json

# Cleanup
kubectl delete -f basic-volume-sharing.yaml
```

---

##  [Exercise 2: Advanced Communication Patterns (20 minutes)](/01-application-design-build/labs/lab09-solution/exercise-02/)

Implement sophisticated inter-container communication patterns.

### Step 1: Producer-Consumer with Queue

Create `queue-communication.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: queue-scripts
data:
  queue-manager.py: |
    import os
    import json
    import time
    import fcntl
    from datetime import datetime
    
    class FileQueue:
        def __init__(self, queue_file):
            self.queue_file = queue_file
            self.ensure_queue_exists()
        
        def ensure_queue_exists(self):
            if not os.path.exists(self.queue_file):
                with open(self.queue_file, 'w') as f:
                    json.dump([], f)
        
        def put(self, item):
            """Add item to queue"""
            with open(self.queue_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                queue = json.load(f)
                queue.append(item)
                f.seek(0)
                json.dump(queue, f)
                f.truncate()
        
        def get(self):
            """Get item from queue (FIFO)"""
            with open(self.queue_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                queue = json.load(f)
                if queue:
                    item = queue.pop(0)
                    f.seek(0)
                    json.dump(queue, f)
                    f.truncate()
                    return item
                return None
        
        def size(self):
            """Get queue size"""
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
                return len(queue)
  
  producer.py: |
    import sys
    import os
    sys.path.append('/scripts')
    
    # Import the queue manager
    exec(open('/scripts/queue-manager.py').read())
    
    import time
    import random
    from datetime import datetime
    
    def main():
        queue = FileQueue('/shared-queue/tasks.json')
        
        print("Producer starting...")
        task_id = 0
        
        while True:
            task_id += 1
            
            # Create different types of tasks
            task_types = ['process_image', 'send_email', 'generate_report', 'backup_data']
            task_type = random.choice(task_types)
            
            task = {
                'id': task_id,
                'type': task_type,
                'timestamp': datetime.now().isoformat(),
                'data': f'task_data_{task_id}',
                'priority': random.randint(1, 5)
            }
            
            queue.put(task)
            print(f"Produced task {task_id}: {task_type}")
            
            # Variable production rate
            sleep_time = random.uniform(2, 6)
            time.sleep(sleep_time)
    
    if __name__ == "__main__":
        main()
  
  consumer.py: |
    import sys
    import os
    sys.path.append('/scripts')
    
    # Import the queue manager
    exec(open('/scripts/queue-manager.py').read())
    
    import time
    import random
    from datetime import datetime
    
    def process_task(task):
        """Simulate task processing"""
        task_type = task['type']
        task_id = task['id']
        
        print(f"Processing task {task_id}: {task_type}")
        
        # Different processing times for different task types
        processing_times = {
            'process_image': (3, 8),
            'send_email': (1, 3),
            'generate_report': (5, 12),
            'backup_data': (8, 15)
        }
        
        min_time, max_time = processing_times.get(task_type, (2, 5))
        processing_time = random.uniform(min_time, max_time)
        
        time.sleep(processing_time)
        
        # Create result file
        result = {
            'task_id': task_id,
            'type': task_type,
            'status': 'completed',
            'processing_time': processing_time,
            'processed_by': os.getenv('HOSTNAME', 'unknown'),
            'completed_at': datetime.now().isoformat()
        }
        
        # Write result to shared storage
        result_file = f'/shared-results/result_{task_id}.json'
        with open(result_file, 'w') as f:
            import json
            json.dump(result, f, indent=2)
        
        print(f"Completed task {task_id} in {processing_time:.2f}s")
        return result
    
    def main():
        queue = FileQueue('/shared-queue/tasks.json')
        worker_id = os.getenv('HOSTNAME', 'unknown')
        
        print(f"Consumer {worker_id} starting...")
        
        while True:
            task = queue.get()
            
            if task:
                process_task(task)
            else:
                print("No tasks available, waiting...")
                time.sleep(3)
    
    if __name__ == "__main__":
        main()
  
  monitor.py: |
    import sys
    import os
    sys.path.append('/scripts')
    
    import time
    import json
    from datetime import datetime
    
    # Import the queue manager
    exec(open('/scripts/queue-manager.py').read())
    
    def main():
        queue = FileQueue('/shared-queue/tasks.json')
        
        print("Monitor starting...")
        time.sleep(5)  # Let other containers start
        
        while True:
            queue_size = queue.size()
            
            # Count completed tasks
            result_files = []
            if os.path.exists('/shared-results'):
                result_files = [f for f in os.listdir('/shared-results') if f.endswith('.json')]
            
            completed_tasks = len(result_files)
            
            # Calculate processing statistics
            total_processing_time = 0
            task_types = {}
            
            for result_file in result_files:
                try:
                    with open(f'/shared-results/{result_file}', 'r') as f:
                        result = json.load(f)
                        total_processing_time += result.get('processing_time', 0)
                        task_type = result.get('type', 'unknown')
                        task_types[task_type] = task_types.get(task_type, 0) + 1
                except:
                    pass
            
            avg_processing_time = total_processing_time / completed_tasks if completed_tasks > 0 else 0
            
            print(f"=== Queue Monitor Report ===")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Queue size: {queue_size}")
            print(f"Completed tasks: {completed_tasks}")
            print(f"Average processing time: {avg_processing_time:.2f}s")
            print(f"Task types processed: {task_types}")
            print(f"============================")
            
            time.sleep(10)
    
    if __name__ == "__main__":
        main()
---
apiVersion: v1
kind: Pod
metadata:
  name: queue-communication
spec:
  containers:
  # Task producer
  - name: producer
    image: python:3.11-alpine
    command: ["python", "/scripts/producer.py"]
    volumeMounts:
    - name: queue-scripts
      mountPath: /scripts
    - name: shared-queue
      mountPath: /shared-queue
    - name: shared-results
      mountPath: /shared-results
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Task consumer 1
  - name: consumer-1
    image: python:3.11-alpine
    command: ["python", "/scripts/consumer.py"]
    volumeMounts:
    - name: queue-scripts
      mountPath: /scripts
    - name: shared-queue
      mountPath: /shared-queue
    - name: shared-results
      mountPath: /shared-results
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Task consumer 2
  - name: consumer-2
    image: python:3.11-alpine
    command: ["python", "/scripts/consumer.py"]
    volumeMounts:
    - name: queue-scripts
      mountPath: /scripts
    - name: shared-queue
      mountPath: /shared-queue
    - name: shared-results
      mountPath: /shared-results
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Queue monitor
  - name: monitor
    image: python:3.11-alpine
    command: ["python", "/scripts/monitor.py"]
    volumeMounts:
    - name: queue-scripts
      mountPath: /scripts
    - name: shared-queue
      mountPath: /shared-queue
    - name: shared-results
      mountPath: /shared-results
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  volumes:
  - name: queue-scripts
    configMap:
      name: queue-scripts
      defaultMode: 0755
  - name: shared-queue
    emptyDir: {}
  - name: shared-results
    emptyDir: {}
```

Test queue communication:
```bash
# Apply the queue configuration
kubectl apply -f queue-communication.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/queue-communication --timeout=60s

# Monitor different containers
kubectl logs queue-communication -c producer --tail=5
kubectl logs queue-communication -c consumer-1 --tail=5
kubectl logs queue-communication -c consumer-2 --tail=5
kubectl logs queue-communication -c monitor --tail=10

# Check shared queue and results
kubectl exec queue-communication -c monitor -- ls -la /shared-queue/
kubectl exec queue-communication -c monitor -- ls -la /shared-results/

# Check queue contents
kubectl exec queue-communication -c monitor -- cat /shared-queue/tasks.json

# Check a result file
kubectl exec queue-communication -c monitor -- find /shared-results -name "*.json" | head -1 | xargs cat

# Cleanup
kubectl delete -f queue-communication.yaml
```

### Step 2: Configuration Hot-Reload Pattern

Create `config-hotreload.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  config.yaml: |
    app:
      name: "hot-reload-demo"
      version: "1.0.0"
      log_level: "INFO"
      max_connections: 100
      timeout: 30
      features:
        feature_a: true
        feature_b: false
        feature_c: true
---
apiVersion: v1
kind: Pod
metadata:
  name: config-hotreload
spec:
  containers:
  # Main application
  - name: app
    image: python:3.11-alpine
    command:
    - sh
    - -c
    - |
      pip install PyYAML > /dev/null 2>&1
      python3 << 'EOF'
      import yaml
      import time
      import os
      from datetime import datetime
      
      config_file = '/shared-config/config.yaml'
      last_modified = 0
      config = {}
      
      def load_config():
          global config, last_modified
          try:
              stat = os.stat(config_file)
              if stat.st_mtime > last_modified:
                  with open(config_file, 'r') as f:
                      config = yaml.safe_load(f)
                  last_modified = stat.st_mtime
                  print("Configuration reloaded at", datetime.now())
                  print("Current config:", config)
                  return True
          except Exception as e:
              print("Error loading config:", e)
          return False
      
      print("Application starting...")
      
      # Initial config load
      load_config()
      
      counter = 0
      while True:
          counter += 1
          
          # Check for config changes
          load_config()
          
          # Simulate application work using current config
          app_config = config.get('app', {})
          log_level = app_config.get('log_level', 'INFO')
          max_connections = app_config.get('max_connections', 50)
          
          print("Iteration " + str(counter) + ": Running with log_level=" + log_level + ", max_connections=" + str(max_connections))
          
          time.sleep(5)
      EOF
    volumeMounts:
    - name: shared-config
      mountPath: /shared-config
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  # Config manager
  - name: config-manager
    image: python:3.11-alpine
    command:
    - sh
    - -c
    - |
      pip install PyYAML > /dev/null 2>&1
      python3 << 'EOF'
      import yaml
      import time
      import shutil
      import random
      from datetime import datetime
      
      print("Config manager starting...")
      
      # Copy initial config to shared volume
      shutil.copy('/initial-config/config.yaml', '/shared-config/config.yaml')
      print("Initial configuration copied")
      
      counter = 0
      while True:
          time.sleep(20)  # Update config every 20 seconds
          counter += 1
          
          # Load current config
          with open('/shared-config/config.yaml', 'r') as f:
              config = yaml.safe_load(f)
          
          # Make some changes
          app_config = config['app']
          
          # Randomly change some settings
          if counter % 3 == 0:
              app_config['log_level'] = random.choice(['DEBUG', 'INFO', 'WARN', 'ERROR'])
          
          if counter % 4 == 0:
              app_config['max_connections'] = random.randint(50, 200)
          
          if counter % 5 == 0:
              features = app_config['features']
              for feature in features:
                  features[feature] = random.choice([True, False])
          
          # Update timestamp
          app_config['last_update'] = datetime.now().isoformat()
          
          # Write updated config
          with open('/shared-config/config.yaml', 'w') as f:
              yaml.dump(config, f, default_flow_style=False)
          
          print("Configuration updated #" + str(counter) + " at " + str(datetime.now()))
          print("New config:", config)
      EOF
    volumeMounts:
    - name: initial-config
      mountPath: /initial-config
    - name: shared-config
      mountPath: /shared-config
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
  
  # Config validator
  - name: config-validator
    image: python:3.11-alpine
    command:
    - sh
    - -c
    - |
      pip install PyYAML > /dev/null 2>&1
      python3 << 'EOF'
      import yaml
      import time
      import os
      from datetime import datetime
      
      config_file = '/shared-config/config.yaml'
      last_validated = 0
      
      def validate_config():
          global last_validated
          try:
              stat = os.stat(config_file)
              if stat.st_mtime > last_validated:
                  with open(config_file, 'r') as f:
                      config = yaml.safe_load(f)
                  
                  # Validation rules
                  app_config = config.get('app', {})
                  
                  errors = []
                  
                  if app_config.get('max_connections', 0) < 10:
                      errors.append("max_connections must be >= 10")
                  
                  if app_config.get('max_connections', 0) > 500:
                      errors.append("max_connections must be <= 500")
                  
                  if app_config.get('log_level') not in ['DEBUG', 'INFO', 'WARN', 'ERROR']:
                      errors.append("log_level must be DEBUG, INFO, WARN, or ERROR")
                  
                  if errors:
                      print("CONFIG VALIDATION FAILED at " + str(datetime.now()) + ":")
                      for error in errors:
                          print("  - " + error)
                  else:
                      print("CONFIG VALIDATION PASSED at " + str(datetime.now()))
                  
                  last_validated = stat.st_mtime
                  
          except Exception as e:
              print("Validation error:", e)
      
      print("Config validator starting...")
      time.sleep(5)  # Let initial config be copied
      
      while True:
          validate_config()
          time.sleep(3)
      EOF
    volumeMounts:
    - name: shared-config
      mountPath: /shared-config
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  volumes:
  - name: initial-config
    configMap:
      name: app-config
  - name: shared-config
    emptyDir: {}
```

Test configuration hot-reload:
```bash
# Apply the config hot-reload setup
kubectl apply -f config-hotreload.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/config-hotreload --timeout=60s

# Monitor configuration changes
kubectl logs config-hotreload -c app --tail=10 -f &
kubectl logs config-hotreload -c config-manager --tail=5 -f &
kubectl logs config-hotreload -c config-validator --tail=5 -f &

# Let it run for a bit, then stop following logs
sleep 60
pkill -f "kubectl logs"

# Check current configuration
kubectl exec config-hotreload -c app -- cat /shared-config/config.yaml

# Cleanup
kubectl delete -f config-hotreload.yaml
```

---

## [Exercise 3: Volume Types and Performance (5 minutes)](/01-application-design-build/labs/lab09-solution/exercise-03/)

Compare different volume types for inter-container communication.

### Step 1: Volume Performance Comparison

Create `volume-performance.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-performance
spec:
  containers:
  # EmptyDir volume test
  - name: emptydir-writer
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Testing emptyDir volume performance..."
      
      start_time=$(date +%s)
      for i in $(seq 1 1000); do
        echo "Line $i: This is test data for performance measurement" >> /emptydir-vol/test-$i.txt
      done
      end_time=$(date +%s)
      
      duration=$((end_time - start_time))
      echo "EmptyDir write test: $duration seconds for 1000 files"
      
      # Keep container running
      while true; do sleep 60; done
    volumeMounts:
    - name: emptydir-storage
      mountPath: /emptydir-vol
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  # Memory volume test
  - name: memory-writer
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Testing memory volume performance..."
      
      start_time=$(date +%s)
      for i in $(seq 1 1000); do
        echo "Line $i: This is test data for performance measurement" >> /memory-vol/test-$i.txt
      done
      end_time=$(date +%s)
      
      duration=$((end_time - start_time))
      echo "Memory volume write test: $duration seconds for 1000 files"
      
      # Show memory usage
      df -h /memory-vol
      
      # Keep container running
      while true; do sleep 60; done
    volumeMounts:
    - name: memory-storage
      mountPath: /memory-vol
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
  
  # Reader container for both volumes
  - name: reader
    image: busybox:1.35
    command:
    - sh
    - -c
    - |
      echo "Volume reader starting..."
      sleep 10  # Wait for writers to create files
      
      while true; do
        echo "=== Volume Statistics ==="
        echo "EmptyDir volume:"
        ls /emptydir-vol/ | wc -l
        du -sh /emptydir-vol/
        
        echo "Memory volume:"
        ls /memory-vol/ | wc -l
        du -sh /memory-vol/
        
        echo "========================="
        sleep 15
      done
    volumeMounts:
    - name: emptydir-storage
      mountPath: /emptydir-vol
    - name: memory-storage
      mountPath: /memory-vol
    resources:
      requests:
        memory: "32Mi"
        cpu: "50m"
  
  volumes:
  # Regular emptyDir (uses node's default storage)
  - name: emptydir-storage
    emptyDir: {}
  
  # Memory-backed emptyDir
  - name: memory-storage
    emptyDir:
      medium: Memory
      sizeLimit: 100Mi
```

Test volume performance:
```bash
# Apply the performance test
kubectl apply -f volume-performance.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/volume-performance --timeout=60s

# Check performance results
kubectl logs volume-performance -c emptydir-writer
kubectl logs volume-performance -c memory-writer
kubectl logs volume-performance -c reader --tail=10

# Check actual volume usage
kubectl exec volume-performance -c reader -- df -h

# Cleanup
kubectl delete -f volume-performance.yaml
```

---

## 🎯 Volume Communication Patterns

### 1. Shared Log Files
```yaml
volumeMounts:
- name: logs
  mountPath: /var/log/app
```

### 2. Configuration Sharing
```yaml
volumeMounts:
- name: config
  mountPath: /etc/config
```

### 3. Data Processing Pipeline
```yaml
volumeMounts:
- name: pipeline-data
  mountPath: /data/input   # Producer writes here
- name: pipeline-data
  mountPath: /data/output  # Consumer reads from here
```

### 4. State Synchronization
```yaml
volumeMounts:
- name: shared-state
  mountPath: /app/state
```

## 🔍 Volume Types for Communication

### EmptyDir
- **Use case**: Temporary data sharing
- **Lifetime**: Pod lifetime
- **Performance**: Good for regular files

### EmptyDir (Memory)
- **Use case**: High-performance temporary data
- **Lifetime**: Pod lifetime
- **Performance**: Fastest, but limited by memory

### ConfigMap
- **Use case**: Configuration sharing
- **Lifetime**: Until ConfigMap is deleted
- **Performance**: Read-only, cached

### Secret
- **Use case**: Sensitive data sharing
- **Lifetime**: Until Secret is deleted
- **Performance**: Read-only, cached

### PersistentVolume
- **Use case**: Persistent data sharing
- **Lifetime**: Independent of pod
- **Performance**: Varies by storage type

## 📝 Best Practices

1. **Choose appropriate volume type** based on data lifetime and performance needs
2. **Use file locking** when multiple containers write to the same files
3. **Implement proper error handling** for file operations
4. **Monitor disk usage** to prevent storage exhaustion
5. **Use structured data formats** (JSON, YAML) for complex data sharing
6. **Implement graceful degradation** when shared data is unavailable

## 🔍 Troubleshooting Commands

```bash
# Check volume mounts
kubectl describe pod <pod-name>

# List files in shared volume
kubectl exec <pod-name> -c <container-name> -- ls -la /shared-path

# Check disk usage
kubectl exec <pod-name> -c <container-name> -- df -h

# Monitor file changes
kubectl exec <pod-name> -c <container-name> -- watch ls -la /shared-path

# Check file permissions
kubectl exec <pod-name> -c <container-name> -- ls -la /shared-path/filename

# Test file locking
kubectl exec <pod-name> -c <container-name> -- fuser /shared-path/filename
```

## 🎯 Key Takeaways

- Shared volumes enable effective inter-container communication
- Different volume types offer different performance and persistence characteristics
- File locking is crucial for concurrent access
- Proper error handling and monitoring are essential
- Choose volume types based on data requirements and lifetime

## 📚 Additional Resources

- [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Volume Types](https://kubernetes.io/docs/concepts/storage/volumes/#volume-types)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)