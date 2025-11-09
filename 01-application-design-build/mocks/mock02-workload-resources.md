# Mock Exam: Workload Resources

**Domain**: Application Design and Build (20%)  
**Topic**: Choose and use the right workload resource  
**Time Limit**: 40 minutes  
**Questions**: 5  

---

## [Question 1: Pod vs Deployment Decision (8 minutes)](/01-application-design-build/mocks/mock-exam-02/q01/)
**Points**: 20%

You need to deploy different types of applications. For each scenario, choose the appropriate workload resource and justify your choice:

**Scenarios**:

1. **Database Instance**: A single PostgreSQL database that needs persistent storage and should not be automatically restarted if it fails due to data corruption.

2. **Web Application**: A stateless web service that needs to handle varying traffic loads and requires high availability.

3. **Log Processor**: A service that processes log files once and exits. If it fails, it should retry up to 3 times.

4. **Monitoring Agent**: A system monitoring tool that must run on every worker node in the cluster.

5. **Session Store**: A Redis cache that maintains client session data and requires ordered startup/shutdown.

**Tasks**:
1. Create YAML manifests for each scenario in `/tmp/workloads/`
2. Name the files: `database.yaml`, `webapp.yaml`, `processor.yaml`, `monitor.yaml`, `cache.yaml`
3. Include a comment at the top of each file explaining your choice

**Requirements**:
- Use appropriate resource types
- Include proper resource limits where applicable
- Consider scaling and availability requirements

---

## [Question 2: Job Configuration (8 minutes)](/01-application-design-build/mocks/mock-exam-02/q02/)
**Points**: 18%

Create a Job that processes a batch of data with these requirements:

**Job Specifications**:
- Name: `data-processor`
- Namespace: `batch-processing`
- Image: `busybox:1.35`
- Command: `["sh", "-c", "for i in $(seq 1 100); do echo Processing item $i; sleep 0.1; done; echo Batch complete"]`

**Configuration Requirements**:
1. **Parallelism**: Run 3 pods simultaneously
2. **Completions**: Process 5 total batches
3. **Retry Policy**: Retry failed pods up to 2 times
4. **TTL**: Clean up completed job after 300 seconds
5. **Active Deadline**: Job must complete within 10 minutes
6. **Resource Limits**: 100m CPU, 128Mi memory per pod

**Tasks**:
1. Create the namespace `batch-processing`
2. Create and apply the Job manifest
3. Monitor the job until completion
4. Verify all 5 completions were successful

**Save YAML as**: `/tmp/batch-job.yaml`

---

## [Question 3: StatefulSet vs Deployment (10 minutes)](/01-application-design-build/mocks/mock-exam-02/q03/)
**Points**: 22%

Deploy two different applications to demonstrate the difference between StatefulSet and Deployment:

### Part A: Stateless Web App (Deployment)
Create a Deployment for a stateless web application:
- Name: `web-frontend`
- Image: `nginx:1.24-alpine`
- Replicas: 3
- Rolling update strategy: max 1 unavailable, max 1 surge
- Resource requests: 50m CPU, 64Mi memory

### Part B: Stateful Database (StatefulSet)
Create a StatefulSet for a database:
- Name: `database-cluster`
- Image: `postgres:15-alpine`
- Replicas: 3
- Service name: `database-svc`
- Environment: `POSTGRES_DB=testdb`, `POSTGRES_USER=testuser`, `POSTGRES_PASSWORD=testpass`
- Persistent storage: 1Gi per pod using `ReadWriteOnce`
- Resource requests: 200m CPU, 256Mi memory

**Tasks**:
1. Create both manifests in `/tmp/stateful-vs-stateless/`
2. Apply both resources
3. Scale the Deployment to 5 replicas
4. Scale the StatefulSet to 5 replicas
5. Observe the differences in pod naming and startup order
6. Document your observations in `/tmp/observations.txt`

---

## [Question 4: DaemonSet Implementation (8 minutes)](/01-application-design-build/mocks/mock-exam-02/q04/)
**Points**: 18%

Create a DaemonSet for a logging agent that must run on every node:

**DaemonSet Specifications**:
- Name: `log-collector`
- Namespace: `kube-system`
- Image: `fluent/fluent-bit:2.1`

