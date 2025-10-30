# CKAD Study Guide & Mock Exam Practice

A comprehensive study guide focused on passing the **Certified Kubernetes Application Developer (CKAD)** exam through hands-on practice and realistic mock scenarios.

## 📋 Exam Overview

- **Duration**: 2 hours (120 minutes)
- **Questions**: 15-20 hands-on performance-based tasks
- **Passing Score**: 66%
- **Kubernetes Version**: v1.30
- **Environment**: Browser-based terminal with kubectl and text editors
- **Allowed Resources**: Kubernetes documentation, kubectl help, man pages

## 📚 Table of Contents

1. [Official CKAD Curriculum v1.34](#-official-ckad-curriculum-v134)
2. [Quick Start](#-quick-start)
3. [Study Approach](#study-approach)
4. [Repository Structure](#-repository-structure)
5. [Study Timeline](#️-study-timeline-4-6-weeks)
6. [Mock Exam Strategy](#-mock-exam-strategy)
7. [Essential kubectl Commands](#essential-kubectl-commands)
8. [Success Metrics](#-success-metrics)
9. [Additional Resources](#-additional-resources)

## 🎯 Official CKAD Curriculum v1.34

Based on the official CNCF CKAD Curriculum v1.34, the exam covers these domains:

### [Application Design and Build (20%)](/01-application-design-build/)
- **Define, build and modify container images**
  - Understand and use FROM, RUN, CMD, and ENTRYPOINT
  - Understand and use COPY and ADD
  - Understand and use WORKDIR and USER
  - Understand security concerns
  - Create minimalist images

- **Choose and use the right workload resource**
  - Understand when to use Deployments vs DaemonSets vs StatefulSets vs Jobs
  - Know when to use a pod vs a workload resource

- **Understand multi-container Pod design patterns**
  - Ambassador, adapter, sidecar patterns
  - Shared volumes between containers
  - Init containers

### [Application Deployment (20%)](/02-application-deployment/)
- **Use Kubernetes primitives to implement common deployment strategies**
  - Blue/green deployments
  - Rolling updates and rollbacks
  - Canary deployments

- **Understand Deployments and how to perform rolling updates**
  - Managing Deployment history
  - Rollback strategies
  - Scaling applications

- **Use the Helm package manager to deploy existing packages**
  - Install, upgrade, and uninstall charts
  - Understand chart structure
  - Use values and templates

### [Application Observability and Maintenance (15%)](/03-observability-maintenance/)
- **Understand API deprecations**
  - Know how to migrate APIs
  - Use kubectl convert
  - Understand deprecation timeline

- **Implement probes and health checks**
  - Liveness, readiness, and startup probes
  - Configure probe parameters
  - Understand probe types (HTTP, TCP, exec)

- **Use built-in CLI tools to monitor Kubernetes applications**
  - kubectl top, logs, describe
  - Monitor resource usage
  - Debug application issues

- **Utilize container logs**
  - Access logs for containers
  - Understand logging architecture
  - Debug based on logs

### [Application Environment, Configuration and Security (25%)](/04-environment-config-security/)
- **Discover and use resources that extend Kubernetes (CRD)**
  - Understand Custom Resource Definitions
  - Work with custom resources
  - Use kubectl with CRDs

- **Understand authentication, authorization and admission control**
  - ServiceAccounts and tokens
  - RBAC (Role-Based Access Control)
  - Understand admission controllers

- **Understand and define resource requirements, limits and quotas**
  - Resource requests and limits
  - ResourceQuotas and LimitRanges
  - Quality of Service classes

- **Understand ConfigMaps and Secrets**
  - Create and consume ConfigMaps
  - Create and consume Secrets
  - Mount as volumes or environment variables

- **Create & consume Secrets**
  - Understand Secret types
  - Use Secrets securely
  - Best practices for Secret management

- **Understand SecurityContexts**
  - Pod and container security contexts
  - runAsUser, runAsGroup, fsGroup
  - Security capabilities and privileges

### [Services and Networking (20%)](/05-services-networking/)
- **Demonstrate basic understanding of NetworkPolicies**
  - Create ingress and egress rules
  - Understand pod-to-pod communication
  - Namespace isolation

- **Provide and troubleshoot access to applications via services**
  - ClusterIP, NodePort, LoadBalancer, ExternalName
  - Endpoints and EndpointSlices
  - Service discovery

- **Use Ingress rules to expose applications**
  - Create Ingress resources
  - Path-based and host-based routing
  - TLS termination
  - Ingress controllers

## 🚀 Quick Start

### Prerequisites
- Basic Kubernetes knowledge
- Docker fundamentals
- kubectl CLI experience
- YAML syntax familiarity

### Study Approach
1. **📚 Learn Theory** - Study each domain's concepts and best practices
2. **🛠️ Practice Labs** - Hands-on exercises for each topic
3. **⚡ Quick Drills** - Fast-paced kubectl commands and YAML creation
4. **🎯 Mock Exams** - Realistic timed practice scenarios
5. **🔍 Review & Debug** - Analyze mistakes and strengthen weak areas

## 📁 Repository Structure

```
ckad-study-guide/
├── 01-application-design-build/          # 20% - Images, Jobs, Multi-containers
├── 02-application-deployment/            # 20% - Deployments, Updates, Helm
├── 03-observability-maintenance/         # 15% - Monitoring, Probes, Debugging
├── 04-environment-config-security/       # 25% - Config, Secrets, RBAC
├── 05-services-networking/               # 20% - Services, Ingress, NetPol
├── mock-exams/                          # Full practice exam scenarios
├── quick-reference/                     # Cheatsheets and templates
├── setup/                              # Environment setup scripts
└── solutions/                          # Detailed solutions and explanations
```

## ⏱️ Study Timeline (4-6 weeks)

### Week 1-2: Foundation & Core Concepts
- Application Design and Build
- Application Deployment
- Basic kubectl proficiency

### Week 3-4: Advanced Topics
- Environment, Configuration & Security
- Services and Networking
- Observability and Maintenance

### Week 5-6: Mock Exams & Review
- Daily mock exam practice
- Identify and fix knowledge gaps
- Speed and accuracy improvement

## 🎯 Mock Exam Strategy

### Time Management Tips
- **Read carefully**: Understand requirements before starting
- **Use shortcuts**: Leverage kubectl generators and aliases
- **Practice typing**: Fast YAML creation is crucial
- **Skip and return**: Don't get stuck on difficult questions
- **Verify solutions**: Always test your deployments

### Question Types by Domain
1. **Application Design & Build (20%)**
   - Container image creation and optimization
   - Multi-container pod patterns (sidecar, init containers)
   - Workload resource selection (Pods, Deployments, Jobs)

2. **Application Deployment (20%)**
   - Rolling updates and rollbacks
   - Deployment strategies (blue/green, canary)
   - Helm chart deployment and management

3. **Observability & Maintenance (15%)**
   - Health probes configuration
   - Application monitoring and logging
   - API deprecation handling

4. **Environment & Security (25%)**
   - ConfigMaps and Secrets management
   - RBAC and ServiceAccounts
   - SecurityContexts and resource quotas
   - Custom Resource Definitions (CRDs)

5. **Services & Networking (20%)**
   - Service types and endpoints
   - Ingress configuration
   - NetworkPolicies implementation

### Essential kubectl Commands
```bash
# Quick pod creation
kubectl run nginx --image=nginx --restart=Never

# Generate YAML templates
kubectl create deployment web --image=nginx --dry-run=client -o yaml

# Fast resource inspection
kubectl get pods -o wide
kubectl describe pod <pod-name>
kubectl logs <pod-name> -c <container>

# Debugging
kubectl exec -it <pod> -- /bin/bash
kubectl port-forward <pod> 8080:80
```

## 📚 Additional Resources

- [Official CKAD Curriculum](https://github.com/cncf/curriculum)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Github CKAD | TechLynk Selenium](https://github.com/anshulc55/CKAD.git)


## 🎯 Success Metrics

- [ ] Complete all domain practice exercises
- [ ] Score 80%+ on mock exams consistently
- [ ] Solve any YAML creation task under 2 minutes
- [ ] Debug failing pods within 3 minutes
- [ ] Create Services and Ingress resources efficiently

---

*Good luck with your CKAD certification journey! Remember: practice makes perfect.* 🚀
