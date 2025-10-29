# Lab 4: Simple Job

**Objective**: Learn to create and manage Kubernetes Jobs for batch processing

**Time**: 25 minutes

**Prerequisites**: Kubernetes cluster access, kubectl configured

---

## Exercise 1: Basic Job Creation (10 minutes)

Create simple jobs to understand the basic concepts.

### Step 1: Imperative Job Creation

```bash
# Create a simple job
kubectl create job hello-job --image=busybox -- echo "Hello from Kubernetes Job!"

# Check job status
kubectl get jobs

# Check pods created by the job
kubectl get pods -l job-name=hello-job

# View job logs
kubectl logs job/hello-job

# Check job details
kubectl describe job hello-job

# Cleanup
kubectl delete job hello-job
```

### Step 2: Declarative Job Manifest

Create `simple-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: simple-calculation
  labels:
    app: calculator
spec:
  # Job will complete when 1 pod succeeds
  completions: 1
  # Only 1 pod runs at a time
  parallelism: 1
  # Retry up to 3 times on failure
  backoffLimit: 3
  template:
    metadata:
      labels:
        app: calculator
    spec:
      containers:
      - name: calculator
        image: python:3.11-alpine
        command:
        - python
        - -c
        - |
          import math
          import time
          
          print("Starting calculation...")
          time.sleep(2)
          
          # Calculate factorial of 10
          result = math.factorial(10)
          print(f"Factorial of 10 is: {result}")
          
          # Calculate some more complex operations
          pi_approx = sum(1/16**k * (4/(8*k+1) - 2/(8*k+4) - 1/(8*k+5) - 1/(8*k+6)) for k in range(100))
          print(f"Pi approximation: {pi_approx}")
          
          print("Calculation complete!")
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      restartPolicy: Never
```

Apply and monitor:
```bash
# Apply the job
kubectl apply -f simple-job.yaml

# Watch job progress
kubectl get jobs -w

# Check pod status
kubectl get pods -l app=calculator

# View logs
kubectl logs -l app=calculator

# Check job events
kubectl describe job simple-calculation

# Cleanup
kubectl delete -f simple-job.yaml
```

---

## Exercise 2: Job with Different Completion Patterns (10 minutes)

Explore different job completion and parallelism patterns.

### Step 1: Multiple Completions Job

Create `multiple-completions.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processor
spec:
  # Need 5 successful completions
  completions: 5
  # Run 2 pods in parallel
  parallelism: 2
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          # Simulate data processing
          WORKER_ID=$(cat /proc/sys/kernel/random/uuid | cut -d'-' -f1)
          echo "Worker $WORKER_ID starting..."
          
          # Simulate variable processing time
          SLEEP_TIME=$((RANDOM % 10 + 5))
          echo "Processing for $SLEEP_TIME seconds..."
          sleep $SLEEP_TIME
          
          echo "Worker $WORKER_ID completed successfully!"
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
      restartPolicy: Never
```

Monitor the parallel execution:
```bash
# Apply the job
kubectl apply -f multiple-completions.yaml

# Watch pods being created and completed
kubectl get pods -l job-name=data-processor -w

# Check job progress
kubectl get job data-processor -w

# View logs from all pods
kubectl logs -l job-name=data-processor

# Cleanup
kubectl delete -f multiple-completions.yaml
```

### Step 2: Work Queue Pattern Job

Create `work-queue-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: work-queue-processor
spec:
  # Don't specify completions for work queue pattern
  parallelism: 3
  backoffLimit: 1
  template:
    spec:
      containers:
      - name: worker
        image: python:3.11-alpine
        command:
        - python
        - -c
        - |
          import time
          import random
          import os
          
          worker_id = os.getenv('HOSTNAME', 'unknown')
          print(f"Worker {worker_id} started")
          
          # Simulate work queue processing
          tasks = ['task1', 'task2', 'task3', 'task4', 'task5']
          
          for task in tasks:
              print(f"Worker {worker_id} processing {task}")
              # Simulate variable work time
              work_time = random.uniform(1, 3)
              time.sleep(work_time)
              print(f"Worker {worker_id} completed {task}")
          
          print(f"Worker {worker_id} finished all tasks")
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
      restartPolicy: Never
```

Execute and observe:
```bash
# Apply the job
kubectl apply -f work-queue-job.yaml

# Monitor parallel workers
kubectl get pods -l job-name=work-queue-processor

# View logs from different workers
for pod in $(kubectl get pods -l job-name=work-queue-processor -o name); do
    echo "=== Logs from $pod ==="
    kubectl logs $pod
    echo
done

# Cleanup
kubectl delete -f work-queue-job.yaml
```