**Node Requirements**:
- Run on all nodes including master/control plane
- Use node selector to target nodes with label `logging=enabled`
- Tolerate master node taints

**Configuration**:
- Mount host `/var/log` to container `/host/var/log` (read-only)
- Mount host `/var/lib/docker/containers` to `/host/var/lib/docker/containers` (read-only)
- Resource limits: 100m CPU, 128Mi memory
- Resource requests: 50m CPU, 64Mi memory
- Run as privileged container

**Tasks**:
1. Label required nodes with `logging=enabled`
2. Create and apply the DaemonSet
3. Verify pods are running on expected nodes
4. Check that pods have access to host logs

**Save YAML as**: `/tmp/logging-daemonset.yaml`

---

## [Question 5: Workload Resource Troubleshooting (6 minutes)](/01-application-design-build/mocks/mock-exam-02/q05/)
**Points**: 22%

You have several problematic workload resources. Identify and fix the issues:

### Problem 1: Failing Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: broken-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox:1.35
        command: ["sh", "-c", "exit 1"]
      restartPolicy: Always
  completions: 3
  parallelism: 2
```

### Problem 2: Stuck Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stuck-deployment
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.24
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
```

### Problem 3: DaemonSet Not Scheduling
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-agent
spec:
  selector:
    matchLabels:
      app: agent
  template:
    spec:
      containers:
      - name: agent
        image: monitoring-agent:latest
      nodeSelector:
        node-type: compute
```

**Tasks**:
1. Apply each resource and observe the problems
2. Fix all issues and create corrected versions
3. Save corrected YAML files in `/tmp/fixed/`
4. Document what was wrong and how you fixed it in `/tmp/fixes.txt`

---

## Answer Key & Solutions

### Question 1: Pod vs Deployment Decision

<details>
<summary>Solution</summary>

**database.yaml**:
```yaml
# Using Pod for database - single instance, manual control over lifecycle
apiVersion: v1
kind: Pod
metadata:
  name: postgres-db
  labels:
    app: database
spec:
  containers:
  - name: postgres
    image: postgres:15-alpine
    env:
    - name: POSTGRES_DB
      value: "mydb"
    - name: POSTGRES_USER
      value: "dbuser"
    - name: POSTGRES_PASSWORD
      value: "dbpass"
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: data
    emptyDir: {}
  restartPolicy: Never
```

**webapp.yaml**:
```yaml
# Using Deployment for web app - needs scaling and high availability
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
```

**processor.yaml**:
```yaml
# Using Job for one-time processing task with retry logic
apiVersion: batch/v1
kind: Job
metadata:
  name: log-processor
spec:
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command: ["sh", "-c", "echo Processing logs; sleep 30; echo Done"]
      restartPolicy: Never
```

**monitor.yaml**:
```yaml
# Using DaemonSet for monitoring agent - needs to run on every node
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: monitor
  template:
    metadata:
      labels:
        app: monitor
    spec:
      containers:
      - name: monitor
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        hostNetwork: true
        hostPID: true
```

**cache.yaml**:
```yaml
# Using StatefulSet for Redis cache - needs ordered startup and persistent identity
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cache
spec:
  serviceName: redis-svc
  replicas: 3
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
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```
</details>

### Question 2: Job Configuration

<details>
<summary>Solution</summary>

```bash
# Create namespace
kubectl create namespace batch-processing

# Create Job
cat > /tmp/batch-job.yaml << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processor
  namespace: batch-processing
spec:
  parallelism: 3
  completions: 5
  backoffLimit: 2
  ttlSecondsAfterFinished: 300
  activeDeadlineSeconds: 600
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command: ["sh", "-c", "for i in \$(seq 1 100); do echo Processing item \$i; sleep 0.1; done; echo Batch complete"]
        resources:
          limits:
            cpu: "100m"
            memory: "128Mi"
      restartPolicy: Never
EOF

kubectl apply -f /tmp/batch-job.yaml

# Monitor job
kubectl get jobs -n batch-processing -w
```
</details>

### Question 3: StatefulSet vs Deployment

<details>
<summary>Solution</summary>

**web-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
```

**database-statefulset.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: database-svc
spec:
  clusterIP: None
  selector:
    app: database
  ports:
  - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database-cluster
