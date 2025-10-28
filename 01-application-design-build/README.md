# Application Design and Build (20%)

## 📚 Topics Covered

### Container Images
- Building Docker images
- Multi-stage builds
- Image optimization
- Security best practices

### Jobs and CronJobs
- Batch workloads
- Scheduled tasks
- Job patterns
- Cleanup policies

### Multi-Container Pods
- Sidecar pattern
- Init containers
- Container communication
- Shared volumes

## 🛠️ Practice Labs

### Lab 1: Container Images
- [Basic Dockerfile creation](labs/lab01-dockerfile-basics.md)
- [Multi-stage build optimization](labs/lab02-multistage-builds.md)
- [Security scanning and hardening](labs/lab03-image-security.md)

### Lab 2: Jobs and CronJobs
- [Simple batch job](labs/lab04-simple-job.md)
- [Parallel processing jobs](labs/lab05-parallel-jobs.md)
- [Scheduled maintenance tasks](labs/lab06-cronjobs.md)

### Lab 3: Multi-Container Pods
- [Sidecar logging container](labs/lab07-sidecar-logging.md)
- [Init container setup](labs/lab08-init-containers.md)
- [Shared volume communication](labs/lab09-shared-volumes.md)

## ⚡ Quick Drills

Practice these commands until you can execute them quickly:

```bash
# Create a simple job
kubectl create job hello --image=busybox -- echo "Hello World"

# Create a cronjob
kubectl create cronjob hello --image=busybox --schedule="*/1 * * * *" -- echo "Hello World"

# Multi-container pod
kubectl run multi-pod --image=nginx --dry-run=client -o yaml > multi-pod.yaml
# Edit to add sidecar container

# Check job status
kubectl get jobs
kubectl describe job hello
kubectl logs job/hello
```

## 🎯 Mock Scenarios

- [Mock 1: Containerize a Node.js application](mocks/mock01-nodejs-containerization.md)
- [Mock 2: Create a data processing job](mocks/mock02-data-processing-job.md)
- [Mock 3: Implement logging sidecar](mocks/mock03-logging-sidecar.md)

## 🔑 Key Concepts to Master

- [ ] Write efficient Dockerfiles
- [ ] Understand init containers vs sidecar containers
- [ ] Configure job completion and failure policies
- [ ] Implement proper resource limits
- [ ] Use volume mounts between containers
- [ ] Debug multi-container pod issues

## 📝 Common Exam Tasks

1. "Create a Job that runs 5 parallel workers"
2. "Add an init container that downloads configuration"
3. "Create a CronJob that runs daily at 2 AM"
4. "Build a multi-stage Docker image"
5. "Add a sidecar container for log processing"