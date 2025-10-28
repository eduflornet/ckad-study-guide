# Mock Exam 1 - Foundation Level

**Time Limit**: 90 minutes  
**Questions**: 15  
**Passing Score**: 10/15 (67%)  
**Difficulty**: Beginner to Intermediate

---

## Instructions

1. Use namespace `exam` for all resources unless specified otherwise
2. Ensure all pods are running and functional
3. Test your solutions before moving to the next question
4. You may use `kubectl` generators and documentation

### Setup
```bash
kubectl create namespace exam
kubectl config set-context --current --namespace=exam
```

---

## Question 1 (5 points) - Pod Creation
**Domain**: Application Design and Build

Create a pod named `web-server` with the following specifications:
- Image: `nginx:1.20`
- Label: `app=web`
- Container port: 80
- Resource limits: CPU 500m, Memory 512Mi

<details>
<summary>Solution Approach</summary>

```bash
kubectl run web-server --image=nginx:1.20 --port=80 --dry-run=client -o yaml > web-server.yaml
```

Edit the YAML to add labels and resource limits.
</details>

---

## Question 2 (6 points) - ConfigMap and Environment Variables
**Domain**: Environment, Configuration and Security

1. Create a ConfigMap named `app-config` with the following data:
   - `database_url=postgresql://localhost:5432/mydb`
   - `debug_mode=true`
   - `max_connections=100`

2. Create a pod named `config-pod` using image `busybox:1.35` that:
   - Uses the ConfigMap as environment variables
   - Runs the command: `sleep 3600`
   - Verify the environment variables are set correctly

<details>
<summary>Solution Approach</summary>

```bash
kubectl create configmap app-config --from-literal=database_url=postgresql://localhost:5432/mydb --from-literal=debug_mode=true --from-literal=max_connections=100

kubectl run config-pod --image=busybox:1.35 --command -- sleep 3600 --dry-run=client -o yaml > config-pod.yaml
```

Edit to add `envFrom` configuration.
</details>

---

## Question 3 (8 points) - Deployment and Scaling
**Domain**: Application Deployment

1. Create a deployment named `api-server` with:
   - Image: `httpd:2.4`
   - 3 replicas
   - Label: `tier=backend`

2. Scale the deployment to 5 replicas

3. Update the image to `httpd:2.4.54`

4. Check the rollout status and history

<details>
<summary>Solution Approach</summary>

```bash
kubectl create deployment api-server --image=httpd:2.4 --replicas=3
kubectl label deployment api-server tier=backend
kubectl scale deployment api-server --replicas=5
kubectl set image deployment/api-server httpd=httpd:2.4.54
kubectl rollout status deployment/api-server
kubectl rollout history deployment/api-server
```
</details>

---

## Question 4 (7 points) - Service Creation
**Domain**: Services and Networking

1. Create a ClusterIP service named `web-service` that:
   - Selects pods with label `app=web`
   - Exposes port 80
   - Target port 80

2. Test the service by creating a temporary pod and accessing the service

<details>
<summary>Solution Approach</summary>

```bash
kubectl expose pod web-server --name=web-service --port=80 --target-port=80
kubectl run test-pod --image=busybox:1.35 -it --rm -- wget -qO- web-service
```
</details>

---

## Question 5 (6 points) - Job Creation
**Domain**: Application Design and Build

Create a Job named `data-processor` with:
- Image: `busybox:1.35`
- Command: `echo "Processing data..." && sleep 30 && echo "Done!"`
- Should complete successfully once
- Job should be deleted automatically after completion (TTL: 30 seconds)

<details>
<summary>Solution Approach</summary>

```bash
kubectl create job data-processor --image=busybox:1.35 -- sh -c 'echo "Processing data..." && sleep 30 && echo "Done!"'
```

Edit YAML to add `ttlSecondsAfterFinished: 30`.
</details>

---

## Question 6 (8 points) - Secret and Volume Mount
**Domain**: Environment, Configuration and Security

1. Create a Secret named `db-credentials` with:
   - `username=admin`
   - `password=secret123`

2. Create a pod named `database-client` with:
   - Image: `postgres:13`
   - Mount the secret as volume at `/etc/db-creds`
   - Environment variables from secret: `POSTGRES_USER` and `POSTGRES_PASSWORD`

<details>
<summary>Solution Approach</summary>

```bash
kubectl create secret generic db-credentials --from-literal=username=admin --from-literal=password=secret123
kubectl run database-client --image=postgres:13 --dry-run=client -o yaml > database-client.yaml
```

Edit YAML to add volume mount and environment variables.
</details>

---

## Question 7 (7 points) - Multi-Container Pod
**Domain**: Application Design and Build

Create a pod named `app-stack` with two containers:

**Container 1**: `web-app`
- Image: `nginx:1.20`
- Port: 80

**Container 2**: `log-processor`
- Image: `busybox:1.35`
- Command: `tail -f /var/log/nginx/access.log`
- Shared volume: Mount `/var/log/nginx` from web-app

<details>
<summary>Solution Approach</summary>

```bash
kubectl run app-stack --image=nginx:1.20 --dry-run=client -o yaml > app-stack.yaml
```