spec:
  serviceName: database-svc
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "testdb"
        - name: POSTGRES_USER
          value: "testuser"
        - name: POSTGRES_PASSWORD
          value: "testpass"
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

**Observations**:
- Deployment pods have random suffixes (web-frontend-abc123-xyz)
- StatefulSet pods have ordinal suffixes (database-cluster-0, database-cluster-1, database-cluster-2)
- StatefulSet pods start up sequentially (0, then 1, then 2)
- Deployment pods start up simultaneously
- StatefulSet maintains persistent storage per pod
</details>

### Question 4: DaemonSet Implementation

<details>
<summary>Solution</summary>

```bash
# Label nodes
kubectl label nodes --all logging=enabled

# Create DaemonSet
cat > /tmp/logging-daemonset.yaml << EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      nodeSelector:
        logging: enabled
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.1
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
        securityContext:
          privileged: true
        volumeMounts:
        - name: varlog
          mountPath: /host/var/log
          readOnly: true
        - name: dockerlogs
          mountPath: /host/var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: dockerlogs
        hostPath:
          path: /var/lib/docker/containers
EOF

kubectl apply -f /tmp/logging-daemonset.yaml
```
</details>

### Question 5: Workload Resource Troubleshooting

<details>
<summary>Solution</summary>

**Fixed Job** (`/tmp/fixed/job.yaml`):
```yaml
# Issue: restartPolicy should be Never or OnFailure for Jobs, not Always
apiVersion: batch/v1
kind: Job
metadata:
  name: fixed-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox:1.35
        command: ["sh", "-c", "echo 'Success'; exit 0"]  # Fixed exit code
      restartPolicy: Never  # Fixed restart policy
  completions: 3
  parallelism: 2
  backoffLimit: 3  # Added retry limit
```

**Fixed Deployment** (`/tmp/fixed/deployment.yaml`):
```yaml
# Issue: Missing selector and high resource requests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fixed-deployment
spec:
  replicas: 3
  selector:  # Added missing selector
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.24
        resources:
          requests:
            memory: "64Mi"    # Reduced memory
            cpu: "50m"        # Reduced CPU
          limits:
            memory: "128Mi"
            cpu: "100m"
```

**Fixed DaemonSet** (`/tmp/fixed/daemonset.yaml`):
```yaml
# Issue: Missing selector labels in template and using :latest tag
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fixed-node-agent
spec:
  selector:
    matchLabels:
      app: agent
  template:
    metadata:
      labels:
        app: agent  # Added missing labels
    spec:
      containers:
      - name: agent
        image: monitoring-agent:v1.0  # Fixed image tag
      nodeSelector:
        node-type: compute
```

**fixes.txt**:
```
Problem 1 - Job Issues:
- restartPolicy was "Always" but Jobs require "Never" or "OnFailure"
- Command was failing (exit 1), changed to successful command
- Added backoffLimit for retry attempts

Problem 2 - Deployment Issues:
- Missing selector field that matches template labels
- Resource requests too high (2Gi memory, 1000m CPU) causing scheduling issues
- Reduced to reasonable values (64Mi memory, 50m CPU)

Problem 3 - DaemonSet Issues:
- Template metadata was missing labels that match selector
- Using :latest tag which is not recommended
- Fixed by adding proper labels and specific version tag
```
</details>

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 90-100% | All workload types correctly chosen and implemented with proper configurations |
| 80-89% | Good understanding of workload types, minor configuration issues |
| 70-79% | Basic concepts correct, some confusion between resource types |
| 60-69% | Limited understanding, needs more practice with workload selection |
| Below 60% | Poor understanding of Kubernetes workload resources |

## Key Learning Objectives

After completing this mock exam, you should understand:

1. **When to use each workload resource type**
2. **Job configuration for batch processing**
3. **Differences between StatefulSet and Deployment**
4. **DaemonSet implementation for node-level services**
5. **Common troubleshooting scenarios**

## Common Mistakes to Avoid

1. **Using Deployment for stateful applications**
2. **Wrong restartPolicy for Jobs** (Never/OnFailure, not Always)
3. **Missing selectors** in Deployment/StatefulSet specs
4. **Excessive resource requests** causing scheduling issues
5. **Using `:latest` tags** in production manifests