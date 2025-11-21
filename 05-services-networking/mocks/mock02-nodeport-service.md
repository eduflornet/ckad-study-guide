# Mock Scenario 2: NodePort Service

**Scenario:**
A deployment named `api` is running in the `apps` namespace. Expose it externally using a NodePort service named `api-service` on port 8080. Ensure the service is accessible from outside the cluster.

**Requirements:**
- Service type: NodePort
- Service name: api-service
- Port: 8080
- Namespace: apps

**Questions:**
1. Write the YAML manifest for the NodePort service.
2. How do you find the assigned NodePort?
3. What command tests external access to the service?

**Expected Outcome:**
- Service is accessible via the NodePort on any cluster node IP.