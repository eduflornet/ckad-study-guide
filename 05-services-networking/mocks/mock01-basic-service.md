# Mock Scenario 1: Basic ClusterIP Service

**Scenario:**
You are given a deployment named `web` running in the `default` namespace. Your task is to expose it internally using a ClusterIP service named `web-service` on port 80. Verify that the service endpoints match the pod IPs.

**Requirements:**
- Service type: ClusterIP
- Service name: web-service
- Port: 80
- Namespace: default

**Questions:**
1. Write the YAML manifest for the service.
2. How do you verify the service endpoints?
3. What command lists all ClusterIP services in the namespace?

**Expected Outcome:**
- Service is created and endpoints are correct.
- You can list and describe the service using kubectl.