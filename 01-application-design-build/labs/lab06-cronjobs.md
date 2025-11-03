# Lab 6: CronJobs

**What is a Cron format?**

It's a text string that defines when a Cron Job should run. It has 5 required fields, each representing a unit of time:

MINUTE HOUR DAY_OF_MONTH MONTH DAY_OF_WEEK

Example: 0 5 * * 1

→ Perform the work every Monday at 5:00 AM.

**Meaning of each field**

Field Valid         values ​​Meaning

MINUTE 0–59         Minute of the hour
HOUR 0–23           Hour of the day
DAY_OF_MONTH 1–31   Day of the month
MONTH 1–12          Month of the year
DAY_OF_WEEK 0–7     (0 and 7 = Sunday) Day of the week

🧠 Special characters
* → any value
, → list of values ​​(e.g., 1, 15)
- → range (e.g., 1–5)
/ → increments (e.g., */10 = every 10 units)

📦 Useful Examples for CKAD

0 * * * *       Every hour on the hour
*/5 * * * *     Every 5 minutes
0 0 * * *       Every day at midnight
0 9-17 * * 1-5  Every hour between 9 and 17, Monday to Friday
30 2 1 * *      At 2:30 AM on the 1st of each month

**Objective**: Master scheduled jobs using Kubernetes CronJobs

**Time**: 30 minutes

**Prerequisites**: Kubernetes cluster access, understanding of cron syntax

---

## Exercise 1: Basic CronJob Creation (10 minutes)

Learn to create and manage scheduled jobs.

### Step 1: Simple CronJob

Create `basic-cronjob.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cron
  labels:
    app: scheduled-demo
spec:
  # Run every minute
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox:1.35
            command:
            - sh
            - -c
            - |
              echo "Hello from CronJob at $(date)"
              echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
              echo "Pod name: $HOSTNAME"
            resources:
              requests:
                memory: "16Mi"
                cpu: "25m"
          restartPolicy: OnFailure
```

Deploy and monitor:
```bash
# Apply the CronJob
kubectl apply -f basic-cronjob.yaml

# Check CronJob status
kubectl get cronjobs

# Wait and check for created jobs
kubectl get jobs

# Check pods created by the jobs
kubectl get pods -l job-name

# View logs from recent executions
kubectl logs -l job-name --tail=20

# Cleanup
kubectl delete -f basic-cronjob.yaml
```

### Step 2: CronJob with Different Schedules

Create `schedule-examples.yaml`:
```yaml
# Daily backup at 2 AM
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox:1.35
            command: ["sh", "-c", "echo 'Running daily backup at $(date)'"]
          restartPolicy: OnFailure
---
# Weekly report on Sundays at 9 AM
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-report
spec:
  schedule: "0 9 * * 0"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: reporter
            image: busybox:1.35
            command: ["sh", "-c", "echo 'Generating weekly report at $(date)'"]
          restartPolicy: OnFailure
---
# Every 15 minutes during business hours (9 AM - 5 PM, Mon-Fri)
apiVersion: batch/v1
kind: CronJob
metadata:
  name: health-check
spec:
  schedule: "*/15 9-17 * * 1-5"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: health-checker
            image: busybox:1.35
            command: ["sh", "-c", "echo 'Health check at $(date)'"]
          restartPolicy: OnFailure
```

Test schedule validation:
```bash
# Apply all schedules
kubectl apply -f schedule-examples.yaml

# Check all CronJobs
kubectl get cronjobs

# Describe to see next scheduled time
kubectl describe cronjob daily-backup
kubectl describe cronjob weekly-report
kubectl describe cronjob health-check

# Cleanup
kubectl delete -f schedule-examples.yaml
```

---

## Exercise 2: CronJob Configuration and Management (15 minutes)

Explore advanced CronJob features and management.

### Step 1: CronJob with Advanced Configuration

