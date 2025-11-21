# Mock Scenario 3: Ingress Path-Based Routing

**Scenario:**
You have two services, `app1` and `app2`, running in the `web` namespace. Configure an Ingress resource to route `/app1` to `app1` and `/app2` to `app2`. Use the hostname `web.local`.

**Requirements:**
- Ingress resource with path-based rules
- Host: web.local
- Paths: /app1 → app1, /app2 → app2
- Namespace: web

**Questions:**
1. Write the YAML manifest for the Ingress resource.
2. How do you test the routing from within the cluster?
3. What command lists all Ingress resources in the namespace?

**Expected Outcome:**
- Requests to `/app1` and `/app2` are routed to the correct services.