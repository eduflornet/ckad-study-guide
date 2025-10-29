# Lab 5: Parallel Processing Jobs

**Objective**: Master parallel job execution patterns and work distribution

**Time**: 35 minutes

**Prerequisites**: Kubernetes cluster access, understanding of basic Jobs

---

## Exercise 1: Fixed Completion Parallel Jobs (15 minutes)

Learn to run jobs with fixed number of completions in parallel.

### Step 1: Simple Parallel Job

Create `parallel-fixed.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-calculator
  labels:
    type: parallel-demo
spec:
  # Need 6 total completions
  completions: 6
  # Run 3 pods in parallel
  parallelism: 3
  backoffLimit: 2
  template:
    metadata:
      labels:
        type: parallel-demo
    spec:
      containers:
      - name: calculator
        image: python:3.11-alpine
        command:
        - python
        - -c
        - |
          import time
          import random
          import os
          import math
          
          pod_name = os.getenv('HOSTNAME', 'unknown')
          completion_index = os.getenv('JOB_COMPLETION_INDEX', '0')
          
          print(f"Pod {pod_name} (completion {completion_index}) starting...")
          
          # Simulate different work based on completion index
          numbers = [10, 15, 20, 25, 30, 35]
          number = numbers[int(completion_index) % len(numbers)]
          
          print(f"Calculating factorial of {number}...")
          
          # Simulate work time
          work_time = random.uniform(3, 8)
          time.sleep(work_time)
          
          result = math.factorial(number)
          print(f"Pod {pod_name}: factorial({number}) = {result}")
          print(f"Pod {pod_name} completed in {work_time:.2f} seconds")
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
      restartPolicy: Never
```

Execute and monitor:
```bash
# Apply the job
kubectl apply -f parallel-fixed.yaml

# Monitor job progress
kubectl get job parallel-calculator -w

# In another terminal, watch pods
kubectl get pods -l type=parallel-demo -w

# Check completion status
kubectl describe job parallel-calculator

# View logs from all pods
kubectl logs -l type=parallel-demo

# Cleanup
kubectl delete -f parallel-fixed.yaml
```

### Step 2: Dynamic Parallelism Scaling

Create `dynamic-parallel.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dynamic-processor
spec:
  completions: 10
  parallelism: 2  # Start with 2 parallel pods
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          WORKER_ID=$(cat /proc/sys/kernel/random/uuid | cut -d'-' -f1)
          COMPLETION_INDEX=${JOB_COMPLETION_INDEX:-$RANDOM}
          
          echo "Worker $WORKER_ID (index: $COMPLETION_INDEX) starting..."
          
          # Simulate variable work based on index
          if [ $((COMPLETION_INDEX % 3)) -eq 0 ]; then
            WORK_TIME=10  # Some tasks take longer
          else
            WORK_TIME=5   # Others are quicker
          fi
          
          echo "Worker $WORKER_ID processing for $WORK_TIME seconds..."
          sleep $WORK_TIME
          
          echo "Worker $WORKER_ID (index: $COMPLETION_INDEX) completed!"
        resources:
          requests:
            memory: "16Mi"
            cpu: "25m"
      restartPolicy: Never
```

Test scaling:
```bash
# Apply the job
kubectl apply -f dynamic-parallel.yaml

# Initially 2 pods running
kubectl get pods -l job-name=dynamic-processor

# Scale up parallelism
kubectl patch job dynamic-processor -p '{"spec":{"parallelism":4}}'

# Watch more pods get created
kubectl get pods -l job-name=dynamic-processor -w

# Scale down parallelism
kubectl patch job dynamic-processor -p '{"spec":{"parallelism":1}}'

# Monitor completion
kubectl get job dynamic-processor -w

# Cleanup
kubectl delete -f dynamic-parallel.yaml
```

---

## Exercise 2: Work Queue Pattern (15 minutes)

Implement jobs that process from a shared work queue.

### Step 1: Create Shared Work Queue