Create `advanced-cronjob.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-processor
  labels:
    app: data-processing
    environment: production
spec:
  # Run every 5 minutes
  schedule: "*/5 * * * *"
  
  # Keep last 3 successful jobs
  successfulJobsHistoryLimit: 3
  
  # Keep last 1 failed job for debugging
  failedJobsHistoryLimit: 1
  
  # Don't start new job if previous is still running
  concurrencyPolicy: Forbid
  
  # Allow 10 seconds delay before considering job as failed to start
  startingDeadlineSeconds: 10
  
  # Suspend the CronJob (useful for maintenance)
  suspend: false
  
  jobTemplate:
    metadata:
      labels:
        app: data-processing
        job-type: scheduled
    spec:
      # Job should complete within 4 minutes
      activeDeadlineSeconds: 240
      backoffLimit: 2
      template:
        metadata:
          labels:
            app: data-processing
        spec:
          containers:
          - name: processor
            image: python:3.11-alpine
            command:
            - python
            - -c
            - |
              import time
              import random
              import datetime
              
              print(f"Data processing started at {datetime.datetime.now()}")
              
              # Simulate data processing work
              datasets = ['users', 'orders', 'products', 'analytics']
              
              for dataset in datasets:
                  print(f"Processing {dataset} dataset...")
                  
                  # Simulate variable processing time
                  process_time = random.uniform(10, 30)
                  time.sleep(process_time)
                  
                  print(f"Completed {dataset} processing in {process_time:.2f}s")
              
              print(f"All data processing completed at {datetime.datetime.now()}")
            resources:
              requests:
                memory: "64Mi"
                cpu: "100m"
              limits:
                memory: "128Mi"
                cpu: "200m"
            env:
            - name: BATCH_SIZE
              value: "1000"
            - name: PROCESSING_MODE
              value: "incremental"
          restartPolicy: OnFailure
```

Test advanced features:
```bash
# Apply the advanced CronJob
kubectl apply -f advanced-cronjob.yaml

# Monitor CronJob and its jobs
kubectl get cronjobs data-processor -w

# Check jobs created (should see history limits in action)
kubectl get jobs -l app=data-processing

# View detailed CronJob information
kubectl describe cronjob data-processor

# Test suspension
kubectl patch cronjob data-processor -p '{"spec":{"suspend":true}}'

# Check status - should show as suspended
kubectl get cronjob data-processor

# Resume the CronJob
kubectl patch cronjob data-processor -p '{"spec":{"suspend":false}}'

# Cleanup
kubectl delete -f advanced-cronjob.yaml
```

### Step 2: CronJob with Concurrency Policies

Create `concurrency-test.yaml`:
```yaml
# Test Forbid policy
apiVersion: batch/v1
kind: CronJob
metadata:
  name: long-running-forbid
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: long-task
            image: busybox:1.35
            command:
            - sh
            - -c
            - |
              echo "Long task started at $(date)"
              sleep 180  # Sleep for 3 minutes (longer than schedule interval)
              echo "Long task completed at $(date)"
            resources:
              requests:
                memory: "16Mi"
                cpu: "25m"
          restartPolicy: OnFailure
---
# Test Allow policy
apiVersion: batch/v1
kind: CronJob
metadata:
  name: long-running-allow
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  concurrencyPolicy: Allow
  successfulJobsHistoryLimit: 5
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: concurrent-task
            image: busybox:1.35
            command:
            - sh
            - -c
            - |
              echo "Concurrent task $HOSTNAME started at $(date)"
              sleep 180  # Sleep for 3 minutes
              echo "Concurrent task $HOSTNAME completed at $(date)"
            resources:
              requests:
                memory: "16Mi"
                cpu: "25m"
          restartPolicy: OnFailure
---
# Test Replace policy
apiVersion: batch/v1
kind: CronJob
metadata:
  name: long-running-replace
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  concurrencyPolicy: Replace
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: replaceable-task
            image: busybox:1.35
            command:
            - sh
            - -c
            - |
              echo "Replaceable task $HOSTNAME started at $(date)"
              sleep 180  # Sleep for 3 minutes
              echo "Replaceable task $HOSTNAME completed at $(date)"
            resources:
              requests:
                memory: "16Mi"
                cpu: "25m"
          restartPolicy: OnFailure
```

Test concurrency policies:
```bash
# Apply all concurrency tests
kubectl apply -f concurrency-test.yaml

# Monitor jobs created by each CronJob
kubectl get jobs -l app=cronjob-name --show-labels

# Watch how different policies handle overlapping executions
kubectl get jobs -w

# After a few minutes, check the results
echo "=== Forbid Policy Results ==="
kubectl get jobs -l cronjob=long-running-forbid

echo "=== Allow Policy Results ==="
kubectl get jobs -l cronjob=long-running-allow

echo "=== Replace Policy Results ==="
kubectl get jobs -l cronjob=long-running-replace

# Cleanup
kubectl delete -f concurrency-test.yaml
```

---

## Exercise 3: Real-World CronJob Examples (5 minutes)

Create practical CronJob examples.

### Step 1: Database Backup CronJob