---

## Exercise 3: Job Failure and Retry Handling (5 minutes)

Learn how jobs handle failures and retries.

### Step 1: Job with Intentional Failures

Create `failing-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: unreliable-job
spec:
  completions: 1
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: unreliable-worker
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting unreliable task..."
          
          # 70% chance of failure
          if [ $((RANDOM % 10)) -lt 7 ]; then
            echo "Task failed! Something went wrong."
            exit 1
          else
            echo "Task completed successfully!"
            exit 0
          fi
        resources:
          requests:
            memory: "16Mi"
            cpu: "25m"
      restartPolicy: Never
```

Test failure handling:
```bash
# Apply the job
kubectl apply -f failing-job.yaml

# Watch the job retry failed pods
kubectl get jobs unreliable-job -w

# Check failed and successful pods
kubectl get pods -l job-name=unreliable-job

# View logs from failed pods
kubectl logs -l job-name=unreliable-job

# Check job events for failure details
kubectl describe job unreliable-job

# Cleanup
kubectl delete -f failing-job.yaml
```

### Step 2: Job with Timeout

Create `timeout-job.yaml`:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-job
spec:
  # Job must complete within 30 seconds
  activeDeadlineSeconds: 30
  completions: 1
  backoffLimit: 1
  template:
    spec:
      containers:
      - name: slow-worker
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Starting long-running task..."
          # This will take 60 seconds, longer than the deadline
          sleep 60
          echo "Task completed!"
        resources:
          requests:
            memory: "16Mi"
            cpu: "25m"
      restartPolicy: Never
```

Test timeout behavior:
```bash
# Apply the job
kubectl apply -f timeout-job.yaml

# Watch for timeout
kubectl get job timeout-job -w

# Check why it failed
kubectl describe job timeout-job

# Cleanup
kubectl delete -f timeout-job.yaml
```

---

## 🎯 Job Patterns and Best Practices

### Job Completion Patterns

1. **Single Completion**:
   ```yaml
   spec:
     completions: 1
     parallelism: 1
   ```

2. **Multiple Completions**:
   ```yaml
   spec:
     completions: 10
     parallelism: 3
   ```

3. **Work Queue Pattern**:
   ```yaml
   spec:
     # Don't set completions
     parallelism: 5
   ```

### Resource Management

```yaml
spec:
  template:
    spec:
      containers:
      - name: worker
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### Job Cleanup

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: auto-cleanup-job
spec:
  # Automatically clean up after 300 seconds
  ttlSecondsAfterFinished: 300
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["echo", "Job with auto-cleanup"]
      restartPolicy: Never
```

---

## 🔍 Troubleshooting Commands

```bash
# Check job status
kubectl get jobs

# Get detailed job information
kubectl describe job <job-name>

# View job events
kubectl get events --field-selector involvedObject.name=<job-name>

# Check pods created by job
kubectl get pods -l job-name=<job-name>

# View logs from all job pods
kubectl logs -l job-name=<job-name>

# Check failed pods specifically
kubectl get pods -l job-name=<job-name> --field-selector=status.phase=Failed

# Delete completed jobs
kubectl delete jobs --field-selector=status.successful=1

# Delete failed jobs
kubectl delete jobs --field-selector=status.failed=1
```

## 📝 Common Job Issues

1. **Wrong Restart Policy**: Jobs require `restartPolicy: Never` or `OnFailure`
2. **Resource Limits**: Insufficient resources causing OOMKilled
3. **Backoff Limit**: Job gives up after too many failures
4. **Active Deadline**: Job times out before completion
5. **Pod Cleanup**: Completed pods accumulate without TTL

## 🎯 Key Takeaways

- Jobs are for run-to-completion workloads
- Use `completions` for fixed work and parallelism for concurrent execution
- Handle failures with appropriate `backoffLimit`
- Clean up completed jobs with `ttlSecondsAfterFinished`
- Monitor job progress with `kubectl get jobs` and `kubectl describe job`

## 📚 Additional Resources

- [Kubernetes Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Job Patterns](https://kubernetes.io/docs/concepts/workloads/controllers/job/#job-patterns)
- [Parallel Processing](https://kubernetes.io/docs/concepts/workloads/controllers/job/#parallel-jobs)