Create `work-queue-config.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: work-queue
data:
  tasks.txt: |
    process-file-1.txt
    process-file-2.txt
    process-file-3.txt
    analyze-data-set-A
    analyze-data-set-B
    analyze-data-set-C
    generate-report-Q1
    generate-report-Q2
    generate-report-Q3
    backup-database-users
    backup-database-orders
    backup-database-products
    send-email-campaign-1
    send-email-campaign-2
    cleanup-temp-files
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: work-processor
data:
  processor.py: |
    import time
    import random
    import os
    import fcntl
    
    def get_next_task():
        """Get next task from the queue file"""
        try:
            with open('/shared/queue/tasks.txt', 'r+') as f:
                # Lock the file to prevent race conditions
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                
                lines = f.readlines()
                if not lines:
                    return None
                
                # Take the first task
                task = lines[0].strip()
                
                # Write remaining tasks back
                f.seek(0)
                f.writelines(lines[1:])
                f.truncate()
                
                return task
        except Exception as e:
            print(f"Error reading queue: {e}")
            return None
    
    def process_task(task):
        """Simulate task processing"""
        print(f"Processing task: {task}")
        
        # Simulate different processing times
        if 'database' in task:
            time.sleep(random.uniform(8, 12))  # Database tasks take longer
        elif 'report' in task:
            time.sleep(random.uniform(5, 8))   # Reports take medium time
        else:
            time.sleep(random.uniform(2, 5))   # Other tasks are quick
        
        print(f"Completed task: {task}")
    
    def main():
        worker_id = os.getenv('HOSTNAME', 'unknown')
        print(f"Worker {worker_id} started")
        
        tasks_processed = 0
        
        while True:
            task = get_next_task()
            if task is None:
                print(f"Worker {worker_id} found no more tasks")
                break
            
            process_task(task)
            tasks_processed += 1
        
        print(f"Worker {worker_id} processed {tasks_processed} tasks and is exiting")
    
    if __name__ == "__main__":
        main()
```

### Step 2: Work Queue Job

Create `work-queue-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: work-queue-job
spec:
  # No completions specified - work queue pattern
  parallelism: 4
  backoffLimit: 2
  template:
    spec:
      volumes:
      - name: work-queue
        configMap:
          name: work-queue
      - name: work-processor
        configMap:
          name: work-processor
          defaultMode: 0755
      - name: shared-queue
        emptyDir: {}
      
      initContainers:
      - name: setup-queue
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Setting up work queue..."
          cp /config/tasks.txt /shared/queue/
          echo "Queue initialized with $(wc -l < /shared/queue/tasks.txt) tasks"
        volumeMounts:
        - name: work-queue
          mountPath: /config
        - name: shared-queue
          mountPath: /shared/queue
      
      containers:
      - name: worker
        image: python:3.11-alpine
        command:
        - python
        - /scripts/processor.py
        volumeMounts:
        - name: work-processor
          mountPath: /scripts
        - name: shared-queue
          mountPath: /shared/queue
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
      restartPolicy: Never
```

Execute work queue job:
```bash
# Apply configurations
kubectl apply -f work-queue-config.yaml

# Apply the job
kubectl apply -f work-queue-job.yaml

# Monitor workers
kubectl get pods -l job-name=work-queue-job -w

# Check logs from different workers
for pod in $(kubectl get pods -l job-name=work-queue-job -o name); do
    echo "=== Worker: $pod ==="
    kubectl logs $pod
    echo
done

# Check job completion
kubectl get job work-queue-job

# Cleanup
kubectl delete -f work-queue-job.yaml
kubectl delete -f work-queue-config.yaml
```

---

## Exercise 3: Advanced Parallel Patterns (5 minutes)

Explore indexed jobs and advanced parallelism.

### Step 1: Indexed Job (Kubernetes 1.21+)

Create `indexed-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: indexed-processor
spec:
  completions: 5
  parallelism: 3
  completionMode: Indexed  # Available in Kubernetes 1.21+
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Processing with completion index: ${JOB_COMPLETION_INDEX}"
          
          # Different work based on index
          case ${JOB_COMPLETION_INDEX} in
            0) echo "Processing dataset A"; sleep 5 ;;
            1) echo "Processing dataset B"; sleep 3 ;;
            2) echo "Processing dataset C"; sleep 7 ;;
            3) echo "Processing dataset D"; sleep 4 ;;
            4) echo "Processing dataset E"; sleep 6 ;;
            *) echo "Unknown index"; sleep 2 ;;
          esac
          
          echo "Index ${JOB_COMPLETION_INDEX} completed"
        resources:
          requests:
            memory: "16Mi"
            cpu: "25m"
      restartPolicy: Never
```