Create `database-backup.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: YWRtaW4=  # admin (base64)
  password: cGFzc3dvcmQ=  # password (base64)
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  # Daily at 2:30 AM
  schedule: "30 2 * * *"
  successfulJobsHistoryLimit: 7  # Keep one week of backups
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - sh
            - -c
            - |
              # Simulate database backup
              BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).sql"
              echo "Starting database backup: $BACKUP_FILE"
              
              # In real scenario, you would use:
              # pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_FILE
              
              echo "SELECT 'Backup completed at $(date)' as status;" > /tmp/$BACKUP_FILE
              echo "Backup file created: $BACKUP_FILE ($(wc -c < /tmp/$BACKUP_FILE) bytes)"
              
              # Upload to cloud storage (simulated)
              echo "Uploading backup to cloud storage..."
              sleep 5
              echo "Backup uploaded successfully"
            env:
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            resources:
              requests:
                memory: "128Mi"
                cpu: "100m"
              limits:
                memory: "256Mi"
                cpu: "200m"
          restartPolicy: OnFailure
```

### Step 2: Log Cleanup CronJob

Create `log-cleanup.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-cleanup
spec:
  # Run every Sunday at 3 AM
  schedule: "0 3 * * 0"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: busybox:1.35
            command:
            - sh
            - -c
            - |
              echo "Starting log cleanup at $(date)"
              
              # Simulate log cleanup
              LOG_DIRS="/var/log/app /var/log/nginx /var/log/system"
              
              for dir in $LOG_DIRS; do
                echo "Cleaning logs in $dir"
                
                # Find and "delete" logs older than 30 days
                echo "Finding logs older than 30 days in $dir..."
                
                # Simulate finding old files
                OLD_FILES=$((RANDOM % 20 + 5))
                FREED_SPACE=$((OLD_FILES * RANDOM % 1000 + 100))
                
                echo "Found $OLD_FILES old log files"
                echo "Freed ${FREED_SPACE}MB of disk space"
                
                sleep 2
              done
              
              echo "Log cleanup completed at $(date)"
            resources:
              requests:
                memory: "32Mi"
                cpu: "50m"
          restartPolicy: OnFailure
```

Test real-world examples:
```bash
# Apply database backup CronJob
kubectl apply -f database-backup.yaml

# Apply log cleanup CronJob
kubectl apply -f log-cleanup.yaml

# Check CronJobs
kubectl get cronjobs

# Manually trigger a job for testing
kubectl create job --from=cronjob/database-backup manual-backup-test

# Check the manual job
kubectl get jobs manual-backup-test
kubectl logs job/manual-backup-test

# Clean up manual job
kubectl delete job manual-backup-test

# Cleanup
kubectl delete -f database-backup.yaml
kubectl delete -f log-cleanup.yaml
```

---

## 🎯 Cron Schedule Reference

### Common Cron Expressions

```bash
# Every minute
"*/1 * * * *"

# Every 5 minutes
"*/5 * * * *"

# Every hour at minute 0
"0 * * * *"

# Every day at 2:30 AM
"30 2 * * *"

# Every Monday at 9 AM
"0 9 * * 1"

# Every weekday at 6 PM
"0 18 * * 1-5"

# First day of every month at midnight
"0 0 1 * *"

# Every 15 minutes during business hours (9 AM - 5 PM, Mon-Fri)
"*/15 9-17 * * 1-5"
```

### Cron Format
```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# │ │ │ │ │
# * * * * *
```

## 🔍 Management Commands

```bash
# List all CronJobs
kubectl get cronjobs

# Get detailed CronJob info
kubectl describe cronjob <name>

# Suspend a CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":true}}'

# Resume a CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":false}}'

# Manually create a job from CronJob
kubectl create job --from=cronjob/<cronjob-name> <job-name>

# Update CronJob schedule
kubectl patch cronjob <name> -p '{"spec":{"schedule":"0 2 * * *"}}'

# Delete old jobs
kubectl delete jobs --field-selector=status.successful=1

# View CronJob events
kubectl get events --field-selector involvedObject.name=<cronjob-name>
```

## 📝 Best Practices

1. **Set appropriate history limits** to prevent accumulation
2. **Use resource limits** to prevent resource exhaustion
3. **Handle timezone considerations** (CronJobs use cluster timezone)
4. **Choose appropriate concurrency policy** based on job characteristics
5. **Monitor failed jobs** and set up alerting
6. **Test with manual job creation** before relying on schedule
7. **Use startingDeadlineSeconds** for time-sensitive jobs

## 🎯 Key Takeaways

- CronJobs provide reliable job scheduling in Kubernetes
- Concurrency policies control overlapping job execution
- History limits prevent accumulation of completed jobs
- Manual job creation useful for testing CronJob templates
- Proper resource management essential for long-running scheduled jobs

## 📚 Additional Resources

- [CronJob Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Cron Expression Generator](https://crontab.guru/)
- [Time Zone Considerations](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/#time-zones)