Edit YAML to add second container and shared volume.
</details>

---

## Question 8 (6 points) - Liveness and Readiness Probes
**Domain**: Application Observability and Maintenance

Create a pod named `health-check-app` with:
- Image: `nginx:1.20`
- Liveness probe: HTTP GET on port 80, path `/`
- Readiness probe: HTTP GET on port 80, path `/`
- Initial delay: 10 seconds for both probes
- Period: 5 seconds for both probes

<details>
<summary>Solution Approach</summary>

```bash
kubectl run health-check-app --image=nginx:1.20 --dry-run=client -o yaml > health-check-app.yaml
```

Edit YAML to add liveness and readiness probes.
</details>

---

## Question 9 (7 points) - NodePort Service and Ingress
**Domain**: Services and Networking

1. Create a NodePort service named `external-web` for the `web-server` pod
   - Port: 80
   - NodePort: 30080

2. Create an Ingress named `web-ingress` that:
   - Routes traffic from `myapp.local` to the `web-service`
   - Uses path `/app`

<details>
<summary>Solution Approach</summary>

```bash
kubectl expose pod web-server --name=external-web --type=NodePort --port=80 --target-port=80
kubectl create ingress web-ingress --rule="myapp.local/app*=web-service:80"
```
</details>

---

## Question 10 (8 points) - CronJob
**Domain**: Application Design and Build

Create a CronJob named `backup-job` that:
- Runs every day at 2:00 AM
- Image: `busybox:1.35`
- Command: `echo "Backup started at $(date)" && sleep 60 && echo "Backup completed"`
- Keep 3 successful jobs and 1 failed job in history

<details>
<summary>Solution Approach</summary>

```bash
kubectl create cronjob backup-job --image=busybox:1.35 --schedule="0 2 * * *" -- sh -c 'echo "Backup started at $(date)" && sleep 60 && echo "Backup completed"'
```

Edit YAML to add job history limits.
</details>

---

## Question 11 (6 points) - Resource Limits and Requests
**Domain**: Environment, Configuration and Security

Update the `api-server` deployment to have:
- CPU request: 100m, CPU limit: 500m
- Memory request: 128Mi, Memory limit: 512Mi
- Verify the changes are applied

<details>
<summary>Solution Approach</summary>

```bash
kubectl set resources deployment api-server --requests=cpu=100m,memory=128Mi --limits=cpu=500m,memory=512Mi
kubectl describe deployment api-server
```
</details>

---

## Question 12 (7 points) - Network Policy
**Domain**: Services and Networking

Create a NetworkPolicy named `deny-all` that:
- Denies all ingress traffic to pods with label `tier=backend`
- Allows ingress traffic only from pods with label `tier=frontend`
- Applies to the current namespace

<details>
<summary>Solution Approach</summary>

Create a YAML file with NetworkPolicy specification using pod selectors and ingress rules.
</details>

---

## Question 13 (6 points) - Init Container
**Domain**: Application Design and Build

Create a pod named `init-demo` with:

**Init Container**:
- Name: `init-setup`
- Image: `busybox:1.35`
- Command: `echo "Initializing..." && sleep 10 && echo "Setup complete"`

**Main Container**:
- Name: `main-app`
- Image: `nginx:1.20`
- Should start only after init container completes

<details>
<summary>Solution Approach</summary>

```bash
kubectl run init-demo --image=nginx:1.20 --dry-run=client -o yaml > init-demo.yaml
```

Edit YAML to add init container specification.
</details>

---

## Question 14 (8 points) - Troubleshooting
**Domain**: Application Observability and Maintenance

A pod named `broken-app` exists but is not running properly:

1. Identify why the pod is failing
2. Check the logs and events
3. Fix the issue by updating the pod configuration
4. Ensure the pod runs successfully

**Note**: You may need to create this broken pod first for practice.

<details>
<summary>Solution Approach</summary>

```bash
kubectl describe pod broken-app
kubectl logs broken-app
kubectl get events --sort-by=.metadata.creationTimestamp
```

Common issues: image pull errors, resource limits, incorrect commands.
</details>

---

## Question 15 (7 points) - Persistent Volume Claim
**Domain**: Application Design and Build

1. Create a PersistentVolumeClaim named `app-storage` with:
   - Storage: 1Gi
   - Access mode: ReadWriteOnce
   - Storage class: default (or available storage class)

2. Create a pod named `storage-pod` that:
   - Uses the PVC mounted at `/data`
   - Image: `busybox:1.35`
   - Command: `sleep 3600`

<details>
<summary>Solution Approach</summary>

```yaml
# Create PVC YAML and pod YAML with volume mount
```
</details>

---

## Scoring

| Score Range | Grade | Comments |
|-------------|-------|----------|
| 90-100 | Excellent | Ready for CKAD exam |
| 80-89 | Good | Minor areas to improve |
| 67-79 | Pass | Need more practice on weak areas |
| Below 67 | Needs Work | Significant practice required |

## Next Steps

1. Review incorrect answers in the [solutions](../solutions/mock-exam-01-solutions.md)
2. Practice weak domain areas
3. Attempt [Mock Exam 2](mock-exam-02.md) when ready
4. Focus on speed and accuracy for exam preparation