Test indexed job:
```bash
# Check Kubernetes version first
kubectl version --short

# Apply if supported (Kubernetes 1.21+)
kubectl apply -f indexed-job.yaml

# Monitor indexed completion
kubectl get job indexed-processor -o wide

# View logs with completion index
kubectl logs -l job-name=indexed-processor

# Cleanup
kubectl delete -f indexed-job.yaml
```

### Step 2: Job with Pod Failure Policy (Kubernetes 1.25+)

Create `failure-policy-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: failure-policy-job
spec:
  completions: 3
  parallelism: 2
  backoffLimit: 6
  podFailurePolicy:  # Available in Kubernetes 1.25+
    rules:
    - action: FailJob
      onExitCodes:
        containerName: worker
        operator: In
        values: [42]  # Fail entire job on exit code 42
    - action: Ignore
      onExitCodes:
        containerName: worker
        operator: In
        values: [1]   # Ignore exit code 1 (don't count as failure)
  template:
    spec:
      containers:
      - name: worker
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          RANDOM_EXIT=$((RANDOM % 4))
          echo "Worker will exit with code: $RANDOM_EXIT"
          
          case $RANDOM_EXIT in
            0) echo "Success!"; exit 0 ;;
            1) echo "Temporary failure (ignored)"; exit 1 ;;
            2) echo "Retry-able failure"; exit 2 ;;
            3) echo "Critical failure!"; exit 42 ;;
          esac
        resources:
          requests:
            memory: "16Mi"
            cpu: "25m"
      restartPolicy: Never
```

Test failure policy:
```bash
# Apply if supported (Kubernetes 1.25+)
kubectl apply -f failure-policy-job.yaml

# Monitor job behavior with different exit codes
kubectl get job failure-policy-job -w

# Check events for policy actions
kubectl describe job failure-policy-job

# Cleanup
kubectl delete -f failure-policy-job.yaml
```

---

## 🎯 Parallel Job Patterns Summary

### Fixed Completion Count
```yaml
spec:
  completions: 10    # Need exactly 10 successful pods
  parallelism: 3     # Run 3 at a time
```

### Work Queue
```yaml
spec:
  # No completions specified
  parallelism: 5     # 5 workers processing queue
```

### Indexed Jobs
```yaml
spec:
  completions: 8
  parallelism: 4
  completionMode: Indexed  # Each pod gets JOB_COMPLETION_INDEX
```

### Dynamic Scaling
```bash
# Scale up during execution
kubectl patch job my-job -p '{"spec":{"parallelism":10}}'

# Scale down
kubectl patch job my-job -p '{"spec":{"parallelism":2}}'
```

## 🔍 Monitoring Commands

```bash
# Watch job progress
kubectl get jobs -w

# Monitor pods by job
kubectl get pods -l job-name=<job-name> -w

# Check job details
kubectl describe job <job-name>

# View aggregated logs
kubectl logs -l job-name=<job-name>

# Check resource usage
kubectl top pods -l job-name=<job-name>

# Get job metrics
kubectl get job <job-name> -o jsonpath='{.status}'
```

## 📝 Performance Considerations

1. **Right-size parallelism** based on cluster capacity
2. **Consider resource limits** to avoid overwhelming nodes  
3. **Use work queues** for dynamic workload distribution
4. **Monitor completion times** to optimize parallelism
5. **Handle failures gracefully** with appropriate backoff limits

## 🎯 Key Takeaways

- Parallel jobs enable efficient workload processing
- Work queue pattern provides dynamic load balancing
- Indexed jobs give predictable task assignment
- Dynamic scaling allows runtime optimization
- Proper resource management prevents cluster overload

## 📚 Additional Resources

- [Parallel Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/#parallel-jobs)
- [Job Patterns](https://kubernetes.io/docs/concepts/workloads/controllers/job/#job-patterns)
- [Indexed Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/#completion-mode)